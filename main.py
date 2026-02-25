# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, Response
import plistlib
import uuid
import requests

app = Flask(__name__)

# 🔐 YOUR USER BOT TOKEN (same as main.py)
USER_BOT_TOKEN = "7159490173:AAEfsvxSCSLWiGqBCAm0uNNUEo7k11x3-UM"

# ===============================
# DOWNLOAD ROUTE (WITH USER ID)
# ===============================
@app.route('/download')
def download():
    uid = request.args.get("uid")
    
    if not uid:
        return "Missing Telegram User ID"

    return redirect(f"/api/get-profile?uid={uid}")


# ===============================
# GENERATE UDID PROFILE
# ===============================
@app.route('/api/get-profile', methods=['GET'])
def get_profile():
    uid = request.args.get("uid", "unknown")
    root_url = request.url_root.replace("http://", "https://")
    enroll_url = f"{root_url}api/enroll?uid={uid}"

    profile_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <dict>
        <key>URL</key>
        <string>{enroll_url}</string>
        <key>DeviceAttributes</key>
        <array>
            <string>UDID</string>
            <string>PRODUCT</string>
            <string>VERSION</string>
        </array>
    </dict>
    <key>PayloadOrganization</key>
    <string>IRRA ESIGN</string>
    <key>PayloadDisplayName</key>
    <string>Get Device UDID</string>
    <key>PayloadIdentifier</key>
    <string>com.irra.udid.{uuid.uuid4()}</string>
    <key>PayloadUUID</key>
    <string>{uuid.uuid4()}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
    <key>PayloadType</key>
    <string>Profile Service</string>
</dict>
</plist>"""

    return Response(
        profile_xml,
        mimetype="application/x-apple-aspen-config",
        headers={
            "Content-Disposition": "attachment; filename=udid.mobileconfig"
        }
    )


# ===============================
# AUTO SEND UDID TO TELEGRAM BOT
# ===============================
@app.route('/api/enroll', methods=['POST'])
def enroll():
    try:
        uid = request.args.get("uid")
        plist_data = plistlib.loads(request.data)

        udid = plist_data.get("UDID", "Unknown")
        product = plist_data.get("PRODUCT", "Unknown")
        version = plist_data.get("VERSION", "Unknown")

        # Send ONLY UDID (so your bot detects it)
        message = udid

        if uid:
            requests.post(
                f"https://api.telegram.org/bot{USER_BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": uid,
                    "text": message
                },
                timeout=10
            )

        return "SUCCESS"

    except Exception as e:
        return str(e), 500


@app.route('/')
def home():
    return "UDID API 24/7 Running 🚀"
