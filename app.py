from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Firebase service-account configuration
import json

firebase_key = os.environ.get(r"C:\Users\ADMIN\Downloads\raksha1-7b718-firebase-adminsdk-fbsvc-e3821087ef.json")
print("FIREBASE_KEY PRESENT:", bool(firebase_key))

if not firebase_key:
    raise RuntimeError("FIREBASE_KEY environment variable is not set")

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_key))
    firebase_admin.initialize_app(cred)

# Firestore database
db = firestore.client()


# ==========================================
# HOME / HEALTH CHECK
# ==========================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "firebase": "connected",
        "message": "Emergency Response System is running",
        "status": "success"
    })


# ==========================================
# CREATE EMERGENCY
# ==========================================

@app.route("/emergency", methods=["POST"])
def create_emergency():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data received"
            }), 400

        emergency = {
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "type": data.get("type", ""),
            "location": data.get("location", ""),
            "description": data.get("description", ""),
            "status": "pending",
            "created_at": firestore.SERVER_TIMESTAMP
        }

        # Save to Firestore
        result = db.collection("emergencies").add(emergency)

        document_id = result[1].id

        return jsonify({
            "status": "success",
            "message": "Emergency report saved successfully",
            "id": document_id
        }), 201

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ==========================================
# GET ALL EMERGENCIES
# ==========================================

@app.route("/emergencies", methods=["GET"])
def get_emergencies():

    try:

        emergency_ref = db.collection("emergencies")
        documents = emergency_ref.stream()

        emergencies = []

        for document in documents:

            data = document.to_dict()

            emergencies.append({
                "id": document.id,
                "name": data.get("name", ""),
                "phone": data.get("phone", ""),
                "type": data.get("type", ""),
                "location": data.get("location", ""),
                "description": data.get("description", ""),
                "status": data.get("status", "")
            })

        return jsonify({
            "status": "success",
            "count": len(emergencies),
            "emergencies": emergencies
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )