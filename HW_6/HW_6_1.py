# -*- coding: utf-8 -*-
"""
python HW_6_1.py --db ID_data.db
"""
import argparse, sqlite3, re
from typing import Dict, Optional, Tuple

# 僅保留在程式內使用，不建入 DB
THIRD_TO_CITIZENSHIP: Dict[str, str] = {
    '0':'在臺灣出生之本籍國民','1':'在臺灣出生之本籍國民','2':'在臺灣出生之本籍國民',
    '3':'在臺灣出生之本籍國民','4':'在臺灣出生之本籍國民','5':'在臺灣出生之本籍國民',
    '6':'入籍國民，原為外國人','7':'入籍國民，原為無戶籍國民',
    '8':'入籍國民，原為港澳居民或澳門居民','9':'入籍國民，原為大陸地區人民'
}

# 9 碼（少最後檢查碼） & 10 碼（完整）
BASE9 = re.compile(r'^[A-Z][1289][0-9]{7}$')
FULL10 = re.compile(r'^[A-Z][1289][0-9]{8}$')

def load_letter_maps(con: sqlite3.Connection) -> Tuple[Dict[str,int], Dict[str,str]]:
    """
    從 DB 的 county_table 載入對照：
    - letter_to_code: {'A':10, ...} 由 number 欄位而來
    - letter_to_city: {'A':'臺北市', ...} 由 county 欄位而來
    """
    cur = con.cursor()
    t_exists = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='county_table'"
    ).fetchone()
    if not t_exists:
        raise SystemExit("找不到資料表 county_table（需含 letter, county, number 欄位）")

    rows = cur.execute("SELECT letter, county, number FROM county_table").fetchall()
    letter_to_code: Dict[str, int] = {}
    letter_to_city: Dict[str, str] = {}
    for letter, county, number in rows:
        if isinstance(letter, str):
            letter = letter.strip().upper()
        code = int(number)  # number 在 DB 裡是 TEXT，轉成 int
        letter_to_code[letter] = code
        letter_to_city[letter] = str(county)
    if not letter_to_code or not letter_to_city:
        raise SystemExit("county_table 內沒有有效對照資料")
    return letter_to_code, letter_to_city

def compute_checksum(id9: str, letter_to_code: Dict[str,int]) -> Optional[int]:
    if not BASE9.match(id9):
        return None
    letter = id9[0]
    code = letter_to_code.get(letter)
    if code is None:
        return None
    x, y = code // 10, code % 10
    weights = [8,7,6,5,4,3,2,1]
    digits8 = id9[1:]
    total = x*1 + y*9 + sum(int(d)*w for d,w in zip(digits8, weights))
    return (10 - (total % 10)) % 10

def ensure_columns(con: sqlite3.Connection):
    """
    你的 DB 目前 ID_table 已有: ID, country, gender, citizenship
    這裡只會補上 ID_full（若不存在）
    """
    cur = con.cursor()
    try:
        cur.execute("ALTER TABLE ID_table ADD COLUMN ID_full TEXT")
        con.commit()
    except Exception:
        pass

def build_view_enriched(con: sqlite3.Connection):
    """
    只建立 v_id_enriched（用 county_table 做 JOIN；citizenship 中文解釋用 CASE 組出來，不建表）
    """
    cur = con.cursor()
    cur.execute("DROP VIEW IF EXISTS v_id_enriched")

    case_expr = "CASE substr(t.ID,3,1) " + " ".join(
        [f"WHEN '{k}' THEN '{v}'" for k, v in THIRD_TO_CITIZENSHIP.items()]
    ) + " ELSE '未知' END"

    sql = f"""
        CREATE VIEW v_id_enriched AS
        SELECT
            t.ID,
            t.ID_full,
            t.gender,
            t.citizenship,
            t.country,
            c.county AS city_from_db,
            {case_expr} AS citizenship_from_map
        FROM ID_table t
        LEFT JOIN county_table c
            ON substr(t.ID,1,1) = c.letter
    """
    cur.execute(sql)
    con.commit()

def update_in_place(con: sqlite3.Connection):
    letter_to_code, letter_to_city = load_letter_maps(con)
    ensure_columns(con)

    cur = con.cursor()
    rows = cur.execute("SELECT rowid, ID FROM ID_table").fetchall()

    patched = 0
    to_delete = []

    # 先清空要重算的欄位
    cur.execute("UPDATE ID_table SET country=NULL, gender=NULL, citizenship=NULL, ID_full=NULL")
    con.commit()

    for rowid, _id in rows:
        if isinstance(_id, str):
            _id = _id.strip().upper()

        if isinstance(_id, str) and BASE9.match(_id):
            chk = compute_checksum(_id, letter_to_code)
            if chk is None:
                to_delete.append(rowid)
                continue

            id_full = _id + str(chk)
            country = letter_to_city.get(_id[0], '未知')
            gender = '男性' if _id[1] in ('1', '8') else '女性'
            citizen = THIRD_TO_CITIZENSHIP.get(_id[2], '未知')

            cur.execute(
                """UPDATE ID_table
                   SET ID_full=?, country=?, gender=?, citizenship=?
                   WHERE rowid=?""",
                (id_full, country, gender, citizen, rowid)
            )
            patched += 1
        else:
            to_delete.append(rowid)

    if to_delete:
        cur.executemany("DELETE FROM ID_table WHERE rowid=?", [(rid,) for rid in to_delete])
    con.commit()

    # 建 VIEW（不用建任何對照表）
    build_view_enriched(con)

    return len(rows), patched, len(to_delete), letter_to_code, letter_to_city

def explain_and_print(full_id: str, letter_to_city: Dict[str,str]):
    city = letter_to_city.get(full_id[0], '未知')
    gender = '男性' if full_id[1] in ('1','8') else '女性'
    citizen = THIRD_TO_CITIZENSHIP.get(full_id[2], '未知')
    print(f"{full_id} {city} {gender} {citizen}")

def verify_and_format(user_in: str, letter_to_code: Dict[str,int], letter_to_city: Dict[str,str]) -> bool:
    """
    回傳 True 表示為真並已印出說明；False 表示為假（呼叫端會提示請重新輸入）
    - 支援 10 碼完整 ID
    - 也支援 9 碼（少最後一碼），會自動補上正確檢查碼後輸出
    """
    s = (user_in or "").strip().upper()
    # 移除空白與破折號等常見分隔
    s = re.sub(r'[\s\-_]', '', s)

    # 10 碼完整驗證
    if FULL10.match(s):
        id9 = s[:9]
        chk = compute_checksum(id9, letter_to_code)
        if chk is None:
            return False
        if str(chk) != s[-1]:
            return False
        explain_and_print(s, letter_to_city)
        return True

    # 9 碼（自動補檢查碼）
    if BASE9.match(s):
        chk = compute_checksum(s, letter_to_code)
        if chk is None:
            return False
        full_id = s + str(chk)
        explain_and_print(full_id, letter_to_city)
        return True

    return False

def interactive_cli(letter_to_code: Dict[str,int], letter_to_city: Dict[str,str]):
    print("\n--- 進入身分證字號查驗模式 ---")
    print("輸入 10 碼身分證號（或前 9 碼我會自動補檢查碼）。輸入 q 離開。")
    while True:
        try:
            s = input("請輸入身分證字號：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已離開。")
            break
        if s.lower() in ("q", "quit", "exit"):
            print("已離開。")
            break
        if verify_and_format(s, letter_to_code, letter_to_city):
            # 真
            pass
        else:
            # 假
            print("此身分證字號為假，請重新輸入。")


def main():
    ap = argparse.ArgumentParser(description="In-place update ID_data.db（city/code 從 county_table 讀取；citizenship 僅在程式內對照）")
    ap.add_argument("--db", required=True, help="SQLite DB path (e.g., ID_data.db)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    try:
        t = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ID_table'").fetchone()
        if not t:
            raise SystemExit("找不到資料表 ID_table")
        total, patched, deleted, letter_to_code, letter_to_city = update_in_place(con)
        print("=== 完成 ===")
        print(f"原始筆數: {total}")
        print(f"成功補齊: {patched}")
        print(f"已刪除無效: {deleted}")
        print("已建立 v_id_enriched")
    finally:
        con.close()

    # ★ 不結束，直接進入互動驗證 CLI
    interactive_cli(letter_to_code, letter_to_city)

if __name__ == "__main__":
    main()
