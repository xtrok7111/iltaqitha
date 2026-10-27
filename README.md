# التقطها

تطبيق يساعد المتدرب يصور خطوات التمرين وهو يطبق، وينبهه اذا فيه صورة ناقصة قبل ما يقفل البرنامج.

## التشغيل

```
pip install -r requirements.txt
streamlit run app.py
```

حط Gemini API key في الشريط الجانبي. بدونه التطبيق يشتغل بس الصور تراجعها بنفسك.

## الاختبار

```
python tests/make_test_images.py
set GEMINI_API_KEY=...
python tests/test_accuracy.py
```

## صور من التطبيق

![](screenshots/1_steps.jpg)
![](screenshots/2_alerts.jpg)
![](screenshots/3_missing.jpg)
![](screenshots/4_before_close.jpg)

## نتيجة الاختبار

جربته على 10 صور (4 كاملة و 6 ناقصة): حكم على 10 صح، وكشف الـ 6 الناقصة. التفاصيل في `tests/results.csv`.
