
# ✈️ Airline Flight Information System

An intelligent, web-based Airline Flight Information System built using **Python, Django, Machine Learning, and SQLite**. The platform simplifies flight information management, booking operations, personalized recommendations, and flight delay prediction through an integrated web application.

## 📌 Project Overview

The Airline Flight Information System provides a centralized platform where users can search for flights, explore flight details, book tickets, manage reservations, and receive intelligent travel assistance.

The system integrates Machine Learning to predict possible flight delays and provide insights into prediction results. It also includes **AeroMate AI**, a rule-based travel assistant that helps users access relevant information through a chat interface.

## ✨ Key Features

### 👤 User Management
- User registration and login
- Secure authentication
- User-specific booking history
- Profile-based access

### ✈️ Flight Management
- Search available flights
- View flight details
- Explore Economy, Business, and First Class fares
- Manage flight information through Django Admin

### 🎫 Booking Management
- Book flight tickets
- Track booking history
- Cancel bookings
- Automatically update seat availability

### 🤖 Machine Learning
- Flight delay prediction
- Trained ML models for prediction
- Advanced prediction using the optimized model
- Prediction history

### 📊 Explainable AI
- Global model explanation dashboard
- Individual prediction explanations
- Feature importance visualization
- Insights into factors influencing predictions

### 🎯 Flight Recommendations
- Personalized flight recommendations
- Alternative flight suggestions
- Preference-based recommendations

### 🔔 Notifications
- User notifications
- Booking-related updates

### 💰 Travel Budget Planner
- Manage travel budgets
- Edit and delete budget entries
- Budget analytics and charts

### 💬 AeroMate AI
- Floating chatbot interface
- Rule-based travel assistance
- Access to relevant flight and booking information
- Answers to common travel-related questions

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Machine Learning | Scikit-learn, Pandas, NumPy |
| Model Storage | Joblib, Git LFS |
| Explainable AI | SHAP |
| Version Control | Git, GitHub |

## 📂 Project Structure

```text
Airline-Flight-Information-System/
│
├── accounts/             # User authentication
├── config/               # Django project configuration
├── flights/              # Flight search and booking
├── ml_model/             # Machine Learning models
├── notifications/        # Notification management
├── recommendations/      # Flight recommendations
├── travel_assistant/     # AeroMate AI chatbot
│
├── manage.py
├── requirements.txt
├── .gitignore
├── .gitattributes
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/satyavathiakula18-tech/Airline-Flight-Information-System.git
```

### 2. Open the project folder

```bash
cd Airline-Flight-Information-System
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Download Git LFS files

Install Git LFS if it is not already installed, then run:

```bash
git lfs install
git lfs pull
```

### 7. Apply database migrations

```bash
python manage.py migrate
```

### 8. Create an administrator account

```bash
python manage.py createsuperuser
```

### 9. Start the development server

```bash
python manage.py runserver
```

Open the application at:

http://127.0.0.1:8000/

## 🧠 Machine Learning Models

The project includes trained flight delay prediction models stored using Git Large File Storage (Git LFS).

Model files:

- `flight_delay_model.joblib`
- `flight_delay_model_best.joblib`
- `flight_delay_model_optimized.joblib`

The models are used by the application to generate flight delay predictions.

## 💬 AeroMate AI

AeroMate AI is an integrated, rule-based chatbot designed to provide travel assistance within the application. It helps users access relevant flight and booking information without needing to navigate multiple pages.

## 🔐 Security Notes

- Keep secret keys and database credentials outside version control.
- Never upload `.env` files or private credentials.
- Configure production security settings before deployment.
- Use HTTPS and secure cookies in production.

## 🚀 Future Enhancements

- Live airline and flight-status API integration
- Online payment gateway
- Email and SMS notifications
- Cloud deployment
- More advanced conversational AI integration
- Mobile application support

## 👨‍💻 Project Information

**Project Name:** Airline Flight Information System

**Project Type:** Web Application with Machine Learning Integration

**Framework:** Django

**Repository:** [GitHub Repository](https://github.com/satyavathiakula18-tech/Airline-Flight-Information-System)

---

*Developed as an academic project to combine web development, machine learning, and intelligent travel assistance in one platform.*
