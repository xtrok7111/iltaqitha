from PIL import Image, ImageDraw, ImageFont, ImageFilter

font = ImageFont.load_default(size=20)
p = "trainee@ubuntu-lab:~/lab1$ "


def make(lines, name):
    img = Image.new("RGB", (900, 50 + len(lines) * 30), (30, 30, 30))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((15, 20 + i * 30), line, fill=(230, 230, 230), font=font)
    img.save("tests/images/" + name)
    return img


make(["trainee@ubuntu-lab:~$ whoami", "trainee", "trainee@ubuntu-lab:~$ hostname", "ubuntu-lab"], "complete/step1.png")
make([p + "touch notes.txt", p + "ls -l", "total 0", "-rw-r--r-- 1 trainee trainee 0 Oct 25 18:02 notes.txt"], "complete/step3.png")
make([p + "chmod 640 notes.txt", p + "ls -l", "total 0", "-rw-r----- 1 trainee trainee 0 Oct 25 18:04 notes.txt"], "complete/step4.png")
make([p + "python3 server.py", "Server running on port 8080"], "complete/step5.png")

# الناقصة
make(["trainee", "ubuntu-lab"], "incomplete/step1_no_command.png")
make([p + "ls -l", "total 0"], "incomplete/step3_no_file.png")
make([p + "chmod 644 notes.txt", p + "ls -l", "total 0", "-rw-r--r-- 1 trainee trainee 0 Oct 25 18:04 notes.txt"], "incomplete/step4_wrong_perm.png")
make([p + "touch notes.txt", p + "ls -l", "total 0", "-rw-r--r-- 1 trainee trainee 0 Oct 25 18:02 notes.txt"], "incomplete/step4_wrong_step.png")
make([p + "python3 server.py", "^C", "KeyboardInterrupt"], "incomplete/step5_after_close.png")
img = make([p + "python3 server.py", "Server running on port 8080"], "incomplete/step5_blurry.png")
img.resize((600, 80)).filter(ImageFilter.GaussianBlur(3)).save("tests/images/incomplete/step5_blurry.png")
