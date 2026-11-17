
from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_flights, name='search_flights'),

    path(
        'flight/<int:flight_id>/',
        views.flight_details,
        name='flight_details'
    ),

    path(
        'flight/<int:flight_id>/book/',
        views.book_flight,
        name='book_flight'
    ),

    path('my-bookings/', views.my_bookings, name='my_bookings'),

    path(
        'cancel-booking/<int:booking_id>/',
        views.cancel_booking,
        name='cancel_booking'
    ),

    path(
        'alternative-flights/<int:flight_id>/',
        views.alternative_flights,
        name='alternative_flights'
    ),

    path(
        'my-preferences/',
        views.my_preferences,
        name='my_preferences'
    ),

    path(
        'recommendations/',
        views.flight_recommendations,
        name='flight_recommendations'
    ),

    path(
        'predict-delay/',
        views.predict_flight_delay,
        name='predict_flight_delay'
    ),

    path(
        'predict-delay-advanced/',
        views.predict_flight_delay_advanced,
        name='predict_flight_delay_advanced'
    ),

    path(
        'travel-budget/',
        views.travel_budget_planner,
        name='travel_budget_planner'
    ),

    path(
        'travel-budget/edit/<int:budget_id>/',
        views.edit_travel_budget,
        name='edit_travel_budget'
    ),

    path(
        'travel-budget/delete/<int:budget_id>/',
        views.delete_travel_budget,
        name='delete_travel_budget'
    ),

    path(
        'explainable-ai/',
        views.explainable_ai,
        name='explainable_ai'
    ),

    # Prediction History
    path(
        'prediction-history/',
        views.prediction_history,
        name='prediction_history'
    ),
]
