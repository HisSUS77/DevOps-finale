from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Needed for flash messages
DATABASE = 'myapp.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Home page with links
@app.route('/')
def home():
    return render_template('index.html')

# Display users
@app.route('/users')
def list_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('users.html', users=users)

# Add user via form
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        conn.close()
        flash(f'✅ User {name} added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('⚠️ Email already exists!', 'error')
    return redirect(url_for('list_users'))

# Delete user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('🗑️ User deleted successfully!', 'success')
    return redirect(url_for('list_users'))

# API endpoint to get user count
@app.route('/api/user_count')
def user_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'count': count})

# API endpoint to get all users (JSON)
@app.route('/api/users')
def api_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    users_list = [{'id': user[0], 'name': user[1], 'email': user[2]} for user in users]
    return jsonify(users_list)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
