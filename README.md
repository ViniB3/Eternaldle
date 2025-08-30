# Eternaldle

Jogo Eternaldle (Versão SQLite)
Bem-vindo ao Eternaldle, um jogo de adivinhação de personagens.

Esta versão utiliza SQLite, o que significa que a base de dados é um simples ficheiro no projeto. Isto torna o jogo extremamente fácil de configurar e partilhar, sem a necessidade de instalar um servidor de base de dados como o MySQL.

Como Executar o Jogo
Siga estes três passos simples para colocar o jogo a funcionar.

Passo 1: Instalar as Dependências
Primeiro, precisa de instalar as bibliotecas Python que o jogo utiliza. Abra o seu terminal na pasta do projeto e execute o seguinte comando:

pip install -r requirements.txt

Isto irá instalar automaticamente o Flask e o Flask-Cors a partir do ficheiro requirements.txt.

Passo 2: Criar a Base de Dados
Em seguida, execute o script que cria e preenche o ficheiro da base de dados (eternaldle.db). Este passo só precisa de ser feito uma vez.

python setup_database.py

Após executar este comando, você verá um novo ficheiro chamado eternaldle.db na sua pasta.

Passo 3: Iniciar o Servidor do Jogo
Finalmente, inicie o servidor Flask. O seu jogo estará online localmente.

python app.py

O terminal irá mostrar que o servidor está a correr em http://127.0.0.1:5000.

Passo 4: Jogar
Abra o seu navegador de internet e aceda ao ficheiro index.html. O jogo estará pronto para jogar!
