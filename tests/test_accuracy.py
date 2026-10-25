import sys
import csv
from PIL import Image
sys.path.append(".")
from checker import get_client, extract_steps, check_image

client = get_client()
text = open("sample/exercise_linux.txt", encoding="utf-8").read()
steps = extract_steps(text, client)

print("steps:", [s["step_no"] for s in steps], "expected: [1, 3, 4, 5]")
print("temporary:", [s["step_no"] for s in steps if s.get("temporary")], "expected: [5]")
for s in steps:
    print(s["step_no"], s["evidence"])

steps = {s["step_no"]: s for s in steps}
correct = 0
caught = 0
total_bad = 0
out = open("tests/results.csv", "w", newline="", encoding="utf-8-sig")
w = csv.writer(out)
w.writerow(["file", "expected", "result", "note"])

for row in csv.DictReader(open("tests/expected.csv", encoding="utf-8")):
    img = Image.open("tests/images/" + row["file"])
    r = check_image(img, steps[int(row["step"])], client)
    print(row["file"], row["expected"], r["status"], r.get("note", ""))
    w.writerow([row["file"], row["expected"], r["status"], r.get("note", "")])
    if r["status"] == row["expected"]:
        correct += 1
    if row["expected"] != "accepted":
        total_bad += 1
        if r["status"] in ["missing", "unclear"]:
            caught += 1

out.close()
print(f"accuracy: {correct}/10")
print(f"incomplete caught: {caught}/{total_bad}")
