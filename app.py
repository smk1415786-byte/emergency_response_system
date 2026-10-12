from flask import Flask, request, jsonify, render_template, redirect
import qrcode
import os
from supabase import create_client, Client

app = Flask(__name__)

# ==========================================
# SUPABASE CONFIGURATION
# ==========================================
supabase_url = "https://wxldcfpeyfksyiqvwigc.supabase.co"
supabase_key = "sb_publishable_N2cgV1VIcxF5AFCI3cvNWA_CiMh0ofw"
supabase: Client = create_client(supabase_url, supabase_key)


# ==========================================
# HOME PAGE & REGISTER VEHICLE
# ==========================================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            # 1. Get data from the form
            vehicle_data = {
                "vehicle_number": request.form.get("vehicle", ""),
                "owner_name": request.form.get("name", ""),
                "owner_phone": request.form.get("phone", ""),
                "family_phone": request.form.get("family", "")
            }

            # 2. Save to Supabase
            result = supabase.table("vehicles").insert(vehicle_data).execute()
            
            # 3. Get the auto-generated UUID from Supabase
            inserted_data = result.data
            if not inserted_data:
                return "Error saving to database", 500
                
            vehicle_id = inserted_data[0].get("id")

            # 4. Generate the QR Code URL pointing to your Render deployment
            url = f"https://emergency-response-system-jl3r.onrender.com/v/{vehicle_id}"
            img = qrcode.make(url)

            # 5. Ensure the directory exists and save the image
            if not os.path.exists("static/qrcodes"):
                os.makedirs("static/qrcodes")

            path = f"static/qrcodes/{vehicle_id}.png"
            img.save(path)

            # 6. Render the success page with the generated QR code
            return render_template("success.html", qr=path)

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    # If it is a GET request, just show the form
    return render_template("home.html")


# ==========================================
# VIEW VEHICLE (AFTER SCAN)
# ==========================================
@app.route("/v/<id>")
def view(id):
    # Fetch vehicle from Supabase by ID
    result = supabase.table("vehicles").select("*").eq("id", id).execute()
    
    if not result.data:
        return "❌ Vehicle not found", 404

    data = result.data[0]
    
    # Map the Supabase columns back to what your vehicle.html template expects
    template_data = {
        "id": id,
        "vehicle": data.get("vehicle_number"),
        "name": data.get("owner_name"),
        "phone": data.get("owner_phone"),
        "family": data.get("family_phone")
    }

    return render_template("vehicle.html", data=template_data)


# ==========================================
# CALL OWNER
# ==========================================
@app.route("/call/owner/<id>")
def call_owner(id):
    result = supabase.table("vehicles").select("owner_phone").eq("id", id).execute()
    if not result.data:
        return "Error: Vehicle not found", 404

    phone = result.data[0].get("owner_phone")
    return redirect(f"tel:{phone}")


# ==========================================
# CALL FAMILY
# ==========================================
@app.route("/call/family/<id>")
def call_family(id):
    result = supabase.table("vehicles").select("family_phone").eq("id", id).execute()
    if not result.data:
        return "Error: Vehicle not found", 404

    phone = result.data[0].get("family_phone")
    return redirect(f"tel:{phone}")


# ==========================================
# WHATSAPP OWNER
# ==========================================
@app.route("/whatsapp/owner/<id>")
def whatsapp_owner(id):
    result = supabase.table("vehicles").select("owner_phone").eq("id", id).execute()
    if not result.data:
        return "Error: Vehicle not found", 404

    phone = result.data[0].get("owner_phone")
    msg = "Your vehicle seems to be in an issue. Please check."
    return redirect(f"https://wa.me/{phone}?text={msg}")


# ==========================================
# WHATSAPP FAMILY
# ==========================================
@app.route("/whatsapp/family/<id>")
def whatsapp_family(id):
    result = supabase.table("vehicles").select("family_phone").eq("id", id).execute()
    if not result.data:
        return "Error: Vehicle not found", 404

    phone = result.data[0].get("family_phone")
    msg = "Emergency! Please check immediately."
    return redirect(f"https://wa.me/{phone}?text={msg}")


# ==========================================
# API: CREATE EMERGENCY
# ==========================================
@app.route("/emergency", methods=["POST"])
def create_emergency():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        emergency = {
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "type": data.get("type", ""),
            "location": data.get("location", ""),
            "description": data.get("description", ""),
            "status": "pending"
        }

        result = supabase.table("emergencies").insert(emergency).execute()
        inserted_data = result.data
        record_id = inserted_data[0].get("id") if inserted_data else None

        return jsonify({"status": "success", "message": "Emergency report saved successfully", "id": record_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# API: GET ALL EMERGENCIES
# ==========================================
@app.route("/emergencies", methods=["GET"])
def get_emergencies():
    try:
        result = supabase.table("emergencies").select("*").execute()
        return jsonify({"status": "success", "count": len(result.data), "emergencies": result.data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# RUN SERVER
# ==========================================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)