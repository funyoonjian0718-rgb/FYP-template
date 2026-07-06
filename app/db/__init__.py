"""Database models and initialization."""
from app.db.models import User, QueryHistory, PasswordResetToken
from app.db.models_embeddings import Embedding

#inside the all list of the entire DB will only search for following 4
__all__ = ["User", "QueryHistory", "PasswordResetToken", "Embedding"]
