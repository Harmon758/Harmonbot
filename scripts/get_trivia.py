
import os
import time
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
import dotenv
import psycopg
import requests
from rich.progress import (
    Progress,
    BarColumn, MofNCompleteColumn, SpinnerColumn, TextColumn, TimeElapsedColumn
)


DEFAULT_DELAY = 20


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


print("Getting robots.txt:")
response = session.get("https://www.j-archive.com/robots.txt")

user_agents = {}
for user_agent_section in response.text.split("\n\n"):
    lines = user_agent_section.split('\n')
    if lines[0].lower().startswith("user-agent:"):
        user_agents[lines[0].split(':')[1].strip()] = lines[1:]
    else:
        print(
            "Encountered section of robots.txt that doesn't start with "
            "\"User-Agent:\""
        )

delay = DEFAULT_DELAY

for line in user_agents.get('*', []):
    if line.lower().startswith("crawl-delay:"):
        delay = int(line.split(':')[1])
        print(f"Using specified crawl delay of {delay} seconds")
        break
else:
    print(
        "Couldn't find crawl delay directive for wildcard User-Agent; "
        f"using default delay of {DEFAULT_DELAY} seconds"
    )


waiting_progress = Progress(
    SpinnerColumn(),
    TextColumn("Waiting {task.remaining:.0f} second(s)"),
    transient = True
)
waiting_progress.start()

for second in waiting_progress.track(range(delay)):
    time.sleep(1)
waiting_progress.remove_task(waiting_progress.task_ids[0])

overall_progress = Progress(
    TextColumn("{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TimeElapsedColumn()
)
overall_progress.start()

print("Getting seasons:")

response = session.get("https://j-archive.com/listseasons.php")
parsed = BeautifulSoup(response.text, "lxml")
for a in overall_progress.track(
    parsed.table.find_all('a'), description = "Processing seasons"
):
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

    for second in waiting_progress.track(range(delay)):
        time.sleep(1)
    waiting_progress.remove_task(waiting_progress.task_ids[0])

    season_progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn()
    )
    season_progress.start()

    season_response = session.get(season_url)
    parsed_season = BeautifulSoup(season_response.text, "lxml")
    for season_a in season_progress.track(
        parsed_season.table.find_all('a'),
        description = f"Processing games from {season_name}"
    ):
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

        for second in waiting_progress.track(range(delay)):
            time.sleep(1)
        waiting_progress.remove_task(waiting_progress.task_ids[0])

        print(f"Processing game: {game_id} ...")

        game_response = session.get(
            "https://j-archive.com/showgame.php",
            params = {"game_id": game_id}
        )
        parsed_game = BeautifulSoup(game_response.text, "lxml")

        if season_name == "Trebek pilots":
            if parsed_game.title.text.split("taped")[1].strip() != airdate:
                print(f"Airdate mismatch for game {game_id}")
        elif parsed_game.title.text.split("aired")[1].strip() != airdate:
            print(f"Airdate mismatch for game {game_id}")

        round_tables = parsed_game.find_all("table", class_ = "round")
        for round, round_table in enumerate(round_tables):
            categories = []
            for categonry_td in round_table.find_all(
                "td", class_ = "category_name"
            ):
                categories.append(categonry_td.text)

            category_index = -1
            skipped_count = 0
            for clue_td in round_table.find_all("td", class_ = "clue"):
                category_index += 1
                daily_double = False

                if clue_td.contents == ['\n']:
                    continue

                suggest_correction_a = clue_td.find(
                    'a', title = "Suggest a correction for this clue"
                )

                if not suggest_correction_a:
                    skipped_count += 1
                    continue

                clue_id = int(
                    parse_qs(
                        urlparse(
                            suggest_correction_a["href"]
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

            if skipped_count:
                print(f"Skipped {skipped_count} clues in game {game_id}")

        # TODO: Final round?, clue ID not exposed

    season_progress.update(
        season_progress.task_ids[0],
        description = f"Processed {season_name}",
        refresh = True
    )
    season_progress.stop()

overall_progress.update(
    overall_progress.task_ids[0],
    description = "Processed all seasons",
    refresh = True
)

overall_progress.stop()
waiting_progress.stop()
connection.close()
session.close()

