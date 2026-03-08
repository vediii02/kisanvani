from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings
from db.base import Base
from db.models.organisation import Organisation  # noqa: F401
from db.models.organisation_phone import OrganisationPhoneNumber  # noqa: F401
from db.models.company import Company  # noqa: F401
from db.models.farmer import Farmer  # noqa: F401
from db.models.call_session import CallSession  # noqa: F401
from db.models.call_state import CallState  # noqa: F401
from db.models.call_transcript import CallTranscript  # noqa: F401
from db.models.call_metrics import CallMetrics  # noqa: F401
from db.models.call_summary import CallSummary  # noqa: F401
from db.models.case import Case  # noqa: F401
from db.models.advisory import Advisory  # noqa: F401
from db.models.kb_entry import KBEntry  # noqa: F401
try:
    from db.models.knowledge_base import KnowledgeEntry  # noqa: F401
except Exception:
    # Allow migrations to run even if optional pgvector Python package
    # is unavailable in the execution environment.
    KnowledgeEntry = None  # noqa: F401
from db.models.escalation import Escalation  # noqa: F401
from db.models.user import User  # noqa: F401
from db.models.product import Product  # noqa: F401
from db.models.brand import Brand  # noqa: F401
from db.models.organisation_kb import OrganisationKnowledgeBase  # noqa: F401
from db.models.audit import AuditLog, PlatformConfig, BannedProduct  # noqa: F401
from db.models.farmer_query import FarmerQuery  # noqa: F401
from db.models.farmer_questions import FarmerQuestion  # noqa: F401

config = context.config
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in ("checkpoints", "checkpoint_writes", "checkpoint_blobs", "checkpoint_migrations"):
        return False
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
