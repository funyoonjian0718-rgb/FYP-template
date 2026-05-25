#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '.')
from app.rag.mysql_embeddings import MySQLEmbeddingService
emb = MySQLEmbeddingService()
count = emb.count()
print(f'Total embeddings in MySQL: {count}')
