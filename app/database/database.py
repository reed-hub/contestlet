import time
import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager with lazy initialization and connection pooling"""
    
    def __init__(self):
        self._settings = None
        self._engine = None
        self._session_factory = None
        self._initialized = False
    
    @property
    def settings(self):
        """Lazy load settings"""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    @property
    def engine(self):
        """Lazy load engine"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """Lazy load session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def _create_engine(self):
        """Create database engine with environment-specific configuration"""
        url = self.settings.database_url
        
        # Engine configuration based on database type
        if self.settings.is_postgresql:
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.settings.debug
            )
        else:
            # SQLite configuration
            engine = create_engine(
                url,
                connect_args=self.settings.connect_args,
                echo=self.settings.debug
            )
        
        # Add engine event listeners
        self._setup_engine_events(engine)
        return engine
    
    def _setup_engine_events(self, engine):
        """Setup database engine event listeners"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance"""
            if self.settings.is_sqlite:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries in debug mode"""
            if self.settings.debug:
                query_times = conn.info.setdefault('query_start_time', [])
                query_times.append(time.time())
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log query execution time in debug mode"""
            query_times = conn.info.get('query_start_time', [])
            start_time = query_times.pop() if query_times else None
            if start_time:
                execution_time = time.time() - start_time
                if execution_time > 1.0:  # Log slow queries (>1s)
                    print(f"🐌 Slow query ({execution_time:.2f}s): {statement[:100]}...")
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_dependency(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from db_manager.get_session_dependency()

def get_engine():
    """Get database engine"""
    return db_manager.engine

def get_session_factory():
    """Get session factory"""
    return db_manager.session_factory

# Import Base after db_manager is defined to avoid circular imports
from app.models import Base
