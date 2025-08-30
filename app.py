from flask import Flask, jsonify, request, session
from flask_cors import CORS
import sqlite3
import random
from datetime import timedelta
import os

app = Flask(__name__)

# Configuração de Segurança e Sessão
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Configuração do CORS para permitir comunicação com o frontend
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

DB_FILE = "eternaldle.db"
all_characters = []

def get_db_connection():
    """Cria e retorna uma conexão com a base de dados SQLite."""
    conn = sqlite3.connect(DB_FILE)
    # Retorna as linhas como dicionários para fácil acesso por nome de coluna
    conn.row_factory = sqlite3.Row
    return conn

def load_characters_from_db():
    """Carrega todos os personagens da base de dados para a memória."""
    global all_characters
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eternaldle")
        characters_raw = cursor.fetchall()
        conn.close()

        # Converte os objetos sqlite3.Row em dicionários
        all_characters = [dict(row) for row in characters_raw]
        
        print("--- VERIFICAÇÃO DE DADOS ---")
        if all_characters:
            print(f"Carregados {len(all_characters)} personagens com sucesso.")
        else:
            print("AVISO: Nenhum personagem foi carregado da base de dados.")
        print("--------------------------")
        
    except sqlite3.Error as e:
        print(f"ERRO CRÍTICO: Não foi possível carregar os personagens da base de dados: {e}")
        all_characters = []


@app.route('/api/start_game', methods=['GET'])
def start_game():
    """Inicia um novo jogo, escolhendo um personagem aleatório como solução."""
    if not all_characters:
        return jsonify({'error': 'Erro no servidor: Não foi possível carregar os personagens.'}), 500

    solution_character = random.choice(all_characters)
    session['solution'] = dict(solution_character)
    session.permanent = True

    print(f"--- Jogo Iniciado. Solução: {session['solution']['NOME']} ---")

    character_names = [char['NOME'] for char in all_characters]
    return jsonify({
        'characterNames': character_names
    })

@app.route('/api/guess', methods=['POST'])
def handle_guess():
    """Lida com o palpite de um utilizador e retorna a comparação detalhada."""
    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    solution = session.get('solution')

    if not solution:
        print("ERRO: Tentativa de palpite sem um jogo iniciado na sessão.")
        return jsonify({'error': 'O jogo não foi iniciado. Por favor, atualize a página.'}), 400

    guess_character = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)

    if not guess_character:
        return jsonify({'error': 'Personagem inválido.'}), 404

    print(f"--- DADOS DO PALPITE ('{guess_name}') ---")
    print("Encontrado na memória:", guess_character)
    print("---------------------------------")
    
    results = {}
    
    # Compara cada propriedade
    for key, solution_value in solution.items():
        guess_value = guess_character[key]
        status = 'incorrect'

        if str(guess_value).lower() == str(solution_value).lower():
            status = 'correct'
        elif key in ['CLASSE', 'ALCANCE']:
            # Verifica se alguma das classes/alcances do palpite está na solução
            guess_items = {item.strip().lower() for item in str(guess_value).split(',')}
            solution_items = {item.strip().lower() for item in str(solution_value).split(',')}
            if guess_items.intersection(solution_items):
                status = 'partial'
        elif key in ['ANO_DE_LANCAMENTO', 'QUANTIDADE_DE_ARMA']:
            if int(guess_value) < int(solution_value):
                status = 'lower'
            else:
                status = 'higher'
        
        results[key.lower()] = {'value': guess_value, 'status': status}

    is_correct = guess_name.lower() == solution['NOME'].lower()

    response_data = {'results': results, 'isCorrect': is_correct}
    print("--- RESPOSTA ENVIADA PARA O FRONTEND ---")
    print(response_data)
    print("--------------------------------------")
    
    return jsonify(response_data)


if __name__ == '__main__':
    # Carrega os personagens para a memória uma vez, antes de o servidor começar a aceitar pedidos.
    load_characters_from_db()
    app.run(debug=True, host='0.0.0.0')

