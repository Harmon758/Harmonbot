
# https://github.com/chadwickbureau/register

import io
import os
import string
from zipfile import ZipFile

import dotenv
import pandas
import psycopg
import requests
import sqlalchemy


dotenv.load_dotenv()

connection = psycopg.connect(
    "user=harmonbot "
    f"password={os.getenv('DATABASE_PASSWORD')} "
    "dbname=harmonbot "
    f"host={os.getenv('POSTGRES_HOST') or 'localhost'}"
)

connection.execute("CREATE SCHEMA IF NOT EXISTS baseball")
connection.commit()


response = requests.get(
    "https://github.com/chadwickbureau/register/archive/refs/heads/master.zip"
)

file = ZipFile(io.BytesIO(response.content))

dataframes = []
for hexdigit in string.hexdigits[:16]:
    dataframe = pandas.read_csv(
        file.open(f"register-master/data/people-{hexdigit}.csv"),
        low_memory = False, dtype_backend = "numpy_nullable"
    )
    dataframes.append(dataframe)

dataframe = pandas.concat(dataframes)


engine = sqlalchemy.create_engine(
    f"postgresql+psycopg://harmonbot:{os.getenv('DATABASE_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST') or 'localhost'}/harmonbot"
)

dataframe.to_sql(
    "people", engine,
    schema = "baseball", if_exists = "replace", index = False,
    dtype = {  # https://github.com/pandas-dev/pandas/issues/35347
        "birth_year": sqlalchemy.INT,
        "birth_month": sqlalchemy.INT,
        "birth_day": sqlalchemy.INT,
        "death_year": sqlalchemy.INT,
        "death_month": sqlalchemy.INT,
        "death_day": sqlalchemy.INT,
        "pro_played_first": sqlalchemy.INT,
        "pro_played_last": sqlalchemy.INT,
        "mlb_played_first": sqlalchemy.INT,
        "mlb_played_last": sqlalchemy.INT,
        "col_played_first": sqlalchemy.INT,
        "col_played_last": sqlalchemy.INT,
        "pro_managed_first": sqlalchemy.INT,
        "pro_managed_last": sqlalchemy.INT,
        "mlb_managed_first": sqlalchemy.INT,
        "mlb_managed_last": sqlalchemy.INT,
        "col_managed_first": sqlalchemy.INT,
        "col_managed_last": sqlalchemy.INT,
        "pro_umpired_first": sqlalchemy.INT,
        "pro_umpired_last": sqlalchemy.INT,
        "mlb_umpired_first": sqlalchemy.INT,
        "mlb_umpired_last": sqlalchemy.INT
    }
)

