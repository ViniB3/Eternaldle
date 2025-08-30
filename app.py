from flask import Flask, jsonify, request, session
from flask_mysqldb import MySQL
from flask_cors import CORS
import random
from datetime import timedelta

app = Flask(__name__)

# --- Configuração ---
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root' # Altere para a sua senha do MySQL
app.config['MYSQL_DB'] = 'eternal'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = 'dificil'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
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
    data = request.get_json()
    guess_name = data.get('guess', '').strip()
    solution_name = session.get('solution_name')

    if not solution_name:
        return jsonify({'error': 'O jogo não foi iniciado. Por favor, atualize a página.'}), 400

    guess_char = next((char for char in all_characters if char['NOME'].lower() == guess_name.lower()), None)
    solution_char = next((char for char in all_characters if char['NOME'].lower() == solution_name.lower()), None)

    if not guess_char or not solution_char:
        return jsonify({'error': 'Personagem inválido.'}), 404
        
    # LOG DE DEPURAÇÃO: Mostra os dados do personagem adivinhado
    print(f"\n--- DADOS DO PALPITE ('{guess_name}') ---")
    print(f"Encontrado na memória: {guess_char}")
    print("---------------------------------")

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

    results['imagem_url'] = {'value': guess_char.get('IMAGEM_URL', '')}

    # LOG DE DEPURAÇÃO: Mostra a resposta final a ser enviada
    response_data = {'results': results, 'isCorrect': is_correct}
    print(f"--- RESPOSTA ENVIADA PARA O FRONTEND ---")
    import json
    print(json.dumps(response_data, indent=2))
    print("--------------------------------------")

    return jsonify(response_data)

# --- Inicialização da Aplicação ---
with app.app_context():
    all_characters = get_all_characters()
    if not all_characters:
        print("AVISO: Nenhum personagem foi carregado do banco de dados.")
    else:
        # LOG DE DEPURAÇÃO: Mostra o primeiro personagem carregado para verificar o URL da imagem
        print("\n--- VERIFICAÇÃO DE DADOS CARREGADOS ---")
        print(f"Dados do primeiro personagem na memória: {all_characters[0]}")
        print("---------------------------------------\n")

if __name__ == '__main__':
    app.run(debug=True)

