
import os
import time
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import dotenv
import psycopg
import requests


dotenv.load_dotenv()

connection = psycopg.connect(
    "user=harmonbot "
    f"password={os.getenv('DATABASE_PASSWORD')} "
    "dbname=harmonbot "
    f"host={os.getenv('POSTGRES_HOST') or 'localhost'}"
)
session = requests.Session()

connection.execute("CREATE SCHEMA IF NOT EXISTS trivia")
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS trivia.seasons (
        name      TEXT PRIMARY KEY,
        url       TEXT
    )
    """
)
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS trivia.games (
        id       INT PRIMARY KEY,
        season   TEXT REFERENCES trivia.seasons (name),
        airdate  DATE
    )
    """
)
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS trivia.clues (
        id            INT PRIMARY KEY,
        text          TEXT,
        answer        TEXT,
        value         INT,
        category      TEXT,
        daily_double  BOOL DEFAULT FALSE,
        double        BOOL DEFAULT FALSE,
        game_id       INT REFERENCES trivia.games (id)
    )
    """
)
connection.commit()

print("Processing seasons ...")
response = session.get("https://j-archive.com/listseasons.php")
parsed = BeautifulSoup(response.text, "lxml")
for a in parsed.table.find_all('a'):
    season_name = a.text
    season_url = "https://j-archive.com/" + a["href"]

    connection.execute(
        """
        INSERT INTO trivia.seasons (name, url)
        VALUES (%(name)s, %(url)s)
        ON CONFLICT (name) DO
        UPDATE SET url = %(url)s
        """,
        {"name": season_name, "url": season_url}
    )
    connection.commit()

    print(f"Processing {season_name} ...")
    time.sleep(10)

    season_response = session.get(season_url)
    parsed_season = BeautifulSoup(season_response.text, "lxml")
    for season_a in parsed_season.table.find_all('a'):
        game_url = season_a["href"]
        parsed_game_url = urlparse(game_url)
        try:
            game_id = int(parse_qs(parsed_game_url.query)["game_id"][0])
            if season_name == "Trebek pilots":
                airdate = season_a.text.split("taped")[1].strip()
            else:
                airdate = season_a.text.split("aired")[1].strip()
        except (KeyError, IndexError):
            if not game_url.startswith((
                "http://www.j-archive.com/media/",
                "https://www.j-archive.com/media/", "https://youtu.be/",
                "https://www.youtube.com/", "showplayer.php"
            )):
                print(f"Skipping URL: {game_url}")
            continue

        cursor = connection.execute(
            """
            INSERT INTO trivia.games (id, season, airdate)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING *
            """,
            (game_id, season_name, airdate)
        )
        connection.commit()

        if not cursor.fetchone():  # Skip games already processed
            continue

        print(f"Processing game: {game_id} ...")
        time.sleep(10)

        game_response = session.get(
            "https://j-archive.com/showgame.php",
            params = {"game_id": game_id}
        )
        parsed_game = BeautifulSoup(game_response.text, "lxml")

        if (
            (
                season_name == "Trebek pilots" and
                parsed_game.title.text.split("taped")[1].strip() != airdate
            ) or
            parsed_game.title.text.split("aired")[1].strip() != airdate
        ):
            print(f"Airdate mismatch for game {game_id}")

        round_tables = parsed_game.find_all("table", class_ = "round")
        for round, round_table in enumerate(round_tables):
            categories = []
            for categonry_td in round_table.find_all(
                "td", class_ = "category_name"
            ):
                categories.append(categonry_td.text)

            category_index = 0
            for clue_td in round_table.find_all("td", class_ = "clue"):
                daily_double = False

                if clue_td.contents == ['\n']:
                    continue

                clue_id = int(
                    parse_qs(
                        urlparse(
                            clue_td.find(
                                'a',
                                title = "Suggest a correction for this clue"
                            )["href"]
                        ).query
                    )["clue_id"][0]
                )

                clue_text = clue_td.find("td", class_ = "clue_text").text

                clue_answer = (
                    clue_td.find("em", class_ = "correct_response").text
                )

                if clue_value_td := clue_td.find("td", class_ = "clue_value"):
                    clue_value = int(
                        clue_value_td.text.lstrip('$').replace(',', "")
                    )
                else:
                    clue_value = int(
                        clue_td.find(
                            "td", class_ = "clue_value_daily_double"
                        ).text.split()[1].lstrip('$').replace(',', "")
                    )
                    daily_double = True

                category = categories[category_index % len(categories)]
                category_index += 1

                connection.execute(
                    """
                    INSERT INTO trivia.clues (
                        id, text, answer, value, category, daily_double,
                        double, game_id
                    )
                    VALUES (
                        %(id)s, %(text)s, %(answer)s, %(value)s, %(category)s,
                        %(daily_double)s, %(double)s, %(game_id)s
                    )
                    ON CONFLICT (id) DO
                    UPDATE SET text = %(text)s, answer = %(answer)s,
                               value = %(value)s, category = %(category)s,
                               daily_double = %(daily_double)s,
                               double = %(double)s, game_id = %(game_id)s
                    """,
                    {
                        "id": clue_id, "text": clue_text,
                        "answer": clue_answer, "value": clue_value,
                        "category": category, "daily_double": daily_double,
                        "double": bool(round), "game_id": game_id
                    }
                )
                connection.commit()

        # TODO: Final round?, clue ID not exposed

connection.close()
session.close()

