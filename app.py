import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')

DATABASE_URL = os.environ.get('DATABASE_URL')

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn


def init_db():
    if not DATABASE_URL or not PSYCOPG2_AVAILABLE:
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS questions_store ("
            "id SERIAL PRIMARY KEY, "
            "data JSONB NOT NULL, "
            "updated_at TIMESTAMP DEFAULT NOW()"
            ")"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS student_attempts ("
            "id SERIAL PRIMARY KEY, "
            "student_name TEXT NOT NULL, "
            "problem_text TEXT NOT NULL, "
            "selected_answer TEXT NOT NULL, "
            "is_correct BOOLEAN NOT NULL, "
            "attempt_number INTEGER NOT NULL, "
            "question_index INTEGER, "
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print('DB init error: ' + str(e))


init_db()

SYSTEM_PROMPT = (
    "CEVAP FORMATI (KESINLIKLE UY):\n\n"
    "[HESAPLA]\n"
    "Problemi adim adim coz. Her islemi yaz: hangi sayilar, hangi islem, hangi sonuc. Sonucu iki kere kontrol et, farkli bir yoldan da dogrula.\n"
    "[/HESAPLA]\n\n"
    "[SONUC]\n"
    "DOGRU veya YANLIS (ogrencinin sectigi secenek, yukarida hesapladigin dogru cevaba uyuyor mu?)\n"
    "[/SONUC]\n\n"
    "[MESAJ]\n"
    "Eger DOGRU ise: ictenlikle tebrik et\n"
    "Eger YANLIS ise: TEK bir Sokratik soru sor\n"
    "[/MESAJ]\n\n"
    "Rolun: Sen, matematik konusunda mutlak yetkinlige sahip bir uzman ve Sokratik yontemle ogrenciyi yonlendiren ust duzey bir pedagogsun.\n\n"
    "Kritik Kurallar:\n"
    "- [HESAPLA] blogunda gercekten adim adim yaz, atlama yapma, her islemi goster\n"
    "- [SONUC] blogunda sadece DOGRU veya YANLIS yaz\n"
    "- [MESAJ] blogunda dogru cevabi asla soyleme veya ima etme, sadece soru veya tebrik yaz\n"
    "- Ogrenci anlamiyorsa farkli bir metafor kullan, ayni cumleyi tekrarlama\n"
    "- Her seferinde SADECE BIR soru sor\n"
    "- 7-8 yas seviyesine uygun basit ve somut dil kullan\n"
    "- [MESAJ] blogunun ici Markdown icermemeli, tek cumle olmali (tebrik haric)"
)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY bulunamadi.'}), 500

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 800,
                'system': SYSTEM_PROMPT,
                'messages': messages
            }
        )
        result = response.json()

        if 'error' in result:
            return jsonify({'error': result['error'].get('message', 'API hatasi')}), 400

        reply = ''.join(block.get('text', '') for block in result.get('content', [])).strip()
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': 'Sunucu hatasi: ' + str(e)}), 500


@app.route('/api/questions', methods=['POST'])
def save_questions():
    try:
        data = request.get_json()
        questions = data.get('questions', [])

        if DATABASE_URL and PSYCOPG2_AVAILABLE:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM questions_store')
            cur.execute(
                'INSERT INTO questions_store (data) VALUES (%s)',
                (json.dumps(questions),)
            )
            conn.commit()
            cur.close()
            conn.close()
        else:
            with open('questions.json', 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        if DATABASE_URL and PSYCOPG2_AVAILABLE:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT data FROM questions_store ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return jsonify({'questions': row[0]})
            else:
                return jsonify({'questions': []})
        else:
            if os.path.exists('questions.json'):
                with open('questions.json', 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                return jsonify({'questions': questions})
            else:
                return jsonify({'questions': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/attempts', methods=['POST'])
def log_attempt():
    try:
        data = request.get_json()
        student_name = data.get('student_name', 'Bilinmeyen')
        problem_text = data.get('problem_text', '')
        selected_answer = data.get('selected_answer', '')
        is_correct = data.get('is_correct', False)
        attempt_number = data.get('attempt_number', 1)
        question_index = data.get('question_index', 0)

        if DATABASE_URL and PSYCOPG2_AVAILABLE:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO student_attempts '
                '(student_name, problem_text, selected_answer, is_correct, attempt_number, question_index) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (student_name, problem_text, selected_answer, is_correct, attempt_number, question_index)
            )
            conn.commit()
            cur.close()
            conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/attempts', methods=['GET'])
def get_attempts():
    try:
        if DATABASE_URL and PSYCOPG2_AVAILABLE:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'SELECT student_name, problem_text, selected_answer, is_correct, attempt_number, question_index, created_at '
                'FROM student_attempts ORDER BY created_at DESC LIMIT 500'
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            attempts = []
            for row in rows:
                attempts.append({
                    'student_name': row[0],
                    'problem_text': row[1],
                    'selected_answer': row[2],
                    'is_correct': row[3],
                    'attempt_number': row[4],
                    'question_index': row[5],
                    'created_at': row[6].isoformat() if row[6] else None
                })
            return jsonify({'attempts': attempts})
        else:
            return jsonify({'attempts': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print('Mathique calisiyor: http://localhost:' + str(port))
    app.run(host='0.0.0.0', port=port, debug=False)
