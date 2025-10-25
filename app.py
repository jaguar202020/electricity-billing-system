from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# DB connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',  # apna password yahan
        database='electricity_billing'
    )
    return conn

# Table → Primary Key mapping
PK_MAP = {
    'Customers': 'customer_id',
    'Meters': 'meter_id',
    'Readings': 'reading_id',
    'Bills': 'bill_id'
}

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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

# Add new record
@app.route('/add/<table_name>', methods=['GET', 'POST'])
def add_record(table_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        fields = request.form
        columns = ', '.join(fields.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        values = list(fields.values())
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('add_record.html', table_name=table_name)

# View record
@app.route('/view/<table_name>/<int:id>')
def view_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    pk = PK_MAP[table_name]
    cursor.execute(f"SELECT * FROM {table_name} WHERE {pk}=%s", (id,))
    record = cursor.fetchone()
    conn.close()
    return render_template('view.html', table_name=table_name, record=record)

# Update record
@app.route('/update/<table_name>/<int:id>', methods=['GET', 'POST'])
def update_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    pk = PK_MAP[table_name]

    if request.method == 'POST':
        fields = request.form
        set_clause = ', '.join([f"{k}=%s" for k in fields])
        values = list(fields.values())
        values.append(id)
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk}=%s", values)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute(f"SELECT * FROM {table_name} WHERE {pk}=%s", (id,))
    record = cursor.fetchone()
    conn.close()
    return render_template('update.html', table_name=table_name, record=record)

# Delete record with child handling
@app.route('/delete/<table_name>/<int:id>')
def delete_record(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    pk = PK_MAP[table_name]

    # Handle foreign key child deletion
    if table_name == 'Customers':
        # Delete Bills first
        cursor.execute("DELETE FROM Bills WHERE customer_id=%s", (id,))
        # Delete Readings for all meters of this customer
        cursor.execute("DELETE FROM Readings WHERE meter_id IN (SELECT meter_id FROM Meters WHERE customer_id=%s)", (id,))
        # Delete Meters
        cursor.execute("DELETE FROM Meters WHERE customer_id=%s", (id,))
    elif table_name == 'Meters':
        # Delete Readings first
        cursor.execute("DELETE FROM Readings WHERE meter_id=%s", (id,))

    cursor.execute(f"DELETE FROM {table_name} WHERE {pk}=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
