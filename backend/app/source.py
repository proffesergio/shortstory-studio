"""Optional metadata previews. Do not enable without the required Reddit permission."""
import math
import os
import re
import requests
from datetime import datetime, timezone


def rank(post: dict, niche: str) -> float:
    # Candidate prioritization only; scores are not a prediction of virality.
    text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
    keywords = set(re.findall(r'[a-z]{4,}', niche.lower()))
    topical = len([w for w in keywords if w in text])
    upvotes = max(post.get('score', 0), 0)
    comments = max(post.get('num_comments', 0), 0)
    age_h = max(1, (datetime.now(timezone.utc).timestamp() - post.get('created_utc', 0)) / 3600)
    return round(2 * topical + math.log1p(upvotes) + 0.5 * math.log1p(comments) - math.log1p(age_h), 2)


def preview_community(community: str, niche: str):
    if not os.getenv('REDDIT_AUTHORIZED', 'false').lower() in ('true','1','yes'):
        raise PermissionError('Reddit data integration is disabled until appropriate permission is confirmed.')
    client_id = os.getenv('REDDIT_CLIENT_ID', '')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
    agent = os.getenv('REDDIT_USER_AGENT', '')
    if not client_id or not client_secret or not agent:
        raise RuntimeError('Configure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT.')
    with requests.Session() as session:
        session.headers.update({'User-Agent': agent})
        oauth = session.post('https://www.reddit.com/api/v1/access_token', auth=(client_id, client_secret),
                             data={'grant_type': 'client_credentials'}, timeout=15)
        oauth.raise_for_status()
        session.headers['Authorization'] = 'bearer ' + oauth.json()['access_token']
        r = session.get(f'https://oauth.reddit.com/r/{community}/top',
                        params={'t':'week','limit':30}, timeout=20)
        r.raise_for_status()
        posts = []
        for child in r.json().get('data', {}).get('children', []):
            p = child['data']
            if p.get('over_18') or p.get('stickied') or not p.get('is_self'):
                continue
            if len(p.get('selftext', '')) < 250 or p.get('removed_by_category'):
                continue
            posts.append({'title': p.get('title'), 'community': p.get('subreddit'),
                          'source_url': 'https://www.reddit.com' + p.get('permalink',''),
                          'score': p.get('score'), 'comments':p.get('num_comments'),
                          'rank':rank(p, niche), 'excerpt':p.get('selftext','')[:220]})
        return sorted(posts, key=lambda x: x['rank'], reverse=True)[:15]
