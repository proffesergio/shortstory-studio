"""Single-owner MVP uploader. Multi-tenant SaaS needs per-user OAuth credentials."""
from .config import TOKEN_FILE

SCOPE = ['https://www.googleapis.com/auth/youtube.upload']


def upload(video, title, description, privacy='private'):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    if privacy not in ('private','unlisted','public'):
        raise ValueError('Invalid privacy')
    if not TOKEN_FILE.exists():
        raise RuntimeError('No YouTube OAuth token. Run scripts/youtube_auth.py first.')
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), scopes=SCOPE)
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json(), encoding='utf8')
    if not credentials.valid:
        raise RuntimeError('YouTube OAuth credentials are expired or invalid. Reauthorize.')
    service = build('youtube','v3',credentials=credentials,cache_discovery=False)
    request = service.videos().insert(part='snippet,status', body={
      'snippet':{'title':title[:100], 'description':description[:5000], 'categoryId':'24'},
      'status':{'privacyStatus':privacy, 'selfDeclaredMadeForKids':False, 'containsSyntheticMedia':False}},
      media_body=MediaFileUpload(str(video),mimetype='video/mp4',resumable=True,chunksize=8*1024*1024))
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response['id']
