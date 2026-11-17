
from pathlib import Path
import pandas as pd

DATASET_DIR = Path(__file__).parent / "dataset"

for file in sorted(DATASET_DIR.glob("Flights_2022_*.csv")):

    print("\n" + "=" * 65)
    print("FILE:", file.name)

    df = pd.read_csv(file, nrows=10000, low_memory=False)

    df.columns = df.columns.str.strip()

    airline_columns = [
        "Marketing_Airline_Network",
        "Reporting_Airline",
        "Operating_Airline",
        "IATA_Code_Marketing_Airline",
        "IATA_CODE_Reporting_Airline",
        "IATA_Code_Operating_Airline"
    ]

    for column in airline_columns:

        if column in df.columns:

            print(f"\nColumn: {column}")

            print("Unique airline codes:")
            print(df[column].dropna().unique()[:20])

            print("Unique count:", df[column].nunique())

