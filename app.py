import sqlite3
from flask import Flask, request

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, secret TEXT)')
    cursor.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY, owner TEXT, text TEXT)')
    cursor.execute("INSERT INTO users (username, secret) VALUES ('admin', 'SUPER_SECRET_FLAG_2026')")
    cursor.execute("INSERT INTO users (username, secret) VALUES ('user1', 'just_some_password')")
    cursor.execute("INSERT INTO messages (id, owner, text) VALUES (1, 'admin', 'Секретный чат админа: Завтра увольняем аналитика.')")
    cursor.execute("INSERT INTO messages (id, owner, text) VALUES (2, 'user1', 'Привет, это обычное сообщение пользователя.')")
    conn.commit()
    return conn


db_conn = init_db()


@app.route('/')
def index():
    return """
    <h1>Лабораторная работа №2 (SQLi + IDOR)</h1>
    <ul>
        <li><code>/user?name=ИМЯ</code> — SQLi</li>
        <li><code>/message?id=НОМЕР</code> — IDOR</li>
    </ul>
    """


@app.route('/user')
def get_user():
    username = request.args.get('name', '')
    cursor = db_conn.cursor()
    query = f"SELECT username, secret FROM users WHERE username = '{username}'"
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return f"Результат поиска для {username}: {str(result)}"
    except Exception as e:
        return f"Ошибка базы данных: {str(e)}"


@app.route('/message')
def get_message():
    message_id = request.args.get('id', '')
    current_user = "user1"
    cursor = db_conn.cursor()
    cursor.execute(f"SELECT owner, text FROM messages WHERE id = {message_id}")
    result = cursor.fetchone()
    if result:
        owner, text = result
        return f"Сообщение #{message_id} (Владелец: {owner}): {text}"
    return "Сообщение не найдено."


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, threaded=False)
