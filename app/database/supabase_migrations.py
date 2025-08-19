import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.supabase_config import supabase_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseMigration:
    """
    Handles database migrations for Supabase.
    """
    
    def __init__(self):
        self.client = supabase_config.client
        self.migrations_table = "_migrations"
        
    async def ensure_migrations_table(self):
        """Create the migrations table if it doesn't exist."""
        try:
            await self.client.execute("""
            CREATE TABLE IF NOT EXISTS public._migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(name)
            )
            """)
            logger.info("Migrations table ensured")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure migrations table: {e}")
            return False
            
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        try:
            result = await self.client.table(self.migrations_table).select("name").execute()
            return [migration['name'] for migration in result.data]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
            
    async def apply_migration(self, name: str, sql: str) -> bool:
        """Apply a single migration."""
        try:
            # Start a transaction
            await self.client.rpc('begin')
            
            # Execute the migration SQL
            await self.client.execute(sql)
            
            # Record the migration
            await self.client.table(self.migrations_table).insert({
                'name': name,
                'applied_at': datetime.utcnow().isoformat()
            }).execute()
            
            # Commit the transaction
            await self.client.rpc('commit')
            
            logger.info(f"Applied migration: {name}")
            return True
            
        except Exception as e:
            # Rollback on error
            await self.client.rpc('rollback')
            logger.error(f"Failed to apply migration {name}: {e}")
            return False
            
    async def run_migrations(self):
        """Run all pending migrations."""
        if not await self.ensure_migrations_table():
            logger.error("Failed to ensure migrations table")
            return False
            
        applied_migrations = await self.get_applied_migrations()
        
        # Define migrations in order
        migrations = [
            {
                'name': '0001_initial_schema',
                'sql': """
                    -- Create employees table
                    CREATE TABLE IF NOT EXISTS public.employees (
                        id BIGSERIAL PRIMARY KEY,
                        employee_code TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        job_title TEXT,
                        department TEXT,
                        phone_number TEXT UNIQUE,
                        web_fingerprint TEXT,
                        device_token TEXT UNIQUE,
                        zk_template TEXT,
                        qr_code TEXT UNIQUE,
                        status TEXT DEFAULT 'Active',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    
                    -- Create users table
                    CREATE TABLE IF NOT EXISTS public.users (
                        id BIGSERIAL PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('Viewer', 'Manager', 'HR', 'Admin', 'Scanner')),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    
                    -- Create attendance table
                    CREATE TABLE IF NOT EXISTS public.attendance (
                        id BIGSERIAL PRIMARY KEY,
                        employee_id BIGINT NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
                        check_time TIMESTAMP WITH TIME ZONE NOT NULL,
                        date DATE NOT NULL,
                        type TEXT NOT NULL,
                        location_id BIGINT,
                        notes TEXT,
                        work_duration_hours DOUBLE PRECISION,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    
                    -- Create indexes
                    CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON public.attendance(employee_id);
                    CREATE INDEX IF NOT EXISTS idx_attendance_date ON public.attendance(date);
                    CREATE INDEX IF NOT EXISTS idx_attendance_type ON public.attendance(type);
                    
                    -- Add trigger for updated_at
                    CREATE OR REPLACE FUNCTION update_modified_column() 
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW; 
                    END;
                    $$ LANGUAGE plpgsql;
                    
                    -- Apply triggers to all tables
                    DO $$
                    DECLARE
                        t text;
                    BEGIN
                        FOR t IN 
                            SELECT table_name FROM information_schema.columns 
                            WHERE column_name = 'updated_at' 
                            AND table_schema = 'public'
                        LOOP
                            EXECUTE format('DROP TRIGGER IF EXISTS update_%s_updated_at ON %I', t, t);
                            EXECUTE format('CREATE TRIGGER update_%s_updated_at
                                BEFORE UPDATE ON %I
                                FOR EACH ROW EXECUTE FUNCTION update_modified_column()', 
                                t, t);
                        END LOOP;
                    END;
                    $$;
                """
            },
            # Add more migrations here as needed
        ]
        
        # Apply pending migrations
        success = True
        for migration in migrations:
            if migration['name'] not in applied_migrations:
                logger.info(f"Applying migration: {migration['name']}")
                if not await self.apply_migration(migration['name'], migration['sql']):
                    logger.error(f"Failed to apply migration: {migration['name']}")
                    success = False
                    break
                    
        if success:
            logger.info("All migrations applied successfully")
        else:
            logger.error("Some migrations failed to apply")
            
        return success


async def run_supabase_migrations():
    """Run all pending Supabase migrations."""
    migrator = SupabaseMigration()
    return await migrator.run_migrations()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_supabase_migrations())
