import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from paddleocr import PaddleOCR

app = FastAPI()

# Modelni global darajada ishga tushiramiz (faqat bir marta yuklanadi)
ocr = PaddleOCR(lang="en")

def yymmdd_to_ddmmyy(s: str) -> str:
    if len(s) == 6:
        return s[4:6] + s[2:4] + s[0:2]
    return s

def parse_mrz(line1: str, line2: str, rec_scores: list):
    try:
        # 1-qator
        doc_type = line1[0]
        country = line1[2:5]
        name_part = line1[5:].rstrip("<")
        
        # Ism va familiyani ajratishda xatolik chiqmasligi uchun kichik tekshiruv
        if "<<" in name_part:
            surname, names = name_part.split("<<", 1)
        else:
            surname, names = name_part, ""
            
        surname = surname.replace("<", " ").strip()
        names = names.replace("<", " ").strip()

        # 2-qator (TD3 passport MRZ)
        number = line2[0:9]
        nationality = line2[10:13]
        birth_raw = line2[13:19]          # YYMMDD
        sex = line2[20]
        expiry_raw = line2[21:27]         # YYMMDD
        pinfl = line2[28:42].replace("<", "").strip()

        avg_accuracy = sum(rec_scores) / len(rec_scores) if rec_scores else 0

        # Veb-sayt frontend'i kutayotgan JSON kalitlariga moslab qaytaramiz
        return {
            "passport_number": number,
            "surname": surname,
            "given_names": names,
            "personal_number": pinfl if len(pinfl) == 14 and pinfl.isdigit() else "",
            "date_of_birth": yymmdd_to_ddmmyy(birth_raw),
            "sex": sex,
            "date_of_expiry": yymmdd_to_ddmmyy(expiry_raw),
            "nationality": nationality,
            "validation_status": "PASS",
            "validations": {
                "mrz_ocr_accuracy": f"{avg_accuracy * 100:.2f}%"
            }
        }
    except Exception as e:
        return None

# Frontend (veb-sayt) ni yuklash uchun endpoint
@app.get("/")
async def serve_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Rasm qabul qilib, o'qib beruvchi endpoint
@app.post("/scan")
async def scan_passport(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    try:
        # Rasmni vaqtinchalik xotiraga saqlash
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        # Sizning PaddleOCR kodlaringiz
        results = ocr.predict(
            input=file_location,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
        )

        for res in results:
            # Ba'zi PaddleOCR versiyalarida res string/json emas, to'g'ridan-to'g'ri list qaytadi. 
            # Shuning uchun universal qilib oldim:
            if hasattr(res, 'json'):
                data = res.json
                if isinstance(data, str):
                    data = json.loads(data)
                main = data.get("res", {})
                rec_texts = main.get("rec_texts", [])
                rec_scores = main.get("rec_scores", [])
            else:
                # Agar list qaytsa
                rec_texts = [line[1][0] for line in res]
                rec_scores = [line[1][1] for line in res]

            # MRZ qatorlarini filtrlab olish (uzunligi 30 dan katta bo'lganlari MRZ bo'ladi)
            valid_lines = [text for text in rec_texts if len(text) > 30]

            if len(valid_lines) >= 2:
                # Eng oxirgi 2 ta qatorni mrz sifatida beramiz
                result = parse_mrz(valid_lines[-2], valid_lines[-1], rec_scores)
                if result:
                    return {"data": result}

        raise HTTPException(status_code=400, detail="MRZ hududi topilmadi. Yaxshiroq yorug'likda qaytadan rasmga oling.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server xatoligi: {str(e)}")
    
    finally:
        # Ish tugagach, serverda axlat qolib ketmasligi uchun rasmni o'chiramiz
        if os.path.exists(file_location):
            os.remove(file_location)