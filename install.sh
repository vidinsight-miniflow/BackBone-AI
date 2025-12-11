#!/bin/bash
# BackBone-AI Quick Install Script

set -e

echo "=================================="
echo "BackBone-AI Kurulum"
echo "=================================="
echo ""

# Check Python version
echo "✓ Python versiyonu kontrol ediliyor..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python $python_version bulundu"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "✓ Virtual environment oluşturuluyor..."
    python3 -m venv venv
    echo "  ✓ Virtual environment oluşturuldu"
else
    echo "✓ Virtual environment zaten mevcut"
fi
echo ""

# Activate virtual environment
echo "✓ Virtual environment aktifleştiriliyor..."
source venv/bin/activate
echo ""

# Upgrade pip
echo "✓ pip güncelleniyor..."
pip install --upgrade pip > /dev/null 2>&1
echo "  ✓ pip güncellendi"
echo ""

# Install dependencies
echo "✓ Bağımlılıklar yükleniyor..."
echo "  (Bu birkaç dakika sürebilir...)"
pip install -r requirements.txt > /dev/null 2>&1
echo "  ✓ Tüm bağımlılıklar yüklendi"
echo ""

# Create .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "✓ .env dosyası oluşturuluyor..."
    cp .env.example .env
    echo "  ✓ .env dosyası oluşturuldu"
    echo ""
    echo "⚠️  DİKKAT: .env dosyasını düzenleyip API anahtarınızı ekleyin!"
    echo ""
else
    echo "✓ .env dosyası zaten mevcut"
    echo ""
fi

echo "=================================="
echo "✅ Kurulum tamamlandı!"
echo "=================================="
echo ""
echo "Sonraki adımlar:"
echo ""
echo "1. API anahtarınızı ekleyin:"
echo "   nano .env"
echo ""
echo "2. Kodu test edin:"
echo "   source venv/bin/activate"
echo "   backbone-ai generate --schema examples/simple_schema.json"
echo ""
echo "3. API modunda çalıştırın:"
echo "   uvicorn app.api.main:app --reload"
echo ""
echo "Daha fazla bilgi: README.md veya QUICKSTART.md"
echo ""
