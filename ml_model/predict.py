
import os
import joblib
import pandas as pd


# Locate saved model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "flight_delay_model.joblib"
)


# Load trained model
print("Loading Flight Delay Prediction Model...")

model = joblib.load(MODEL_PATH)


# Get flight details
print("\n===== FLIGHT DELAY PREDICTION =====")

year = int(input("Enter Year: "))
month = int(input("Enter Month (1-12): "))
day = int(input("Enter Day of Month: "))
day_of_week = int(input("Enter Day of Week (1-7): "))

airline = input("Enter Airline Code (Example: AA): ").strip().upper()
origin = input("Enter Origin Airport (Example: DCA): ").strip().upper()
destination = input("Enter Destination Airport (Example: TUL): ").strip().upper()

departure_time = int(input("Enter Scheduled Departure Time (HHMM): "))
distance = float(input("Enter Flight Distance (miles): "))


# Prepare input data
flight_data = pd.DataFrame([{
    "Year": year,
    "Month": month,
    "DayofMonth": day,
    "DayOfWeek": day_of_week,
    "Marketing_Airline_Network": airline,
    "Origin": origin,
    "Dest": destination,
    "CRSDepTime": departure_time,
    "Distance": distance
}])


# Make prediction
prediction = model.predict(flight_data)[0]

probabilities = model.predict_proba(flight_data)[0]

delay_probability = probabilities[list(model.classes_).index(1)]


# Display result
print("\n========== PREDICTION RESULT ==========")

if prediction == 1:
    print("FLIGHT STATUS: LIKELY DELAYED")
else:
    print("FLIGHT STATUS: LIKELY ON TIME")

print(
    f"Estimated delay risk: {delay_probability * 100:.2f}%"
)

print("=======================================")
