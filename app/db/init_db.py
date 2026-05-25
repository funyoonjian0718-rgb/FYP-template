from app.db.base import Base
from app.db.session import engine
# Import models to register them with Base
from app.db import models, models_embeddings  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

