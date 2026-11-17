
import re

from django.db.models import Min
from django.utils import timezone

from flights.models import (
    Airport,
    Flight,
    Booking,
    FlightPrediction,
    TravelBudget,
)


def find_airports(message):
    """
    Identify airport codes, cities or airport names
    mentioned in the user's question.
    """
    text = message.lower()
    matches = []

    airports = Airport.objects.all().order_by("code")

    for airport in airports:
        code_match = re.search(
            r"(?<![a-z0-9])"
            + re.escape(airport.code.lower())
            + r"(?![a-z0-9])",
            text,
        )

        city_match = airport.city.lower() in text
        name_match = airport.name.lower() in text

        if code_match or city_match or name_match:
            if airport not in matches:
                matches.append(airport)

    return matches[:2]


def search_flights(message):
    airports = find_airports(message)

    if len(airports) < 2:
        return (
            "Please mention both your departure and destination "
            "airport or city. For example: Show flights from DEL to BOM."
        )

    source = airports[0]
    destination = airports[1]

    flights = (
        Flight.objects.filter(
            source=source,
            destination=destination,
            departure_time__gte=timezone.now(),
            available_seats__gt=0,
        )
        .annotate(
            cheapest_price=Min("prices__price")
        )
        .select_related(
            "airline",
            "source",
            "destination",
        )
        .order_by("departure_time")[:5]
    )

    if not flights:
        return (
            f"I couldn't find available future flights from "
            f"{source.city} to {destination.city}."
        )

    response = (
        f"Here are available flights from {source.city} "
        f"to {destination.city}:\n\n"
    )

    for flight in flights:
        price = (
            f"₹{flight.cheapest_price}"
            if flight.cheapest_price is not None
            else "Fare not available"
        )

        response += (
            f"✈️ {flight.flight_number}\n"
            f"Airline: {flight.airline.name}\n"
            f"Departure: {flight.departure_time}\n"
            f"Arrival: {flight.arrival_time}\n"
            f"Available seats: {flight.available_seats}\n"
            f"Starting fare: {price}\n\n"
        )

    response += (
        "Please open the flight details page to compare "
        "travel classes and complete your booking."
    )

    return response


def get_booking_information(user):
    if not user.is_authenticated:
        return "Please log in to view your bookings."

    bookings = (
        Booking.objects.filter(user=user)
        .select_related(
            "flight",
            "flight__airline",
            "flight__source",
            "flight__destination",
        )
        .order_by("-booking_date")[:5]
    )

    if not bookings:
        return "You don't have any bookings yet."

    response = "Here are your recent bookings:\n\n"

    for booking in bookings:
        response += (
            f"Booking ID: {booking.id}\n"
            f"Flight: {booking.flight.flight_number}\n"
            f"Route: {booking.flight.source.code} to "
            f"{booking.flight.destination.code}\n"
            f"Class: {booking.travel_class}\n"
            f"Passengers: {booking.passengers}\n"
            f"Amount: ₹{booking.total_price}\n"
            f"Status: {booking.booking_status}\n\n"
        )

    return response


def get_prediction_information(user):
    if not user.is_authenticated:
        return "Please log in to view your flight prediction history."

    predictions = FlightPrediction.objects.filter(
        user=user
    ).order_by("-created_at")[:5]

    if not predictions:
        return "You don't have any saved flight predictions yet."

    response = "Your recent flight delay predictions:\n\n"

    for item in predictions:
        response += (
            f"Route: {item.origin} to {item.destination}\n"
            f"Prediction: {item.prediction}\n"
            f"Delay probability: {item.probability * 100:.2f}%\n"
            f"Risk level: {item.risk_level or 'Not specified'}\n\n"
        )

    response += (
        "Remember: these are model estimates, not guaranteed "
        "real-world flight status updates."
    )

    return response


def get_budget_information(user):
    if not user.is_authenticated:
        return "Please log in to view your travel budgets."

    budgets = TravelBudget.objects.filter(
        user=user
    ).order_by("-created_at")[:5]

    if not budgets:
        return "You haven't created a travel budget yet."

    response = "Your recent travel budgets:\n\n"

    for budget in budgets:
        response += (
            f"Trip: {budget.trip_name}\n"
            f"Destination: {budget.destination}\n"
            f"Total budget: ₹{budget.total_budget}\n"
            f"Expenses: ₹{budget.total_expenses}\n"
            f"Remaining: ₹{budget.remaining_budget}\n\n"
        )

    return response


def get_response(message, user):
    text = message.lower().strip()

    if not text:
        return "Please type a question."

    if any(word in text for word in [
        "hello", "hi", "hey", "good morning", "good evening"
    ]):
        return (
            "Hello! 👋 Welcome to AeroMate AI.\n\n"
            "I'm your airline travel assistant. I can help you "
            "search flights, compare fares, understand bookings, "
            "review delay predictions and manage travel budgets.\n\n"
            "How can I help you today?"
        )

    if any(word in text for word in [
        "search flight", "find flight", "show flight",
        "available flight", "flights from", "flight from",
        "fare from", "price from",
    ]):
        return search_flights(message)

    if any(word in text for word in [
        "my booking", "my bookings", "booking history",
        "booking status", "reservation",
    ]):
        return get_booking_information(user)

    if any(word in text for word in [
        "prediction history", "delay history",
        "my predictions", "previous prediction",
    ]):
        return get_prediction_information(user)

    if any(word in text for word in [
        "travel budget", "my budget", "trip expenses",
        "remaining budget",
    ]):
        return get_budget_information(user)

    if any(word in text for word in [
        "delay prediction", "flight delay", "delayed flight",
        "on time prediction",
    ]):
        return (
            "Our system uses a trained Machine Learning model "
            "to estimate the likelihood of a flight delay.\n\n"
            "You can open the Advanced Flight Delay Prediction "
            "page and enter the flight details to receive a "
            "prediction and explanation.\n\n"
            "The prediction is an estimate, not live flight status."
        )

    if any(word in text for word in [
        "cancel", "cancellation",
    ]):
        return (
            "To cancel a booking, log in and open My Bookings. "
            "Select your confirmed booking and use the cancellation "
            "option if available. Check the booking status afterward."
        )

    if any(word in text for word in [
        "baggage", "luggage",
    ]):
        return (
            "Baggage allowances depend on the airline, route and "
            "ticket class. Please check the airline's official "
            "baggage policy before travelling."
        )

    if any(word in text for word in [
        "economy", "business class", "first class",
        "compare fare", "ticket class",
    ]):
        return (
            "Your airline system supports Economy, Business and "
            "First Class fares. Open a flight's details page to "
            "compare the available prices."
        )

    if any(word in text for word in [
        "thank you", "thanks",
    ]):
        return "You're welcome! Happy travels. ✈️"

    return (
        "I'm AeroMate AI, your airline assistant.\n\n"
        "I can currently help with:\n"
        "• Flight search\n"
        "• Flight fares and travel classes\n"
        "• Booking information\n"
        "• Flight delay predictions\n"
        "• Prediction history\n"
        "• Travel budgets\n"
        "• Cancellation guidance\n"
        "• Baggage information\n\n"
        "Try asking: 'Show flights from DEL to BOM'."
    )
