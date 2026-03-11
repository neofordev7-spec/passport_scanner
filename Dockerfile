FROM python:3.10-slim

# OpenCV va PaddleOCR ishlashi uchun kerakli tizim kutubxonalari
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval oddiy kutubxonalarni o'rnatish
COPY requirements.txt .

# Pip'ni eng yangi versiyaga ko'tarish (yuklashdagi xatoliklarni kamaytiradi)
RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Maxsus muhit (environment) o'rnatilishi:
# Diqqat: Uzilib qolmasligi uchun timeout va retries qo'shildi!
RUN python -m pip install paddlepaddle==3.2.0 \
    --default-timeout=1000 \
    --retries=5 \
    --extra-index-url https://www.paddlepaddle.org.cn/packages/stable/cpu/

RUN python -m pip install "paddleocr[all]" \
    --default-timeout=1000 \
    --retries=5

# Qolgan barcha kodlarni nusxalaymiz
COPY . .

# Serverni ishga tushirish
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]