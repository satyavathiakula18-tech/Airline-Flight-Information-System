
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import os

DATASET_DIR = Path(__file__).parent / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

# Additional months to download
months = [8, 9, 10, 11, 12]

year = 2022

for month in months:

    csv_name = f"Flights_{year}_{month}.csv"
    csv_path = DATASET_DIR / csv_name

    if csv_path.exists():
        print(f"Already exists: {csv_name}")
        continue

    zip_name = f"flight_data_{year}_{month}.zip"
    zip_path = DATASET_DIR / zip_name

    url = (
        "https://transtats.bts.gov/PREZIP/"
        "On_Time_Reporting_Carrier_On_Time_Performance_"
        f"1987_present_{year}_{month}.zip"
    )

    try:
        print(f"\nDownloading {csv_name}...")

        urlretrieve(url, zip_path)

        print("Download complete. Extracting...")

        with ZipFile(zip_path, "r") as archive:

            csv_files = [
                name for name in archive.namelist()
                if name.lower().endswith(".csv")
            ]

            if not csv_files:
                raise ValueError("No CSV file found in ZIP.")

            with archive.open(csv_files[0]) as source:
                with open(csv_path, "wb") as destination:
                    while True:
                        chunk = source.read(1024 * 1024)

                        if not chunk:
                            break

                        destination.write(chunk)

        os.remove(zip_path)

        print(f"Saved successfully: {csv_name}")

    except Exception as error:
        print(f"Failed for {year}-{month}: {error}")

        if zip_path.exists():
            zip_path.unlink()

print("\nDataset downloading process completed!")
print("Dataset folder:", DATASET_DIR)
