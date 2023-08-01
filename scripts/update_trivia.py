
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
    WHERE text = '=' OR answer = '='
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET invalid = TRUE
    WHERE game_id = 1740 AND category = 'A'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET invalid = TRUE
    WHERE game_id = 4279 AND text = '1'
    """
)
connection.commit()

# Add acceptable answers

acceptable_answers_dict = {
    "Antony": ["Antony", "Mark Antony"],
    "Benjamin Franklin": ["Ben Franklin", "Benjamin Franklin"],
    "the Capitol": [
        "Capitol", "Capitol Building", "United States Capitol",
        "United States Capitol Building", "U.S. Capitol",
        "U.S. Capitol Building"
    ],
    "Cosmo Kramer": ["Cosmo Kramer", "Kramer"],
    "Creedence Clearwater Revival": ["CCR", "Creedence Clearwater Revival"],
    "gall bladder": ["gall bladder", "gallbladder"],
    "Harry S. Truman": ["Harry S. Truman", "Truman"],
    "John Kennedy's mother": [
        "JFK's mother", "John F. Kennedy's mother", "John Kennedy's mother"
    ],
    "Judas Iscariot": ["Judas", "Judas Iscariot"],
    "(Kenneth) Starr": ["Ken Starr", "Kenneth Starr", "Starr"],
    "Luciano Pavarotti": ["Luciano Pavarotti", "Pavarotti"],
    "Louis Pasteur": ["Louis Pasteur", "Pasteur"],
    "Louis Renault": ["Louis Renault", "Renault"],
    "Love Canal (Niagara)": ["Love Canal", "Niagara", "Niagara Falls"],
    "Phnom Penh, Cambodia": ["Phnom Penh", "Phnom Penh, Cambodia"],
    "a po' boy": ["po boy", "po' boy", "po-boy", "poor boy"],
    "Sam Adams": ["Sam Adams", "Samuel Adams"],
    "Sarkozy": ["Nicolas Sarkozy", "Sarkozy"],
    "Sir Winston Churchill": [
        "Churchill", "Sir Winston Churchill", "Winston Churchill"
    ],
    "with a kiss": ["by kiss", "by kissing him", "kiss", "with a kiss"]
}

with connection.cursor() as cursor:
    for answer, acceptable_answers in acceptable_answers_dict.items():
        cursor.execute(
            """
            UPDATE trivia.clues
            SET acceptable_answers = %s
            WHERE answer = %s AND acceptable_answers IS NULL
            """,
            (acceptable_answers, answer)
        )
        connection.commit()

        if cursor.rowcount:
            print(f'Updated {cursor.rowcount} rows for "{answer}"')

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY[
        'Isaac Newton', 'Newton', 'Sir Isaac Newton'
    ]
    WHERE answer = 'Isaac Newton' OR answer = 'Sir Isaac Newton'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Bragg', 'Fort Bragg']
    WHERE text LIKE '%fort%' AND answer = 'Fort Bragg'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['peregrine', 'peregrine falcon']
    WHERE text LIKE '%falcon%' AND answer = 'the peregrine falcon'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Abraham Lincoln', 'Lincoln']
    WHERE text LIKE '%president %' AND answer = 'Lincoln'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['bantam', 'bantam chicken']
    WHERE game_id = 8158 AND answer = 'the bantam chicken'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['femoral', 'femoral arteries']
    WHERE game_id = 3656 AND answer = 'the femoral arteries'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['lawnmowers', 'lawnmower racing']
    WHERE game_id = 4245 AND answer = 'lawnmower racing'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['San Andreas', 'San Andreas Fault']
    WHERE id IN (109115, 144801, 331840) AND answer = 'San Andreas Fault'
    """
)
connection.commit()

