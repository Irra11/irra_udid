# -*- coding: utf-8 -*-
from flask import Flask, request, Response, redirect
import plistlib
import uuid
import requests
import json

app = Flask(__name__)

# 🔐 CONFIGURATION
USER_BOT_TOKEN = "7159490173:AAEfsvxSCSLWiGqBCAm0uNNUEo7k11x3-UM"
BOT_USERNAME = "Irra_EsignBot" # Your Bot Username without @

@app.route('/download')
def download():
    uid = request.args.get("uid")
    if not uid:
        return "Missing Telegram User ID", 400
    
    root_url = "https://panelbottelegram.onrender.com/"
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
        headers={"Content-Disposition": "attachment; filename=pella.mobileconfig"}
    )

@app.route('/api/enroll', methods=['POST'])
def enroll():
    try:
        uid = request.args.get("uid")
        plist_data = plistlib.loads(request.data)
        udid = plist_data.get("UDID", "Unknown")

        if uid and udid != "Unknown":
            # Bot sends message with confirm button
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Click to Confirm UDID", "callback_data": f"set_udid_{udid}"}
                ]]
            }
            payload = {
                "chat_id": uid,
                "text": f"📱 **ទទួលបាន UDID រួចរាល់!**\n\n🆔 `{udid}`\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីបន្ត៖",
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(f"https://api.telegram.org/bot{USER_BOT_TOKEN}/sendMessage", data=payload)

        # ✅ THE TRICK: Redirect to a 'Success' page with code 301
        # This tells the iPhone to open this URL after installation
        return redirect(f"https://panelbottelegram.onrender.com/success", code=301)

    except Exception:
        return Response(status=500)

@app.route('/success')
def success():
    # This page runs a small JavaScript to force Telegram to open
    html = f"""
    <html>
    <head>
        <title>Redirecting...</title>
        <script>
            window.location.href = "tg://resolve?domain={BOT_USERNAME}";
            setTimeout(function() {{
                window.location.href = "https://t.me/{BOT_USERNAME}";
            }}, 500);
        </script>
    </head>
    <body style="text-align:center; font-family:sans-serif; margin-top:50px;">
        <h2>✅ Installation Complete!</h2>
        <p>Redirecting you back to Telegram...</p>
        <a href="tg://resolve?domain={BOT_USERNAME}" style="font-size:20px; color:blue;">Click here if not redirected</a>
    </body>
    </html>
    """
    return html

@app.route('/')
def home():
    return "API is Online 🚀"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
