from paddleocr import PaddleOCR
import json

ocr = PaddleOCR(lang='en')

results = ocr.predict(
    input="2.png",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=True,
)

for res in results:
    # 1) Konsolga structured natijani chiqaradi
    res.print()

    # 2) JSON ko‘rinishiga olib ko‘ramiz
    data = res.json
    if isinstance(data, str):
        data = json.loads(data)


    a = json.dumps(data, indent=2, ensure_ascii=False)

    main = data.get("res", [])
    rec_texts = main.get("rec_texts", [])
    rec_scores = main.get("rec_scores", [])
    for text, score in zip(rec_texts, rec_scores):
        print(f"{text}      {float(100*score):.2f}%")