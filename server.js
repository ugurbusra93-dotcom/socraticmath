require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json({limit:'5mb'}));

const QUESTIONS_FILE = path.join(__dirname, 'questions.json');

const SYSTEM_PROMPT = "CEVAP FORMATI (KESINLIKLE UY):\n\n[HESAPLA]\nProblemi adim adim coz. Her islemi yaz: hangi sayilar, hangi islem, hangi sonuc. Sonucu iki kere kontrol et, farkli bir yoldan da dogrula.\n[/HESAPLA]\n\n[SONUC]\nDOGRU veya YANLIS (ogrencinin sectigi secenek, yukarida hesapladigin dogru cevaba uyuyor mu?)\n[/SONUC]\n\n[MESAJ]\nEger DOGRU ise: ictenlikle tebrik et\nEger YANLIS ise: TEK bir Sokratik soru sor\n[/MESAJ]\n\nRolun: Sen, matematik konusunda mutlak yetkinlige sahip bir uzman ve Sokratik yontemle ogrenciyi yonlendiren ust duzey bir pedagogsun.\n\nKritik Kurallar:\n- [HESAPLA] blogunda gercekten adim adim yaz, atlama yapma, her islemi goster\n- [SONUC] blogunda sadece DOGRU veya YANLIS yaz\n- [MESAJ] blogunda dogru cevabi asla soyleme veya ima etme, sadece soru veya tebrik yaz\n- Ogrenci anlamiyorsa farkli bir metafor kullan, ayni cumleyi tekrarlama\n- Her seferinde SADECE BIR soru sor\n- 7-8 yas seviyesine uygun basit ve somut dil kullan\n- [MESAJ] blogunun ici Markdown icermemeli, tek cumle olmali (tebrik haric)";

app.post('/api/chat', async function(req, res) {
  const messages = req.body.messages;

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY bulunamadi.' });
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 400,
        system: SYSTEM_PROMPT,
        messages: messages
      })
    });

    const data = await response.json();
    if (data.error) {
      return res.status(400).json({ error: data.error.message });
    }
    const reply = data.content.map(function(b) { return b.text || ''; }).join('').trim();
    res.json({ reply: reply });

  } catch (err) {
    res.status(500).json({ error: 'Sunucu hatasi: ' + err.message });
  }
});

app.post('/api/questions', function(req, res) {
  try {
    fs.writeFileSync(QUESTIONS_FILE, JSON.stringify(req.body.questions || []));
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/questions', function(req, res) {
  try {
    if (fs.existsSync(QUESTIONS_FILE)) {
      const data = fs.readFileSync(QUESTIONS_FILE, 'utf8');
      res.json({ questions: JSON.parse(data) });
    } else {
      res.json({ questions: [] });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 3000;
app.listen(PORT, function() {
  console.log('Mathique calisiyor: http://localhost:' + PORT);
});