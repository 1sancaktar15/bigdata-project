#!/bin/bash

echo "Tüm docker servisleri başlatılıyor..."
docker-compose up -d

echo ""
echo "Data generator başlatılıyor..."
docker-compose exec data-generator python app.py &

echo ""
echo "Jupyter Lab için bağlantı: http://localhost:8888"
