#!/usr/bin/env python3
"""Diagnostics and small helpers for DB, ingestion, and Ollama checks.

Usage examples:
  python diag.py --print-db
  python diag.py --init-db
  python diag.py --create-user 123@gmail.com 12345678
  python diag.py --ingest
  python diag.py --check-chroma
  python diag.py --check-ollama
"""
from __future__ import annotations

import argparse
import os
import sys
import requests

# Ensure backend project root is on sys.path so `import app.*` works when
# running this script directly from `backend` or `backend/scripts`.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.settings import settings
from app.db.init_db import init_db as _init_db
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.db.models import User


def print_db() -> None:
    print("DATABASE_URL:", settings.database_url)


def init_db() -> None:
    print("Initializing database...")
    _init_db()
    print("Done. Tables created (if not exist).")


def create_user(email: str, password: str) -> None:
    sess = SessionLocal()
    try:
        existing = sess.query(User).filter(User.email == email).first()
        if existing:
            print(f"User already exists: {email} (id={existing.id})")
            return
        u = User(email=email, password_hash=hash_password(password))
        sess.add(u)
        sess.commit()
        print(f"Created user {email} (id={u.id})")
    finally:
        sess.close()


def set_password(email: str, password: str) -> None:
    sess = SessionLocal()
    try:
        user = sess.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found, creating: {email}")
            user = User(email=email, password_hash=hash_password(password))
            sess.add(user)
            sess.commit()
            print(f"Created user {email} (id={user.id})")
            return
        user.password_hash = hash_password(password)
        sess.commit()
        print(f"Updated password for {email} (id={user.id})")
    finally:
        sess.close()


def run_ingest() -> None:
    print("Running ingestion pipeline (Chroma)...")
    try:
        from app.rag.ingest import main as ingest_main

        ingest_main()
    except Exception as e:
        print("Ingest failed:", repr(e))
        raise


def check_chroma() -> None:
    import os

    path = settings.vectorstore_dir
    print(f"Checking Chroma dir: {path}")
    if not os.path.exists(path):
        print("Chroma directory does not exist.")
        return
    entries = os.listdir(path)
    print("Chroma files:", entries)


def check_ollama() -> None:
    url = settings.ollama_base_url
    print(f"Checking Ollama base URL: {url}")
    try:
        r = requests.get(url, timeout=3)
        print("Ollama reachable, status:", r.status_code)
    except Exception as e:
        print("Ollama check failed:", repr(e))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--print-db", action="store_true")
    p.add_argument("--init-db", action="store_true")
    p.add_argument("--create-user", nargs=2, metavar=("EMAIL", "PASSWORD"))
    p.add_argument("--set-password", nargs=2, metavar=("EMAIL", "PASSWORD"), help="Set password for existing user or create user if missing")
    p.add_argument("--ingest", action="store_true")
    p.add_argument("--check-chroma", action="store_true")
    p.add_argument("--check-ollama", action="store_true")
    args = p.parse_args(argv)

    if args.print_db:
        print_db()
    if args.init_db:
        init_db()
    if args.create_user:
        email, password = args.create_user
        create_user(email, password)
    if args.set_password:
        email, password = args.set_password
        set_password(email, password)
    if args.ingest:
        run_ingest()
    if args.check_chroma:
        check_chroma()
    if args.check_ollama:
        check_ollama()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
