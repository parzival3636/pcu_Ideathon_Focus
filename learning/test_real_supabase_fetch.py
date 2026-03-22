import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

if not os.getenv("SUPABASE_URL"):
    # Try one level up if not found (for different run contexts)
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

import requests

def test_fetch():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_ANON_KEY not set")
        return

    print(f"Connecting to REST API: {url}")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    # Supabase REST endpoint for 'sessions' table
    endpoint = f"{url}/rest/v1/sessions?select=*&limit=5"
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print("\nLatest 5 sessions:")
        for row in data:
            print(f"- Topic: {row.get('goal') or row.get('session_name')}, Created At: {row.get('created_at')}")
        
        if not data:
            print("No sessions found in the table.")
            
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_fetch()
