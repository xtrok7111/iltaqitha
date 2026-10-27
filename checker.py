import os, re, json, time
from PIL import Image, ImageFilter, ImageStat
from google import genai
from google.genai import types

# جربت gemini-2.5-flash بس صار ما يشتغل للمفاتيح الجديدة
MODEL = 'gemini-3.5-flash'
# لو خلصت الحصة اليومية (20 طلب بالمجاني) نجرب هذا
MODEL2 = 'gemini-flash-lite-latest'

extract_prompt = """Read these lab instructions. Return only the steps that ask the student to take a screenshot.
For each step return:
step_no, title (short, in Arabic), evidence (list of things that must be visible in the screenshot),
temporary (true if the output disappears when the program is closed).
If the step has a command, the command itself must be in evidence not only the output,
and the username/hostname in the terminal prompt if it is a terminal.
Do not add steps that are not in the instructions.
Return JSON: {"steps": [...]}

Instructions:
"""

check_prompt = """This screenshot is for this step: %s
Things that must be visible:
%s

Rules:
accepted = everything in the list is visible and readable
missing = something is missing or the output is wrong or it is a screenshot of another step (output without the command = missing)
unclear = text can't be read
Don't guess.
Return JSON: {"status": "", "missing": [], "confidence": 0-100, "note": "short note in Arabic"}"""


def get_client(key=None):
    if not key:
        key = os.getenv("GEMINI_API_KEY")
    if key:
        return genai.Client(api_key=key)
    return None


def ask(client, contents):
    # النسخة المجانية 5 طلبات بالدقيقة بس، فلو طلع خطأ ننتظر ونعيد
    model = MODEL
    for i in range(4):
        try:
            res = client.models.generate_content(model=model, contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
            return json.loads(res.text)
        except Exception as e:
            if i == 3:
                raise
            print("retry", i + 1, str(e)[:50])
            if "PerDay" in str(e) and model != MODEL2:
                model = MODEL2
                continue
            time.sleep(20)


def extract_steps(text, client):
    if client:
        try:
            data = ask(client, [extract_prompt + text])
            # print(data)
            return data["steps"]
        except Exception as e:
            print("AI failed:", e)

    # بدون AI: أي سطر فيه screenshot او صور
    steps = []
    for line in text.splitlines():
        l = line.lower().replace("ّ", "")  # عشان صوّر
        if "screenshot" in l or "صور" in l:
            m = re.match(r"(\d+)\.\s*", line)
            if m:
                no = int(m.group(1))
                title = line[m.end():]
            else:
                no = len(steps) + 1
                title = line
            temp = False
            if "تختفي" in l or "يختفي" in l:
                temp = True
            steps.append({"step_no": no, "title": title, "evidence": ["المطلوب في الخطوة ظاهر"], "temporary": temp})
    return steps


def check_image(img, step, client):
    # اول شي نشوف الصورة نفسها قبل نرسلها
    if img.width < 500:
        return {"status": "unclear", "note": "الصورة صغيرة، صور الشاشة كاملة"}

    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    sharpness = ImageStat.Stat(edges).var[0]
    # الصور المغبشة طلعت تحت 50 والواضحة فوق 700 فحطيت 100
    if sharpness < 100:
        return {"status": "unclear", "note": "الصورة مغبشة صورها مرة ثانية"}

    if client is None:
        return {"status": "review", "note": "راجعها بنفسك"}

    evidence = "\n".join(step["evidence"])
    try:
        r = ask(client, [check_prompt % (step["title"], evidence), img.convert("RGB")])
    except Exception as e:
        print(e)
        return {"status": "error", "note": "صار خطأ بالتحليل، راجعها بنفسك"}

    if "status" not in r:
        r["status"] = "unclear"
    # لو قال مقبولة بس هو مو متأكد ما نعتمدها
    if r["status"] == "accepted" and r.get("confidence", 0) < 70:
        r["status"] = "review"
    return r

# TODO: لو فيه وقت نخليه يصور الشاشة تلقائي بدل الرفع
