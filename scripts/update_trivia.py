
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
    SET acceptable_answers = ARRAY['gall bladder','gallbladder']
    WHERE answer = 'gall bladder'
    """
)
connection.commit()

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
    SET acceptable_answers = ARRAY[
        $$JFK's mother$$,$$John F. Kennedy's mother$$,$$John Kennedy's mother$$
    ]
    WHERE answer = $$John Kennedy's mother$$
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Abraham Lincoln','Lincoln']
    WHERE text LIKE '%president %' and answer = 'Lincoln'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Sam Adams','Samuel Adams']
    WHERE answer = 'Sam Adams'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Nicolas Sarkozy','Sarkozy']
    WHERE answer = 'Sarkozy'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY[
        'by kiss','by kissing him','kiss','with a kiss'
    ]
    WHERE answer = 'with a kiss'
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

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['femoral','femoral arteries']
    WHERE game_id = 3656 and answer = 'the femoral arteries'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['lawnmowers','lawnmower racing']
    WHERE game_id = 4245 and answer = 'lawnmower racing'
    """
)
connection.commit()

