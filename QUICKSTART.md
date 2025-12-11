# 🚀 Hızlı Başlangıç (5 Dakika)

BackBone-AI'yi 3 adımda kurun ve kullanın.

---

## Otomatik Kurulum (Önerilen)

### Linux / Mac:
```bash
./install.sh
```

### Windows:
```cmd
install.bat
```

Kurulum scripti:
- ✅ Virtual environment oluşturur
- ✅ Tüm bağımlılıkları yükler
- ✅ .env dosyasını oluşturur

---

## Manuel Kurulum

### 1. Bağımlılıkları Yükle

```bash
# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. API Anahtarını Ekle

```bash
# .env dosyasını oluştur
cp .env.example .env

# Düzenle ve API anahtarını ekle
nano .env  # veya: notepad .env (Windows)
```

**Minimum konfigürasyon:**
```bash
# Bir provider seç
DEFAULT_LLM_PROVIDER=openai

# API anahtarını ekle
OPENAI_API_KEY=sk-your-key-here
```

**Provider seçenekleri:**
- `openai` - Hızlı ve kaliteli ($$$)
- `google` - En ucuz ($ - 10x daha ucuz!)
- `anthropic` - Karmaşık şemalar için ($$$$)

### 3. İlk Projeyi Oluştur

```bash
# Basit blog örneği
backbone-ai generate \
  --schema examples/simple_schema.json \
  --output ./my_blog
```

---

## Oluşturulan Kodu Kullan

```python
from models.database import create_tables, SessionLocal
from models.user import User
from models.post import Post

# Tabloları oluştur
create_tables()

# Session aç
db = SessionLocal()

# Kullanıcı oluştur
user = User(
    username="ahmet",
    email="ahmet@example.com",
    status="active"
)
db.add(user)
db.commit()

# Post oluştur
post = Post(
    title="İlk Yazım",
    content="Merhaba Dünya!",
    author_id=user.id,
    status="published"
)
db.add(post)
db.commit()

# Sorgula
all_users = db.query(User).all()
print(f"{len(all_users)} kullanıcı bulundu")

db.close()
```

---

## Örnekler

```bash
# Basit (2 tablo)
backbone-ai generate --schema examples/simple_schema.json

# Orta (5 tablo)
backbone-ai generate --schema examples/blog_schema.json

# Karmaşık (10+ tablo)
backbone-ai generate --schema examples/ecommerce_schema.json
```

---

## API Modu

```bash
# API'yi başlat
uvicorn app.api.main:app --reload

# Tarayıcıda aç
http://localhost:8000/docs

# Kod oluştur
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d @examples/simple_schema.json
```

---

## Sorun Giderme

### ImportError: No module named 'X'
**Çözüm:**
```bash
pip install -r requirements.txt
```

### API anahtarı yok
**Çözüm:**
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Rate limit aşıldı
**Çözüm:** Google'a geç (daha ucuz, daha yüksek limit)
```bash
DEFAULT_LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-key
```

---

## Oluşturulan Kod Özellikleri

✅ **Modern SQLAlchemy 2.0** - En yeni syntax
✅ **Type Hints** - Tam tip desteği
✅ **Async Destek** - Hem sync hem async
✅ **Otomatik Timestamps** - created_at, updated_at
✅ **Soft Delete** - Veri silmeden işaretle
✅ **İlişkiler** - Otomatik relationship'ler
✅ **Helper Methods** - to_dict(), soft_delete()

---

## Yardım

- Test: `python test_static_analysis.py`
- Konfigürasyon: `backbone-ai config`
- Yardım: `backbone-ai --help`
- Issues: https://github.com/vidinsight-miniflow/BackBone-AI/issues
