import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64, re, time

def gmail_service_from_env():
    creds = Credentials.from_authorized_user_info({
        "client_id": os.getenv("GMAIL_CLIENT_ID"),
        "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
        "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
        "token_uri": "https://oauth2.googleapis.com/token",
    })
    return build("gmail", "v1", credentials=creds)

def fetch_clubgg_verification_code(since, timeout=120):
    gmail = gmail_service_from_env()
    deadline = time.time() + timeout
    query = 'from:support@clubgg.com subject:"ClubGG Email Verification Code" newer_than:1d'

    while time.time() < deadline:
        msgs = gmail.users().messages().list(userId="me", q=query, maxResults=10).execute()
        for m in msgs.get("messages", []):
            msg = gmail.users().messages().get(userId="me", id=m["id"], format="full").execute()
            internal_date = int(msg.get("internalDate", "0")) / 1000
            if internal_date + 10 <= since.timestamp():
                continue
            text = extract_text(msg)
            m = re.search(r"\b(\d{6})\b", text)
            if m:
                return m.group(1)
        time.sleep(3)
    raise TimeoutError("Timed out waiting for ClubGG verification email")

def extract_text(msg):
    def walk(parts, out):
        for p in parts or []:
            if p.get("mimeType") in ("text/plain", "text/html") and "data" in p.get("body", {}):
                out.append(base64.urlsafe_b64decode(p["body"]["data"]).decode())
            walk(p.get("parts"), out)
    out = []
    walk(msg.get("payload", {}).get("parts"), out)
    return "\n".join(out + [msg.get("snippet", "")])
