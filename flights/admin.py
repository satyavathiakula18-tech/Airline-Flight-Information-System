

from django.contrib import admin
from .models import Airline, Airport, Flight, FlightPrice, Booking  
from .models import UserPreference
from .models import TravelBudget


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country')
    search_fields = ('name', 'code', 'country')


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'country')
    search_fields = ('name', 'code', 'city')


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        'flight_number',
        'airline',
        'source',
        'destination',
        'departure_time',
        'arrival_time',
        'total_seats',
    )

    search_fields = ('flight_number', 'airline__name')
    list_filter = ('airline', 'source', 'destination')


@admin.register(FlightPrice)
class FlightPriceAdmin(admin.ModelAdmin):
    list_display = ('flight', 'price', 'travel_class', 'updated_at')
    list_filter = ('travel_class',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'flight',
        'travel_class',
        'passengers',
        'total_price',
        'booking_status',
        'booking_date',
    )

    list_filter = ('booking_status', 'travel_class')
    search_fields = ('user__username', 'flight__flight_number')

    admin.site.register(UserPreference)

    admin.site.register(TravelBudget)