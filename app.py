import sqlite3
import random
import os
from flask import Flask, jsonify, session, request, send_from_directory
from flask_cors import CORS

# Modificação Definitiva: Configura o Flask para servir ficheiros estáticos
# a partir do diretório raiz do projeto. Esta é a forma mais robusta.
app = Flask(__name__, static_folder='.', static_url_path='')

# Chave secreta para gerir as sessões de utilizador.
# Numa aplicação real, esta chave deve ser mais segura e não deve ser partilhada.
app.config['SECRET_KEY'] = 'a_chave_secreta_super_dificil_de_adivinhar'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Configuração do CORS para permitir pedidos do frontend.
# O supports_credentials=True é essencial para que a sessão funcione.
CORS(app, supports_credentials=True)

DATABASE_FILE = 'eternaldle.db'

# --- Lógica de Criação da Base de Dados (para garantir que existe) ---
# Esta parte agora é mais para desenvolvimento local, o Render usará o "Build Command".
def create_database_if_not_exists():
    """Verifica se o ficheiro da base de dados existe e, se não, cria-o."""
    if not os.path.exists(DATABASE_FILE):
        print(f"O ficheiro da base de dados '{DATABASE_FILE}' não foi encontrado. Por favor, execute 'python setup_database.py' para o criar.")
        # O ideal é não criar automaticamente aqui para manter o servidor focado em servir.
        # A criação deve ser um passo de "build" ou configuração inicial.

# --- Carregamento de Dados ---
def get_all_characters():
    """Busca todos os dados dos personagens da base de dados SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # Permite aceder às colunas pelo nome
        cur = conn.cursor()
        cur.execute("SELECT * FROM eternaldle")
        characters_raw = cur.fetchall()
        conn.close()

        # Converte os resultados para uma lista de dicionários
        characters_clean = [dict(row) for row in characters_raw]
        
        # VERIFICAÇÃO DE DADOS (para depuração)
        print("\n--- VERIFICAÇÃO DE DADOS CARREGADOS ---")
        abigail_data = next((char for char in characters_clean if char['NOME'] == 'Abigail'), None)
        if abigail_data:
            print(f"Dados da Abigail: {abigail_data}")
        else:
            print("Personagem Abigail não encontrada na base de dados.")
        print("--------------------------------------\n")

        return characters_clean
    except sqlite3.OperationalError as e:
        print(f"ERRO DE BASE DE DADOS: {e}. Verifique se o ficheiro '{DATABASE_FILE}' existe e tem a tabela 'eternaldle'.")
        print("Execute 'python setup_database.py' para criar a base de dados.")
        return None

# --- Rotas da Aplicação ---

# Rota para servir o ficheiro index.html (PÁGINA PRINCIPAL)
@app.route('/')
def serve_index():
    """Serve a página principal do jogo."""
    # Com a nova configuração do Flask, esta é a forma correta de enviar o ficheiro.
    return app.send_static_file('index.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Inicia um novo jogo, escolhendo um personagem aleatório como solução."""
    all_characters = get_all_characters()
    if all_characters is None:
        return jsonify({'error': 'Falha ao carregar os dados dos personagens. Verifique os logs do servidor.'}), 500

    # Adicionada verificação para o caso de a base de dados estar vazia
    if not all_characters:
        print("ERRO: A base de dados de personagens está vazia. O comando de build pode ter falhado.")
        return jsonify({'error': 'A base de dados de personagens está vazia. Verifique a configuração do deploy.'}), 500

    solution_character = random.choice(all_characters)
    session['solution'] = dict(solution_character)
    
    print(f"O jogo começou. Solução é: {session['solution']['NOME']}")

    character_names = [char['NOME'] for char in all_characters]
    return jsonify({'characterNames': character_names})

@app.route('/api/guess', methods=['POST'])
def handle_guess():
    """Lida com o palpite de um utilizador e retorna a comparação detalhada."""
    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    
    # Verifica se a sessão e a solução existem
    if 'solution' not in session:
        print("ERRO: Tentativa de palpite sem um jogo iniciado na sessão.")
        return jsonify({'error': 'O jogo não foi iniciado. Por favor, atualize a página.'}), 400

    solution = session['solution']
    
    all_characters = get_all_characters()
    if all_characters is None:
        return jsonify({'error': 'Falha ao recarregar os dados dos personagens.'}), 500
        
    guess_character = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)

    if not guess_character:
        return jsonify({'error': 'Personagem não encontrado.'}), 404

    # --- Lógica de Comparação ---
    results = {}
    is_correct = (guess_character['NOME'].lower() == solution['NOME'].lower())

    # Compara cada propriedade
    for key in solution.keys():
        guess_value = guess_character.get(key)
        solution_value = solution.get(key)
        status = 'incorrect'

        if guess_value == solution_value:
            status = 'correct'
        # Lógica para campos numéricos (ano e quantidade de armas)
        elif key in ['ANO_DE_LANCAMENTO', 'QUANTIDADE_DE_ARMA']:
            try:
                if int(guess_value) < int(solution_value):
                    status = 'lower'
                elif int(guess_value) > int(solution_value):
                    status = 'higher'
            except (ValueError, TypeError):
                # Se a conversão falhar, mantém como 'incorrect'
                status = 'incorrect'
        # Lógica para campos com múltiplos valores (Classe e Alcance)
        elif key in ['CLASSE', 'ALCANTE']:
            guess_parts = {part.strip() for part in str(guess_value).split(',')}
            solution_parts = {part.strip() for part in str(solution_value).split(',')}
            if guess_parts.intersection(solution_parts):
                status = 'partial' # Pelo menos um valor em comum

        results[key.lower()] = {'value': guess_value, 'status': status}

    # Garante que o URL da imagem está sempre presente
    if 'IMAGEM_URL' in guess_character:
        results['imagem_url'] = {'value': guess_character['IMAGEM_URL']}

    # --- Depuração no Servidor ---
    print("\n--- DADOS DO PALPITE ('%s') ---" % guess_name)
    print(f"Encontrado na memória: {guess_character}")
    print("---------------------------------")
    print(f"--- RESPOSTA ENVIADA PARA O FRONTEND (Solução era: {solution['NOME']}) ---")
    import json
    print(json.dumps({'results': results, 'isCorrect': is_correct}, indent=2, ensure_ascii=False))
    print("---------------------------------\n")

    return jsonify({'results': results, 'isCorrect': is_correct})

if __name__ == '__main__':
    create_database_if_not_exists()
    # Para desenvolvimento local, pode usar: app.run(debug=True)
    # Para produção, o Gunicorn será usado.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

