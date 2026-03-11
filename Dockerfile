FROM python:3.10-slim

# OpenCV va PaddleOCR ishlashi uchun kerakli tizim kutubxonalari
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval oddiy kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# SIZ SO'RAGAN MAXSUS MUHIT (ENVIRONMENT) O'RNATILISHI:
RUN python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
RUN python -m pip install "paddleocr[all]"

# Qolgan barcha kodlarni (server.py va index.html) nusxalaymiz
COPY . .

# Serverni ishga tushirish (Railway portini avtomatik ulaydi)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]