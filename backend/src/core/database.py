"""
Database Connections
Manages PostgreSQL (SQLAlchemy) and MongoDB (Motor) connections.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine

from src.core.config import settings


# =============================================================================
# PostgreSQL Configuration (SQLAlchemy)
# =============================================================================

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


# Create async engine
engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.
    Usage: async with get_db_context() as db:
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# MongoDB Configuration (Motor)
# =============================================================================

class MongoDB:
    """MongoDB connection manager."""

    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    async def connect(cls):
        """Initialize MongoDB connection."""
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        cls.db = cls.client[settings.MONGODB_DB]

        # Verify connection
        await cls.client.admin.command("ping")
        print(f"Connected to MongoDB: {settings.MONGODB_DB}")

    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("Disconnected from MongoDB")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance."""
        if cls.db is None:
            raise RuntimeError("MongoDB not connected. Call MongoDB.connect() first.")
        return cls.db

    @classmethod
    def get_collection(cls, name: str):
        """Get a MongoDB collection by name."""
        return cls.get_db()[name]


# Convenience functions for MongoDB collections
def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    return MongoDB.get_db()


# =============================================================================
# Database Initialization
# =============================================================================

async def init_db():
    """Initialize database connections and create tables."""
    # Create PostgreSQL tables
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from src.auth import models as auth_models
        from src.members import models as member_models
        from src.hierarchy import models as hierarchy_models
        from src.events import models as event_models
        from src.communications import models as comm_models
        from src.donations import models as donation_models
        from src.voting import models as voting_models
        from src.workers import models as worker_models

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("PostgreSQL tables created")

    # Connect to MongoDB
    await MongoDB.connect()

    # Create MongoDB indexes
    await create_mongodb_indexes()


async def create_mongodb_indexes():
    """Create indexes for MongoDB collections."""
    db = MongoDB.get_db()

    # Voter profiles indexes
    await db.voter_profiles.create_index([("voter_id", 1)], unique=True)
    await db.voter_profiles.create_index([("address.district", 1)])
    await db.voter_profiles.create_index([("predicted_affinity.party_score", -1)])

    # Social posts indexes (sentiment analysis)
    await db.social_posts.create_index([("posted_at", -1)])
    await db.social_posts.create_index([("analysis.topics", 1)])
    await db.social_posts.create_index([("location.district", 1)])
    await db.social_posts.create_index([("source", 1), ("posted_at", -1)])

    # Sentiment aggregates indexes
    await db.sentiment_aggregates.create_index([
        ("date", -1),
        ("topic", 1),
        ("region.name", 1)
    ])

    # Member activity logs (with TTL - 90 days)
    await db.member_activity_logs.create_index([("member_id", 1), ("timestamp", -1)])
    await db.member_activity_logs.create_index(
        [("timestamp", 1)],
        expireAfterSeconds=7776000  # 90 days
    )

    # Engagement analytics
    await db.engagement_analytics.create_index([("date", -1), ("unit_id", 1)])

    # Model registry
    await db.model_registry.create_index([("model_name", 1), ("version", 1)], unique=True)

    # Prediction logs
    await db.prediction_logs.create_index([("model_name", 1), ("created_at", -1)])

    print("MongoDB indexes created")


async def close_db():
    """Close all database connections."""
    await engine.dispose()
    await MongoDB.disconnect()
    print("All database connections closed")


# =============================================================================
# Synchronous Database Access (for Celery)
# =============================================================================

# Create sync engine
sync_engine = create_engine(
    settings.POSTGRES_URL_SYNC,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


def get_sync_db():
    """
    Get synchronous database session for Celery tasks.
    Usage: db = get_sync_db()
    """
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
