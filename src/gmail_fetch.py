import base64, os
from email.header import decode_header
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def _service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def fetch_latest(n=20):
    srv = _service()
    results = srv.users().messages().list(userId='me', maxResults=n, q="newer_than:7d").execute()
    msgs = results.get('messages', [])
    out = []
    for m in msgs:
        msg = srv.users().messages().get(userId='me', id=m['id'], format='full').execute()
        headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
        subject = headers.get('subject','(no subject)')
        from_email = headers.get('from','unknown')

        # extract body
        def get_text(payload):
            if 'parts' in payload:
                for part in payload['parts']:
                    t = get_text(part)
                    if t: return t
            data = payload.get('body', {}).get('data')
            if data:
                raw = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                return BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
            return ""
        body = get_text(msg['payload'])
        out.append({"from_email": from_email, "subject": subject, "body": body})
    return out
