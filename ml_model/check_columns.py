
import pandas as pd
from pathlib import Path

folder = Path(__file__).parent / "dataset"

for file in sorted(folder.glob("Flights_2022_*.csv")):
    print("\n" + "=" * 60)
    print("FILE:", file.name)

    df = pd.read_csv(file, nrows=5)

    print("Airline-related columns:")
    for column in df.columns:
        if "airline" in column.lower():
            print(repr(column))

    print("\nRequired column check:")
    for column in [
        "Year", "Month", "DayofMonth", "DayOfWeek",
        "Origin", "Dest", "CRSDepTime", "Distance",
        "DepDel15", "FlightDate", "Cancelled", "Diverted"
    ]:
        print(column, ":", column in df.columns)
