
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

# Add acceptable_answers and invalid columns
connection.execute(
    """
    ALTER TABLE trivia.clues
    ADD COLUMN IF NOT EXISTS acceptable_answers TEXT[]
    """
)
connection.execute(
    """
    ALTER TABLE trivia.clues
    ADD COLUMN IF NOT EXISTS invalid BOOL DEFAULT FALSE
    """
)
connection.commit()

# Denote invalid clues

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

# Add acceptable answers

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Harry S. Truman','Truman']
    WHERE answer = 'Harry S. Truman'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['bantam','bantam chicken']
    WHERE game_id = 8158 and answer = 'the bantam chicken'
    """
)
connection.commit()

