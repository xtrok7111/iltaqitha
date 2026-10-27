import io
import zipfile
from datetime import datetime
import streamlit as st
from PIL import Image
from checker import get_client, extract_steps, check_image

st.set_page_config(page_title="التقطها")
# عشان العربي
st.markdown("<style>.stApp {direction: rtl; text-align: right;}</style>", unsafe_allow_html=True)

if "steps" not in st.session_state:
    st.session_state.steps = []
    st.session_state.results = {}

key = st.sidebar.text_input("Gemini API Key", type="password")
client = get_client(key)
if st.sidebar.button("التمرين التجريبي"):
    st.session_state.text = open("sample/exercise_linux.txt", encoding="utf-8").read()


def status_text(s):
    if s == "accepted":
        return "مقبولة"
    elif s == "missing":
        return "ناقصة"
    elif s == "unclear":
        return "غير واضحة"
    elif s == "review":
        return "تحتاج مراجعتك"
    else:
        return "ما تم التحليل"


def is_done(no):
    r = st.session_state.results.get(no)
    if r is None:
        return False
    return r["status"] == "accepted" or r.get("ok") == True


st.title("التقطها")
st.write("حط تعليمات التمرين وارفع الصور اول باول وانت تطبق")

text = st.text_area("تعليمات التمرين", height=200, key="text")
if st.button("استخرج الخطوات"):
    st.session_state.steps = extract_steps(text, client)
    st.session_state.results = {}

steps = st.session_state.steps
results = st.session_state.results
# st.write(steps)

if len(steps) == 0:
    st.stop()

done_count = 0
for s in steps:
    if is_done(s["step_no"]):
        done_count += 1
st.progress(done_count / len(steps), text=f"{done_count} من {len(steps)} خطوات موثقة")

# الخطوات اللي تختفي لازم تتصور والبرنامج شغال
temp = []
for s in steps:
    if s.get("temporary") and not is_done(s["step_no"]):
        temp.append(str(s["step_no"]))
if temp:
    st.warning("انتبه: خطوة " + ", ".join(temp) + " الناتج يختفي اذا قفلت البرنامج، صورها وهو شغال")

# لو رفع صورة لخطوة متأخرة وفيه خطوة قبلها ناقصة
if results:
    last = max(results.keys())
    forgot = [str(s["step_no"]) for s in steps if s["step_no"] < last and not is_done(s["step_no"])]
    if forgot:
        st.error("نسيت خطوة " + ", ".join(forgot) + " قبل اللي بعدها")

for s in steps:
    no = s["step_no"]
    st.subheader(f"خطوة {no}: {s['title']}")
    st.write("لازم يظهر: " + "، ".join(s["evidence"]))

    f = st.file_uploader("ارفع الصورة", type=["png", "jpg", "jpeg"], key=f"file{no}")
    if f is not None:
        if no not in results or results[no]["name"] != f.name:
            with st.spinner("جاري الفحص..."):
                r = check_image(Image.open(f), s, client)
            r["name"] = f.name
            r["data"] = f.getvalue()
            r["time"] = datetime.now().strftime("%H:%M")
            results[no] = r
            st.rerun()

    if no in results:
        r = results[no]
        st.write("النتيجة:", status_text(r["status"]), "-", r.get("note", ""))
        if r.get("missing"):
            st.write("الناقص: " + "، ".join(r["missing"]))
        if r["status"] == "review" or r["status"] == "error":
            r["ok"] = st.checkbox("راجعتها وهي تمام", key=f"ok{no}")

st.divider()
if st.button("تأكد قبل ما تقفل البرنامج"):
    left = [str(s["step_no"]) for s in steps if not is_done(s["step_no"])]
    if left:
        st.error("لا تقفل البرنامج! باقي خطوة " + ", ".join(left))
    else:
        st.success("كل الخطوات موثقة تقدر تقفل البرنامج")

# تحميل الصور مرتبة مع تقرير
if results:
    buf = io.BytesIO()
    report = "تقرير التوثيق\n\n"
    with zipfile.ZipFile(buf, "w") as z:
        for no in sorted(results):
            r = results[no]
            z.writestr(f"step{no}.png", r["data"])
            line = f"step {no}: {r['status']} - {r['time']}"
            if r.get("ok"):
                line += " (راجعتها بنفسي)"
            report += line + "\n"
        z.writestr("report.txt", report)
    st.download_button("تحميل الصور", buf.getvalue(), "screenshots.zip")
