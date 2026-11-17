
from pathlib import Path
import pandas as pd

DATASET_DIR = Path(__file__).parent / "dataset"

all_airlines = []

for file in sorted(DATASET_DIR.glob("Flights_2022_*.csv")):

    print(f"\nProcessing {file.name}...")

    # Read only the airline identifier column.
    columns = pd.read_csv(file, nrows=0).columns.str.strip()

    if "IATA_Code_Marketing_Airline" in columns:
        airline_column = "IATA_Code_Marketing_Airline"

    elif "IATA_CODE_Reporting_Airline" in columns:
        airline_column = "IATA_CODE_Reporting_Airline"

    else:
        print("Airline column not found!")
        continue

    df = pd.read_csv(
        file,
        usecols=[airline_column],
        low_memory=False
    )

    df.columns = ["Airline"]

    counts = df["Airline"].value_counts().reset_index()
    counts.columns = ["Airline", "Flight_Count"]
    counts["Month_File"] = file.name

    all_airlines.append(counts)

    print("Unique airlines:", df["Airline"].nunique())
    print("Total records:", len(df))

# Combine all monthly results.
result = pd.concat(all_airlines, ignore_index=True)

# Aggregate airline counts across all months.
summary = (
    result.groupby("Airline", as_index=False)["Flight_Count"]
    .sum()
    .sort_values("Flight_Count", ascending=False)
)

summary["Percentage"] = (
    summary["Flight_Count"] / summary["Flight_Count"].sum()
) * 100

output_path = DATASET_DIR.parent / "airline_distribution.csv"

summary.to_csv(output_path, index=False)

print("\n" + "=" * 55)
print("AIRLINE DISTRIBUTION SUMMARY")
print("=" * 55)

print(summary.to_string(index=False))

print("\nReport saved:", output_path)
