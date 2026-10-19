
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Read database settings from .env
load_dotenv()

# Build the connection URL safely, including special characters in passwords
connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "sales_analytics"),
)

try:
    engine = create_engine(connection_url)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE(), CURRENT_USER()"))
        database, user = result.fetchone()

        print("Connection successful!")
        print("Database:", database)
        print("MySQL user:", user)

except Exception as error:
    print("Connection failed.")
    print("Error type:", type(error).__name__)
    print("Check your .env settings and MySQL server.")
