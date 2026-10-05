from flask import Flask, render_template, request, redirect
import qrcode
import os
import uuid
import json

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# 🔥 LOAD FIREBASE KEY FROM RENDER ENV
cred = credentials.Certificate(r"C:\Users\ADMIN\Downloads\raksha1-7b718-firebase-adminsdk-fbsvc-15c34ef6ec.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# =========================
# HOME PAGE (REGISTER)
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        vehicle = request.form["vehicle"]
        name = request.form["name"]
        phone = request.form["phone"]
        family = request.form["family"]

        # UNIQUE ID
        unique_id = str(uuid.uuid4())[:8]

        # SAVE TO FIREBASE
        db.collection("vehicles").document(unique_id).set({
            "vehicle": vehicle,
            "name": name,
            "phone": phone,
            "family": family
        })

        # 🔥 YOUR RENDER URL
        url = f"https://emergency-response-system-jl3r.onrender.com/v/{unique_id}"

        # QR GENERATE
        img = qrcode.make(url)

        if not os.path.exists("static/qrcodes"):
            os.makedirs("static/qrcodes")

        path = f"static/qrcodes/{unique_id}.png"
        img.save(path)

        return render_template("success.html", qr=path)

    return render_template("home.html")


# =========================
# VIEW VEHICLE (AFTER SCAN)
# =========================
@app.route("/v/<id>")
def view(id):
    doc = db.collection("vehicles").document(id).get()

    if not doc.exists:
        return "❌ Vehicle not found"

    data = doc.to_dict()
    data["id"] = id

    return render_template("vehicle.html", data=data)


# =========================
# CALL OWNER
# =========================
@app.route("/call/owner/<id>")
def call_owner(id):
    doc = db.collection("vehicles").document(id).get()

    if not doc.exists:
        return "Error"

    phone = doc.to_dict()["phone"]

    return redirect(f"tel:{phone}")


# =========================
# CALL FAMILY
# =========================
@app.route("/call/family/<id>")
def call_family(id):
    doc = db.collection("vehicles").document(id).get()

    if not doc.exists:
        return "Error"

    phone = doc.to_dict()["family"]

    return redirect(f"tel:{phone}")


# =========================
# WHATSAPP OWNER
# =========================
@app.route("/whatsapp/owner/<id>")
def whatsapp_owner(id):
    doc = db.collection("vehicles").document(id).get()

    if not doc.exists:
        return "Error"

    phone = doc.to_dict()["phone"]

    msg = "Your vehicle seems to be in an issue. Please check."
    return redirect(f"https://wa.me/{phone}?text={msg}")


# =========================
# WHATSAPP FAMILY
# =========================
@app.route("/whatsapp/family/<id>")
def whatsapp_family(id):
    doc = db.collection("vehicles").document(id).get()

    if not doc.exists:
        return "Error"

    phone = doc.to_dict()["family"]

    msg = "Emergency! Please check immediately."
    return redirect(f"https://wa.me/{phone}?text={msg}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
