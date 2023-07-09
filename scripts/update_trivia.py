
import os

import dotenv
import psycopg


dotenv.load_dotenv()

connection = psycopg.connect(
    "user=harmonbot "
    f"password={os.getenv('DATABASE_PASSWORD')} "
    "dbname=harmonbot "
    f"host={os.getenv('POSTGRES_HOST') or 'localhost'}"
)

connection.execute(
    """
    ALTER TABLE trivia.clues
    ADD COLUMN IF NOT EXISTS invalid BOOL DEFAULT FALSE
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET invalid = TRUE
    WHERE text = '=' or answer = '='
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET invalid = TRUE
    WHERE game_id = 1740 and category = 'A'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET invalid = TRUE
    WHERE game_id = 4279 and text = '1'
    """
)
connection.commit()

