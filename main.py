import sqlite3
import random
import time
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "element_hero_secret_key_2026"

    # --- 資料庫與初始化 ---
DB_NAME = "database.db"

def get_db():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    with get_db() as conn:
        # 學生表
        conn.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, 
            real_name TEXT, nickname TEXT,
            grade TEXT, classroom TEXT, seat_num TEXT
        )''')
        # 題庫表
        conn.execute('''CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            element TEXT, q_text TEXT, 
            oa TEXT, ob TEXT, oc TEXT, od TEXT, oe TEXT, 
            answer TEXT,
            wrong_count INTEGER DEFAULT 0, attempt_count INTEGER DEFAULT 0
        )''')
        # 成績表
        conn.execute('''CREATE TABLE IF NOT EXISTS scores (
            username TEXT, element TEXT, 
            score INTEGER, seconds REAL, 
            PRIMARY KEY (username, element)
        )''')

        # --- 自動生成 500 題種子題庫 ---
        check = conn.execute("SELECT count(*) FROM questions").fetchone()[0]
        if check == 0:
            print("正在生成 500 題化學題庫，請稍候...")

            # 定義真實化學數據
            element_data = {
                '氫': {'num': 1, 'sym': 'H', 'period': 1, 'group': 1, 'type': '非金屬'},
                '氧': {'num': 8, 'sym': 'O', 'period': 2, 'group': 16, 'type': '非金屬'},
                '氮': {'num': 7, 'sym': 'N', 'period': 2, 'group': 15, 'type': '非金屬'},
                '碳': {'num': 6, 'sym': 'C', 'period': 2, 'group': 14, 'type': '非金屬'},
                '矽': {'num': 14, 'sym': 'Si', 'period': 3, 'group': 14, 'type': '類金屬'},
                '鈉': {'num': 11, 'sym': 'Na', 'period': 3, 'group': 1, 'type': '鹼金屬'},
                '鎂': {'num': 12, 'sym': 'Mg', 'period': 3, 'group': 2, 'type': '鹼土金屬'},
                '鋁': {'num': 13, 'sym': 'Al', 'period': 3, 'group': 13, 'type': '貧金屬'},
                '鐵': {'num': 26, 'sym': 'Fe', 'period': 4, 'group': 8, 'type': '過渡金屬'},
                '銅': {'num': 29, 'sym': 'Cu', 'period': 4, 'group': 11, 'type': '過渡金屬'}
            }

            questions_to_insert = []
            keys = ['A', 'B', 'C', 'D', 'E']

            for name, data in element_data.items():
                # 每個元素生成 5 種題型，每種 10 題 = 50 題/元素

                # 題型 1: 原子序 (10題)
                for _ in range(10):
                    q_text = f"【基礎】請問元素「{name}」的原子序是多少？"
                    ans = str(data['num'])
                    # 生成干擾選項 (答案附近數字)
                    opts = {ans}
                    while len(opts) < 5:
                        opts.add(str(data['num'] + random.randint(-5, 5)))
                    opts_list = list(opts)
                    random.shuffle(opts_list)
                    ans_key = keys[opts_list.index(ans)]
                    questions_to_insert.append((name, q_text, *opts_list, ans_key))

                # 題型 2: 元素符號 (10題)
                for _ in range(10):
                    q_text = f"【符號】化學符號「{data['sym']}」代表哪一個元素？" if random.random() > 0.5 else f"【符號】元素「{name}」的化學符號是？"
                    ans = data['sym'] if '符號是' in q_text else name

                    # 干擾項
                    fake_pool = list(element_data.values()) if '符號是' in q_text else list(element_data.keys())
                    opts = {ans}
                    while len(opts) < 5:
                        if '符號是' in q_text:
                            opts.add(random.choice(['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','K','Ca','Fe','Cu','Zn','Ag','Au']))
                        else:
                            opts.add(random.choice(['氫','氦','鋰','鈹','硼','碳','氮','氧','氟','氖','鈉','鎂','鋁','矽','磷','硫','氯','鉀','鈣','鐵','銅','鋅','銀','金']))

                    opts_list = list(opts)
                    random.shuffle(opts_list)
                    ans_key = keys[opts_list.index(ans)]
                    questions_to_insert.append((name, q_text, *opts_list, ans_key))

                # 題型 3: 元素分類 (10題)
                for _ in range(10):
                    q_text = f"【性質】在週期表中，{name} 被歸類為哪一種類型？"
                    ans = data['type']
                    types = ['鹼金屬', '鹼土金屬', '過渡金屬', '非金屬', '鹵素', '惰性氣體', '類金屬', '貧金屬']
                    opts = {ans}
                    while len(opts) < 5:
                        opts.add(random.choice(types))
                    opts_list = list(opts)
                    random.shuffle(opts_list)
                    ans_key = keys[opts_list.index(ans)]
                    questions_to_insert.append((name, q_text, *opts_list, ans_key))

                # 題型 4: 週期與族 (10題)
                for _ in range(10):
                    is_period = random.random() > 0.5
                    if is_period:
                        q_text = f"【位置】{name} 位於週期表的第幾週期？"
                        ans = str(data['period'])
                        pool = range(1, 8)
                    else:
                        q_text = f"【位置】{name} 位於週期表的第幾族？"
                        ans = str(data['group'])
                        pool = range(1, 19)

                    opts = {ans}
                    while len(opts) < 5:
                        opts.add(str(random.choice(pool)))
                    opts_list = list(opts)
                    random.shuffle(opts_list)
                    ans_key = keys[opts_list.index(ans)]
                    questions_to_insert.append((name, q_text, *opts_list, ans_key))

                # 題型 5: 電子數計算 (10題)
                for _ in range(10):
                    q_text = f"【進階】若 {name} 原子為中性，則其核外電子數應為多少？"
                    ans = str(data['num'])
                    opts = {ans}
                    while len(opts) < 5:
                        opts.add(str(data['num'] + random.randint(-3, 3)))
                    opts_list = list(opts)
                    random.shuffle(opts_list)
                    ans_key = keys[opts_list.index(ans)]
                    questions_to_insert.append((name, q_text, *opts_list, ans_key))

            conn.executemany("INSERT INTO questions (element, q_text, oa, ob, oc, od, oe, answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", questions_to_insert)
            conn.commit()
            print(f"成功初始化 {len(questions_to_insert)} 題題目！(每元素 50 題)")

init_db()

    # --- 快取排行榜機制 ---
    # 結構: {'all': {element: data}, 'class': {class_id: {element: data}}, 'time': timestamp}
CACHE_TIMEOUT = 300 # 5分鐘
lb_cache = {'global': {}, 'timestamp': 0}

def get_global_leaderboard(element):
        # 簡單快取：如果超過時間或沒資料就重抓
        now = time.time()
        if element not in lb_cache['global'] or (now - lb_cache['timestamp'] > CACHE_TIMEOUT):
            with get_db() as conn:
                # 分數高優先，秒數少優先
                data = conn.execute('''
                    SELECT s.nickname, s.grade, s.classroom, sc.score, sc.seconds
                    FROM scores sc JOIN students s ON sc.username = s.username
                    WHERE sc.element = ?
                    ORDER BY sc.score DESC, sc.seconds ASC
                ''', (element,)).fetchall()
                lb_cache['global'][element] = [dict(row) for row in data]
                lb_cache['timestamp'] = now
        return lb_cache['global'][element]

    # --- 路由邏輯 ---

@app.route('/')
def index():
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
        u = request.form.get('username')
        p = request.form.get('password')

        # 老師登入 (固定)
        if u == 'admin' and p == '1234':
            session.clear()
            session['role'] = 'teacher'
            return redirect(url_for('teacher_dash'))

        # 學生登入
        # 密碼加密比對
        p_hash = hashlib.sha256(p.encode()).hexdigest()
        with get_db() as conn:
            user = conn.execute("SELECT * FROM students WHERE username=? AND password=?", (u, p_hash)).fetchone()
            if user:
                session.clear()
                session['role'] = 'student'
                session['user'] = u
                session['nickname'] = user['nickname']
                session['grade'] = user['grade']
                session['classroom'] = user['classroom']
                return redirect(url_for('student_dash'))

        return render_template('login.html', error="帳號或密碼錯誤")

@app.route('/register', methods=['GET', 'POST'])
def register():
        if request.method == 'POST':
            try:
                d = request.form
                p_hash = hashlib.sha256(d['password'].encode()).hexdigest()
                with get_db() as conn:
                    conn.execute("INSERT INTO students (username, password, real_name, nickname, grade, classroom, seat_num) VALUES (?,?,?,?,?,?,?)",
                                 (d['username'], p_hash, d['real_name'], d['nickname'], d['grade'], d['classroom'], d['seat_num']))
                    conn.commit()
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                return render_template('register.html', error="帳號已被註冊")
        return render_template('register.html')

@app.route('/logout')
def logout():
        session.clear()
        return redirect(url_for('index'))

    # --- 學生端功能 ---

@app.route('/student')
def student_dash():
        if session.get('role') != 'student':
            return redirect(url_for('index'))
        return render_template('student_dash.html', user=session)

@app.route('/api/leaderboard')
def api_leaderboard():
        if session.get('role') != 'student':
            return jsonify([])
        ele = request.args.get('element')
        mode = request.args.get('mode') # 'global' or 'class'

        data = []
        if mode == 'global':
            data = get_global_leaderboard(ele)
        else:
            # 班級排行不快取，因為人數少查詢快
            with get_db() as conn:
                data = conn.execute('''
                    SELECT s.nickname, sc.score, sc.seconds
                    FROM scores sc JOIN students s ON sc.username = s.username
                    WHERE sc.element = ? AND s.grade = ? AND s.classroom = ?
                    ORDER BY sc.score DESC, sc.seconds ASC
                ''', (ele, session['grade'], session['classroom'])).fetchall()
                data = [dict(row) for row in data]

        return jsonify(data)

@app.route('/quiz/<element>')
def quiz_page(element):
        if session.get('role') != 'student':
            return redirect(url_for('index'))
        return render_template('quiz.html', element=element)

@app.route('/api/get_questions/<element>')
def get_questions(element):
        with get_db() as conn:
                qs = conn.execute("SELECT * FROM questions WHERE element=? ORDER BY RANDOM() LIMIT 5",(element,)).fetchall()
        # 轉換成 JSON 並隨機洗牌選項
        q_list = []
        for q in qs:
            opts = [
                {'txt': q['oa'], 'key': 'A'}, {'txt': q['ob'], 'key': 'B'},
                {'txt': q['oc'], 'key': 'C'}, {'txt': q['od'], 'key': 'D'},
                {'txt': q['oe'], 'key': 'E'}
            ]
            random.shuffle(opts)
            q_list.append({
                'id': q['id'],
                'text': q['q_text'],
                'options': opts,
                'correct': q['answer'] # 前端為了即時紅綠燈，需要知道答案，但會在 JS 裡隱藏
            })
        return jsonify(q_list)

@app.route('/api/submit_score', methods=['POST'])
def submit_score():
        data = request.json
        u = session['user']
        ele = data['element']
        score = data['score']
        seconds = data['seconds']

        with get_db() as conn:
            # 1. 更新題目統計 (作答分佈圖用)
            for log in data['logs']:
                # log: {qid: 1, correct: true/false}
                is_wrong = 0 if log['correct'] else 1
                conn.execute("UPDATE questions SET attempt_count = attempt_count + 1, wrong_count = wrong_count + ? WHERE id = ?", (is_wrong, log['qid']))

            # 2. 更新個人最佳紀錄
            curr = conn.execute("SELECT score, seconds FROM scores WHERE username=? AND element=?", (u, ele)).fetchone()
            should_update = False
            if not curr:
                should_update = True
            elif score > curr['score']:
                should_update = True
            elif score == curr['score'] and seconds < curr['seconds']:
                should_update = True

            if should_update:
                conn.execute("INSERT OR REPLACE INTO scores (username, element, score, seconds) VALUES (?, ?, ?, ?)",
                             (u, ele, score, seconds))
                conn.commit()
                # 清除該元素的快取，讓下次請求看到新紀錄
                if ele in lb_cache['global']:
                    del lb_cache['global'][ele]

        return jsonify({'status': 'ok'})

    # --- 老師端功能 ---

@app.route('/teacher')
def teacher_dash():
        if session.get('role') != 'teacher':
            return redirect(url_for('index'))
        return render_template('teacher_dash.html')

@app.route('/api/teacher/data')
def teacher_data():
        if session.get('role') != 'teacher':
            return jsonify({})
        ele = request.args.get('element')
        grade = request.args.get('grade')
        cls = request.args.get('class')

        with get_db() as conn:
            # 1. 題目分佈數據
            chart_data = conn.execute("SELECT id, q_text, wrong_count FROM questions WHERE element=? ORDER BY wrong_count DESC LIMIT 10", (ele,)).fetchall()

            # 2. 班級成績表
            sql = '''SELECT s.classroom, s.seat_num, s.real_name, sc.score 
                     FROM scores sc JOIN students s ON sc.username = s.username 
                     WHERE sc.element = ?'''
            params = [ele]
            if grade != 'all':
                sql += " AND s.grade = ?"
                params.append(grade)
            if cls != 'all':
                sql += " AND s.classroom = ?"
                params.append(cls)
            sql += " ORDER BY s.grade, s.classroom, s.seat_num"

            scores = conn.execute(sql, params).fetchall()

            # 3. 題庫列表
            questions = conn.execute("SELECT * FROM questions WHERE element=?", (ele,)).fetchall()

        return jsonify({
            'chart': [dict(row) for row in chart_data],
            'scores': [dict(row) for row in scores],
            'questions': [dict(row) for row in questions]
        })

@app.route('/api/teacher/question', methods=['POST', 'DELETE', 'PUT'])
def manage_question():
            if session.get('role') != 'teacher':
                return jsonify({'status': 'denied'})
            with get_db() as conn:
                if request.method == 'DELETE':
                    qid = request.args.get('id')
                    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
                elif request.method == 'POST':
                    d = request.json
                    conn.execute("INSERT INTO questions (element, q_text, oa, ob, oc, od, oe, answer) VALUES (?,?,?,?,?,?,?,?)",
                                 (d['ele'], d['q'], d['oa'], d['ob'], d['oc'], d['od'], d['oe'], d['ans']))
                elif request.method == 'PUT':
                    d = request.json
                    conn.execute('''UPDATE questions SET q_text=?, oa=?, ob=?, oc=?, od=?, oe=?, answer=? 
                                    WHERE id=?''', (d['q'], d['oa'], d['ob'], d['oc'], d['od'], d['oe'], d['ans'], d['id']))
                conn.commit()
            return jsonify({'status': 'ok'})
if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080, debug=True)