# Eco Cleanse

**Eco Cleanse** is a Personal Carbon Footprint & AQI Tracker built with **Python, Flask, Streamlit**. It allows users to calculate their yearly carbon emissions, track air quality in multiple cities, and compare with others via a leaderboard.

---

## Features
- **Carbon Footprint Calculator**
  - Tracks emissions from **transportation, electricity, diet, and cooking methods**.
  - Uses country-specific emission factors (India, US, UK) and cooking method adjustments.
  - Converts results into **tonnes of CO2 per year** for clear visualization.
- **Leaderboard**
  - Tracks top users’ carbon footprints for **friendly competition**.
  - Persistent storage using **SQLite** for both user authentication and leaderboard.
- **AQI Tracker**
  - Real-time air quality (AQI) tracking for **20+ cities worldwide** using OpenAQ API.
  - Categorizes AQI into standard levels: Good, Moderate, Unhealthy, etc.
  - Displays a **color-coded Plotly pie chart** for AQI categories.
- **User Authentication**
  - Sign up and login functionality with **hashed passwords** using SHA-256.
  - Allows personalized tracking and leaderboard contributions.
- **Interactive UI**
  - Built with **Streamlit** for clean, responsive interface.
  - Supports **wide layout** and intuitive controls for inputs.
- **Suggestions for Reducing Carbon Footprint**
  - Tailored tips for **transportation, electricity, diet, and cooking methods**.

---

