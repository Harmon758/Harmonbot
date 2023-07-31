
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
    "Judas Iscariot": ["Judas", "Judas Iscariot"],
    "(Kenneth) Starr": ["Ken Starr", "Kenneth Starr", "Starr"],
    "Luciano Pavarotti": ["Luciano Pavarotti", "Pavarotti"],
    "Louis Pasteur": ["Louis Pasteur", "Pasteur"],
    "Louis Renault": ["Louis Renault", "Renault"],
    "Love Canal (Niagara)": ["Love Canal", "Niagara", "Niagara Falls"],
    "Phnom Penh, Cambodia": ["Phnom Penh", "Phnom Penh, Cambodia"],
    "Sam Adams": ["Sam Adams", "Samuel Adams"],
    "Sarkozy": ["Nicolas Sarkozy", "Sarkozy"],
    "Sir Winston Churchill": [
        "Churchill", "Sir Winston Churchill", "Winston Churchill"
    ],
    "with a kiss": ["by kiss", "by kissing him", "kiss", "with a kiss"]
}

for answer, acceptable_answers in acceptable_answers_dict.items():
    connection.execute(
        """
        UPDATE trivia.clues
        SET acceptable_answers = %s
        WHERE answer = %s
        """,
        (acceptable_answers, answer)
    )
    connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY[
        $$JFK's mother$$, $$John F. Kennedy's mother$$,
        $$John Kennedy's mother$$
    ]
    WHERE answer = $$John Kennedy's mother$$
    """
)
connection.commit()

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
    SET acceptable_answers = ARRAY['peregrine', 'peregrine falcon']
    WHERE text LIKE '%falcon %' and answer = 'the peregrine falcon'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['Abraham Lincoln', 'Lincoln']
    WHERE text LIKE '%president %' and answer = 'Lincoln'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['po boy', $$po' boy$$, 'po-boy', 'poor boy']
    WHERE answer = $$a po' boy$$
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['bantam', 'bantam chicken']
    WHERE game_id = 8158 and answer = 'the bantam chicken'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['femoral', 'femoral arteries']
    WHERE game_id = 3656 and answer = 'the femoral arteries'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['lawnmowers', 'lawnmower racing']
    WHERE game_id = 4245 and answer = 'lawnmower racing'
    """
)
connection.commit()

connection.execute(
    """
    UPDATE trivia.clues
    SET acceptable_answers = ARRAY['San Andreas', 'San Andreas Fault']
    WHERE id IN (109115, 144801, 331840) and answer = 'San Andreas Fault'
    """
)
connection.commit()

