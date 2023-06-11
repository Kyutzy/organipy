import mysql.connector
import dotenv

dotenv.load_dotenv()

def connect():
    cnx = mysql.connector.connect(user="", password='',
                                host='127.0.0.1',
                                database='Organify')
    cursor = cnx.cursor()
    return cursor, cnx

def isConnected(func):
    def wrapper(*args, **kwargs):
        cursor, cnx = connect()
        final = func(cursor, cnx, *args, **kwargs)
        cursor.close()
        cnx.close()
        return final
    return wrapper

@isConnected
def getData(cursor, cnx, hash):
    print(hash)
    cursor.execute(f"SELECT * FROM userbase WHERE tokenUsuario = '{hash}'")
    return cursor.fetchone()

@isConnected
def createData(cursor, cnx, hash, data, image):
    cursor.execute(f"INSERT INTO userbase (nomeUsuario, tokenUsuario, fotoCapa, contaVinculada) VALUES ('{hash}', '{data}', '{image}', 0)")
    cnx.commit()
    return 0

@isConnected
def updateData(cursor, cnx, hash, image):
    cursor.execute(f"UPDATE userbase SET fotoCapa = '{image}' WHERE tokenUsuario = '{hash}'")
    cnx.commit()
    return 0
