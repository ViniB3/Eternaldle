import sqlite3
import os
import traceback
import redis
from datetime import datetime  # Importa a biblioteca de data e hora
from flask import Flask, jsonify, session, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)

# Configuração de caminhos
project_root = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(project_root, 'eternaldle.db')

# Configuração de Sessão e Segurança
app.config['SECRET_KEY'] = 'a_chave_secreta_super_dificil_de_adivinhar'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Definir como True se usar HTTPS (produção)

CORS(app, supports_credentials=True)

# --- Optional Redis (Upstash) support for daily counter ---
redis_client = None
REDIS_URL = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_URL')
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        print("Connected to Redis for daily counters.")
    except Exception as e:
        print(f"WARN: Could not connect to Redis at {REDIS_URL}: {e}")
        redis_client = None

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
    # Try Redis first if available
    if redis_client:
        try:
            key = f"eternaldle:daily:{today}:count"
            new = redis_client.incr(key)
            # store solution name for reference (non-critical)
            try:
                redis_client.set(f"eternaldle:daily:{today}:solution", solution_name)
            except Exception:
                pass
            return int(new)
        except Exception as e:
            print(f"ERRO increment_today_correct_count (redis): {e}")
            # fallback to sqlite

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
    # Try Redis first if available
    if redis_client:
        try:
            key = f"eternaldle:daily:{today}:count"
            val = redis_client.get(key)
            return int(val) if val else 0
        except Exception as e:
            print(f"ERRO get_today_correct_count (redis): {e}")
            # fallback to sqlite

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
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT winners_count FROM daily_stats WHERE data = ?", (today,))
        row = cur.fetchone()
        conn.close()
        return row['winners_count'] if row else 0
    except Exception as e:
        print(f"Erro ao obter contagem: {e}")
        return 0

# --- Rotas da API ---


# Static files are served from the 'static/' folder by Flask. Removed custom /style.css route.


@app.route('/favicon.ico')
def serve_favicon():
    """Serve um favicon se existir; caso contrário retorna 204 (sem conteúdo)."""
    favicon_path = os.path.join(project_root, 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_from_directory(project_root, 'favicon.ico')
    return ('', 204)

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Inicializa o jogo e seleciona o personagem do dia baseado na data."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM eternaldle")
        all_characters = [dict(row) for row in cur.fetchall()]
        conn.close()

        if not all_characters:
            return jsonify({'error': 'A base de dados está vazia.'}), 500

        # Ordenar alfabeticamente para garantir que o índice seja consistente em todos os clientes
        sorted_characters = sorted(all_characters, key=lambda x: x['NOME'])
        
        # Lógica de seleção diária: muda o personagem a cada 24 horas
        epoch = datetime(2024, 1, 1)
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
        return jsonify({'error': 'Erro no servidor ao iniciar jogo.'}), 500

@app.route('/api/record_win', methods=['POST'])
def record_win():
    """Regista que um utilizador acertou no personagem de hoje."""
    if 'solution' not in session:
        return jsonify({'error': 'Sessão inválida.'}), 400
    
    # Evita incrementos múltiplos do mesmo utilizador na mesma sessão
    if session.get('has_won_today'):
        return jsonify({'winnersToday': get_winners_count()})

    today = get_today_str()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Incrementa o contador ou cria o registo para o novo dia
        cur.execute("""
            INSERT INTO daily_stats (data, winners_count) 
            VALUES (?, 1) 
            ON CONFLICT(data) DO UPDATE SET winners_count = winners_count + 1
        """, (today,))
        
        conn.commit()
        conn.close()
        
        session['has_won_today'] = True
        return jsonify({'winnersToday': get_winners_count()})
    except Exception as e:
        print(f"Erro ao gravar vitória: {e}")
        return jsonify({'error': 'Erro ao atualizar estatísticas.'}), 500

@app.route('/api/guess', methods=['POST'])
def handle_guess():
    """Valida o palpite do utilizador e compara com a solução da sessão."""
    if 'solution' not in session:
        return jsonify({'error': 'Jogo não iniciado.'}), 400

    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    solution = session['solution']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eternaldle WHERE NOME = ?", (guess_name,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Personagem não encontrado.'}), 404

    guess_character = dict(row)
    results = {}
    is_correct = (guess_character['NOME'].lower() == solution['NOME'].lower())
    
    # Lógica de comparação de atributos
    for key in solution.keys():
        if key in ['IMAGEM_URL']: continue
        
        guess_value = guess_character.get(key)
        solution_value = solution.get(key)
        status = 'incorrect'
        
        if str(guess_value).lower() == str(solution_value).lower():
            status = 'correct'
        elif key in ['ANO_DE_LANCAMENTO', 'QUANTIDADE_DE_ARMA']:
            try:
                if int(guess_value) < int(solution_value): status = 'higher'
                elif int(guess_value) > int(solution_value): status = 'lower'
            except: status = 'incorrect'
        elif key in ['CLASSE', 'ALCANCE']:
            guess_parts = {part.strip().lower() for part in str(guess_value).split(',')}
            solution_parts = {part.strip().lower() for part in str(solution_value).split(',')}
            if guess_parts.intersection(solution_parts): status = 'partial'
            
        results[key.lower()] = {'value': guess_value, 'status': status}
    
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

# Admin endpoint to migrate existing SQLite daily_stats into Redis (protected by MIGRATE_TOKEN)
@app.route('/admin/migrate_counts', methods=['POST'])
def migrate_counts():
    token = request.headers.get('Authorization', '').split()[-1]
    if token != os.environ.get('MIGRATE_TOKEN'):
        return ('Forbidden', 403)
    if not redis_client:
        return ('Redis not configured', 400)
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute('SELECT date, correct_count, solution_name FROM daily_stats')
        rows = cur.fetchall()
        conn.close()
        for date, count, sol in rows:
            key = f"eternaldle:daily:{date}:count"
            redis_client.set(key, int(count))
            if sol:
                redis_client.set(f"eternaldle:daily:{date}:solution", sol)
        return ('OK', 200)
    except Exception as e:
        print(f"Migration error: {e}")
        return ('Internal Error', 500)

if __name__ == '__main__':
    # Garante que a base de dados existe antes de arrancar (opcional se usar setup_database.py)
    app.run(debug=True, host='0.0.0.0', port=5000)