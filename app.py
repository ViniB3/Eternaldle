import sqlite3
import random
import os
from flask import Flask, jsonify, session, request, send_from_directory
from flask_cors import CORS

# --- Configuração do Flask e Caminhos ---
app = Flask(__name__)
project_root = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(project_root, 'eternaldle.db')

# Chave secreta e configuração de cookies para a sessão
app.config['SECRET_KEY'] = 'a_chave_secreta_super_dificil_de_adivinhar'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app, supports_credentials=True)

# --- VERIFICADOR DE ARRANQUE ---
# Esta verificação é executada assim que o servidor Gunicorn inicia o 'app.py'.
if not os.path.exists(DATABASE_FILE):
    print("="*60)
    print(f"!!! FATAL ERROR: A base de dados '{DATABASE_FILE}' não foi encontrada. !!!")
    print("Isto significa que o 'Build Command' ('python setup_database.py') pode ter falhado ou não foi executado.")
    print("Verifique os logs da fase de 'Build' no Render para encontrar o erro.")
    print("Lembre-se: O ficheiro 'eternaldle.db' NÃO deve estar no seu repositório GitHub.")
    print("="*60)
# A aplicação irá falhar na primeira chamada à API, mas este log dir-nos-á porquê.

# --- Funções da Base de Dados ---
def get_all_characters():
    """Busca todos os dados dos personagens da base de dados SQLite."""
    if not os.path.exists(DATABASE_FILE):
        # Esta é uma segunda verificação, caso a primeira falhe
        print(f"ERRO DENTRO DA API: O ficheiro da base de dados '{DATABASE_FILE}' desapareceu ou nunca foi criado.")
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
        print(f"ERRO DE SQL: {e}. A tabela 'eternaldle' pode estar em falta na base de dados.")
        return None

# --- Rotas da Aplicação (API e Frontend) ---

@app.route('/')
def serve_index():
    """Serve a página principal do jogo."""
    return send_from_directory(project_root, 'eternaldle.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Inicia um novo jogo, escolhendo um personagem aleatório como solução."""
    all_characters = get_all_characters()
    if all_characters is None or not all_characters:
        print("ERRO na API start_game: A lista de personagens está vazia ou a base de dados falhou.")
        return jsonify({'error': 'Falha crítica ao carregar os dados dos personagens. Verifique os logs do servidor.'}), 500

    solution_character = random.choice(all_characters)
    session['solution'] = dict(solution_character)
    print(f"O jogo começou. Solução é: {session['solution']['NOME']}")
    character_names = [char['NOME'] for char in all_characters]
    return jsonify({'characterNames': character_names})

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
        return jsonify({'error': 'Falha ao recarregar os dados dos personagens para o palpite.'}), 500
        
    guess_character = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)
    if not guess_character:
        return jsonify({'error': 'Personagem não encontrado.'}), 404

    # --- Lógica de Comparação (mantida como antes) ---
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
    # Esta parte é para execução local e não é usada pelo Gunicorn no Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

