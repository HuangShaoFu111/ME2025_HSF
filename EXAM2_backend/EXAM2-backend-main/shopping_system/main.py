from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from datetime import datetime
import sqlite3
import logging
import re 
import os


# 讓 Flask 從「目前目錄」找 HTML，static 用現成的 /static
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'dev-secret'  # 用於 session，正式環境請改環境變數

# Email 驗證（作業規格：只接受 gmail）
EMAIL_RE = re.compile(r'^[A-Za-z0-9._%+-]+@gmail\.com$')

# 路徑修改
DB_PATH = os.path.join(os.path.dirname(__file__), 'shopping_data.db')
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 補齊空缺程式碼

@app.route('/page_register', methods=['GET', 'POST'], endpoint='register')
def page_register():

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email    = (data.get('email') or '').strip()
        # 基本檢查
        if not username or not password or not email:
            msg = {"status": "error", "message": "請完整輸入帳號、密碼、信箱"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        if not EMAIL_RE.match(email):
            msg = {"status": "error", "message": "Email 格式不符（需為 XXX@gmail.com）"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        if len(password) < 8:
            msg = {"status": "error", "message": "密碼至少 8 碼"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        # 寫入 DB
        conn = get_db_connection()
        if conn is None:
            msg = {"status": "error", "message": "資料庫連線失敗"}
            if request.is_json: return jsonify(msg), 500
            flash(msg["message"]); return redirect(url_for('register'))

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                # 檢查重複
                cur.execute("SELECT 1 FROM users WHERE username=? OR email=?", (username, email))
                if cur.fetchone():
                    if request.is_json:
                        return jsonify({"status":"error","message":"此名稱或信箱已被使用"}), 400
                    flash("此名稱或信箱已被使用")
                    return redirect(url_for('register'))

                # ★ 只插入 3 欄（users 就這 3 欄）
                cur.execute(
                    "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (username, password, email)
                )
                conn.commit()  # 保險起見保留明確 commit
                app.logger.info(f"Register OK -> {username} -> DB: {DB_PATH}")

        except sqlite3.Error as e:
            app.logger.exception(f"Register failed: {e}")
            if request.is_json:
                return jsonify({"status":"error","message":"註冊失敗"}), 500
            flash("註冊失敗")
            return redirect(url_for('register'))

        # 成功導回登入頁（名稱依你的登入路由）
        if request.is_json:
            return jsonify({"status":"success","message":"註冊成功"}), 200
        return redirect(url_for('page_login'))

    return render_template('page_register.html')



def login_user(username, password):
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                return {"status": "success", "message": "Login successful"}
            else:
                return {"status": "error", "message": "Invalid username or password"}
        except sqlite3.Error as e:
            logging.error(f"Database query error: {e}")
            return {"status": "error", "message": "An error occurred"}
        finally:
            conn.close()
    else:
        return {"status": "error", "message": "Database connection error"}

@app.route('/page_login' , methods=['GET', 'POST'])
def page_login():
    try:
        if request.method == 'POST':
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            result = login_user(username, password)
            if result["status"] == "success":
                session['username'] = username
            return jsonify(result)
        return render_template('page_login_.html')

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 補齊剩餘副程式
@app.route('/')
def index():
    if session.get('username'):
        return render_template('index.html')
    return redirect(url_for('page_login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('page_login'))


# 補齊空缺程式碼
if __name__ == '__main__':
    app.run()


