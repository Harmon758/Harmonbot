
import contextlib
import json
import os
import sys

import asyncpg

BETA = any("beta" in arg.lower() for arg in sys.argv)

@contextlib.asynccontextmanager
async def create_database_connection():
	connection = await asyncpg.connect(
		user = "harmonbot", 
		password = os.getenv("DATABASE_PASSWORD"), 
		database = "harmonbot_beta" if BETA else "harmonbot", 
		host = os.getenv("POSTGRES_HOST") or "localhost"
	)
	await initialize_database_connection(connection)
	try:
		yield connection
	finally:
		await connection.close()

async def create_database_pool():
	return await asyncpg.create_pool(
		user = "harmonbot", 
		password = os.getenv("DATABASE_PASSWORD"), 
		database = "harmonbot_beta" if BETA else "harmonbot", 
		host = os.getenv("POSTGRES_HOST") or "localhost", 
		init = initialize_database_connection
	)

async def initialize_database_connection(connection):
	await connection.set_type_codec(
		"jsonb", 
		encoder = json.dumps, decoder = json.loads, 
		schema = "pg_catalog"
	)

