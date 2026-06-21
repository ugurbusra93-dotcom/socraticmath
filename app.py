import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), 'questions.json')

SYSTEM_PROMPT = """CEVAP FORMATI (KESINLIKLE UY):

[HESAPLA]
Problemi adim adim coz. Her islemi yaz: hangi sayilar, hangi islem, hangi sonuc. Sonucu iki kere kontrol et, farkli bir yoldan da dogrula.
[/HESAPLA]

[SONUC]
DOGRU veya YANLIS (ogrencinin sectigi secenek, yukarida hesapladigin dogru cevaba uyuyor mu?)
[/SONUC]

[MESAJ]
Eger DOGRU ise: ictenlikle tebrik et
Eger YANLIS ise: TEK bir Sokratik soru sor
[/MESAJ]

Rolun: Sen, matematik konusunda mutlak yetkinlige sahip bir uzman ve Sokratik yontemle ogrenciyi yonlendiren ust duzey bir pedagogsun.

Kritik Kurallar:
- [HESAPLA] blogunda gercekten adim adim yaz, atlama yapma, her islemi goster
- [SONUC] blogunda sadece DOGRU veya YANLIS yaz
- [MESAJ] blogunda dogru cevabi asla soyleme veya ima etme, sadece soru veya tebrik yaz
- Ogrenci anlamiyorsa farkli bir metafor kullan, ayni cumleyi tekrarlama
- Her seferinde SADECE BIR soru sor
- 7-8 yas seviyesine uygun basit ve somut dil kullan
- [MESAJ] blogunun ici Markdown icermemeli, tek cumle olmali (tebrik haric)"""


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
                'max_tokens': 400,
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
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        if os.path.exists(QUESTIONS_FILE):
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            return jsonify({'questions': questions})
        else:
            return jsonify({'questions': []})
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
    print(f'Mathique calisiyor: http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)