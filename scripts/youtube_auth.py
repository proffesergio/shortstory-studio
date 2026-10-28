"""One-time OAuth for the single-owner local MVP. Never commit secrets/ tokens."""
import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parents[1]
CLIENT = Path(os.getenv('YOUTUBE_CLIENT_SECRETS_FILE',str(ROOT/'secrets/client_secret.json')))
TOKEN = Path(os.getenv('YOUTUBE_TOKEN_FILE',str(ROOT/'secrets/youtube_token.json')))
if not CLIENT.is_file():
    sys.exit('Place Google OAuth desktop client secret at ' + str(CLIENT))
flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT),scopes=['https://www.googleapis.com/auth/youtube.upload'])
creds = flow.run_local_server(port=0)
TOKEN.parent.mkdir(parents=True, exist_ok=True)
TOKEN.write_text(creds.to_json(),encoding='utf-8')
try: TOKEN.chmod(0o600)
except OSError: pass
print('OAuth token stored locally (excluded from Git):',TOKEN)
