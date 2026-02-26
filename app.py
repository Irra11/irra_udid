# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, Response
import plistlib
import uuid
import requests
import json

app = Flask(__name__)

# 🔐 CONFIGURATION
USER_BOT_TOKEN = "7159490173:AAEfsvxSCSLWiGqBCAm0uNNUEo7k11x3-UM"

@app.route('/download')
def download():
    uid = request.args.get("uid")
    if not uid:
        return "Missing Telegram User ID", 400
    return redirect(f"/api/get-profile?uid={uid}")

@app.route('/api/get-profile', methods=['GET'])
def get_profile():
    uid = request.args.get("uid", "unknown")
    root_url = request.url_root.replace("http://", "https://")
    enroll_url = f"{root_url}api/enroll?uid={uid}"

    profile_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    <string>Pella Esign</string>
    <key>PayloadDisplayName</key>
    <string>Pella UDID Auto-Installer</string>
    <key>PayloadIdentifier</key>
    <string>com.pella.udid.{uuid.uuid4()}</string>
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
        headers={"Content-Disposition": "attachment; filename=pella_udid.mobileconfig"}
    )

@app.route('/api/enroll', methods=['POST'])
def enroll():
    try:
        uid = request.args.get("uid")
        plist_data = plistlib.loads(request.data)
        udid = plist_data.get("UDID", "Unknown")

        if uid:
            # We send a message with a button back to the user
            # This allows the main.py to handle the 'click' event
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Click to Confirm UDID", "callback_data": f"set_udid_{udid}"}
                ]]
            }
            
            payload = {
                "chat_id": uid,
                "text": f"📱 **រកឃើញ UDID របស់អ្នកហើយ!**\n\n🆔 `{udid}`\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីបន្ត៖",
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard)
            }
            
            requests.post(f"https://api.telegram.org/bot{USER_BOT_TOKEN}/sendMessage", data=payload)

        # Redirect the iPhone user back to Telegram automatically
        return redirect("https://t.me/pella_esign_bot", code=302) # Change to your bot username

    except Exception as e:
        return str(e), 500

@app.route('/')
def home():
    return "Pella UDID API is Online 🚀"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
