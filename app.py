from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from cryptography.fernet import Fernet
import base64
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error=True)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/generator')
@login_required
def generator():
    return render_template('generator.html')

@app.route('/generate-password')
@login_required
def generate_password():
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+'
    random_bytes = os.urandom(16)
    password = ''.join(chars[b % len(chars)] for b in random_bytes)
    return {'password': password}

@app.route('/', methods=['GET', 'POST'])
@login_required
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