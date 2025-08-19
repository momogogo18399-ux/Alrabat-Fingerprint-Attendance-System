"""
Utility functions for Supabase integration.
Handles authentication, real-time updates, and other Supabase-specific functionality.
"""
import os
import json
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime
from gotrue import SyncGoTrueClient, User
from postgrest import SyncRequestBuilder
from realtime.connection import Socket
from realtime.types import CallbackHandler

from .supabase_config import supabase_config

class SupabaseAuth:
    """Handles Supabase authentication and user management."""
    
    def __init__(self):
        self.client = supabase_config.client
        self.auth = self.client.auth if self.client else None
        self.current_user: Optional[User] = None
    
    def sign_in(self, email: str, password: str) -> Optional[User]:
        """Sign in a user with email and password."""
        if not self.auth:
            return None
            
        try:
            response = self.auth.sign_in(email=email, password=password)
            self.current_user = response.user
            return self.current_user
        except Exception as e:
            print(f"Sign in error: {e}")
            return None
    
    def sign_out(self) -> bool:
        """Sign out the current user."""
        if not self.auth or not self.current_user:
            return False
            
        try:
            self.auth.sign_out()
            self.current_user = None
            return True
        except Exception as e:
            print(f"Sign out error: {e}")
            return False
    
    def get_current_user(self) -> Optional[User]:
        """Get the currently authenticated user."""
        if not self.auth:
            return None
            
        try:
            self.current_user = self.auth.current_user
            return self.current_user
        except Exception as e:
            print(f"Error getting current user: {e}")
            return None


class SupabaseRealtime:
    """Handles real-time updates from Supabase."""
    
    def __init__(self):
        self.url = supabase_config.url.replace('https://', 'wss://') if supabase_config.url else None
        self.api_key = supabase_config.key
        self.socket: Optional[Socket] = None
        self.channels: Dict[str, Any] = {}
    
    def connect(self) -> bool:
        """Establish a WebSocket connection to Supabase real-time API."""
        if not self.url or not self.api_key:
            print("Missing Supabase URL or API key")
            return False
            
        try:
            self.socket = Socket(self.url, {'params': {'apikey': self.api_key}})
            self.socket.connect()
            return True
        except Exception as e:
            print(f"Failed to connect to Supabase real-time: {e}")
            return False
    
    def subscribe_to_table(
        self,
        table: str,
        event: str,
        schema: str = 'public',
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """Subscribe to changes in a specific table."""
        if not self.socket:
            if not self.connect():
                return False
                
        try:
            channel = self.socket.channel(f'realtime:{schema}.{table}')
            
            def handle_payload(payload: Dict[str, Any]) -> None:
                if callback:
                    callback(payload)
            
            channel.on(event, handle_payload)
            channel.subscribe()
            
            # Store channel reference to prevent garbage collection
            self.channels[f"{schema}.{table}.{event}"] = channel
            return True
            
        except Exception as e:
            print(f"Failed to subscribe to {table} {event}: {e}")
            return False
    
    def close(self) -> None:
        """Close all connections and clean up."""
        if self.socket:
            self.socket.disconnect()
            self.socket = None
        self.channels.clear()


# Utility functions
def format_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Format a database record by converting special types to JSON-serializable formats."""
    if not record:
        return {}
        
    formatted = {}
    for key, value in record.items():
        if isinstance(value, datetime):
            formatted[key] = value.isoformat()
        else:
            formatted[key] = value
    return formatted


def get_supabase_table(table_name: str):
    """Get a Supabase table reference."""
    if not supabase_config.client:
        return None
    return supabase_config.client.table(table_name)


# Initialize singletons
supabase_auth = SupabaseAuth()
supabase_realtime = SupabaseRealtime()
