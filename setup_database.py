import sqlite3
import os

# SOLUÇÃO FINAL: Usar o diretório do projeto para tudo.
# Isto garante que a app encontra a base de dados criada pelo script de build.
project_root = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(project_root, 'eternaldle.db')

# Lista completa de personagens
characters = [
    ('Abigail','Mulher','Lutador','Corpo-a-corpo','Cinza','2023',1,'https://i.imgur.com/guAblq7.jpeg'),
('Adela','Mulher','Mago,Suporte','Longo alcance','Preto','2021',2,'https://i.imgur.com/wZt2Icr.jpeg'),
('Adina','Mulher','Mago','Longo alcance','Cinza','2022',1,'https://i.imgur.com/Hk3GB6X.jpeg'),
('Adriana','Mulher','Mago','Longo alcance','Vermelho','2020',1,'https://i.imgur.com/HTO1Wv8.jpeg'),
('Aiden','Homem','Lutador','Corpo-a-corpo,Longo alcance','Branco','2022',1,'https://i.imgur.com/0BTlO7K.jpeg'),
('Alex','Homem','Lutador','Corpo-a-corpo,Longo alcance','Loiro','2021',4,'https://i.imgur.com/ZVLeiTg.jpeg'),
('Alonso','Homem','Tank','Corpo-a-corpo','Loiro','2023',1,'https://i.imgur.com/w00JlL3.jpeg'),
('Arda','Homem','Mago,Suporte','Longo alcance','Loiro','2023',1,'https://i.imgur.com/4Q4d21g.jpeg'),
('Aya','Mulher','Mago,Carregador','Longo alcance','Castanho','2019',3,'https://imgur.com/4Q4d21g'),
('Barbara','Mulher','Mago','Corpo-a-corpo','Castanho','2021',1,'https://i.imgur.com/qqzCI8Z.jpeg'),
('Bernice','Homem','Carregador','Longo alcance','Loiro','2021',1,'https://i.imgur.com/YSUQsWA.jpeg'),
('Bianca','Mulher','Mago','Longo alcance','Azul','2021',1,'https://i.imgur.com/HF2dTni.png'),
('Blair','Mulher','Lutador','Corpo-a-corpo','Lorio','2025',1,'https://i.imgur.com/ecMnxZ6.png'),
('Camilo','Homem','Lutador','Corpo-a-corpo','Loiro','2021',2,'https://i.imgur.com/TuITtH8.png'),
('Cathy','Mulher','Assassino','Corpo-a-corpo','Castanho','2021',2,'https://i.imgur.com/F5Y6VKU.jpeg'),
('Celine','Mulher','Mago','Longo alcance','Azul','2021',1,'https://i.imgur.com/uhuWQhG.png'),
('Charlotte','Mulher','Suporte','Longo alcance','Rosa','2024',1,'https://i.imgur.com/7TA3K29.png'),
('Chiara','Mulher','Lutador','Corpo-a-corpo','Branco','2020',1,'https://i.imgur.com/4TQnuYs.png'),
('Chloe','Mulher','Carregador','Longo alcance','Loiro','2021',1,'https://i.imgur.com/b26xnFD.png'),
('Daniel','Homem','Assassino','Corpo-a-corpo','Roxo','2021',1,'https://i.imgur.com/z82SVVP.png'),
('Darko','Homem','Lutador','Corpo-a-corpo','Azul','2024',1,'https://i.imgur.com/diZYu2C.png'),
('Debi','Mulher','Lutador','Corpo-a-corpo,Longo alcance','Preto','2023',1,'https://i.imgur.com/h2CVZTv.png'),
('Echion','Homem','Lutador','Corpo-a-corpo','Branco','2021',1,'https://i.imgur.com/vJwfCJ9.png'),
('Elena','Mulher','Tank,Lutador','Corpo-a-corpo','Azul','2022',1,'https://i.imgur.com/sLoOYGc.png'),
('Eleven','Mulher','Tank','Corpo-a-corpo','Rosa','2021',1,'https://i.imgur.com/0RcMoj9.png'),
('Emma','Mulher','Mago','Longo alcance','Azul','2020',2,'https://i.imgur.com/5fSat8d.png'),
('Estelle','Mulher','Tank,Lutador','Corpo-a-corpo','Castanho','2022',1,'https://i.imgur.com/lvgmVHe.png'),
('Eva','Mulher','Mago','Longo alcance','Loiro','2021',1,'https://i.imgur.com/xl3m03T.png'),
('Felix','Homem','Lutador','Corpo-a-corpo','Loiro','2022',1,'https://i.imgur.com/8Ar88WP.png'),
('Fiora','Mulher','Lutador','Corpo-a-corpo','Castanho','2019',3,'https://i.imgur.com/HcEwvds.png'),
('Garnet','Mulher','Tank,Lutador','Corpo-a-corpo','Cinza','2024',1,'https://i.imgur.com/buxbhwh.png'),
('Hart','Mulher','Carregador','Longo alcance','Loiro','2020',1,'https://i.imgur.com/lyRm0Xs.png'),
('Haze','Mulher','Mago','Longo alcance','Cinza','2022',1,'https://i.imgur.com/k30E4Az.png'),
('Henry','Homem','Mago','Longo alcance','Cinza','2025',1,'https://i.imgur.com/qeqaABy.png'),
('Hisui','Mulher','Lutador','Corpo-a-corpo','Preto','2024',1,'https://i.imgur.com/hTHk3kG.png'),
('Hyejin','Mulher','Mago','Longo alcance','Preto','2020',2,'https://i.imgur.com/KAj8Q7C.png'),
('Hyunwoo','Homem','Lutador','Corpo-a-corpo','Vermelho','2019',2,'https://i.imgur.com/16TGp06.png'),
('Irem','Mulher','Lutador,Mago','Corpo-a-corpo,Longo alcance','Loiro','2022',1,'https://i.imgur.com/W81rYME.png'),
('Isaac','Homem','Lutador','Corpo-a-corpo','Cinza','2022',1,'https://i.imgur.com/OLBln7U.png'),
('Isol','Homem','Carregador','Longo alcance','Castanho','2020',2,'https://i.imgur.com/wmeoJEp.png'),
('Istvan','Homem','Lutador','Corpo-a-corpo','Preto','2025',1,'https://i.imgur.com/Le7hNC2.png'),
('Jackie','Mulher','Lutador','Corpo-a-corpo','Branco','2019',4,'https://i.imgur.com/Aaogyhu.png'),
('Jan','Homem','Lutador','Corpo-a-corpo','Branco','2021',2,'https://i.imgur.com/Eeka1Vm.png'),
('Jenny','Mulher','Carregador','Longo alcance','Loiro','2021',1,'https://i.imgur.com/K9scM5R.png'),
('Johann','Homem','Suporte','Longo alcance','Preto','2021',1,'https://i.imgur.com/bT6q0hJ.png'),
('Justyna','Mulher','Mago','Longo alcance','Vermelho','2025',1,'https://i.imgur.com/DHlNNZH.png'),
('Karla','Mulher','Carregador','Longo alcance','Vermelho','2022',1,'https://i.imgur.com/3qAAumX.png'),
('Katja','Mulher','Carregador','Longo alcance','Cinza','2024',1,'https://i.imgur.com/F2jH9MV.png'),
('Kenneth','Homem','Lutador','Corpo-a-corpo','Cinza','2024',1,'https://i.imgur.com/knUVok3.png'),
('Laura','Mulher','Lutador','Corpo-a-corpo','Roxo','2022',1,'https://i.imgur.com/aC4WdzC.png'),
('Leni','Mulher','Suporte','Longo alcance','Castanho','2023',1,'https://i.imgur.com/rqdS60H.png'),
('Lenore','Mulher','Mago','Longo alcance','Azul','2024',1,'https://i.imgur.com/8CNHguu.png'),
('Lenox','Mulher','Tank','Corpo-a-corpo','Verde','2021',1,'https://i.imgur.com/xeLtJYl.png'),
('Leon','Homem','Lutador','Corpo-a-corpo','Castanho','2021',2,'https://i.imgur.com/PDaMLc1.png'),
('Li Dailin','Mulher','Lutador','Corpo-a-corpo','Preto','2020',2,'https://i.imgur.com/zKwoGdL.png'),
('Luke','Homem','Lutador','Corpo-a-corpo','Rosa','2021',1,'https://i.imgur.com/iMHKaj8.png'),
('Ly Anh','Mulher','Lutador','Corpo-a-corpo','Loiro','2023',1,'https://i.imgur.com/TAVp4cs.png'),
('Magnus','Homem','Tank,Lutador','Corpo-a-corpo','Loiro','2019',2,'https://i.imgur.com/OyCNjJq.png'),
('Mai','Mulher','Tank,Suporte','Corpo-a-corpo','Vermelho','2022',1,'https://i.imgur.com/lhNC6t2.png'),
('Markus','Homem','Tank,Lutador','Corpo-a-corpo','Preto','2022',2,'https://i.imgur.com/N5Tc9uT.png'),
('Martina','Mulher','Carregador','Longo alcance','Cinza','2022',1,'https://i.imgur.com/SAJZGbf.png'),
('Mirka','Mulher','Tank,Lutador','Corpo-a-corpo','Rosa','2025',1,'https://i.imgur.com/YNrZ6v7.png'),
('Nadine','Mulher','Mago,Carregador','Longo alcance','Preto','2019',2,'https://i.imgur.com/T4mx5qd.png'),
('Nathapon','Homem','Mago','Longo alcance','Castanho','2021',1,'https://i.imgur.com/4SmisY4.png'),
('NiaH','Mulher','Mago','Longo alcance','Roxo','2025',1,'https://i.imgur.com/aLPOKku.png'),
('Nicky','Mulher','Lutador','Corpo-a-corpo','Loiro','2021',1,'https://i.imgur.com/nTdEzvk.png'),
('Piolo','Homem','Lutador','Corpo-a-corpo','Castanho','2022',1,'https://i.imgur.com/R54pjzp.png'),
('Priya','Mulher','Mago,Suporte','Longo alcance','Verde','2022',1,'https://i.imgur.com/zA0AYr0.png'),
('Rio','Mulher','Carregador','Longo alcance','Branco','2021',1,'https://i.imgur.com/MflGNMX.png'),
('Rozzi','Mulher','Carregador','Longo alcance','Preto','2021',1,'https://i.imgur.com/IolgS2W.png'),
('Shoichi','Homem','Assassino','Corpo-a-corpo','Castanho','2020',1,'https://i.imgur.com/esn6Ln6.png'),
('Silvia','Mulher','Lutador','Longo alcance','Preto','2020',1,'https://i.imgur.com/4UlENti.png'),
('Sissela','Mulher','Mago','Longo alcance','Cinza','2020',2,'https://i.imgur.com/22ZNXqM.png'),
('Sua','Mulher','Lutador,Mago','Corpo-a-corpo','Castanho','2021',2,'https://i.imgur.com/gwX9EMV.png'),
('Tazia','Mulher','Mago','Longo alcance','Vermelho','2022',1,'https://i.imgur.com/hGj9Kxu.png'),
('Theodore','Homem','Carregador,Suporte','Longo alcance','Preto','2023',1,'https://i.imgur.com/tTVYjeR.png'),
('Tia','Mulher','Mago','Longo alcance','Loiro','2022',1,'https://i.imgur.com/MYmciUp.png'),
('Tsubame','Mulher','Carregador','Longo alcance','Preto','2023',1,'https://i.imgur.com/N6ZXJZ0.png'),
('Vanya','Mulher','Lutador','Longo alcance','Azul','2023',1,'https://i.imgur.com/S36csEl.png'),
('William','Homem','Carregador','Longo alcance','Castanho','2021',2,'https://i.imgur.com/wNb4soe.png'),
('Xiukai','Homem','Tank','Corpo-a-corpo','Preto','2020',2,'https://i.imgur.com/eCwd4Pj.png'),
('Xuelin','Mulher','Lutador','Corpo-a-corpo','Verde','2025',1,'https://i.imgur.com/hsk4wJT.png'),
('Yuki','Homem','Lutador','Corpo-a-corpo','Preto','2020',2,'https://i.imgur.com/B0qxDn4.png'),
('Yumin','Homem','Mago','Longo alcance','Preto','2024',1,'https://i.imgur.com/HBXrewM.png'),
('Zahir','Homem','Mago','Longo alcance','Castanho','2019',2,'https://i.imgur.com/j3Kh7O3.png')
]

def create_and_populate_db():
    # Remove a base de dados antiga, se existir, para garantir que começamos do zero
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)

    # Conecta-se à base de dados (irá criar o ficheiro se não existir)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Cria a tabela
    cursor.execute('''
    CREATE TABLE eternaldle (
        NOME TEXT PRIMARY KEY,
        GENERO TEXT,
        CLASSE TEXT,
        ALCANCE TEXT,
        COR_CABELO TEXT,
        ANO_DE_LANCAMENTO TEXT,
        QUANTIDADE_DE_ARMA INTEGER,
        IMAGEM_URL TEXT
    )
    ''')

    # Insere os dados dos personagens
    cursor.executemany('''
    INSERT INTO eternaldle (NOME, GENERO, CLASSE, ALCANCE, COR_CABELO, ANO_DE_LANCAMENTO, QUANTIDADE_DE_ARMA, IMAGEM_URL)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', characters)

    # Confirma as alterações e fecha a conexão
    conn.commit()
    conn.close()

    print(f"Base de dados '{DATABASE_FILE}' criada e preenchida com sucesso!")

if __name__ == '__main__':
    create_and_populate_db()






