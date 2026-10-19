
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_data(file_path: str) -> pd.DataFrame:
    """Extract data from the source Excel file."""
    logger.info(f"Extracting data from {file_path}...")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    df = pd.read_excel(file_path)
    logger.info(f"Extracted {len(df)} rows")

    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean data; create Profit, Year, and Month."""
    logger.info("Starting data transformation...")
    initial_count = len(df)

    # 1. Validate required columns
    required_columns = [
        "Order_ID",
        "Order_Date",
        "Customer",
        "Region",
        "Product",
        "Sales",
        "Cost"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Source data is missing required columns: {missing_columns}"
        )

    logger.info("Input column validation passed")

    # 2. Validate numeric columns
    numeric_columns = ["Sales", "Cost"]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    invalid_numeric_rows = (
        df[numeric_columns].isna().any(axis=1).sum()
    )

    if invalid_numeric_rows > 0:
        raise ValueError(
            f"Found {invalid_numeric_rows} rows with missing or "
            "invalid numeric values in Sales or Cost."
        )

    logger.info("Numeric data validation passed")

    # 3. Remove exact duplicate rows
    df = df.drop_duplicates().copy()
    after_dedup = len(df)

    logger.info(
        f"Removed {initial_count - after_dedup} duplicate rows"
    )

    # 4. Convert dates and remove invalid dates
    df["Order_Date"] = pd.to_datetime(
        df["Order_Date"],
        errors="coerce"
    )

    df = df.dropna(subset=["Order_Date"]).copy()
    after_date_cleaning = len(df)

    logger.info(
        f"Removed {after_dedup - after_date_cleaning} rows "
        "with invalid dates"
    )

    # 5. Feature engineering
    df["Profit"] = df["Sales"] - df["Cost"]
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month

    logger.info(
        f"Transformation complete. Final row count: {len(df)}"
    )

    return df


def load_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Save cleaned data to CSV."""
    logger.info(f"Saving to CSV: {output_path}")

    df.to_csv(output_path, index=False)

    logger.info("CSV export complete")


def load_to_mysql(
    df: pd.DataFrame,
    table_name: str = "sales_data"
) -> int:
    """Load data into a new MySQL table without replacing an existing one."""
    load_dotenv()

    # Check required environment settings
    required = ["DB_USER", "DB_PASSWORD", "DB_NAME"]

    missing = [
        key for key in required
        if not os.getenv(key)
    ]

    if missing:
        raise ValueError(
            f"Missing database settings in .env: {', '.join(missing)}"
        )

    # Build the connection URL safely
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "sales_analytics"),
    )

    engine = create_engine(connection_url)

    try:
        logger.info(
            f"Loading data into MySQL table: {table_name}"
        )

        # Prevent overwriting an existing table
        inspector = inspect(engine)

        if inspector.has_table(table_name):
            raise RuntimeError(
                f"Table '{table_name}' already exists. "
                "No table was replaced. Check it before proceeding."
            )

        # Insert cleaned data into a new table
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="fail",
            index=False
        )

        logger.info(
            f"Successfully loaded {len(df)} rows into MySQL"
        )

        return len(df)

    except Exception as error:
        logger.error(f"MySQL loading failed: {error}")
        raise

    finally:
        engine.dispose()


def run_etl_pipeline(
    source_file: str = "sales_raw_500.xlsx",
    output_csv: str = "sales_cleaned.csv",
    mysql_enabled: bool = False,
    mysql_table: str = "sales_data"
) -> dict:
    """Run extraction, transformation, and loading steps."""
    start_time = datetime.now()

    logger.info("=" * 50)
    logger.info("Starting ETL Pipeline")
    logger.info("=" * 50)

    # 1. Extract
    raw_df = extract_data(source_file)

    # 2. Transform and validate
    clean_df = transform_data(raw_df)

    # 3. Load to CSV
    load_to_csv(clean_df, output_csv)

    # 4. Load to MySQL when enabled
    rows_loaded_mysql = 0
    mysql_status = "DISABLED"

    if mysql_enabled:
        try:
            rows_loaded_mysql = load_to_mysql(
                clean_df,
                table_name=mysql_table
            )
            mysql_status = "LOADED"

        except RuntimeError as error:
            if "already exists" in str(error):
                logger.warning(
                    "MySQL loading skipped: destination table "
                    "already exists. Existing data was not changed."
                )
                mysql_status = "SKIPPED_TABLE_EXISTS"
            else:
                raise

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 5. Generate pipeline summary
    summary = {
        "status": "SUCCESS",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration,
        "rows_extracted": len(raw_df),
        "rows_cleaned": len(clean_df),
        "rows_removed": len(raw_df) - len(clean_df),
        "rows_loaded_mysql": rows_loaded_mysql,
        "mysql_status": mysql_status,
        "output_file": output_csv
    }

    logger.info("=" * 50)
    logger.info("ETL Pipeline Complete!")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Rows extracted: {len(raw_df)}")
    logger.info(f"Rows cleaned: {len(clean_df)}")
    logger.info(f"Rows loaded into MySQL: {rows_loaded_mysql}")
    logger.info(f"MySQL status: {mysql_status}")
    logger.info("=" * 50)

    return summary


if __name__ == "__main__":
    load_dotenv()

    result = run_etl_pipeline(
        source_file="sales_raw_500.xlsx",
        output_csv="sales_cleaned.csv",
        mysql_enabled=True,
        mysql_table="sales_data"
    )

    print("\nETL Summary:")
    for key, value in result.items():
        print(f"  {key}: {value}")
