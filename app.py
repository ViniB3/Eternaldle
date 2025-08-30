from flask import Flask, jsonify, request, session
from flask_mysqldb import MySQL
from flask_cors import CORS
import random
from datetime import timedelta

app = Flask(__name__)

# --- Configuração ---
# IMPORTANTE: Certifique-se de que estas credenciais correspondem à sua configuração do MySQL.
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root' # Altere para a sua senha do MySQL
app.config['MYSQL_DB'] = 'eternal'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' # Retorna linhas como dicionários
app.secret_key = 'dificil' # Altere para uma chave segura
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
# MODIFICADO: Adicionado para melhorar a compatibilidade de cookies de sessão em navegadores modernos
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

mysql = MySQL(app)
CORS(app, supports_credentials=True)

# --- Variáveis Globais ---
all_characters = []

def get_all_characters():
    """Busca todos os dados dos personagens do banco de dados e limpa os dados de texto."""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM eternaldle")
        characters_raw = cur.fetchall()
        cur.close()
        
        characters_clean = []
        for char in characters_raw:
            clean_char = {key: (value.strip() if isinstance(value, str) else value) for key, value in char.items()}
            characters_clean.append(clean_char)
        return characters_clean
    except Exception as e:
        print(f"Erro no banco de dados ao buscar personagens: {e}")
        return []

@app.route('/api/start_game', methods=['GET'])
def start_game():
    """Inicia um novo jogo, escolhendo um personagem aleatório como solução."""
    if not all_characters:
        return jsonify({'error': 'Nenhum personagem disponível para iniciar o jogo.'}), 500

    solution_character = random.choice(all_characters)
    session.permanent = True
    session['solution_name'] = solution_character['NOME']
    
    print(f"--- Jogo Novo Iniciado. Solução: {session['solution_name']} ---")
    
    character_names = [char['NOME'] for char in all_characters]
    
    return jsonify({
        'characterNames': character_names,
        'solutionForTesting': session['solution_name']
    })

def compare_classes(guess_classes, solution_classes):
    """Compara as listas de classes e retorna 'correct', 'partial' ou 'incorrect'."""
    guess_set = set(g.strip() for g in guess_classes.split(','))
    solution_set = set(s.strip() for s in solution_classes.split(','))
    
    if guess_set == solution_set:
        return 'correct'
    if guess_set.intersection(solution_set):
        return 'partial'
    return 'incorrect'

def compare_numeric(guess_value, solution_value):
    """Compara valores numéricos e retorna 'correct', 'higher' ou 'lower'."""
    try:
        g_val = int(guess_value)
        s_val = int(solution_value)
        if g_val == s_val:
            return 'correct'
        return 'higher' if g_val < s_val else 'lower'
    except (ValueError, TypeError):
        return 'incorrect'


@app.route('/api/guess', methods=['POST'])
def handle_guess():
    """Lida com o palpite de um utilizador e retorna a comparação detalhada."""
    # Log de depuração para ver a sessão que o servidor recebe
    print(f"Sessão recebida no palpite: {session}")
    
    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    solution_name = session.get('solution_name')

    if not solution_name:
        return jsonify({'error': 'O jogo não foi iniciado. Por favor, atualize a página.'}), 400

    guess_char = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)
    solution_char = next((char for char in all_characters if char['NOME'].lower() == solution_name.lower()), None)

    if not guess_char or not solution_char:
        return jsonify({'error': 'Personagem inválido.'}), 404

    results = {}
    is_correct = (guess_char['NOME'].lower() == solution_char['NOME'].lower())

    properties_to_compare = {
        'NOME': ('direct', 'nome'),
        'GENERO': ('direct', 'genero'),
        'CLASSE': ('class', 'classe'),
        'ALCANCE': ('direct', 'alcance'),
        'COR_CABELO': ('direct', 'cor_cabelo'),
        'ANO_DE_LANCAMENTO': ('numeric', 'ano_de_lancamento'),
        'QUANTIDADE_DE_ARMA': ('numeric', 'quantidade_de_arma')
    }

    for db_key, (compare_type, frontend_key) in properties_to_compare.items():
        guess_val = guess_char[db_key]
        solution_val = solution_char[db_key]
        status = 'incorrect'

        if compare_type == 'direct':
            if str(guess_val).lower() == str(solution_val).lower():
                status = 'correct'
        elif compare_type == 'class':
            status = compare_classes(str(guess_val), str(solution_val))
        elif compare_type == 'numeric':
            status = compare_numeric(guess_val, solution_val)
        
        if db_key == 'NOME' and is_correct:
            status = 'correct'
        elif db_key == 'NOME':
            status = 'incorrect'

        results[frontend_key] = {'value': guess_val, 'status': status}
        
    if is_correct:
        results['nome']['status'] = 'correct'

    return jsonify({'results': results, 'isCorrect': is_correct})

# --- Inicialização da Aplicação ---
with app.app_context():
    all_characters = get_all_characters()
    if not all_characters:
        print("AVISO: Nenhum personagem foi carregado do banco de dados.")

if __name__ == '__main__':
    app.run(debug=True)

