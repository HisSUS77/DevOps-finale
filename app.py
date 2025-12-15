from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, Response
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Needed for flash messages
DATABASE = 'myapp.db'

# Simple metrics tracking
metrics = {
    'requests_total': 0,
    'users_added': 0,
    'users_deleted': 0,
    'active_users': 0
}

# Track requests
@app.before_request
def before_request():
    metrics['requests_total'] += 1

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
        metrics['users_added'] += 1
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
    metrics['users_deleted'] += 1
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

# Prometheus metrics endpoint
@app.route('/metrics')
def prometheus_metrics():
    # Update active users count
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    metrics['active_users'] = cursor.fetchone()[0]
    conn.close()
    
    # Generate Prometheus format
    prometheus_output = f"""# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total {metrics['requests_total']}

# HELP users_added_total Total number of users added
# TYPE users_added_total counter
users_added_total {metrics['users_added']}

# HELP users_deleted_total Total number of users deleted
# TYPE users_deleted_total counter
users_deleted_total {metrics['users_deleted']}

# HELP active_users_count Current number of active users
# TYPE active_users_count gauge
active_users_count {metrics['active_users']}
"""
    return Response(prometheus_output, mimetype='text/plain')

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
