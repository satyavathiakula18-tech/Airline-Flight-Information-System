import pandas as pd

file_path = "dataset/Flights_2022_7.csv"

df = pd.read_csv(file_path, nrows=5)

print("\nCOLUMN NAMES:")
print(df.columns.tolist())

print("\nFIRST FIVE RECORDS:")
print(df.to_string())

print("\nDATA TYPES:")
print(df.dtypes)