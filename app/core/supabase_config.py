import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional
from .app_config import app_config

# Load environment variables
load_dotenv()

class SupabaseConfig:
    def __init__(self):
        # Use app_config for better error handling
        self.url: str = app_config.supabase_url or ""
        self.key: str = app_config.supabase_key or ""
        self.service_key: str = app_config.supabase_service_key or ""
        self._client: Optional[Client] = None
        self._auth_client = None

    @property
    def client(self) -> Client:
        """Get or create a Supabase client."""
        if not self._client and self.url and self.key:
            try:
                self._client = create_client(self.url, self.key)
                # Test connection
                self._test_connection()
            except Exception as e:
                print(f"❌ Failed في الاتصال بـ Supabase: {e}")
                self._client = None
        return self._client
    
    def _test_connection(self):
        """Test connection to Supabase"""
        try:
            if self._client:
                # Try a simple query
                result = self._client.table('employees').select('id').limit(1).execute()
                print("✅ Successfully connected to Supabase")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            self._client = None

    def get_table(self, table_name: str):
        """Get a Supabase table reference."""
        if not self.client:
            raise ValueError("Supabase client not initialized. Check your SUPABASE_URL and SUPABASE_KEY.")
        return self.client.table(table_name)
    
    def test_connection(self) -> dict:
        """Test connection and return status"""
        try:
            if not self.url or not self.key:
                return {
                    'status': 'error',
                    'message': 'Supabase URL or Key not configured',
                    'configured': False
                }
            
            if not self.client:
                return {
                    'status': 'error',
                    'message': 'Failed to create Supabase client',
                    'configured': False
                }
            
            # Test connection
            try:
                result = self.client.table('employees').select('id').limit(1).execute()
                return {
                    'status': 'connected',
                    'message': 'Successfully connected to Supabase',
                    'configured': True,
                    'url': self.url
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Connection test failed: {str(e)}',
                    'configured': True,
                    'url': self.url
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}',
                'configured': False
            }

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
