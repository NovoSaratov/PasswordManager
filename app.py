from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from cryptography.fernet import Fernet
import base64
import os

app = Flask(__name__)

# Generate or load a key
key_file = 'secret.key'
if not os.path.exists(key_file):
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)
else:
    with open(key_file, 'rb') as f:
        key = f.read()
fernet = Fernet(key)

def get_db_connection():
    conn = sqlite3.connect('passwords.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create table if it doesn't exist
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            password_encrypted TEXT NOT NULL
        )
    ''')
    conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        website = request.form['website']
        username = request.form['username']
        password = request.form['password']
        password_encrypted = fernet.encrypt(password.encode()).decode()
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO entries (website, username, password_encrypted) VALUES (?, ?, ?)',
                (website, username, password_encrypted)
            )
            conn.commit()
        return redirect(url_for('index'))
    with get_db_connection() as conn:
        entries = conn.execute('SELECT website, username, password_encrypted FROM entries').fetchall()
    # Decrypt passwords for display
    decrypted_entries = []
    for entry in entries:
        decrypted_password = fernet.decrypt(entry['password_encrypted'].encode()).decode()
        decrypted_entries.append({
            'website': entry['website'],
            'username': entry['username'],
            'password': decrypted_password
        })
    return render_template('index.html', entries=decrypted_entries)

if __name__ == '__main__':
    app.run(debug=True) 