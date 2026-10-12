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

            # 4. Generate the QR Code URL using your active Render domain
            url = f"https://emergency-response-system-5-p5rb.onrender.com/v/{vehicle_id}"
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
# VIEW VEHICLE (AFTER SCAN) - DEBUG MODE
# ==========================================
@app.route("/v/<id>")
def view(id):
    try:
        # Fetch vehicle from Supabase by ID
        result = supabase.table("vehicles").select("*").eq("id", id).execute()
        
        if not result.data:
            return f"""
            <h3>❌ Vehicle not found</h3>
            <p><b>Debug Info:</b></p>
            <p>Looked for ID: <code>{id}</code></p>
            <p>Supabase Response: <code>{result}</code></p>
            <p>Please check your Supabase 'vehicles' table to see if this ID exists.</p>
            """, 404

        data = result.data[0]
        
        template_data = {
            "id": id,
            "vehicle": data.get("vehicle_number"),
            "name": data.get("owner_name"),
            "phone": data.get("owner_phone"),
            "family": data.get("family_phone")
        }

        return render_template("vehicle.html", data=template_data)
    
    except Exception as e:
        return f"<h3>❌ Database Error</h3><p>{str(e)}</p>", 500


# ==========================================
# CALL & WHATSAPP ROUTES
# ==========================================
@app.route("/call/owner/<id>")
def call_owner(id):
    result = supabase.table("vehicles").select("owner_phone").eq("id", id).execute()
    phone = result.data[0].get("owner_phone") if result.data else ""
    return redirect(f"tel:{phone}")


@app.route("/call/family/<id>")
def call_family(id):
    result = supabase.table("vehicles").select("family_phone").eq("id", id).execute()
    phone = result.data[0].get("family_phone") if result.data else ""
    return redirect(f"tel:{phone}")


@app.route("/whatsapp/owner/<id>")
def whatsapp_owner(id):
    result = supabase.table("vehicles").select("owner_phone").eq("id", id).execute()
    phone = result.data[0].get("owner_phone") if result.data else ""
    return redirect(f"https://wa.me/{phone}?text=Your%20vehicle%20seems%20to%20be%20in%20an%20issue.%20Please%20check.")


@app.route("/whatsapp/family/<id>")
def whatsapp_family(id):
    result = supabase.table("vehicles").select("family_phone").eq("id", id).execute()
    phone = result.data[0].get("family_phone") if result.data else ""
    return redirect(f"https://wa.me/{phone}?text=Emergency!%20Please%20check%20immediately.")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)