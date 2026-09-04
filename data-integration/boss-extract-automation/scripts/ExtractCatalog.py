import requests
import json
import csv
import os
from urllib.parse import urlparse

# --- Configurations ---
HOST = os.getenv('BOSS_HOST')
API_PATH = '/api/boss/data/objects/ora/commonAppsInfra/catalog/v1/artifacts'
API_FILTER = "(deploymentId=1185 and metadataType='BusinessView')"
IDCS_HOST = os.getenv('IDCS_HOST')
IDCS_SCOPE = os.getenv('IDCS_BOSS_SCOPE')

# Set one of these env vars before running:
#   export BOSS_AUTH_HEADER="Bearer <token>"
#   export BOSS_BEARER_TOKEN="<token>"
BOSS_AUTH_HEADER = os.getenv('BOSS_AUTH_HEADER')
BOSS_BEARER_TOKEN = os.getenv('BOSS_BEARER_TOKEN')
# Or source set_boss_env.sh and let script obtain token automatically:
IDCS_CLIENT_ID = os.getenv('IDCS_CLIENT_ID')
IDCS_CLIENT_SECRET = os.getenv('IDCS_CLIENT_SECRET')
BOSS_USERNAME = os.getenv('BOSS_USERNAME')
BOSS_PASSWORD = os.getenv('BOSS_PASSWORD')
# Optional if your environment requires the same cookie as Postman/curl
BOSS_COOKIE = os.getenv('BOSS_COOKIE')
ALLOW_INSECURE_HTTP = os.getenv('ALLOW_INSECURE_HTTP', '').strip().lower() in {'1', 'true', 'yes', 'y'}


def required_env(name, value):
    if not value:
        raise ValueError(f'Missing required env var: {name}')
    return value


def validated_base_url(name, value):
    raw = required_env(name, value).strip()
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f'Invalid URL for {name}: {raw!r}')
    if parsed.scheme != 'https' and not (ALLOW_INSECURE_HTTP and parsed.scheme == 'http'):
        raise ValueError(
            f'{name} must use HTTPS. '
            f'Set ALLOW_INSECURE_HTTP=true only in controlled non-production environments.'
        )
    if parsed.query or parsed.fragment:
        raise ValueError(f'{name} must not include query string or fragment')
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')


def boss_api_url():
    return f"{validated_base_url('BOSS_HOST', HOST)}{API_PATH}"


def idcs_token_url():
    return f"{validated_base_url('IDCS_HOST', IDCS_HOST)}/oauth2/v1/token"


def get_token():
    missing = [
        name
        for name, val in [
            ('IDCS_CLIENT_ID', IDCS_CLIENT_ID),
            ('IDCS_CLIENT_SECRET', IDCS_CLIENT_SECRET),
            ('BOSS_USERNAME', BOSS_USERNAME),
            ('BOSS_PASSWORD', BOSS_PASSWORD),
            ('IDCS_HOST', IDCS_HOST),
            ('IDCS_BOSS_SCOPE', IDCS_SCOPE),
        ]
        if not val
    ]
    if missing:
        raise ValueError(
            'Missing env vars for automatic token retrieval: ' + ', '.join(missing)
        )

    payload = {
        'grant_type': 'password',
        'username': BOSS_USERNAME,
        'password': BOSS_PASSWORD,
        'scope': IDCS_SCOPE,
    }
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    response = requests.post(
        idcs_token_url(),
        headers=headers,
        data=payload,
        auth=requests.auth.HTTPBasicAuth(IDCS_CLIENT_ID, IDCS_CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    token_data = response.json()
    return token_data['access_token']

def fetch_data(offset=0, limit=30):
    auth_header = BOSS_AUTH_HEADER
    if not auth_header and BOSS_BEARER_TOKEN:
        auth_header = f'Bearer {BOSS_BEARER_TOKEN}'
    if not auth_header:
        auth_header = f'Bearer {get_token()}'

    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json'
    }
    if BOSS_COOKIE:
        headers['Cookie'] = BOSS_COOKIE

    params = {
        '$filter': API_FILTER,
        '$offset': offset,
        '$limit': limit
    }
    response = requests.get(
        boss_api_url(),
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def process_items(items):
    csv_filename = 'catalog_output.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Deployment ID', 'Module Name', 'Path', 'Metadata Type', 'ID', 'Self Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            row = {
                'Deployment ID': item.get('deploymentId'),
                'Module Name': item.get('moduleName'),
                'Path': item.get('path'),
                'Metadata Type': item.get('metadataType'),
                'ID': item.get('$id'),
                'Self Link': item.get('$context', {}).get('links', {}).get('$self', {}).get('href', '')
            }
            writer.writerow(row)
    print(f"Output saved to {csv_filename}")

def main():
    # Option 1: Fetch from API (uncomment to use live)
    
    all_items = []
    offset = 0
    limit = 50000
    while True:
        data = fetch_data(offset, limit)
        all_items.extend(data.get('items', []))
        if not data.get('hasMore', False):
            break
        offset += limit  # Or use offset += len(data['items']) if limit isn't strictly followed
        print(offset)
    """

    # Option 2: Load from local file/variable
    with open('sample.json', 'r') as f:
        data = json.load(f)
    all_items = data.get('items', [])
    """
    process_items(all_items)
    print("Total items fetched:", len(all_items))

if __name__ == '__main__':
    try:
        main()
    except ValueError as e:
        # Graceful error for missing/invalid runtime configuration (e.g. auth env vars)
        print(f"Configuration error: {e}")
    except requests.exceptions.RequestException as e:
        # Graceful HTTP/network/auth errors
        print(f"Request failed: {e}")
    except Exception as e:
        # Last-resort guard to avoid hard crash in terminal tasks
        print(f"Unexpected error: {e}")
