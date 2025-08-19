"""
Test script for Supabase integration.
Run this to verify that the Supabase connection is working correctly.
"""
import os
import asyncio
import json
from dotenv import load_dotenv

# Import Supabase utilities
try:
    from app.core.supabase_utils import supabase_auth, supabase_realtime
    from app.database.supabase_manager import supabase_manager
    HAS_SUPABASE = True
except ImportError:
    print("Warning: Supabase dependencies not found. Some features may not work.")
    HAS_SUPABASE = False

# Load environment variables
load_dotenv()

def print_help():
    """Print help information."""
    print("\nSupabase Integration Test")
    print("=" * 22)
    print("1. Test database connection")
    print("2. Test authentication")
    print("3. Test real-time updates")
    print("4. Run all tests")
    print("0. Exit")
    print("=" * 22)

async def test_database_connection():
    """Test database connection and basic operations."""
    print("\nTesting database connection...")
    
    if not HAS_SUPABASE:
        print("❌ Supabase is not available. Please check your installation.")
        return False
    
    try:
        # Test connection by getting the current user
        user = supabase_auth.get_current_user()
        if user:
            print(f"✅ Connected to Supabase as {user.email}")
        else:
            print("⚠️  Not authenticated. Some features may be limited.")
        
        # Test basic database operations
        try:
            # Try to get the first employee
            result = supabase_manager.client.table('employees').select('*').limit(1).execute()
            print(f"✅ Database query successful. Found {len(result.data)} employees.")
            return True
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            print("   Make sure your Supabase tables are properly set up.")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        print("   Please check your SUPABASE_URL and SUPABASE_KEY in .env")
        return False

async def test_authentication():
    """Test user authentication."""
    print("\nTesting authentication...")
    
    if not HAS_SUPABASE:
        print("❌ Supabase is not available. Cannot test authentication.")
        return False
    
    # Try to sign in with environment variables
    email = os.getenv("SUPABASE_ADMIN_EMAIL")
    password = os.getenv("SUPABASE_ADMIN_PASSWORD")
    
    if not email or not password:
        print("⚠️  SUPABASE_ADMIN_EMAIL and SUPABASE_ADMIN_PASSWORD environment variables not set.")
        try:
            email = input("Enter admin email: ").strip()
            password = input("Enter admin password: ").strip()
            if not email or not password:
                print("❌ Email and password are required")
                return False
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return False
    
    try:
        user = supabase_auth.sign_in(email, password)
        if user:
            print(f"✅ Successfully authenticated as {user.email}")
            return True
        else:
            print("❌ Authentication failed: Invalid credentials")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("   Please check your credentials and internet connection")
        return False

def on_attendance_update(payload):
    """Callback for real-time attendance updates."""
    print("\n📡 Real-time update received:")
    print(json.dumps(payload, indent=2, default=str))

async def test_realtime_updates():
    """Test real-time updates."""
    print("\nTesting real-time updates...")
    
    if not HAS_SUPABASE:
        print("❌ Supabase is not available. Cannot test real-time updates.")
        return False
    
    try:
        # Connect to the real-time service
        if not supabase_realtime.connect():
            print("❌ Failed to connect to real-time service")
            return False
        
        # Subscribe to attendance table updates
        if supabase_realtime.subscribe_to_table(
            table="attendance",
            event="INSERT",
            callback=on_attendance_update
        ):
            print("✅ Subscribed to real-time updates on 'attendance' table")
            print("   - Open the web app or desktop app to trigger an attendance event")
            print("   - Press Ctrl+C to stop listening")
            return True
        else:
            print("❌ Failed to subscribe to real-time updates")
            print("   Make sure your Supabase project has real-time enabled")
            return False
    except Exception as e:
        print(f"❌ Error setting up real-time updates: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("Running all tests...\n")
    
    results = {
        "database": await test_database_connection(),
        "authentication": await test_authentication(),
        "realtime": await test_realtime_updates()
    }
    
    print("\nTest Results:")
    print("============")
    for test, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test.upper()}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")

async def main():
    """Main function."""
    while True:
        print_help()
        choice = input("\nEnter your choice (0-4): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            await test_database_connection()
        elif choice == '2':
            await test_authentication()
        elif choice == '3':
            await test_realtime_updates()
            # Keep the connection open for real-time updates
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping real-time updates...")
                supabase_realtime.close()
        elif choice == '4':
            await run_all_tests()
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    import json  # Added for JSON serialization in on_attendance_update
    asyncio.run(main())
