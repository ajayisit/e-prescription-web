from flask import Flask, render_template, request, send_file, session, redirect
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import sqlite3, os, qrcode

app = Flask(__name__)
app.secret_key = "change_this_secret"

# Doctor Credentials
USERNAME = "doctor"
PASSWORD = "1234"

# Doctor Info
DOCTOR_NAME = "Dr. Ajay Kumar Singh"
DOCTOR_REG = "DMC/42887"
CLINIC_NAME = "Ajay Health Clinic"
CONTACT: +918800588070

os.makedirs("prescriptions", exist_ok=True)

def get_serial():
    return "RX" + datetime.now().strftime("%Y%m%d%H%M%S")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["doctor"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/", methods=["GET","POST"])
def index():
    if not session.get("doctor"):
        return redirect("/login")

    if request.method == "POST":
        d = request.form
        serial = get_serial()
        pdf_path = f"prescriptions/{serial}.pdf"

        # Save patient history
        conn = sqlite3.connect("patients.db")
        c = conn.cursor()
        c.execute("""INSERT INTO prescriptions 
        VALUES (NULL,?,?,?,?,?,?)""",
        (d["patient_name"], d["age"], d["gender"],
         d["diagnosis"], d["medicines"],
         datetime.now().strftime("%d-%m-%Y")))
        conn.commit()
        conn.close()

        # QR
        qr = qrcode.make(f"{CLINIC_NAME} | {serial}")
        qr.save("static/qr.png")

        # PDF
        c = canvas.Canvas(pdf_path, pagesize=A4)
        w,h = A4

        c.setFont("Helvetica-Bold",16)
        c.drawString(50,h-50,CLINIC_NAME)

        c.setFont("Helvetica",10)
        c.drawString(50,h-70,f"{DOCTOR_NAME} | Reg: {DOCTOR_REG}")
        c.drawString(400,h-70,f"Rx: {serial}")
        c.line(50,h-80,w-50,h-80)

        c.drawString(50,h-110,f"Patient: {d['patient_name']}")
        c.drawString(250,h-110,f"Age: {d['age']}")
        c.drawString(350,h-110,f"Gender: {d['gender']}")

        c.drawString(50,h-140,"Diagnosis:")
        c.drawString(80,h-160,d["diagnosis"])

        c.setFont("Helvetica-Bold",12)
        c.drawString(50,h-200,"Rx")
        c.setFont("Helvetica",11)

        y=h-225
        for m in d["medicines"].split("\n"):
            c.drawString(70,y,m)
            y-=18

        c.drawImage("static/qr.png",50,90,80,80)
        c.drawImage("static/signature.png",w-200,90,120,40)

        c.drawString(50,70,"Scan QR to verify")
        c.drawString(w-200,70,DOCTOR_NAME)

        c.save()
        return send_file(pdf_path, as_attachment=True)

    return render_template("index.html")

@app.route("/history")
def history():
    if not session.get("doctor"):
        return redirect("/login")

    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute("SELECT * FROM prescriptions ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return render_template("history.html", patients=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

