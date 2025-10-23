
# -*- coding: utf-8 -*-
# Simple Flask app for "教師用成績系統"
# Version A: HTML forms
# Version B: AJAX (fetch + JSON)
#
# DB file is referenced directly in code (no CLI arguments).

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

app = Flask(__name__)
app.secret_key = "dev-secret-for-class"   # for session cookies (OK for homework)

# --- helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_teacher(username: str, password: str) -> bool:
    with get_db() as conn:
        cur = conn.execute("SELECT 1 FROM teachers WHERE username=? AND password=?", (username.strip(), password.strip()))
        row = cur.fetchone()
    return bool(row)

def list_grades():
    with get_db() as conn:
        cur = conn.execute("SELECT name, student_id, score FROM grades ORDER BY student_id ASC")
        return [dict(r) for r in cur.fetchall()]

def add_grade(name: str, student_id: int, score: int):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO grades(name, student_id, score)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                name=excluded.name,
                score=excluded.score
        """, (name.strip(), int(student_id), int(score)))
        conn.commit()


def delete_grade(student_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM grades WHERE student_id=?", (int(student_id),))
        conn.commit()

# -------------------- HTML form version --------------------
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # validate
        if not username or not password:
            error = "請輸入帳號與密碼"
        elif check_teacher(username, password):
            session["username"] = username
            return redirect(url_for("grades_page"))
        else:
            # find out which part is wrong for the message
            with get_db() as conn:
                cur = conn.execute("SELECT 1 FROM teachers WHERE username=?", (username,))
                user_exists = cur.fetchone()
            error = "密碼錯誤" if user_exists else "查無此帳號"

    return render_template("index.html", error=error)

@app.route("/grades", methods=["GET", "POST"])
def grades_page():
    if "username" not in session:
        return redirect(url_for("index"))

    msg = None
    if request.method == "POST":
        # from the HTML form submission: add new grade
        name = request.form.get("name","").strip()
        sid  = request.form.get("student_id","").strip()
        sc   = request.form.get("score","").strip()
        if name and sid.isdigit() and sc.isdigit():
            add_grade(name, int(sid), int(sc))
            msg = "新增成功！"
        else:
            msg = "請輸入正確的資料（學號與成績必須是數字）"

    grades = list_grades()
    return render_template("grades.html", username=session.get("username"), grades=grades, msg=msg)

@app.post("/delete")
def delete_form():
    if "username" not in session:
        return redirect(url_for("index"))
    sid = request.form.get("delete_id","").strip()
    if sid.isdigit():
        delete_grade(int(sid))
    return redirect(url_for("grades_page"))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -------------------- AJAX version --------------------
@app.get("/ajax")
def ajax_page():
    return render_template("ajax.html")

# API: login
@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password:
        return jsonify({"ok": False, "error": "請輸入帳號與密碼"}), 400
    if check_teacher(username, password):
        session["username"] = username
        return jsonify({"ok": True, "username": username})
    # wrong reason
    with get_db() as conn:
        cur = conn.execute("SELECT 1 FROM teachers WHERE username=?", (username,))
        user_exists = cur.fetchone()
    return jsonify({"ok": False, "error": "密碼錯誤" if user_exists else "查無此帳號"}), 401

# API: list grades
@app.get("/api/grades")
def api_list_grades():
    if "username" not in session:
        return jsonify({"ok": False, "error": "尚未登入"}), 401
    return jsonify({"ok": True, "items": list_grades(), "username": session.get("username")})

# API: add grade
@app.post("/api/grades")
def api_add_grade():
    if "username" not in session:
        return jsonify({"ok": False, "error": "尚未登入"}), 401
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    sid = str(data.get("student_id") or "").strip()
    sc  = str(data.get("score") or "").strip()
    if not (name and sid.isdigit() and sc.isdigit()):
        return jsonify({"ok": False, "error": "格式錯誤：學號與成績必須是數字"}), 400

    add_grade(name, int(sid), int(sc))
    return jsonify({"ok": True, "items": list_grades()})

# API: delete grade by student_id
@app.delete("/api/grades/<int:student_id>")
def api_delete_grade(student_id: int):
    if "username" not in session:
        return jsonify({"ok": False, "error": "尚未登入"}), 401
    delete_grade(student_id)
    return jsonify({"ok": True, "items": list_grades()})

if __name__ == "__main__":
    # For homework demo; do not enable debug in production
    app.run(host="0.0.0.0", port=5000, debug=True)
