from paddleocr import PaddleOCR
import json

def yymmdd_to_ddmmyy(s: str) -> str:
    if len(s) == 6:
        return s[4:6] + s[2:4] + s[0:2]
    return s

def parse_mrz(line1: str, line2: str, rec_scores: list):
    # 1-qator
    doc_type = line1[0]
    country = line1[2:5]
    name_part = line1[5:].rstrip("<")
    surname, names = name_part.split("<<", 1)
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

    return {
        "type": doc_type,
        "country": country,
        "surname": surname,
        "names": names,
        "number": number,
        "nationality": nationality,
        "date_of_birth": yymmdd_to_ddmmyy(birth_raw),     # DDMMYY
        "sex": sex,
        "expiration_date": yymmdd_to_ddmmyy(expiry_raw),  # DDMMYY
        "PINFL": pinfl if len(pinfl) == 14 and pinfl.isdigit() else "",
        "accuracy": f"{avg_accuracy * 100:.2f}%"
    }

ocr = PaddleOCR(lang="en")

results = ocr.predict(
    input="2.png",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
)

for res in results:
    data = res.json
    if isinstance(data, str):
        data = json.loads(data)

    main = data.get("res", {})
    rec_texts = main.get("rec_texts", [])
    rec_scores = main.get("rec_scores", [])

    if len(rec_texts) >= 2:
        result = parse_mrz(rec_texts[0], rec_texts[1], rec_scores)
        print(json.dumps(result, indent=2, ensure_ascii=False))