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
