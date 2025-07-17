@echo off
echo Tum docker servisleri baslatiliyor...
docker-compose up -d

echo.
echo Data generator baslatiliyor...
docker-compose exec data-generator python app.py

echo.
echo Jupyter Lab icin baglanti: http://localhost:8888

pause
