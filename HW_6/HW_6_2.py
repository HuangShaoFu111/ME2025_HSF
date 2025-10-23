# -*- coding: utf-8 -*-
"""
Homework 2 CLI  (use existing table: user_data)
python hw2_user_system.py --db users.db
"""
import argparse
import re
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, Dict

# ========= 驗證規則 =========
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$")
SPECIALS = r"!@#$%^&*()_+\-=\[\]{};':\",.<>/?\\|`~"

def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))

def has_upper_lower(pw: str) -> bool:
    return any(c.isupper() for c in pw) and any(c.islower() for c in pw)

def has_special(pw: str) -> bool:
    return any(c in SPECIALS for c in pw)

def long_enough(pw: str) -> bool:
    return len(pw) >= 8

def no_simple_sequence(pw: str) -> bool:
    s = pw.lower()
    seqs = ["0123456789", "abcdefghijklmnopqrstuvwxyz"]
    for base in seqs:
        for L in range(3, 6):
            for i in range(len(base) - L + 1):
                frag = base[i:i+L]
                if frag in s or frag[::-1] in s:
                    return False
    return True

def password_checks(pw: str):
    fails = []
    if not long_enough(pw):
        fails.append("字數需至少 8 碼")
    if not has_upper_lower(pw):
        fails.append("需同時包含大寫與小寫英文字母")
    if not has_special(pw):
        fails.append("需包含至少 1 個特殊字元")
    if not no_simple_sequence(pw):
        fails.append("不可使用連號或連續字母（例如 1234、abcd 或其倒序）")
    return (len(fails) == 0, fails)

# ========= DB 相關（直接用既有 user_data） =========
TABLE = "user_data"

def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # 檢查資料表與必備欄位
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,))
    if not cur.fetchone():
        raise RuntimeError(f"資料庫中找不到資料表 `{TABLE}`。請確認 DB 檔案是否正確。")
    cols = get_columns(conn, TABLE)
    need = {"name", "email", "password"}
    if not need.issubset({c.lower() for c in cols}):
        raise RuntimeError(f"`{TABLE}` 需包含欄位 name/email/password（目前只有: {cols}）")
    return conn

def get_columns(conn: sqlite3.Connection, table: str):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [r["name"] for r in cur.fetchall()]

# 取得實際欄位大小寫對應（例如 Email/EMAIL）
def colmap(conn: sqlite3.Connection) -> Dict[str, str]:
    cols = get_columns(conn, TABLE)
    lower = {c.lower(): c for c in cols}
    return {
        "name": lower.get("name", "name"),
        "email": lower.get("email", "email"),
        "password": lower.get("password", "password"),
    }

def get_user(conn: sqlite3.Connection, name: str, email: str) -> Optional[Tuple[str, str, str]]:
    c = colmap(conn)
    sql = f"SELECT {c['email']} AS email,{c['name']} AS name,{c['password']} AS password FROM {TABLE} WHERE {c['email']}=? AND {c['name']}=?"
    row = conn.execute(sql, (email.strip(), name.strip())).fetchone()
    return (row["email"], row["name"], row["password"]) if row else None

def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[Tuple[str, str, str]]:
    c = colmap(conn)
    sql = f"SELECT {c['email']} AS email,{c['name']} AS name,{c['password']} AS password FROM {TABLE} WHERE {c['email']}=?"
    row = conn.execute(sql, (email.strip(),)).fetchone()
    return (row["email"], row["name"], row["password"]) if row else None

def save_user(conn: sqlite3.Connection, name: str, email: str, password: str):
    # 先查是否已有同 email，存在就 UPDATE，否則 INSERT
    existing = get_user_by_email(conn, email)
    c = colmap(conn)
    if existing:
        sql = f"UPDATE {TABLE} SET {c['name']}=?, {c['password']}=? WHERE {c['email']}=?"
        conn.execute(sql, (name.strip(), password, email.strip()))
    else:
        sql = f"INSERT INTO {TABLE} ({c['email']},{c['name']},{c['password']}) VALUES (?,?,?)"
        conn.execute(sql, (email.strip(), name.strip(), password))
    conn.commit()

# ========= 互動流程 =========
def prompt_nonempty(msg: str) -> str:
    while True:
        s = input(msg).strip()
        if s:
            return s
        print("不得為空，請重新輸入。")

def flow_signup(conn: sqlite3.Connection):
    print("\n=== Sign Up 註冊模式 ===")
    name = prompt_nonempty("Name 請輸入名稱： ")

    while True:
        email = prompt_nonempty("Email (需為 XXX@gmail.com)： ")
        if valid_email(email):
            break
        print("Email 格式不符，請重新輸入。")

    while True:
        pwd = prompt_nonempty("Password（至少 8 碼、含大小寫與特殊字元、不可連號）： ")
        ok, fails = password_checks(pwd)
        if ok:
            break
        print("密碼不符合規則：")
        for f in fails:
            print(f" - {f}")
        print("請重新輸入。")

    print(f"\n顯示註冊資訊：save {name} | {email} | {pwd} | Y / N ?")
    while True:
        yn = input("是否儲存（Y 更新/儲存；N 返回主畫面）： ").strip().upper()
        if yn in ("Y", "N"):
            break

    if yn == "N":
        return

    exists = get_user_by_email(conn, email)
    if exists:
        print("資料庫已有相同 Email。是否更新此 Email 資訊？ Y / N")
        yn2 = input("你的選擇： ").strip().upper()
        if yn2 != "Y":
            print("已取消更新，返回主畫面。\n")
            return

    save_user(conn, name, email, pwd)
    print("資料已儲存（或已更新）。\n")

def flow_signin(conn: sqlite3.Connection):
    print("\n=== Sign In 登入模式 ===")
    while True:
        name = prompt_nonempty("請輸入 姓名： ")
        email = prompt_nonempty("請輸入 Email： ")

        row = get_user(conn, name, email)
        if not row:
            print('名字或 Email 錯誤 (a) sign up / (b) sign in')
            print('(按下"a"返回註冊模式)')
            while True:
                pick = input("請選擇 (a/b)： ").strip().lower()
                if pick == "a":
                    flow_signup(conn)
                    return
                elif pick == "b":
                    break  # 繼續 while，讓使用者重新輸入姓名與 Email
                else:
                    print("無效選項，請輸入 a 或 b。")
            continue

        while True:
            pwd = prompt_nonempty("請輸入 Password： ")
            if pwd == row[2]:
                print("🎉 登入成功！\n")
                return
            print("密碼錯誤。忘記密碼 Y / N ?")
            yn = input("你的選擇： ").strip().upper()
            if yn == "Y":
                print("導向註冊模式以更新密碼...\n")
                flow_signup(conn)
                return
            # 選 N → 留在此 while，重輸密碼

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="users.db", help="SQLite 檔案路徑（預設 users.db）")
    args = parser.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = open_db(args.db)

    print("資料庫：", args.db)
    print("操作：輸入 (a) sign up  /  (b) sign in  /  (q) 離開\n")

    while True:
        mode = input("請選擇模式 (a/b/q)： ").strip().lower()
        if mode == "a":
            flow_signup(conn)
        elif mode == "b":
            flow_signin(conn)
        elif mode == "q":
            print("Bye!")
            break
        else:
            print("無效輸入，請重新選擇。")

if __name__ == "__main__":
    main()