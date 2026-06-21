# SocraticMath 🧮
**Yanlışı Sorgulayarak Doğruyu İnşa Et**

Çocuklara matematiği ezberletmek yerine Sokratik sorularla kendi kendilerine buldurtan yapay zeka mentörü.

---

## Kurulum (5 dakika)

### 1. Node.js yükle
https://nodejs.org adresinden **LTS** sürümünü indir ve kur.

### 2. Proje klasörünü aç
Bu `socraticmath` klasörünü istediğin bir yere koy.
Terminal/komut satırında klasöre gir:
```
cd socraticmath
```

### 3. Paketleri yükle
```
npm install
```

### 4. API anahtarını ayarla
`.env.example` dosyasını kopyala, adını `.env` yap:
```
cp .env.example .env
```
Sonra `.env` dosyasını bir metin editörüyle aç ve şunu değiştir:
```
ANTHROPIC_API_KEY=buraya_api_anahtarini_yaz
```
API anahtarını https://console.anthropic.com adresinden alabilirsin.

### 5. Uygulamayı başlat
```
npm start
```

### 6. Tarayıcıda aç
```
http://localhost:3000
```

---

## Excel Formatı

Excel dosyan şu sütunları içermeli:

| problem | A | B | C | D | dogru | tur |
|---------|---|---|---|---|-------|-----|
| Ali'nin 12 bilyesi var... | 8 | 10 | 14 | 15 | B | çok adımlı |

- **problem**: Sorunun tam metni
- **A, B, C, D**: Şıklar
- **dogru**: Doğru şık harfi (A, B, C veya D)
- **tur**: Problem türü (isteğe bağlı — yazarsan AI analizi daha iyi yapar)

---

## Nasıl Çalışır?

1. Öğretmen Excel dosyasını yükler (öğrenci görmez)
2. Öğrenciye problem ve 4 şık gösterilir
3. Doğru şık → Tebrik mesajı
4. Yanlış şık → Socrates devreye girer:
   - Yanlış cevabı analiz eder (hangi hata tipi?)
   - Doğrudan cevap vermez
   - Sokratik sorularla öğrenciyi doğruya yönlendirir
5. Öğrenci Socrates ile sohbet ederek kendi cevabını bulur

---

## Geliştirme Modu (otomatik yenileme)
```
npm run dev
```
