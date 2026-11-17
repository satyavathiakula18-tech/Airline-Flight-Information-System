from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Min
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from flights.xai_utils import explain_flight_prediction
from flights.models import FlightPrediction

import os
import joblib
import pandas as pd
import traceback as tb

from .models import (
    Flight,
    Airport,
    Booking,
    FlightPrice,
    UserPreference,
    TravelBudget,
)
from .forms import UserPreferenceForm, TravelBudgetForm
from notifications.models import Notification

import csv
from pathlib import Path
from django.shortcuts import render
# ==========================================
# 1. FLIGHT SEARCH
# ==========================================

def search_flights(request):
    flights = Flight.objects.all().order_by("departure_time")
    airports = Airport.objects.all().order_by("city")

    source = request.GET.get("source", "").strip()
    destination = request.GET.get("destination", "").strip()
    travel_date = request.GET.get("travel_date", "").strip()

    if source:
        flights = flights.filter(source__code=source)

    if destination:
        flights = flights.filter(destination__code=destination)

    if travel_date:
        flights = flights.filter(departure_time__date=travel_date)

    flights = flights.annotate(
        cheapest_price=Min("prices__price")
    ).order_by("cheapest_price", "departure_time")

    cheapest_flight = (
        flights.exclude(cheapest_price__isnull=True)
        .order_by("cheapest_price")
        .first()
    )

    context = {
        "flights": flights,
        "airports": airports,
        "source": source,
        "destination": destination,
        "travel_date": travel_date,
        "cheapest_flight": cheapest_flight,
    }
    return render(request, "flights/search.html", context)


# ==========================================
# 2. FLIGHT DETAILS
# ==========================================

def flight_details(request, flight_id):
    flight = get_object_or_404(
        Flight.objects.prefetch_related("prices"),
        id=flight_id,
    )
    return render(request, "flights/flight_details.html", {"flight": flight})


# ==========================================
# 3. FLIGHT BOOKING
# ==========================================

@login_required
def book_flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)

    if request.method == "GET":
        return render(
            request,
            "flights/booking.html",
            {"flight": flight},
        )

    travel_class = request.POST.get("travel_class")
    passengers_text = request.POST.get("passengers")

    try:
        passengers = int(passengers_text)
    except (TypeError, ValueError):
        messages.error(request, "Enter a valid passenger count.")
        return redirect("book_flight", flight_id=flight.id)

    if passengers < 1:
        messages.error(request, "At least one passenger is required.")
        return redirect("book_flight", flight_id=flight.id)

    with transaction.atomic():
        locked_flight = Flight.objects.select_for_update().get(id=flight_id)
        price = FlightPrice.objects.filter(
            flight=locked_flight,
            travel_class=travel_class,
        ).first()

        if price is None:
            messages.error(request, "Selected travel class is unavailable.")
            return redirect("book_flight", flight_id=flight.id)

        if passengers > locked_flight.available_seats:
            messages.error(request, "Not enough seats available.")
            return redirect("book_flight", flight_id=flight.id)

        total_price = price.price * passengers
        Booking.objects.create(
            user=request.user,
            flight=locked_flight,
            travel_class=travel_class,
            passengers=passengers,
            total_price=total_price,
            booking_status="Confirmed",
        )

        Notification.objects.create(
            user=request.user,
            title="Booking Confirmed ✈️",
            message=(
                f"Your booking for flight "
                f"{locked_flight.flight_number} has been confirmed."
            ),
            notification_type="Booking",
        )

        locked_flight.available_seats -= passengers
        locked_flight.save(update_fields=["available_seats"])

    messages.success(request, "Your flight has been booked successfully!")
    return redirect("flight_details", flight_id=flight.id)


# ==========================================
# 4. MY BOOKINGS
# ==========================================

@login_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related(
            "flight",
            "flight__airline",
            "flight__source",
            "flight__destination",
        )
        .order_by("-booking_date")
    )
    return render(
        request,
        "flights/my_bookings.html",
        {"bookings": bookings},
    )


# ==========================================
# 5. CANCEL BOOKING
# ==========================================

@login_required
def cancel_booking(request, booking_id):
    if request.method != "POST":
        return redirect("my_bookings")

    with transaction.atomic():
        booking = get_object_or_404(
            Booking.objects.select_for_update(),
            id=booking_id,
            user=request.user,
        )

        if booking.booking_status == "Confirmed":
            flight = Flight.objects.select_for_update().get(
                id=booking.flight_id
            )
            flight.available_seats = min(
                flight.available_seats + booking.passengers,
                flight.total_seats,
            )
            flight.save(update_fields=["available_seats"])

            booking.booking_status = "Cancelled"
            booking.save(update_fields=["booking_status"])

            Notification.objects.create(
                user=request.user,
                title="Booking Cancelled",
                message=(
                    f"Your booking for flight "
                    f"{booking.flight.flight_number} has been cancelled."
                ),
                notification_type="Cancellation",
            )
            messages.success(request, "Booking cancelled successfully!")
        else:
            messages.error(request, "This booking has already been cancelled.")

    return redirect("my_bookings")


# ==========================================
# 6. ORIGINAL FLIGHT DELAY PREDICTION
# Keeps the original nine-feature model
# ==========================================

def predict_flight_delay(request):
    prediction = None
    probability = None
    error = None

    if request.method == "POST":
        try:
            model_path = os.path.join(
                settings.BASE_DIR,
                "ml_model",
                "flight_delay_model.joblib",
            )
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    "Original model file was not found: "
                    "ml_model/flight_delay_model.joblib"
                )

            model = joblib.load(model_path)
            origin = (request.POST.get("origin") or "").strip().upper()
            destination = (request.POST.get("destination") or "").strip().upper()
            airline = (request.POST.get("airline") or "").strip()

            if not origin or not destination or not airline:
                raise ValueError(
                    "Please enter the airline, origin, and destination."
                )

            flight_data = pd.DataFrame([{
                "Year": int(request.POST.get("year")),
                "Month": int(request.POST.get("month")),
                "DayofMonth": int(request.POST.get("day")),
                "DayOfWeek": int(request.POST.get("weekday")),
                "Marketing_Airline_Network": airline,
                "Origin": origin,
                "Dest": destination,
                "CRSDepTime": int(request.POST.get("departure_time")),
                "Distance": float(request.POST.get("distance")),
            }])

            result = model.predict(flight_data)[0]
            probabilities = model.predict_proba(flight_data)[0]
            delayed_index = list(model.classes_).index(1)
            probability = round(
                float(probabilities[delayed_index]) * 100,
                2,
            )
            prediction = "Likely Delayed" if result == 1 else "Likely On Time"

        except (TypeError, ValueError) as exc:
            error = f"Invalid input: {exc}"
        except Exception as exc:
            error = f"Prediction error: {exc}"

    return render(
        request,
        "flights/predict_delay.html",
        {
            "prediction": prediction,
            "probability": probability,
            "error": error,
        },
    )


# ==========================================
# 7. ADVANCED FLIGHT DELAY PREDICTION
# Eight-feature Logistic Regression model
# ==========================================



def predict_flight_delay_advanced(request):
    prediction = None
    probability = None
    risk_level = None
    risk_color = None
    error = None
    threshold = 0.36

    # Individual XAI variables
    explanation_items = []
    positive_contributions = []
    negative_contributions = []
    decision_score = None
    explanation_error = None

    if request.method == "POST":
        try:
            model_path = os.path.join(
                settings.BASE_DIR,
                "ml_model",
                "flight_delay_model_best.joblib",
            )

            threshold_path = os.path.join(
                settings.BASE_DIR,
                "ml_model",
                "best_model_threshold.txt",
            )

            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    "Advanced model file was not found."
                )

            if not os.path.exists(threshold_path):
                raise FileNotFoundError(
                    "Threshold file was not found."
                )

            # Load model
            model = joblib.load(model_path)

            with open(
                threshold_path, "r", encoding="utf-8"
            ) as file:
                threshold = float(file.read().strip())

            if not 0 <= threshold <= 1:
                raise ValueError(
                    "Model threshold must be between 0 and 1."
                )

            # Get form inputs
            origin = (
                request.POST.get("origin") or ""
            ).strip().upper()

            destination = (
                request.POST.get("destination") or ""
            ).strip().upper()

            if not origin or not destination:
                raise ValueError(
                    "Please enter both origin and destination."
                )

            year = int(request.POST.get("year"))
            month = int(request.POST.get("month"))
            day = int(request.POST.get("day"))
            weekday = int(request.POST.get("weekday"))
            departure_time = int(
                request.POST.get("departure_time")
            )
            distance = float(request.POST.get("distance"))

            # Validate inputs
            if month < 1 or month > 12:
                raise ValueError(
                    "Month must be between 1 and 12."
                )

            if day < 1 or day > 31:
                raise ValueError(
                    "Day must be between 1 and 31."
                )

            if weekday < 1 or weekday > 7:
                raise ValueError(
                    "Day of week must be between 1 and 7."
                )

            if departure_time < 0 or departure_time > 2359:
                raise ValueError(
                    "Departure time must be in HHMM format."
                )

            if distance <= 0:
                raise ValueError(
                    "Distance must be greater than zero."
                )

            # Prepare the eight model features
            flight_data = pd.DataFrame([{
                "Year": year,
                "Month": month,
                "DayofMonth": day,
                "DayOfWeek": weekday,
                "Origin": origin,
                "Dest": destination,
                "CRSDepTime": departure_time,
                "Distance": distance,
            }])

            # Generate prediction
            probabilities = model.predict_proba(
                flight_data
            )[0]

            delayed_index = list(
                model.classes_
            ).index(1)

            delay_probability = float(
                probabilities[delayed_index]
            )

            probability = round(
                delay_probability * 100, 2
            )

            is_delayed = (
                delay_probability >= threshold
            )

            prediction = (
                "Likely Delayed"
                if is_delayed
                else "Likely On Time"
            )

            # Display-only risk categories
            if probability < 20:
                risk_level = "Low"
                risk_color = "success"

            elif probability < 40:
                risk_level = "Medium"
                risk_color = "warning"

            else:
                risk_level = "High"
                risk_color = "danger"

            # Generate individual XAI explanation
            try:
                explanation = explain_flight_prediction(
                    model,
                    flight_data.iloc[0].to_dict()
                )

                explanation_items = explanation[
                    "explanations"
                ]

                decision_score = round(
                    explanation["decision_score"], 6
                )

                # Find strongest contribution
                max_contribution = max(
                    (
                        item["magnitude"]
                        for item in explanation_items
                    ),
                    default=0
                )

                # Calculate chart bar widths
                for item in explanation_items:
                    if max_contribution > 0:
                        item["bar_width"] = round(
                            (
                                item["magnitude"]
                                / max_contribution
                            ) * 100,
                            2
                        )
                    else:
                        item["bar_width"] = 0

                # Separate positive and negative factors
                positive_contributions = [
                    item
                    for item in explanation_items
                    if item["contribution"] > 0
                ]

                negative_contributions = [
                    item
                    for item in explanation_items
                    if item["contribution"] < 0
                ]

            except Exception as xai_exc:
                explanation_error = (
                    "Prediction was successful, but the "
                    "individual explanation could not be generated."
                )

                print("XAI ERROR:", repr(xai_exc))

            # Save successful predictions for logged-in users.
            # Anonymous visitors can still use the prediction feature.
            if request.user.is_authenticated:
                try:
                    saved_explanations = []

                    for item in explanation_items:
                        saved_explanations.append({
                            "feature": str(item.get("feature", "")),
                            "contribution": float(item.get("contribution", 0)),
                            "direction": str(item.get("direction", "")),
                            "magnitude": float(item.get("magnitude", 0)),
                            "bar_width": float(item.get("bar_width", 0)),
                        })

                    FlightPrediction.objects.create(
                        user=request.user,
                        year=year,
                        month=month,
                        day=day,
                        weekday=weekday,
                        origin=origin,
                        destination=destination,
                        departure_time=departure_time,
                        distance=distance,
                        prediction=prediction,
                        probability=delay_probability,
                        threshold=threshold,
                        risk_level=risk_level or "",
                        decision_score=decision_score,
                        explanations=saved_explanations,
                    )

                except Exception as save_exc:
                    # A history-saving problem should not prevent the
                    # user from seeing an otherwise successful prediction.
                    print("PREDICTION HISTORY SAVE ERROR:", repr(save_exc))
                    messages.warning(
                        request,
                        "Your prediction was completed, but it could not be "
                        "saved to your prediction history."
                    )

        except Exception as exc:
            print("\n========== FLIGHT PREDICTION ERROR ==========")
            print("Error type:", type(exc).__name__)
            print("Error details:", repr(exc))
            print("=============================================\n")

            error = f"Prediction failed: {exc}"

    # Send results to HTML
    context = {
        "prediction": prediction,
        "probability": probability,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "error": error,
        "model_name": "Advanced Logistic Regression",
        "threshold": round(threshold * 100, 2),

        # XAI results
        "explanation_items": explanation_items,
        "positive_contributions": positive_contributions,
        "negative_contributions": negative_contributions,
        "decision_score": decision_score,
        "explanation_error": explanation_error,
    }

    return render(
        request,
        "flights/predict_delay.html",
        context
    )


# ==========================================
# 8. ALTERNATIVE FLIGHTS
# ==========================================

def alternative_flights(request, flight_id):
    selected_flight = get_object_or_404(
        Flight.objects.select_related("airline", "source", "destination"),
        id=flight_id,
    )

    selected_price = selected_flight.prices.aggregate(
        min_price=Min("price")
    )["min_price"]

    alternatives = list(
        Flight.objects.filter(
            source=selected_flight.source,
            destination=selected_flight.destination,
            departure_time__date=selected_flight.departure_time.date(),
            available_seats__gt=0,
        )
        .exclude(id=selected_flight.id)
        .annotate(cheapest_price=Min("prices__price"))
        .select_related("airline", "source", "destination")
        .order_by("cheapest_price")
    )

    cheapest_alternative = alternatives[0] if alternatives else None
    savings = None
    if (
        selected_price is not None
        and cheapest_alternative is not None
        and cheapest_alternative.cheapest_price is not None
        and cheapest_alternative.cheapest_price < selected_price
    ):
        savings = selected_price - cheapest_alternative.cheapest_price

    return render(
        request,
        "flights/alternative_flights.html",
        {
            "selected_flight": selected_flight,
            "selected_price": selected_price,
            "alternatives": alternatives,
            "cheapest_alternative": cheapest_alternative,
            "savings": savings,
        },
    )


# ==========================================
# 9. USER FLIGHT PREFERENCES
# ==========================================

@login_required
def my_preferences(request):
    preference, created = UserPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = UserPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            saved_preference = form.save(commit=False)
            saved_preference.user = request.user
            saved_preference.save()
            messages.success(
                request,
                "Your flight preferences have been saved!",
            )
            return redirect("my_preferences")
    else:
        form = UserPreferenceForm(instance=preference)

    return render(
        request,
        "flights/my_preferences.html",
        {"form": form},
    )


# ==========================================
# 10. PERSONALIZED FLIGHT RECOMMENDATIONS
# ==========================================

@login_required
def flight_recommendations(request):
    preference = UserPreference.objects.filter(user=request.user).first()
    if not preference:
        return redirect("my_preferences")

    previous_bookings = Booking.objects.filter(
        user=request.user,
        booking_status="Confirmed",
    ).select_related("flight", "flight__airline")

    booked_airlines = {
        booking.flight.airline_id for booking in previous_bookings
    }
    booked_routes = {
        (booking.flight.source_id, booking.flight.destination_id)
        for booking in previous_bookings
    }

    flights = (
        Flight.objects.filter(
            departure_time__gte=timezone.now(),
            available_seats__gt=0,
            prices__travel_class=preference.preferred_class,
        )
        .select_related("airline", "source", "destination")
        .distinct()
    )

    recommendations = []
    for flight in flights:
        price = flight.prices.filter(
            travel_class=preference.preferred_class
        ).order_by("price").first()
        if not price:
            continue

        score = 0
        reasons = []

        if (
            preference.preferred_airline_id
            and flight.airline_id == preference.preferred_airline_id
        ):
            score += 30
            reasons.append("Your preferred airline")

        if (
            preference.preferred_source_id
            and flight.source_id == preference.preferred_source_id
        ):
            score += 25
            reasons.append("Your preferred departure airport")

        if (
            preference.preferred_destination_id
            and flight.destination_id == preference.preferred_destination_id
        ):
            score += 25
            reasons.append("Your preferred destination")

        if (
            preference.max_budget is not None
            and price.price <= preference.max_budget
        ):
            score += 20
            reasons.append("Within your budget")

        if flight.airline_id in booked_airlines:
            score += 10
            reasons.append("Airline you booked before")

        if (flight.source_id, flight.destination_id) in booked_routes:
            score += 10
            reasons.append("Route you travelled before")

        flight.recommendation_price = price.price
        flight.recommendation_score = score
        flight.recommendation_reasons = reasons
        recommendations.append(flight)

    recommendations.sort(
        key=lambda flight: (
            -flight.recommendation_score,
            flight.recommendation_price,
        )
    )
    recommendations = recommendations[:10]

    return render(
        request,
        "flights/recommendations.html",
        {
            "preference": preference,
            "recommendations": recommendations,
        },
    )


# ==========================================
# 11. TRAVEL BUDGET PLANNER
# ==========================================

@login_required
def travel_budget_planner(request):
    if request.method == "POST":
        form = TravelBudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(
                request,
                "Your travel budget has been created successfully!",
            )
            return redirect("travel_budget_planner")
    else:
        form = TravelBudgetForm()

    budgets = TravelBudget.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "flights/travel_budget.html",
        {
            "form": form,
            "budgets": budgets,
        },
    )


# ==========================================
# 12. EDIT TRAVEL BUDGET
# ==========================================

@login_required
def edit_travel_budget(request, budget_id):
    budget = get_object_or_404(
        TravelBudget,
        id=budget_id,
        user=request.user,
    )

    if request.method == "POST":
        form = TravelBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your travel budget was updated successfully!",
            )
            return redirect("travel_budget_planner")
    else:
        form = TravelBudgetForm(instance=budget)

    return render(
        request,
        "flights/edit_travel_budget.html",
        {
            "form": form,
            "budget": budget,
        },
    )


# ==========================================
# 13. DELETE TRAVEL BUDGET
# ==========================================

@login_required
@require_POST
def delete_travel_budget(request, budget_id):
    budget = get_object_or_404(
        TravelBudget,
        id=budget_id,
        user=request.user,
    )
    budget.delete()
    messages.success(request, "Your travel budget was deleted successfully!")
    return redirect("travel_budget_planner")






def explainable_ai(request):
    csv_path = (
        Path(settings.BASE_DIR)
        / "ml_model"
        / "permutation_feature_importance.csv"
    )

    feature_names = {
        "CRSDepTime": "Scheduled Departure Time",
        "Dest": "Destination Airport",
        "Origin": "Origin Airport",
        "DayOfWeek": "Day of Week",
        "DayofMonth": "Day of Month",
        "Distance": "Flight Distance",
        "Year": "Year",
        "Month": "Month",
    }

    features = []
    error = None

    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                importance = float(row["Importance Mean"])
                std = float(row["Importance Std"])

                features.append({
                    "name": feature_names.get(
                        row["Feature"], row["Feature"]
                    ),
                    "importance": importance,
                    "std": std,
                    "width": 0,
                })

        if not features:
            error = "No feature importance data was found."
        else:
            max_importance = max(
                item["importance"] for item in features
            )

            for item in features:
                if max_importance > 0:
                    item["width"] = (
                        item["importance"] / max_importance
                    ) * 100

    except FileNotFoundError:
        error = "Feature importance CSV file was not found."
    except (ValueError, KeyError, OSError) as e:
        error = f"Could not read feature importance data: {e}"

    context = {
        "features": features,
        "error": error,
    }

    return render(
        request,
        "flights/explainable_ai.html",
        context
    )



# ==========================================
# 14. MY FLIGHT PREDICTION HISTORY
# ==========================================

@login_required
def prediction_history(request):
    predictions = FlightPrediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "flights/prediction_history.html",
        {
            "predictions": predictions,
        }
    )
