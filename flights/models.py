
from django.db import models
from django.conf import settings

class Airline(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    country = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"



class Airport(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=5, unique=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.code})"



class Flight(models.Model):
    flight_number = models.CharField(max_length=20, unique=True)

    airline = models.ForeignKey(
        Airline,
        on_delete=models.CASCADE,
        related_name="flights"
    )

    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="departing_flights"
    )

    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="arriving_flights"
    )

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
     
    total_seats = models.PositiveIntegerField(default=180)
    available_seats = models.PositiveIntegerField(default=180)

    def __str__(self):
        return f"{self.flight_number} - {self.source.code} to {self.destination.code}"



class FlightPrice(models.Model):
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='prices'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    travel_class = models.CharField(
        max_length=20,
        choices=[
            ('Economy', 'Economy'),
            ('Business', 'Business'),
            ('First Class', 'First Class'),
        ],
        default='Economy'
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.flight.flight_number} - ₹{self.price}"



class Booking(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    travel_class = models.CharField(
        max_length=20,
        choices=[
            ('Economy', 'Economy'),
            ('Business', 'Business'),
            ('First Class', 'First Class'),
        ]
    )

    passengers = models.PositiveIntegerField(default=1)

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    booking_date = models.DateTimeField(auto_now_add=True)

    booking_status = models.CharField(
        max_length=20,
        default='Confirmed'
    )

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username}"



class UserPreference(models.Model):

    TRAVEL_CLASS_CHOICES = [
        ('Economy', 'Economy'),
        ('Business', 'Business'),
        ('First Class', 'First Class'),
    ]

    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='flight_preference'
    )

    preferred_airline = models.ForeignKey(
        Airline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    preferred_source = models.ForeignKey(
        Airport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_departures'
    )

    preferred_destination = models.ForeignKey(
        Airport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_destinations'
    )

    preferred_class = models.CharField(
        max_length=20,
        choices=TRAVEL_CLASS_CHOICES,
        default='Economy'
    )

    max_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Preferences of {self.user.username}"



class TravelBudget(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='travel_budgets'
    )

    trip_name = models.CharField(max_length=150)

    destination = models.CharField(max_length=150)

    travel_date = models.DateField()

    total_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    flight_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    accommodation_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    food_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    transport_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    other_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_expenses(self):
        return (
            self.flight_cost
            + self.accommodation_cost
            + self.food_cost
            + self.transport_cost
            + self.other_cost
        )

    @property
    def remaining_budget(self):
        return self.total_budget - self.total_expenses

    def __str__(self):
        return f"{self.trip_name} - {self.user.username}"


class FlightPrediction(models.Model):

    PREDICTION_CHOICES = [
        ("Likely Delayed", "Likely Delayed"),
        ("Likely On Time", "Likely On Time"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flight_predictions"
    )

    # Flight information
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    day = models.PositiveIntegerField()
    weekday = models.PositiveIntegerField()

    origin = models.CharField(max_length=10)
    destination = models.CharField(max_length=10)

    departure_time = models.PositiveIntegerField()
    distance = models.FloatField()

    # Prediction results
    prediction = models.CharField(
        max_length=30,
        choices=PREDICTION_CHOICES
    )

    probability = models.FloatField()

    threshold = models.FloatField(default=0.36)

    risk_level = models.CharField(
        max_length=20,
        blank=True
    )

    decision_score = models.FloatField(
        null=True,
        blank=True
    )

    # Store individual XAI contributions
    explanations = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Flight Prediction"
        verbose_name_plural = "Flight Predictions"

    def __str__(self):
        return (
            f"{self.user.username}: "
            f"{self.origin} to {self.destination} - "
            f"{self.prediction}"
        )
