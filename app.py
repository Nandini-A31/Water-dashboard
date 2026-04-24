from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_change_this"  # change this to anything random

DATA_DB  = "data.db"
USERS_DB = "users.db"

# ── Init sensor DB ───────────────────────────────────────
def init_data_db():
    conn = sqlite3.connect(DATA_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS water (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level REAL, temp REAL, ph REAL, timestamp TEXT
    )''')
    conn.commit()
    conn.close()

# ── Init users DB ────────────────────────────────────────
def init_users_db():
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()

    # Create default users — change these!
    default_users = [
        ("admin",  "admin123"),
        ("user1",  "pass1234"),
    ]
    for username, password in default_users:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        except sqlite3.IntegrityError:
            pass  # user already exists

    conn.commit()
    conn.close()

init_data_db()
init_users_db()

# ── Helper ───────────────────────────────────────────────
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user is not None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Routes ───────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if check_login(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('dashboard.html', username=session['username'])

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    if data:
        conn = sqlite3.connect(DATA_DB)
        c = conn.cursor()
        c.execute("INSERT INTO water (level, temp, ph, timestamp) VALUES (?, ?, ?, ?)",
                  (data['level'], data['temp'], data['ph'], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return "OK", 200
    return "Error", 400

@app.route('/data')
@login_required
def get_data():
    conn = sqlite3.connect(DATA_DB)
    c = conn.cursor()
    c.execute("SELECT level, temp, ph, timestamp FROM water ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    data = [{"level": r[0], "temp": r[1], "ph": r[2], "time": r[3]} for r in rows]
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)