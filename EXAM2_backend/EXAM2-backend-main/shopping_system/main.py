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

# --- 檢查/建立 users 表，username 當主鍵 ---
def ensure_user_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email    TEXT NOT NULL
            )
        """)
        conn.commit()

def log_db_schema():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = cur.fetchall()
        print("=== DB PATH ===", DB_PATH)
        print("=== TABLES ===")
        for r in rows:
            print(f"{r['name']}: {r['sql']}")
            cur.execute(f"PRAGMA table_info({r['name']})")
            cols = cur.fetchall()
            print("  -> columns:", [(c[1], c[2]) for c in cols])  # (name, type)

# 補齊空缺程式碼


PW_HAS_UPPER = re.compile(r'[A-Z]')
PW_HAS_LOWER = re.compile(r'[a-z]')

@app.route('/page_register', methods=['GET', 'POST'], endpoint='register')
def page_register():
    ensure_user_table()   
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email    = (data.get('email') or '').strip()

        # ---- 規則檢查 ----
        if not username or not password or not email:
            msg = {"status": "error", "message": "請完整輸入帳號、密碼、信箱"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        if not EMAIL_RE.match(email):
            msg = {"status": "error", "message": "Email 格式不符（需為 XXX@gmail.com）"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        if len(password) < 8 or not PW_HAS_UPPER.search(password) or not PW_HAS_LOWER.search(password):
            # 至少 8 碼 + 同時含大小寫
            msg = {"status": "error", "message": "密碼須至少 8 碼且同時包含英文大小寫，請重新輸入"}
            if request.is_json: return jsonify(msg), 400
            flash(msg["message"]); return redirect(url_for('register'))

        # ---- DB 寫入/更新 ----
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                # 以「帳號」為主鍵判斷是否存在
                cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
                exists = cur.fetchone() is not None

                if exists:
                    # 帳號存在 → 覆寫密碼或信箱
                    cur.execute(
                        "UPDATE users SET password=?, email=? WHERE username=?",
                        (password, email, username)
                    )
                    conn.commit()
                    if request.is_json:
                        return jsonify({"status": "updated", "message": "帳號已存在，成功修改密碼或信箱"}), 200
                    flash("帳號已存在，成功修改密碼或信箱"); return redirect(url_for('page_login'))
                else:
                    # 新帳號 → 直接新增（users 表三欄）
                    cur.execute(
                        "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                        (username, password, email)
                    )
                    conn.commit()
                    if request.is_json:
                        return jsonify({"status": "success", "message": "註冊成功"}), 200
                    return redirect(url_for('page_login'))
        except sqlite3.Error as e:
            app.logger.exception(f"Register failed: {e}")
            if request.is_json:
                return jsonify({"status":"error","message":"註冊失敗"}), 500
            flash("註冊失敗"); return redirect(url_for('register'))

    return render_template('page_register.html')




def login_user(username, password):
    ensure_user_table()  
    conn = get_db_connection()
    ...

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

# 建表（若無）: orders(product, price, number, total, date, time)
def ensure_order_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shop_list_table(
                Product TEXT PRIMARY KEY,
                Price   NUMERIC,
                Number  NUMERIC,
                "Total Price" NUMERIC,
                Date    TEXT,
                Time    TEXT
            )
        """)
        conn.commit()

@app.route('/order', methods=['POST'])
def api_order():
    try:
        payload = request.get_json(force=True)
        items = payload.get('items', [])
        if not items:
            return jsonify({"status":"error","message":"無訂單項目"}), 400

        ensure_order_table()
        now = datetime.now()
        d = now.strftime("%Y-%m-%d")
        t = now.strftime("%H:%M")

        with get_db_connection() as conn:
            cur = conn.cursor()
            for it in items:
                cur.execute(
                    'INSERT OR REPLACE INTO shop_list_table'
                    ' (Product, Price, Number, "Total Price", Date, Time)'
                    ' VALUES (?, ?, ?, ?, ?, ?)',
                    (it.get('name',''), int(it.get('price',0)), int(it.get('qty',0)),
                     int(it.get('total',0)), d, t)
                )
            conn.commit()
        return jsonify({"status":"success"}), 200
    except Exception as e:
        app.logger.exception(e)
        return jsonify({"status":"error","message":"下單失敗"}), 500


# 補齊空缺程式碼
if __name__ == '__main__':
    ensure_user_table()   
    log_db_schema()       
    app.run()



