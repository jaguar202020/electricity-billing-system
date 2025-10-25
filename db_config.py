import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # apna MySQL username daal
        password="root",  # apna password
        database="electricity_billing"
    )
    return conn
