import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class SupabaseService:
    """
    Service to interact with Supabase and manage scraping triggers.
    """
    
    @classmethod
    def get_session_count_today(cls, topic: str) -> int:
        """
        Count how many times a 'goal' (topic) has appeared in the 'sessions' table today.
        """
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            print("[SupabaseService] Error: SUPABASE_URL or key not found")
            return 0

        # Create today's date range (timestamp in milliseconds)
        import time
        today_start = int(datetime.combine(date.today(), datetime.min.time()).timestamp() * 1000)
        
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        # Query: goal=eq.topic & start_time >= today_start
        # Using Supabase REST API syntax for integer comparison
        # We fetch records to count them localy as it's more reliable than complex count headers
        endpoint = f"{url}/rest/v1/sessions?goal=eq.{topic}&start_time=gte.{today_start}&select=*"
        
        try:
            import requests
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return len(data) if isinstance(data, list) else 0
        except Exception as e:
            print(f"[SupabaseService] Error querying sessions: {e}")
            return 0

    @classmethod
    def trigger_scraper(cls, topic: str):
        """
        Independently call the study-content-recommender for a specific topic.
        """
        project_root = Path(__file__).parent.parent.parent
        recommender_path = project_root / 'study-content-recommender'
        main_py = recommender_path / 'main.py'
        
        if not main_py.exists():
            print(f"[SupabaseService] Error: {main_py} not found")
            return False

        print(f"[SupabaseService] Triggering scraping for topic: {topic}")
        
        try:
            # Call main.py with the topic as an argument
            # We assume main.py is modified to accept --topic
            # If not, we run it normally and it might pick up all topics or use a specific one
            process = subprocess.Popen(
                [sys.executable, str(main_py), "--topic", topic],
                cwd=str(recommender_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # We don't wait for it to finish as scraping can take a while
            return True
        except Exception as e:
            print(f"[SupabaseService] Error triggering scraper: {e}")
            return False

    @classmethod
    def check_and_scrape(cls, topic: str):
        """
        Business logic: If count > 3 today, trigger scraper.
        """
        count = cls.get_session_count_today(topic)
        print(f"[SupabaseService] Topic '{topic}' seen {count} times today.")
        
        if count >= 3: # "More than 3 times" means 4th time triggers it? 
                       # Or if count is already 3, the next one makes it 4?
                       # User said "appear more than 3 times daily". 
                       # Usually means if current count >= 3, we should scrape.
            return cls.trigger_scraper(topic)
        return False
