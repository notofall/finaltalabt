"""
PostgreSQL Database Connection Manager
Supports dynamic configuration from setup wizard
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Create Base class for models
Base = declarative_base()

# Path to saved configuration
CONFIG_DIR = Path(__file__).parent.parent / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_database_url():
    """Get database URL from saved config or environment variables"""
    
    # First check for saved configuration from setup wizard
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                db_config = config.get('database', {})
                
                # Check for SQLite type
                if db_config.get('type') == 'sqlite':
                    db_path = CONFIG_DIR / "talabat.db"
                    url = f"sqlite+aiosqlite:///{db_path}"
                    logger.info(f"Using SQLite database: {db_path}")
                    return url
                
                if db_config.get('host'):
                    host = db_config.get('host')
                    port = db_config.get('port', 5432)
                    database = db_config.get('database', 'talabat_db')
                    username = db_config.get('username', 'postgres')
                    password = db_config.get('password', '')
                    ssl_mode = db_config.get('ssl_mode', 'disable')
                    
                    ssl_param = f"?ssl={ssl_mode}" if ssl_mode != "disable" else ""
                    url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}{ssl_param}"
                    logger.info(f"Using saved database config: {host}:{port}/{database}")
                    return url
        except Exception as e:
            logger.warning(f"Could not load saved config: {e}")
    
    # Fall back to environment variables
    from .config import postgres_settings
    logger.info("Using environment variables for database config")
    return postgres_settings.database_url


# Determine pool class based on environment
USE_NULL_POOL = os.environ.get("USE_NULL_POOL", "false").lower() == "true"

# Global engine variable - will be created on first use or after setup
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the database engine"""
    global _engine
    
    if _engine is None:
        database_url = get_database_url()
        
        try:
            from .config import postgres_settings
            
            _engine = create_async_engine(
                database_url,
                poolclass=NullPool if USE_NULL_POOL else AsyncAdaptedQueuePool,
                pool_size=postgres_settings.pool_size if not USE_NULL_POOL else None,
                max_overflow=postgres_settings.max_overflow if not USE_NULL_POOL else None,
                pool_pre_ping=postgres_settings.pool_pre_ping,
                pool_recycle=postgres_settings.pool_recycle if not USE_NULL_POOL else None,
                echo=False,
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    return _engine


def get_session_maker():
    """Get or create the session maker"""
    global _async_session_maker
    
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    
    return _async_session_maker


def reset_engine():
    """Reset the engine to reload configuration"""
    global _engine, _async_session_maker
    if _engine:
        # Note: This should be done carefully in async context
        pass
    _engine = None
    _async_session_maker = None
    logger.info("Database engine reset - will reload config on next connection")


# Create initial engine
try:
    engine = get_engine()
except Exception as e:
    logger.warning(f"Initial engine creation failed (may need setup): {e}")
    engine = None

# Session maker - will be created when engine is available
async_session_maker = None
if engine:
    async_session_maker = get_session_maker()

# Alias for backward compatibility
async_session_pg = async_session_maker


async def init_postgres_db() -> None:
    """
    Initialize database by creating all tables defined in models.
    This should be called during application startup.
    """
    global engine, async_session_maker, async_session_pg
    
    # Ensure engine exists
    if engine is None:
        engine = get_engine()
        async_session_maker = get_session_maker()
        async_session_pg = async_session_maker
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Run migrations for buildings system
        await run_buildings_migrations()
        
        # Run migrations for RFQ system
        await run_rfq_migrations()
        
        # Run migrations for budget system
        await run_budget_migrations()
        
        # Run migrations for project system
        await run_project_migrations()
        
        logger.info("✅ PostgreSQL tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PostgreSQL tables: {e}")
        raise


async def run_buildings_migrations() -> None:
    """Run migrations for buildings system tables"""
    global engine
    
    if engine is None:
        return
    
    migrations = [
        # Add columns to projects table
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_area FLOAT DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS floors_count INTEGER DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS steel_factor FLOAT DEFAULT 120",
    ]
    
    try:
        database_url = get_database_url()
        is_sqlite = 'sqlite' in database_url
        
        if is_sqlite:
            # SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we need to check first
            async with engine.begin() as conn:
                # Check if columns exist
                result = await conn.execute(text("PRAGMA table_info(projects)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'total_area' not in columns:
                    await conn.execute(text("ALTER TABLE projects ADD COLUMN total_area FLOAT DEFAULT 0"))
                if 'floors_count' not in columns:
                    await conn.execute(text("ALTER TABLE projects ADD COLUMN floors_count INTEGER DEFAULT 0"))
                if 'steel_factor' not in columns:
                    await conn.execute(text("ALTER TABLE projects ADD COLUMN steel_factor FLOAT DEFAULT 120"))
            
            logger.info("✅ Buildings system migrations applied for SQLite")
        else:
            # PostgreSQL supports IF NOT EXISTS
            async with engine.begin() as conn:
                for migration in migrations:
                    try:
                        await conn.execute(text(migration))
                    except Exception as e:
                        # Ignore if column already exists
                        pass
            
            logger.info("✅ Buildings system migrations applied for PostgreSQL")
    except Exception as e:
        logger.warning(f"Buildings migrations warning (tables may already exist): {e}")


async def run_rfq_migrations() -> None:
    """Run migrations for RFQ system tables"""
    global engine
    
    if engine is None:
        return
    
    try:
        database_url = get_database_url()
        is_sqlite = 'sqlite' in database_url
        
        async with engine.begin() as conn:
            if is_sqlite:
                # Check quotation_requests columns
                try:
                    result = await conn.execute(text("PRAGMA table_info(quotation_requests)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'request_id' not in columns:
                        await conn.execute(text("ALTER TABLE quotation_requests ADD COLUMN request_id VARCHAR(36)"))
                    if 'request_number' not in columns:
                        await conn.execute(text("ALTER TABLE quotation_requests ADD COLUMN request_number VARCHAR(50)"))
                except:
                    pass
                
                # Check supplier_quotations columns
                try:
                    result = await conn.execute(text("PRAGMA table_info(supplier_quotations)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'is_winner' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN is_winner BOOLEAN DEFAULT 0"))
                    if 'approved_at' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN approved_at DATETIME"))
                    if 'approved_by' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN approved_by VARCHAR(36)"))
                    if 'approved_by_name' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN approved_by_name VARCHAR(255)"))
                    if 'order_id' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN order_id VARCHAR(36)"))
                    if 'order_number' not in columns:
                        await conn.execute(text("ALTER TABLE supplier_quotations ADD COLUMN order_number VARCHAR(50)"))
                except:
                    pass
                
                logger.info("✅ RFQ migrations applied for SQLite")
            else:
                # PostgreSQL migrations
                pg_migrations = [
                    "ALTER TABLE quotation_requests ADD COLUMN IF NOT EXISTS request_id VARCHAR(36)",
                    "ALTER TABLE quotation_requests ADD COLUMN IF NOT EXISTS request_number VARCHAR(50)",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS is_winner BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS approved_by VARCHAR(36)",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS approved_by_name VARCHAR(255)",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS order_id VARCHAR(36)",
                    "ALTER TABLE supplier_quotations ADD COLUMN IF NOT EXISTS order_number VARCHAR(50)",
                ]
                
                for migration in pg_migrations:
                    try:
                        await conn.execute(text(migration))
                    except:
                        pass
                
                logger.info("✅ RFQ migrations applied for PostgreSQL")
    except Exception as e:
        logger.warning(f"RFQ migrations warning: {e}")


async def run_budget_migrations() -> None:
    """Run migrations for budget system - add actual_spent column"""
    global engine
    
    if engine is None:
        return
    
    try:
        database_url = get_database_url()
        is_sqlite = 'sqlite' in database_url
        
        async with engine.begin() as conn:
            if is_sqlite:
                # Check if column exists in SQLite
                try:
                    result = await conn.execute(text("PRAGMA table_info(budget_categories)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'actual_spent' not in columns:
                        await conn.execute(text("ALTER TABLE budget_categories ADD COLUMN actual_spent FLOAT DEFAULT 0"))
                    if 'updated_at' not in columns:
                        await conn.execute(text("ALTER TABLE budget_categories ADD COLUMN updated_at DATETIME"))
                except Exception as e:
                    # Table might not exist yet
                    pass
                
                logger.info("✅ Budget migrations applied for SQLite")
            else:
                # PostgreSQL
                pg_migrations = [
                    "ALTER TABLE budget_categories ADD COLUMN IF NOT EXISTS actual_spent FLOAT DEFAULT 0",
                    "ALTER TABLE budget_categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
                ]
                for migration in pg_migrations:
                    try:
                        await conn.execute(text(migration))
                    except:
                        pass
                
                logger.info("✅ Budget migrations applied for PostgreSQL")
    except Exception as e:
        logger.warning(f"Budget migrations warning: {e}")


async def run_project_migrations() -> None:
    """Run migrations for project system - add supervisor_id and engineer_id columns"""
    global engine
    
    if engine is None:
        return
    
    try:
        database_url = get_database_url()
        is_sqlite = 'sqlite' in database_url
        
        async with engine.begin() as conn:
            if is_sqlite:
                # Check if columns exist in SQLite
                try:
                    result = await conn.execute(text("PRAGMA table_info(projects)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'supervisor_id' not in columns:
                        await conn.execute(text("ALTER TABLE projects ADD COLUMN supervisor_id VARCHAR(36)"))
                    if 'supervisor_name' not in columns:
                        await conn.execute(text("ALTER TABLE projects ADD COLUMN supervisor_name VARCHAR(255)"))
                    if 'engineer_id' not in columns:
                        await conn.execute(text("ALTER TABLE projects ADD COLUMN engineer_id VARCHAR(36)"))
                    if 'engineer_name' not in columns:
                        await conn.execute(text("ALTER TABLE projects ADD COLUMN engineer_name VARCHAR(255)"))
                except Exception as e:
                    pass
                
                logger.info("✅ Project migrations applied for SQLite")
            else:
                # PostgreSQL
                pg_migrations = [
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS supervisor_id VARCHAR(36)",
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS supervisor_name VARCHAR(255)",
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS engineer_id VARCHAR(36)",
                    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS engineer_name VARCHAR(255)",
                ]
                for migration in pg_migrations:
                    try:
                        await conn.execute(text(migration))
                    except:
                        pass
                
                logger.info("✅ Project migrations applied for PostgreSQL")
    except Exception as e:
        logger.warning(f"Project migrations warning: {e}")


async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that provides a database session to routes.
    
    Behavior:
    - On success: auto-commit after route completes
    - On exception: rollback and re-raise
    - Always: close session
    
    This ensures V2 routes don't need explicit commit() calls.
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            # Auto-commit on success (only commits if there are pending changes)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def close_postgres_db() -> None:
    """Close the database connection pool when the application shuts down."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("✅ PostgreSQL connection pool closed")
