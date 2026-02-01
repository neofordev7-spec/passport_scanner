from flask import Flask, render_template, request, jsonify
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import cv2
import numpy as np
import os
import re

app = Flask(__name__)

# -----------------------------------------------------------
# HUGGING FACE: LARGE MODELNI YUKLASH
# -----------------------------------------------------------
print("⏳ TrOCR Large modeli yuklanmoqda (Kutib turing, hajm katta)...")

# 'large-printed' - eng aniq versiyasi
processor = TrOCRProcessor.from_pretrained('microsoft/trocr-large-printed')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-printed')

print("✅ Model tayyor! Server ishga tushdi.")

def clean_mrz_text(text):
    """
    Model natijasini tozalash.
    MRZda faqat A-Z, 0-9 va < bo'ladi.
    """
    text = text.upper().replace(" ", "")
    # Faqat ruxsat berilgan belgilarni qoldiramiz
    text = re.sub(r'[^A-Z0-9<]', '', text)
    return text

def read_line_with_trocr(image_cv2):
    """
    Bitta qator rasmni o'qish
    """
    # OpenCV -> PIL formatga o'tkazish
    image_pil = Image.fromarray(cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)).convert("RGB")
    
    # Modelga yuborish
    pixel_values = processor(images=image_pil, return_tensors="pt").pixel_values
    
    # Generatsiya
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return clean_mrz_text(generated_text)

def process_mrz_image(image_path):
    """
    MRZ rasmini 2 ga bo'lib o'qiydi (Chunki TrOCR bir qatorli matnni yaxshi o'qiydi)
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    # 1. Oq-qora qilish
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Rasmni 2 barobar kattalashtirish (Large modelga mayda detal yoqadi)
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 3. Rasmni o'rtasidan bo'lish (Tepa va Pastki qator)
    h, w = img.shape
    mid = h // 2
    
    # Qatorlarni sal kengroq qilib kesamiz (xatolikni kamaytirish uchun)
    top_crop = img[0:mid, 0:w]      
    bottom_crop = img[mid:h, 0:w]   

    # 4. O'qish
    print("   ... 1-qator o'qilmoqda")
    line1 = read_line_with_trocr(top_crop)
    
    print("   ... 2-qator o'qilmoqda")
    line2 = read_line_with_trocr(bottom_crop)

    results = []
    # MRZ qatori odatda 30-44 belgi bo'ladi
    if len(line1) > 20: results.append(line1)
    if len(line2) > 20: results.append(line2)
    
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Fayl tanlanmadi'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Fayl nomi yo\'q'})

    temp_path = "temp_large.jpg"
    file.save(temp_path)

    try:
        print(f"🚀 Tahlil boshlandi (Large Model): {file.filename}")
        
        lines = process_mrz_image(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if lines:
            print(f"✅ Natija: {lines}")
            return jsonify({'success': True, 'lines': lines})
        else:
            print("❌ O'qib bo'lmadi")
            return jsonify({'success': False, 'error': "MRZ o'qilmadi. Rasmda faqat MRZ zonasi borligiga ishonch hosil qiling."})

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Xatolik: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)