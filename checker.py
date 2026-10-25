import os
import re
import json
from PIL import Image, ImageFilter, ImageStat
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

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
    key = key or os.getenv("GEMINI_API_KEY")
    if key:
        return genai.Client(api_key=key)
    return None


def ask(client, contents):
    res = client.models.generate_content(
        model=MODEL, contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
    return json.loads(res.text)


# لو ما فيه api key ندور على كلمات
def extract_simple(text):
    steps = []
    for line in text.splitlines():
        l = line.lower().replace("ّ", "")
        if "screenshot" in l or "صور" in l:
            m = re.match(r"(\d+)\.\s*", line)
            steps.append({
                "step_no": int(m.group(1)) if m else len(steps) + 1,
                "title": line[m.end():] if m else line,
                "evidence": ["المطلوب في الخطوة ظاهر"],
                "temporary": "تختفي" in l or "يختفي" in l,
            })
    return steps


def extract_steps(text, client):
    if client:
        try:
            return ask(client, [extract_prompt + text])["steps"]
        except Exception as e:
            print(e)
    return extract_simple(text)


def check_image(img, step, client):
    if img.width < 500:
        return {"status": "unclear", "note": "الصورة صغيرة، صور الشاشة كاملة"}
    sharp = ImageStat.Stat(img.convert("L").filter(ImageFilter.FIND_EDGES)).var[0]
    if sharp < 100:
        return {"status": "unclear", "note": "الصورة مغبشة صورها مرة ثانية"}

    if not client:
        return {"status": "review", "note": "راجعها بنفسك"}

    try:
        r = ask(client, [check_prompt % (step["title"], "\n".join(step["evidence"])), img.convert("RGB")])
    except Exception as e:
        print(e)
        return {"status": "error", "note": "صار خطأ بالتحليل، راجعها بنفسك"}

    # اذا مو متأكد ما نقبلها
    if r["status"] == "accepted" and r.get("confidence", 0) < 70:
        r["status"] = "review"
    return r
