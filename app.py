from flask import Flask, render_template, jsonify, request, session

import time
import datetime
import uuid
import fcntl
import os
import tempfile
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("App starting up...")

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Game duration in seconds (10 minutes)
GAME_DURATION = 60


# -------------------
# Data structure for questions

questions = {
    "КомпХ": {
        100: {"question": """
              Аливаа нэг улсад бүртгэлтэй боловч тухайн улсдаа бодит байдлаар оршин байдаггүй банк? 
              a.Арилжааны банк
              b.Халхавч банк
              c. Оффшор банк
              d.Корреспондент банк
            """, "answer": "b"},
        200: {"question": """Шүгэл үлээх, зөрчлийн мэдээлэл илгээсэн буруу хаяг аль вэ ?
               a. Утсаар – 18001646
               b. И-мэйл whistleblowing@golomtbank.com
               c. Төвийн нэгжийн оффисуудад байршиж байгаа хүлээн авах хайрцаг
               d. КомпХ-ийн захирал болон ДАГ-ын захиралтай биечлэн уулзах

               """, "answer": "a"},
        300: {"question": """Аль нь оффшор улс биш вэ?
                a.Сингапур 
                b. Арабын нэгдсэн Эмират 
                c. Малайз
                d. Ирланд
                """, "answer": "a"},
        400: {"question": """KYC гэдэг нь ямар үгийн товчлол вэ?
                a.Know your capital
                b.Know your company
                c.Know your customer
                d.Know your cousin
                """, "answer": "c"},
        500: {"question": """МУТСТ тухай хуулийн дагуу банк нь ямар зохицуулагч байгууллагын арга хэмжээг хэрэгжүүлэх үүрэг хүлээсэн байдаг вэ? 
               a. АНУ-ын сангийн яамны харьяа ОFAC
               b. Европын холбоо
               c. НҮБ-ын аюулгүйн зөвлөл
               d. Бүгд зөв
               """, "answer": "c"}
    },
    "ҮАЭУХ": {
        100: {"question": """Үйл ажиллагааны эрсдэлийн үнэлгээнд үндэслэн хэрэгжүүлэх 3 хувилбаруудыг сонгоно уу.  
                a. Хүлээн зөвшөөрөх, бууруулах, зайлсхийх, тайлагнах
                b. Хүлээн зөвшөөрөх, шилжүүлэх, нуун дарагдуулах, зайлсхийх
                c. Хүлээн зөвшөөрөх, бууруулах, шилжүүлэх, зайлсхийх
        """, "answer": "a"},
        200: {"question": """Үйл ажиллагааны эрсдэл гэж хангалтгүй дотоод процесс, хүн, систем болон гадаад хүчин зүйлээс үүдэлтэй алдагдал бий болохыг хэлнэ. Дараахаас аль нь үйл ажиллагааны эрсдэлд хамаарах вэ?
                a. Стратегийн эрсдэл
                b. Хуулийн эрсдэл
                c. Нэр хүндийн эрсдэл
            """, "answer": "b"},
        300: {"question": """Хэрэглэгчийн хандах, үйлдэл хийх эрхийн хэм хэмжээг албан тушаалын чиг үүрэгт нийцүүлэн, нарийвчлан зааж тодорхойлон гарсан жагсаалтыг юу гэх вэ?
                a. Эрхийн матриц
                b. Эрхийн түвшин
                c. Эрх зохицуулалт
                """, "answer": "a"},
        400: {"question": """ “Эрсдэлийн удирдлагын тогтолцоо, эрсдэлийн аппетитийн мэдэгдэл”-ийг Эрсдэлийн удирдлагын газраас ямар давтамжтайгаар хянах, сайжруулах шаардлагатай вэ?
                a. Хагас жил тутам
                b. Жилд дор хаяж 1 удаа
                c. 2 жилд 1 удаа
                """, "answer": "b"
                },
        500: {"question": """Засаглалын бүтэц, ЭУТ-ны үндсэн зарчмууд нь эрсдэлийн удирдлага, стратегийн шийдвэр гаргалтанд ил тод байдлыг бий болгосноор сайн “.................” тогтоно. Цаашлаад засаглалын бүтэц, ЭУТ-ны үндсэн зарчмуудыг мөрдсөнөөр эрсдэлийн удирдлагын нэгжүүдийг бизнесийн нэгжүүд болон дотоод гадаад аудитын нэгжүүдээс хараат бусаар үйл ажиллагаа явуулах үндэслэл болох юм.
                a. Эрсдэлийн төлөв
                b. Эрсдэлийн соёл
                c. Эрсдэлийн аппетит
                """, "answer": "b"}
    },
    "ДЭУХ": {
        100: {"question": """Картын нууц мэдээлэлд аль нь орохгүй вэ?
                a. Картын дуусах огноо
                b. Пин код
                c. OTP баталгаажуулах код
                d. Картын брэнд
            """, "answer": "d"},
        200: {"question": """
                Харилцагч дижитал орчинд мэдээллээ алдсан, луйварт өртсөн, өөрийн хийгээгүй гүйлгээ гарсан төрлийн гомдлыг банкны ямар бичиг баримтын дагуу шийдвэрлэх вэ?
                a. Дижитал гүйлгээний үед ажиллах заавар
                b.Дижитал эрсдэлийн удирдлагын журам
                c. Цахим сэжигтэй гүйлгээний үед ажиллах заавар 
                d. Харилцагчийн гомдол хүлээн авч, шийдэх журам
                """, "answer": "c"},
        300: {"question": """Харилцагчийг дижитал эрсдэлээс сэргийлж сэжигтэй гүйлгээ болон хандалтыг илрүүлэх сүүлийн үеийн олон улсад ашиглаж буй шийдэл юу вэ?
                a.EKYC
                b.Behavior анализ /зан төлвийн анализ/ 
                c.2FA 
                d.Password + SMS/Email OTP
                e. Device fingerprinting
                """, "answer": "b"},
        400: {"question": """Картын мэдээлэл алдагдсанаас үүдэн гарах санхүүгийн эрсдэлийг бууруулахын тулд харилцагчид хамгийн түрүүнд анхаарах ёстой гурван чухал арга хэмжээний зөв хослол аль нь вэ?
                a. Картын нууц кодыг олон нийтийн газар хэлэх, картын зургийг сошиал орчинд нийтлэх, гүйлгээ хийхдээ VPN ашиглахгүй байх
                b. Картаа байнга биедээ авч явах, банкны мэдэгдлийн үйлчилгээг идэвхжүүлэх, зөвхөн онлайн дэлгүүрээс худалдан авалт хийх
                c. Зөвхөн шинэ гар утсаар гүйлгээ хийх, АТМ-н уншигч хэсэгт ямар нэгэн сэжигтэй зүйл байгаа эсэхийг шалгах, сэжигтэй имэйл дээр дарж нэвтрэх 
                d. Картын нууц мэдээллийг хэнд ч хэлэхгүй байх, сэжигтэй линк болон хуурамч вэбсайтуудаас зайлсхийх, АТМ-д карт оруулах хэсгийг шалгаж нууц кодоо нууцалж оруулах
                """, "answer": "299792458 m/s"},
        500: {"question": """Картын луйврын олон улсын судалгаагаар залилан хийж буй этгээдүүд икоммерс платформууд дээр зөвшөөрөлгүй гүйлгээ хийхдээ хамгийн их ашигладаг мөн хамгийн их хохирол учруулдаг техник юу вэ? Энэхүү эрсдэлээс хамгаалах орчин үеийн хамгийн үр дүнтэй технологийн шийдэл аль нь вэ?
                a. Ашигладаг техник: АТМ скимминг хийх
                Үр дүнтэй шийдэл: Вэбсайтын SSL/TLS шийдлийг суулгах
                b. Ашигладаг техник: Картын мэдээллийг хулгайлахын тулд нууц камер ашиглах
                Үр дүнтэй шийдэл: Харилцагчийн нууц үгийг сар тутамд өөрчлөх
                c. Ашигладаг техник: Картын мэдээллийг фишинг болон хуурамч вэбсайтаар дамжуулан авч, түүгээр икоммерс гүйлгээ гаргах
                Үр дүнтэй шийдэл: Гүйлгээний үед нэмэлт баталгаажуулалт хэрэглэх
                d. Ашигладаг техник: Банкны дотоод сүлжээнд нэвтэрч, мэдээллийн санг хулгайлах
                Үр дүнтэй шийдэл: Зөвхөн бэлэн мөнгөөр гүйлгээ хийхийг зөвлөх
                """, "answer": "c"}
    },
    "Танин мэдэхүй": {
        100: {"question": "Хэзээ ч буурдаггүй үргэлж өсч байдаг зүйл юу?", "answer": "Нас"},
        200: {"question": "Хоттой боловч байшингүй, ойтой боловч модгүй, голтой боловч усгүй тэр юу вэ?", "answer": "Газрын зураг"},
        300: {"question": """Mонгол улс газар нутгаараа дэлхийд хэддүгээрт ордог вэ?
                a. 11
                b. 23
                c. 21
                d. 18
                """, "answer": "d"},
        400: {"question": "Дэлхийн хамтгийн том цөл юу вэ?", "answer": "Антрактид"},
        500: {"question": "Газар дээрх хамгийн хурдан амьтан үчимбэр бол усан доторх хамгийн хурдан амьтан юу вэ?", "answer": "Далбаат загас"}
    },
    "General": {
        100: {"question": "How many sides does a hexagon have?", "answer": "6"},
        200: {"question": "What is the largest mammal?", "answer": "Blue whale"},
        300: {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci"},
        400: {"question": "What is the chemical formula for water?", "answer": "H2O"},
        500: {"question": "What year did World War II end?", "answer": "1945"}
    }
}

# -------------------
# Session variables
# -------------------
def init_game():
    session["score"] = 0
    session["answered"] = []  # list of [category, points]
    session["start_time"] = time.time()
    session.setdefault("player_name", "Player 1")

@app.route("/")
def index():
    # require login
    if 'user' not in session:
        return render_template('login.html')

    if "score" not in session:
        init_game()
    return render_template("index.html", questions=questions, player_name=session.get("player_name", "Player 1"), answered=session.get('answered', []), game_duration=GAME_DURATION)


@app.route('/set_name', methods=['POST'])
def set_name():
    data = request.get_json()
    name = data.get('name', '').strip()
    if name:
        session['player_name'] = name
    return jsonify({'status': 'ok', 'player_name': session.get('player_name', 'Player 1')})

@app.route("/check_answer", methods=["POST"])
def check_answer():
    data = request.get_json()
    category = data["category"]
    points = int(data["points"])
    answer = data["answer"].strip().lower()

    # Prevent answering after time is up
    elapsed = time.time() - session.get("start_time", 0)
    if elapsed >= GAME_DURATION:
        return jsonify({"status": "time_up"})

    q_data = questions[category][points]
    correct_answer = q_data["answer"].strip().lower()

    # Check if already answered
    if [category, points] in session.get("answered", []):
        return jsonify({"status": "already_answered"})

    # Check answer
    if answer == correct_answer:
        session["score"] += points
        result = "correct"
    else:
        result = "incorrect"

    # Mark question as answered
    session["answered"].append([category, points])

    return jsonify({"result": result, "score": session["score"]})

@app.route("/time_left")
def time_left():
    elapsed = time.time() - session.get("start_time", 0)
    remaining = max(0, GAME_DURATION - int(elapsed))
    return jsonify({"time_left": remaining})

@app.route("/end_game", methods=["POST"])
def end_game():
    # Prepare final score and submit to local user.json + optional CTFd endpoint
    final_score = session.get("score", 0)
    player = session.get('player_name', session.get('user', 'Player 1'))

    # Build a submission object with better timestamp and uuid id
    submission = {
        "success": True,
        "data": {
            "challenge": {"category": "UG", "value": 1, "name": "UG", "id": 8},
            "team": None,
            "user_id": session.get('user_id'),
            "date": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
            "id": str(uuid.uuid4()),
            "user": {"name": player, "id": session.get('user_id')},
            "type": "correct",
            "ip": None,
            "challenge_id": 8,
            "team_id": None,
            "provided": f"Final score: {final_score}",
            "meta": {"session_user_token": session.get('user_token')}
        }
    }

    # Optionally skip appending zero-score submissions to reduce noise
    append_submission = final_score != 0

    # Update users and submissions atomically using the helper
    try:
        def cb(data):
            modified = False
            data.setdefault('users', [])
            data.setdefault('submissions', [])

            # update user record if present
            users = data['users']
            user_rec = None
            for u in users:
                if session.get('user_id') and u.get('user_id') == session.get('user_id'):
                    user_rec = u
                    break
                if session.get('user_token') and u.get('token') == session.get('user_token'):
                    user_rec = u
                    break

            if user_rec is not None:
                user_rec['last_final_score'] = final_score
                # mark logged_status true here for audit; we'll clear it below after awards
                user_rec['logged_status'] = True
                modified = True

            # append submission only if meaningful
            if append_submission:
                # dedupe: ensure we don't already have this uuid
                existing_ids = {s.get('data', {}).get('id') for s in data['submissions']}
                if submission['data']['id'] not in existing_ids:
                    data['submissions'].append(submission)
                    modified = True

            return modified

        update_users_with_callback(cb)
    except Exception as e:
        print('Failed to persist submission/users atomically:', e)

    # If final_score > 0, POST an award to the specified awards endpoint once per user (persisted)
    award_result = None
    try:
        import requests
        final = final_score
        if final > 0:
            # find user record from file (best-effort)
            data_root = read_users_data()
            user_rec = None
            for u in data_root.get('users', []):
                if session.get('user_id') and u.get('user_id') == session.get('user_id'):
                    user_rec = u
                    break
                if session.get('user_token') and u.get('token') == session.get('user_token'):
                    user_rec = u
                    break

            if user_rec is not None:
                # diagnostic
                print('Found user_rec for award:', user_rec.get('user_id'))
                # skip if already awarded
                prev_status = user_rec.get('award_response_status')
                already_awarded = user_rec.get('award_sent') or (isinstance(prev_status, int) and 200 <= prev_status < 300)
                print('already_awarded=', already_awarded, 'award_sent=', user_rec.get('award_sent'), 'prev_status=', prev_status)
                if not already_awarded:
                    awards_url = "http://95.40.100.151/api/v1/awards"
                    fixed_token = "ctfd_e1c32838169d3b76f9e1588f992546e35ec7fd39ece8caacecc90b40edead800"
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Token {fixed_token}'
                    }
                    award_payload = {
                        "user_id": user_rec.get('user_id'),
                        "team_id": None,
                        "name": "Bonus: JoePardy",
                        "description": "JoePardy systemiin damjuulj ogson bonus onoo",
                        "value": final,
                        "category": "bonus"
                    }
                    print("[+]")
                    try:
                        print('Posting award to', awards_url)
                        print('Payload:', award_payload)
                        resp = requests.post(awards_url, json=award_payload, headers=headers, timeout=5)
                        status = getattr(resp, 'status_code', None)
                        body_text = None
                        try:
                            body_text = resp.text
                        except Exception:
                            body_text = None
                        award_result = {'attempted': True, 'status': status, 'body': body_text}
                        print('Award POST response status:', status)
                        print('Award POST response body (truncated):', (body_text or '')[:300])
                    except Exception as e:
                        award_result = {'attempted': True, 'error': str(e)}
                        print('Award POST exception:', e)

                    # persist the award attempt and update user record atomically
                    def persist_award(data):
                        modified = False
                        data.setdefault('users', [])
                        data.setdefault('submissions', [])
                        # find persisted user rec
                        persisted = None
                        for uu in data['users']:
                            if session.get('user_id') and uu.get('user_id') == session.get('user_id'):
                                persisted = uu
                                break
                            if session.get('user_token') and uu.get('token') == session.get('user_token'):
                                persisted = uu
                                break
                        # attach audit entry
                        audit = {'award_payload': award_payload}
                        if award_result is not None:
                            audit.update(award_result)
                        data['submissions'].append(audit)
                        modified = True
                        if persisted is not None and award_result and award_result.get('status') and isinstance(award_result.get('status'), int) and 200 <= award_result.get('status') < 300:
                            persisted['award_sent'] = True
                            persisted['award_response_status'] = award_result.get('status')
                            modified = True
                        elif persisted is not None and award_result and award_result.get('error'):
                            persisted['award_sent'] = False
                            persisted['award_response_status'] = None
                            modified = True
                        return modified

                    try:
                        update_users_with_callback(persist_award)
                    except Exception as e:
                        print('Failed persisting award attempt:', e)
    except Exception as e:
        print('Awards submission failed:', e)

    # After handling final score and awards, clear session and cookie (time finished ends session)
    # clear persisted logged_status for the current user so they can log in later
    try:
        def clear_logged_status_cb(data):
            modified = False
            data.setdefault('users', [])
            for u in data['users']:
                if session.get('user_id') and u.get('user_id') == session.get('user_id'):
                    if u.get('logged_status'):
                        u['logged_status'] = False
                        modified = True
                    break
            return modified

        update_users_with_callback(clear_logged_status_cb)
    except Exception as e:
        print('Failed to clear logged_status in user.json:', e)

    resp = jsonify({"status": "game_over", "final_score": final_score, "submitted": True})
    try:
        session.clear()
        # clear the session cookie by setting an expired cookie
        resp.set_cookie(app.session_cookie_name, '', expires=0)
    except Exception:
        pass
    return resp


# --- user login/token handling (appended) ---
import json
from pathlib import Path

USERS_FILE = Path(__file__).parent / 'user.json'
try:
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            USER_DATA = json.load(f).get('users', [])
    else:
        USER_DATA = []
except Exception:
    USER_DATA = []


def read_users_data():
    """Read users file under a shared lock and return parsed JSON (dict).
    If the file doesn't exist, return an empty structure.
    """
    if not USERS_FILE.exists():
        return {"users": [], "submissions": []}
    with open(USERS_FILE, 'r') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass
    return data


def write_users_data_atomic(data):
    """Write `data` to USERS_FILE atomically. Uses a temp file and os.replace.
    Acquires an exclusive lock on the target file path during the replace to
    reduce race windows.
    """
    # ensure parent dir exists
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=USERS_FILE.name, dir=str(USERS_FILE.parent))
    try:
        with os.fdopen(tmp_fd, 'w') as tf:
            json.dump(data, tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())

        # Acquire exclusive lock on the existing file (or create it) while doing replace
        # so other processes that also lock will wait.
        # Open target file for locking (create if missing)
        open_mode = 'a+'
        with open(USERS_FILE, open_mode) as lockf:
            try:
                fcntl.flock(lockf, fcntl.LOCK_EX)
                os.replace(tmp_path, str(USERS_FILE))
            finally:
                try:
                    fcntl.flock(lockf, fcntl.LOCK_UN)
                except Exception:
                    pass
    finally:
        # cleanup leftover temp if any
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def update_users_with_callback(callback):
    """Read users data, call callback(data) which may modify it, then write back atomically.
    The callback should return True if it modified the data and False otherwise.
    """
    data = read_users_data()
    try:
        modified = callback(data)
    except Exception:
        raise
    if modified:
        write_users_data_atomic(data)
    return data


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    token = request.form.get('token', '').strip()
    # Validate token and enforce single-login using persisted user.json
    data = read_users_data()
    users = data.get('users', [])
    for u in users:
        if u.get('token') == token:
            # if already logged (persisted), deny login
            if u.get('logged_status'):
                return render_template('login.html', error='This user has already logged in')
            # accept login, set session
            session['user'] = u.get('name')
            session['player_name'] = u.get('name')
            session['user_token'] = u.get('token')
            session['user_id'] = u.get('user_id')
            init_game()

            # persist logged_status atomically
            def set_logged_cb(d):
                modified = False
                d.setdefault('users', [])
                for uu in d['users']:
                    if uu.get('token') == token:
                        if not uu.get('logged_status'):
                            uu['logged_status'] = True
                            modified = True
                        break
                return modified

            try:
                update_users_with_callback(set_logged_cb)
            except Exception:
                # fallback: if persisting fails, continue with in-memory session
                pass

            return render_template('index.html', questions=questions, player_name=session.get('player_name'), answered=session.get('answered', []), game_duration=GAME_DURATION)

    # invalid token
    return render_template('login.html', error='Invalid token')


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')



if __name__ == "__main__":
    # Load users again in case file changed during development
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r') as f:
                USER_DATA = json.load(f).get('users', [])
    except Exception:
        USER_DATA = []

    # Bind explicitly to localhost and use an alternate port to avoid macOS services
    # that may already be listening on port 5000 (e.g. Control Center / AirPlay).
    app.run(host='0.0.0.0', port=8000, debug=True)

