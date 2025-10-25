from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'electricity.db')

PK_MAP = {
    'Customers': 'customer_id',
    'Meters': 'meter_id',
    'Readings': 'reading_id',
    'Bills': 'bill_id'
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if not exists
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        address TEXT,
        phone TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Meters (
        meter_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        meter_number TEXT,
        installation_date TEXT,
        FOREIGN KEY(customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Readings (
        reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
        meter_id INTEGER,
        reading_date TEXT,
        units_consumed INTEGER,
        FOREIGN KEY(meter_id) REFERENCES Meters(meter_id) ON DELETE CASCADE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bills (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        billing_date TEXT,
        amount_due REAL,
        FOREIGN KEY(customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Customers")
    customers = cursor.fetchall()

    cursor.execute("SELECT * FROM Meters")
    meters = cursor.fetchall()

    cursor.execute("SELECT * FROM Readings")
    readings = cursor.fetchall()

    cursor.execute("SELECT * FROM Bills")
    bills = cursor.fetchall()

    conn.close()
    return render_template('index.html',
                           customers=customers,
                           meters=meters,
                           readings=readings,
                           bills=bills,
                           PK_MAP=PK_MAP)

@app.route('/add/<table_name>', methods=['GET','POST'])
def add_record(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        fields = request.form
        columns = ', '.join(fields.keys())
        placeholders = ', '.join(['?']*len(fields))
        values = list(fields.values())
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('add_record.html', table_name=table_name)

@app.route('/view/<table_name>/<int:id>')
def view_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE {PK_MAP[table_name]}=?", (id,))
    record = cursor.fetchone()
    conn.close()
    return render_template('view.html', table_name=table_name, record=record)

@app.route('/update/<table_name>/<int:id>', methods=['GET','POST'])
def update_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    pk = PK_MAP[table_name]
    if request.method == 'POST':
        fields = request.form
        set_clause = ', '.join([f"{k}=?" for k in fields])
        values = list(fields.values())
        values.append(id)
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk}=?", values)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    cursor.execute(f"SELECT * FROM {table_name} WHERE {pk}=?", (id,))
    record = cursor.fetchone()
    conn.close()
    return render_template('update.html', table_name=table_name, record=record)

@app.route('/delete/<table_name>/<int:id>')
def delete_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    pk = PK_MAP[table_name]

    if table_name == 'Customers':
        cursor.execute("DELETE FROM Bills WHERE customer_id=?", (id,))
        cursor.execute("DELETE FROM Readings WHERE meter_id IN (SELECT meter_id FROM Meters WHERE customer_id=?)", (id,))
        cursor.execute("DELETE FROM Meters WHERE customer_id=?", (id,))
    elif table_name == 'Meters':
        cursor.execute("DELETE FROM Readings WHERE meter_id=?", (id,))
    
    cursor.execute(f"DELETE FROM {table_name} WHERE {pk}=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
