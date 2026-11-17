
from django import forms
from .models import UserPreference


class UserPreferenceForm(forms.ModelForm):

    class Meta:
        model = UserPreference

        fields = [
            'preferred_airline',
            'preferred_source',
            'preferred_destination',
            'preferred_class',
            'max_budget',
        ]

        widgets = {
            'preferred_airline': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'preferred_source': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'preferred_destination': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'preferred_class': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'max_budget': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter your maximum budget',
                    'min': '1',
                    'step': '0.01'
                }
            ),
        }

        labels = {
            'preferred_airline': 'Preferred Airline',
            'preferred_source': 'Departure Airport',
            'preferred_destination': 'Destination Airport',
            'preferred_class': 'Preferred Travel Class',
            'max_budget': 'Maximum Budget (₹)',
        }



from .models import TravelBudget


class TravelBudgetForm(forms.ModelForm):

    class Meta:
        model = TravelBudget

        fields = [
            'trip_name',
            'destination',
            'travel_date',
            'total_budget',
            'flight_cost',
            'accommodation_cost',
            'food_cost',
            'transport_cost',
            'other_cost',
        ]

        widgets = {
            'travel_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'total_budget': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'step': '0.01'}
            ),
            'flight_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'accommodation_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'food_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'transport_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
            'other_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}
            ),
        }

        labels = {
            'trip_name': 'Trip Name',
            'destination': 'Destination',
            'travel_date': 'Travel Date',
            'total_budget': 'Total Budget (₹)',
            'flight_cost': 'Flight Expenses (₹)',
            'accommodation_cost': 'Accommodation (₹)',
            'food_cost': 'Food Expenses (₹)',
            'transport_cost': 'Transport Expenses (₹)',
            'other_cost': 'Other Expenses (₹)',
        }
