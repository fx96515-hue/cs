from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os

from app.db.session import Base

# Import models so metadata is registered
from app.models.user import User  # noqa: F401
from app.models.cooperative import Cooperative  # noqa: F401
from app.models.roaster import Roaster  # noqa: F401
from app.models.source import Source  # noqa: F401
from app.models.market import MarketObservation  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.lot import Lot  # noqa: F401
from app.models.margin import MarginRun  # noqa: F401
from app.models.evidence import EntityEvidence  # noqa: F401
from app.models.entity_alias import EntityAlias  # noqa: F401
from app.models.entity_event import EntityEvent  # noqa: F401
from app.models.web_extract import WebExtract  # noqa: F401
from app.models.news_item import NewsItem  # noqa: F401
from app.models.peru_region import PeruRegion  # noqa: F401
from app.models.region import Region  # noqa: F401
from app.models.knowledge_doc import KnowledgeDoc  # noqa: F401
from app.models.cupping import CuppingResult  # noqa: F401
from app.models.freight_history import FreightHistory  # noqa: F401
from app.models.coffee_price_history import CoffeePriceHistory  # noqa: F401
from app.models.ml_model import MLModel  # noqa: F401

MODEL_IMPORTS = (
    User,
    Cooperative,
    Roaster,
    Source,
    MarketObservation,
    Report,
    Lot,
    MarginRun,
    EntityEvidence,
    EntityAlias,
    EntityEvent,
    WebExtract,
    NewsItem,
    PeruRegion,
    Region,
    KnowledgeDoc,
    CuppingResult,
    FreightHistory,
    CoffeePriceHistory,
    MLModel,
)

config = context.config
fileConfig(str(config.config_file_name))

target_metadata = Base.metadata


def get_url() -> str | None:
    return os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")


def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
