import io
import zipfile
from datetime import datetime
import streamlit as st
from PIL import Image
from checker import get_client, extract_steps, check_image

st.set_page_config(page_title="التقطها")
st.markdown("<style>.stApp {direction: rtl; text-align: right;}</style>", unsafe_allow_html=True)

status_ar = {"accepted": "مقبولة", "missing": "ناقصة", "unclear": "غير واضحة",
             "review": "تحتاج مراجعتك", "error": "ما تم التحليل"}

if "steps" not in st.session_state:
    st.session_state.steps = []
    st.session_state.results = {}
results = st.session_state.results

key = st.sidebar.text_input("Gemini API Key", type="password")
client = get_client(key)
if st.sidebar.button("التمرين التجريبي"):
    st.session_state.text = open("sample/exercise_linux.txt", encoding="utf-8").read()


def done(no):
    r = results.get(no)
    return r is not None and (r["status"] == "accepted" or r.get("ok"))


st.title("التقطها")
text = st.text_area("الصق تعليمات التمرين", height=200, key="text")
if st.button("استخرج الخطوات"):
    st.session_state.steps = extract_steps(text, client)
    st.session_state.results = results = {}

steps = st.session_state.steps
if not steps:
    st.stop()

count = len([s for s in steps if done(s["step_no"])])
st.progress(count / len(steps), text=f"{count} من {len(steps)}")

temp = [str(s["step_no"]) for s in steps if s.get("temporary") and not done(s["step_no"])]
if temp:
    st.warning("خطوة " + ", ".join(temp) + " الناتج يختفي اذا قفلت البرنامج، صورها وهو شغال")

if results:
    last = max(results)
    skipped = [str(s["step_no"]) for s in steps if s["step_no"] < last and not done(s["step_no"])]
    if skipped:
        st.error("نسيت خطوة " + ", ".join(skipped))

for s in steps:
    no = s["step_no"]
    st.subheader(f"خطوة {no}: {s['title']}")
    st.write("لازم يظهر: " + "، ".join(s["evidence"]))
    f = st.file_uploader("ارفع الصورة", type=["png", "jpg", "jpeg"], key=f"f{no}")
    if f and (no not in results or results[no]["name"] != f.name):
        r = check_image(Image.open(f), s, client)
        r["name"] = f.name
        r["data"] = f.getvalue()
        r["time"] = datetime.now().strftime("%H:%M")
        results[no] = r
        st.rerun()
    if no in results:
        r = results[no]
        st.write(status_ar.get(r["status"], r["status"]), "-", r.get("note", ""))
        if r.get("missing"):
            st.write("الناقص: " + "، ".join(r["missing"]))
        if r["status"] in ["review", "error"]:
            r["ok"] = st.checkbox("راجعتها وهي تمام", key=f"ok{no}")

st.divider()
if st.button("تأكد قبل ما تقفل البرنامج"):
    left = [s for s in steps if not done(s["step_no"])]
    if left:
        st.error("لا تقفل البرنامج، باقي خطوة " + ", ".join(str(s["step_no"]) for s in left))
    else:
        st.success("كل الخطوات موثقة")

if results:
    buf = io.BytesIO()
    report = ""
    with zipfile.ZipFile(buf, "w") as z:
        for no, r in sorted(results.items()):
            z.writestr(f"step{no}.png", r["data"])
            report += f"step {no}: {r['status']} {'(manual)' if r.get('ok') else ''} {r['time']}\n"
        z.writestr("report.txt", report)
    st.download_button("تحميل الصور", buf.getvalue(), "screenshots.zip")
