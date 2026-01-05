import sqlite3
import os
import traceback
from datetime import datetime  # Importa a biblioteca de data e hora
from flask import Flask, jsonify, session, request, send_from_directory
from flask_cors import CORS

# --- Configuração do Flask e Caminhos ---
app = Flask(__name__)

# SOLUÇÃO GRATUITA E FINAL: Usar o diretório do projeto para tudo.
project_root = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(project_root, 'eternaldle.db')

# Chave secreta e configuração de cookies para a sessão
app.config['SECRET_KEY'] = 'a_chave_secreta_super_dificil_de_adivinhar'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app, supports_credentials=True)

# --- Funções e Tabela de Estatísticas Diárias ---
def ensure_daily_stats_table():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            solution_name TEXT,
            correct_count INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
    except Exception as e:
        print(f"ERRO ao criar/verificar tabela daily_stats: {e}")
    finally:
        try:
            conn.close()
        except:
            pass


def increment_today_correct_count(solution_name):
    today = datetime.utcnow().date().isoformat()
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO daily_stats (date, solution_name, correct_count)
            VALUES (?, ?, 1)
            ON CONFLICT(date) DO UPDATE SET
                correct_count = correct_count + 1,
                solution_name = excluded.solution_name
        ''', (today, solution_name))
        conn.commit()
        cur.execute('SELECT correct_count FROM daily_stats WHERE date = ?', (today,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"ERRO increment_today_correct_count: {e}")
        try:
            conn.close()
        except:
            pass
        return None


def get_today_correct_count():
    today = datetime.utcnow().date().isoformat()
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute('SELECT correct_count FROM daily_stats WHERE date = ?', (today,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"ERRO get_today_correct_count: {e}")
        try:
            conn.close()
        except:
            pass
        return 0

# Ensure table exists at startup
ensure_daily_stats_table()

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
    """
    Inicia um novo jogo, escolhendo um personagem do dia de forma determinística.
    O personagem é o mesmo para todos durante 24h.
    """
    try:
        all_characters = get_all_characters()

        if not all_characters:
            return jsonify({'error': 'A base de dados parece estar vazia.'}), 500

        # Garante que a ordem dos personagens é sempre a mesma
        sorted_characters = sorted(all_characters, key=lambda x: x['NOME'])
        
        # Lógica para escolher o personagem do dia
        epoch = datetime(2024, 1, 1)  # Uma data de início fixa
        today = datetime.utcnow()
        days_since_epoch = (today - epoch).days
        
        character_index = days_since_epoch % len(sorted_characters)
        solution_character = sorted_characters[character_index]
        
        # Persist session guesses until the daily solution changes
        today = datetime.utcnow().date().isoformat()
        # If the session is for a previous day, clear stored guesses and win flag
        if session.get('solution_date') != today:
            session['guesses'] = []
            session.pop('won_date', None)
        session['solution'] = dict(solution_character)
        session['solution_date'] = today
        session.modified = True

        character_names = [char['NOME'] for char in all_characters]
        previous_guesses = session.get('guesses', [])
        has_won = session.get('won_date') == today
        today_count = get_today_correct_count()

        return jsonify({
            'characterNames': character_names,
            'previousGuesses': previous_guesses,
            'hasWon': has_won,
            'todayCorrectCount': today_count
        })

    except Exception as e:
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
        elif key in ['CLASSE', 'ALCANCE']: # Corrigido para ALCANCE
            guess_parts = {part.strip() for part in str(guess_value).split(',')}
            solution_parts = {part.strip() for part in str(solution_value).split(',')}
            if guess_parts.intersection(solution_parts):
                status = 'partial'
        results[key.lower()] = {'value': guess_value, 'status': status}
    if 'IMAGEM_URL' in guess_character:
        results['imagem_url'] = {'value': guess_character['IMAGEM_URL']}

    # If the guess is correct, increment (once per-session per-day) and return today's correct count
    today_count = None
    if is_correct:
        today_str = datetime.utcnow().date().isoformat()
        # Prevent double-counting from the same session
        if session.get('won_date') != today_str:
            new_count = increment_today_correct_count(solution['NOME'])
            session['won_date'] = today_str
            today_count = new_count
        else:
            today_count = get_today_correct_count()

    response = {'results': results, 'isCorrect': is_correct}
    if today_count is not None:
        response['todayCorrectCount'] = today_count

    # Persist this guess in the session (avoid duplicates in the same session)
    try:
        guesses = session.get('guesses', [])
        guess_entry = {'guess': guess_name, 'results': results, 'isCorrect': is_correct}
        if not any(g.get('guess', '').lower() == guess_name.lower() for g in guesses):
            guesses.append(guess_entry)
            session['guesses'] = guesses
            session.modified = True
    except Exception as e:
        print(f"Warning: could not persist guess in session: {e}")

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

