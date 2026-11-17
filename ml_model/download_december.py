
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import os

DATASET_DIR = Path(__file__).parent / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

year = 2022
month = 12

csv_path = DATASET_DIR / "Flights_2022_12.csv"
zip_path = DATASET_DIR / "flight_data_2022_12.zip"

url = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_"
    "1987_present_2022_12.zip"
)

try:
    print("Downloading December 2022 flight dataset...")

    urlretrieve(url, zip_path)

    print("Download complete. Extracting CSV...")

    with ZipFile(zip_path, "r") as archive:

        csv_files = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]

        if not csv_files:
            raise ValueError("No CSV file found inside ZIP.")

        with archive.open(csv_files[0]) as source:
            with open(csv_path, "wb") as destination:
                while True:
                    chunk = source.read(1024 * 1024)

                    if not chunk:
                        break

                    destination.write(chunk)

    os.remove(zip_path)

    print("\nDecember dataset downloaded successfully!")
    print("Saved at:", csv_path)

except Exception as error:

    print("\nDownload failed:", error)

    if zip_path.exists():
        zip_path.unlink()
