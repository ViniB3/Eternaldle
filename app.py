import sqlite3
import random
import os
import traceback
from flask import Flask, jsonify, session, request, send_from_directory
from flask_cors import CORS

# --- Configuração do Flask e Caminhos ---
app = Flask(__name__)

# SOLUÇÃO GRATUITA E FINAL: Usar o diretório do projeto para tudo.
# O build do Render cria o ficheiro na pasta do projeto, e a app irá encontrá-lo aqui.
project_root = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(project_root, 'eternaldle.db')

# Chave secreta e configuração de cookies para a sessão
app.config['SECRET_KEY'] = 'a_chave_secreta_super_dificil_de_adivinhar'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app, supports_credentials=True)

# --- VERIFICADOR DE ARRANQUE ---
print("="*60)
print("INICIANDO SERVIDOR FLASK")
print(f"Procurando base de dados em: {DATABASE_FILE}")
if not os.path.exists(DATABASE_FILE):
    print("!!! ATENÇÃO: A base de dados NÃO FOI ENCONTRADA no arranque. !!!")
else:
    print(">>> SUCESSO: A base de dados foi encontrada no arranque. <<<")
print("="*60)


# --- Funções da Base de Dados ---
def get_all_characters():
    """Busca todos os dados dos personagens da base de dados SQLite."""
    if not os.path.exists(DATABASE_FILE):
        return None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM eternaldle")
        characters_raw = cur.fetchall()
        conn.close()
        return [dict(row) for row in characters_raw]
    except sqlite3.OperationalError as e:
        print(f"ERRO DE SQL: {e}.")
        return None

# --- Rotas da Aplicação (API e Frontend) ---

@app.route('/')
def serve_index():
    """Serve a página principal do jogo."""
    return send_from_directory(project_root, 'eternaldle.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Inicia um novo jogo, escolhendo um personagem aleatório como solução."""
    print("\n--- Recebido pedido em /api/start_game ---")
    try:
        all_characters = get_all_characters()

        if all_characters is None:
            print("ERRO: get_all_characters() retornou None. A base de dados não existe ou está corrupta.")
            return jsonify({'error': 'O servidor não conseguiu ler a base de dados.'}), 500
        
        if not all_characters:
            print("ERRO: A lista de personagens está vazia.")
            return jsonify({'error': 'A base de dados parece estar vazia.'}), 500

        print(f"Sucesso! {len(all_characters)} personagens carregados da base de dados.")
        
        solution_character = random.choice(all_characters)
        session['solution'] = dict(solution_character)
        
        print(f"Personagem solução escolhido: {session['solution']['NOME']}")
        
        character_names = [char['NOME'] for char in all_characters]
        
        print("Enviando lista de nomes para o frontend...")
        return jsonify({'characterNames': character_names})

    except Exception as e:
        print(f"!!! ERRO INESPERADO EM start_game: {e} !!!")
        traceback.print_exc()
        return jsonify({'error': 'Ocorreu um erro inesperado no servidor.'}), 500

@app.route('/api/guess', methods=['POST'])
def handle_guess():
    """Lida com o palpite de um utilizador e retorna a comparação detalhada."""
    if 'solution' not in session:
        return jsonify({'error': 'O jogo não foi iniciado. Por favor, atualize a página.'}), 400

    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    solution = session['solution']
    
    all_characters = get_all_characters()
    if all_characters is None:
        return jsonify({'error': 'Falha ao recarregar os dados para o palpite.'}), 500
        
    guess_character = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)
    if not guess_character:
        return jsonify({'error': 'Personagem não encontrado.'}), 404

    # --- Lógica de Comparação ---
    results = {}
    is_correct = (guess_character['NOME'].lower() == solution['NOME'].lower())
    for key in solution.keys():
        guess_value = guess_character.get(key)
        solution_value = solution.get(key)
        status = 'incorrect'
        if guess_value == solution_value:
            status = 'correct'
        elif key in ['ANO_DE_LANCAMENTO', 'QUANTIDADE_DE_ARMA']:
            try:
                if int(guess_value) < int(solution_value):
                    status = 'lower'
                elif int(guess_value) > int(solution_value):
                    status = 'higher'
            except (ValueError, TypeError): status = 'incorrect'
        elif key in ['CLASSE', 'ALCANCE']:
            guess_parts = {part.strip() for part in str(guess_value).split(',')}
            solution_parts = {part.strip() for part in str(solution_value).split(',')}
            if guess_parts.intersection(solution_parts):
                status = 'partial'
        results[key.lower()] = {'value': guess_value, 'status': status}
    if 'IMAGEM_URL' in guess_character:
        results['imagem_url'] = {'value': guess_character['IMAGEM_URL']}

    return jsonify({'results': results, 'isCorrect': is_correct})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

