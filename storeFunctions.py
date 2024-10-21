
import sqlite3

def createTable(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS linksID (
        id INTEGER PRIMARY KEY,
        number TEXT NOT NULL
    )
    ''')
    
    
def insertLink(cursor, number):
    cursor.execute('''
    INSERT INTO linksID (number)
    VALUES (?)
    ''', (number,))
    
    
def checkLink(cursor, number):
    cursor.execute('''
    SELECT * FROM linksID WHERE number = ?
    ''', (number,))
    result = cursor.fetchone()
    
    # If the link exist return True, otherwise False
    return result is not None