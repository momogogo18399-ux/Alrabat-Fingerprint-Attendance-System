import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# Load environment variables
load_dotenv()

class SupabaseConfig:
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_KEY", "")
        self.service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
        self._client: Optional[Client] = None
        self._auth_client = None

    @property
    def client(self) -> Client:
        """Get or create a Supabase client."""
        if not self._client and self.url and self.key:
            self._client = create_client(self.url, self.key)
        return self._client

    def get_table(self, table_name: str):
        """Get a Supabase table reference."""
        if not self.client:
            raise ValueError("Supabase client not initialized. Check your SUPABASE_URL and SUPABASE_KEY.")
        return self.client.table(table_name)

    async def listen_to_changes(self, table: str, event: str, callback):
        """Listen to realtime changes in a table."""
        if not self.client:
            raise ValueError("Supabase client not initialized.")
            
        async def handle_payload(payload):
            callback(payload)
            
        return self.client.realtime.subscribe(
            f"realtime:{table}",
            event,
            handle_payload
        )

# Create a singleton instance
supabase_config = SupabaseConfig()
