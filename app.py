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
CLINIC_NAME = "Ajay's Child Clinic"
CLINIC_ADDRESS = "Crossing Republik,Ghaziabad, State - Uttar Pradesh"
CLINIC_PHONE = "+91-8800588070"


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
        c.execute(
    """INSERT INTO prescriptions
    (patient_name, age, gender, diagnosis, medicines, date, pdf_file)
    VALUES (?,?,?,?,?,?,?)""",
    (
        d["patient_name"],
        d["age"],
        d["gender"],
        d["diagnosis"],
        d["medicines"],
        datetime.now().strftime("%d-%m-%Y"),
        pdf_path
    )
)

        conn.commit()
        conn.close()

        # QR
        qr = qrcode.make(f"{CLINIC_NAME} | {serial}")
        qr.save("static/qr.png")

       
                # ---------------- PDF START ----------------
        c = canvas.Canvas(pdf_path, pagesize=A4)
        w, h = A4

        # Header
        c.drawImage("static/logo.png", 50, h-90, 60, 60)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(130, h-50, CLINIC_NAME)

        c.setFont("Helvetica", 10)
        c.drawString(130, h-70, f"{DOCTOR_NAME} | Reg No: {DOCTOR_REG}")
        c.drawString(w-200, h-70, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
        c.setFont("Helvetica", 9)
        c.drawString(130, h-85, CLINIC_ADDRESS)
        c.drawString(130, h-98, f"Phone: {CLINIC_PHONE}")



        c.line(50, h-110, w-50, h-110)

        # Patient details
        c.setFont("Helvetica", 11)
        c.drawString(50, h-140, f"Patient: {d['patient_name']}")
        c.drawString(250, h-140, f"Age: {d['age']}")
        c.drawString(330, h-140, f"Sex: {d['gender']}")

        c.line(50, h-155, w-50, h-155)

        # Diagnosis
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, h-185, "Diagnosis:")

        c.setFont("Helvetica", 11)
        c.drawString(70, h-205, d["diagnosis"])

        # Prescription
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, h-245, "Rx")

        c.setFont("Helvetica", 11)
        y = h-270
        count = 1
        for m in d["medicines"].split("\n"):
            c.drawString(70, y, f"{count}. {m}")
            y -= 18
            count += 1

        # Follow-up
        if d.get("followup"):
            c.line(50, y-10, w-50, y-10)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y-35, "Follow-up:")
            c.setFont("Helvetica", 11)
            c.drawString(130, y-35, d["followup"])

        # Footer
        c.drawImage("static/qr.png", 50, 80, 80, 80)
        c.drawImage("static/signature.png", w-200, 90, 120, 40)

        c.setFont("Helvetica", 9)
        c.drawString(w-200, 70, DOCTOR_NAME)
        c.setFont("Helvetica", 8)
        c.drawString(50, 55, CLINIC_ADDRESS)


        c.setFont("Helvetica", 8)
        c.drawString(
            50,
            40,
            "This is a digitally generated prescription. Valid without physical signature."
        )

        c.save()
        # ---------------- PDF END ----------------

        return send_file(pdf_path, as_attachment=True)

    return render_template("index.html")


@app.route("/history", methods=["GET", "POST"])
def history():
    if not session.get("doctor"):
        return redirect("/login")

    search = ""
    results = []

    if request.method == "POST":
        search = request.form.get("search", "")

        conn = sqlite3.connect("patients.db")
        c = conn.cursor()
        c.execute(
            "SELECT patient_name, age, gender, diagnosis, date FROM prescriptions "
            "WHERE patient_name LIKE ? ORDER BY id DESC",
            (f"%{search}%",)
        )
        results = c.fetchall()
        conn.close()

    return render_template("history.html", results=results, search=search)

@app.route("/reports")
def reports():
    if not session.get("doctor"):
        return redirect("/login")

    today = datetime.now().strftime("%d-%m-%Y")
    current_month = datetime.now().strftime("%m-%Y")

    conn = sqlite3.connect("patients.db")
    c = conn.cursor()

    # Today's count
    c.execute(
        "SELECT COUNT(*) FROM prescriptions WHERE date = ?",
        (today,)
    )
    today_count = c.fetchone()[0]

    # Monthly count
    c.execute(
        "SELECT COUNT(*) FROM prescriptions WHERE date LIKE ?",
        (f"%{current_month}",)
    )
    month_count = c.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        today_count=today_count,
        month_count=month_count,
        month_name=datetime.now().strftime("%B %Y")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/download/<int:pid>")
def download(pid):
    if not session.get("doctor"):
        return redirect("/login")

    conn = sqlite3.connect("patients.db")
    c = conn.cursor()
    c.execute("SELECT pdf_file FROM prescriptions WHERE id = ?", (pid,))
    row = c.fetchone()
    conn.close()

    if row and row[0] and os.path.exists(row[0]):
        return send_file(row[0], as_attachment=True)

    return "File not found", 404



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

