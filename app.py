import streamlit as st
import requests
import plotly.graph_objects as go
import sqlite3
import hashlib

# Example emission factors for different countries (in kg of CO2 per unit)
EMISSION_FACTORS = {
    "India": {
        "Transportation": 0.12,  # kg CO2 per km
        "Electricity": 0.9,      # kg CO2 per kWh
        "Diet": 0.45,            # kg CO2 per meal
        "Waste": 1.2             # kg CO2 per kg of waste
    },
    "US": {
        "Transportation": 0.4,   # kg CO2 per km
        "Electricity": 0.5,      # kg CO2 per kWh
        "Diet": 0.7,             # kg CO2 per meal
        "Waste": 0.8             # kg CO2 per kg of waste
    },
    "UK": {
        "Transportation": 0.3,   # kg CO2 per km
        "Electricity": 0.4,      # kg CO2 per kWh
        "Diet": 0.5,             # kg CO2 per meal
        "Waste": 1.0             # kg CO2 per kg of waste
    },
}

# Cooking method emission factors (additional CO2 emitted per meal)
COOKING_METHOD_EMISSIONS = {
    "Boiling": 0.05,  # kg CO2 per meal
    "Grilling": 0.15,  # kg CO2 per meal
    "Frying": 0.2,     # kg CO2 per meal
    "Baking": 0.1,     # kg CO2 per meal
    "Raw": 0.0         # kg CO2 per meal (no cooking)
}

# SQLite setup for leaderboard and user authentication
conn = sqlite3.connect('carbon_footprint.db')
cursor = conn.cursor()

# Create a table for leaderboard and user data
cursor.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        score REAL NOT NULL
    )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')
conn.commit()

# Function to add user data to the leaderboard
def add_user_to_leaderboard(username, score):
    cursor.execute('INSERT INTO leaderboard (username, score) VALUES (?, ?)', (username, score))
    conn.commit()

# Function to fetch the leaderboard from SQLite
def get_leaderboard():
    cursor.execute('SELECT username, score FROM leaderboard ORDER BY score LIMIT 5')
    return cursor.fetchall()

# Function to clear leaderboard data
def clear_leaderboard():
    cursor.execute('DELETE FROM leaderboard')
    conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to authenticate users
def authenticate_user(username, password):
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    user = cursor.fetchone()
    return user is not None

# Function to register new users
def register_user(username, password):
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Function to fetch AQI data from OpenAQ API (with API key)
def fetch_aqi_data(city="Delhi"):
    api_key = "26f8c68c2e285dadb52c22ed2758513b1b7e4225c33aed72f4691cb01a12cc00"  # Replace with your actual API key
    url = f"https://api.openaq.org/v1/latest?city={city}"
    
    headers = {
        "X-API-Key": api_key  # Use X-API-Key for authentication
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data['results'][0]  # Return the first result
        else:
            st.error(f"No AQI data found for {city}. Try a different city.")
            return None
    else:
        st.error(f"Error fetching data from OpenAQ API. Status code: {response.status_code}")
        return None

# Function to fetch the latest AQI value
def fetch_latest_aqi(city):
    aqi_data = fetch_aqi_data(city)
    if aqi_data:
        latest_aqi = None
        for measurement in aqi_data['measurements']:
            if measurement["parameter"] == "pm25":  # Focus on PM2.5 for AQI
                latest_aqi = measurement["value"]
                break
        return latest_aqi
    return None

# Function to categorize AQI
def categorize_aqi(aqi):
    if aqi <= 50:
        return "Good"
    elif 51 <= aqi <= 100:
        return "Moderate"
    elif 101 <= aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif 151 <= aqi <= 200:
        return "Unhealthy"
    elif 201 <= aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

# Set wide layout and page name
st.set_page_config(layout="wide", page_title="Personal Carbon & AQI Tracker")

# Streamlit app title and description
st.title("📊 Personal Carbon & AQI Tracker")
st.write("This Platform helps you calculate your carbon footprint and displays AQI data for any given city.")

# Section: Login/Signup Toggle
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.sidebar.header("Login / Signup")
    auth_option = st.sidebar.radio("Choose action:", ("Login", "Sign Up"))

    if auth_option == "Login":
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")

    elif auth_option == "Sign Up":
        st.sidebar.subheader("Sign Up")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        
        if st.sidebar.button("Sign Up"):
            if password == confirm_password:
                if register_user(username, password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already taken.")
            else:
                st.error("Passwords do not match.")
else:
    st.header(f"Welcome, {st.session_state.username}!")

    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        del st.session_state.username
        st.success("You have logged out.")

    # Section: Carbon Footprint Calculator
    st.header("🛠 Carbon Footprint Calculator")

    # User inputs for carbon calculator
    st.subheader("🌍 Your Country")
    country = st.selectbox("Select", ["India"])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚗 Daily commute distance (in km)")
        distance = st.slider("Distance", 0.0, 100.0, key="distance_input")

        st.subheader("💡 Monthly electricity consumption (in kWh)")
        electricity = st.slider("Electricity", 0.0, 1000.0, key="electricity_input")

    with col2:
        st.subheader("🍽 Number of meals per day")
        meals = st.number_input("Meals", 0, key="meals_input")

        # New feature: Meal Type
        st.subheader("🍽 Meal Type")
        meal_type = st.selectbox("Select Meal Type", ["Vegetarian", "Non-Vegetarian", "Processed Foods"])

        # New feature: Cooking Method
        st.subheader("🍽 Cooking Method")
        cooking_method = st.selectbox("Select Cooking Method", ["Boiling", "Grilling", "Frying", "Baking", "Raw"])

    # Normalize inputs
    if distance > 0:
        distance = distance * 365  # Convert daily distance to yearly
    if electricity > 0:
        electricity = electricity * 12  # Convert monthly electricity to yearly
    if meals > 0:
        meals = meals * 365  # Convert daily meals to yearly

    # Calculate carbon emissions
    transportation_emissions = EMISSION_FACTORS[country]["Transportation"] * distance
    electricity_emissions = EMISSION_FACTORS[country]["Electricity"] * electricity
    diet_emissions = EMISSION_FACTORS[country]["Diet"] * meals

    # Adjust emissions for cooking method
    cooking_emissions = COOKING_METHOD_EMISSIONS[cooking_method] * meals

    # Convert emissions to tonnes and round off to 2 decimal points
    transportation_emissions = round(transportation_emissions / 1000, 2)
    electricity_emissions = round(electricity_emissions / 1000, 2)
    diet_emissions = round(diet_emissions / 1000, 2)
    cooking_emissions = round(cooking_emissions / 1000, 2)

    # Calculate total emissions
    total_emissions = round(
        transportation_emissions + electricity_emissions + diet_emissions + cooking_emissions, 2
    )

    if st.button("Calculate CO2 Emissions"):

        # Display results
        st.subheader("Results")

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Carbon Emissions by Category")
            st.info(f"🚗 Transportation: {transportation_emissions} tonnes CO2 per year")
            st.info(f"💡 Electricity: {electricity_emissions} tonnes CO2 per year")
            st.info(f"🍽 Diet: {diet_emissions} tonnes CO2 per year")
            st.info(f"🍳 Cooking: {cooking_emissions} tonnes CO2 per year")

        with col4:
            st.subheader("Total Carbon Footprint")
            st.success(f"🌍 Your total carbon footprint is: {total_emissions} tonnes CO2 per year")

        # Suggestions for reducing emissions
        st.subheader("🚀 Ways to Reduce Your Carbon Footprint")

        # Transportation
        st.write("🚗 Transportation:")
        st.write("- Use public transportation, carpool, or bike instead of driving alone.")
        st.write("- Switch to an electric vehicle (EV) or a hybrid vehicle.")
        st.write("- Walk for short trips to reduce your carbon footprint.")
        st.write("- Consider working remotely if possible to reduce daily commute.")

        # Electricity
        st.write("💡 Electricity Consumption:")
        st.write("- Switch to energy-efficient appliances (LED bulbs, energy-efficient ACs, etc.).")
        st.write("- Opt for renewable energy sources such as solar or wind energy.")
        st.write("- Unplug electronic devices when not in use to reduce standby energy consumption.")
        st.write("- Install insulation in your home to reduce heating and cooling energy needs.")

        # Diet
        st.write("🍽 Diet:")
        st.write("- Reduce meat and dairy consumption, as these foods have a higher carbon footprint.")
        st.write("- Choose plant-based meals, which generally have lower emissions.")
        st.write("- Buy local and seasonal produce to reduce emissions from transportation and storage.")
        st.write("- Minimize food waste by buying only what you need and storing food properly.")

        # Cooking Methods
        st.write("🍳 Cooking Methods:")
        st.write("- Use energy-efficient cooking methods like pressure cooking, steaming, or microwaving.")
        st.write("- Reduce cooking time by batch cooking or using the right-sized pot/pan.")
        st.write("- Consider using a stove or induction cooktop instead of an oven, which uses more energy.")
        st.write("- Use solar cooking or slow cookers as alternative methods to reduce energy consumption.")

        # Add user to leaderboard (only if username is provided)
        if st.session_state.username:
            add_user_to_leaderboard(st.session_state.username, total_emissions)
        else:
            add_user_to_leaderboard('Anonymous User', total_emissions)

        # Fetch and display leaderboard
        leaderboard_data = get_leaderboard()

        st.subheader("🏆 Leaderboard")
        leaderboard_display = ""
        for rank, (username, score) in enumerate(leaderboard_data, start=1):
            leaderboard_display += f"{rank}. {username} - {score} tonnes CO2/year\n"

        st.text(leaderboard_display)

    # Clear leaderboard data button
    if st.button("Clear Data"):
        clear_leaderboard()
        st.success("Leaderboard data has been cleared!")


    # Section: AQI Tracker
    st.header("🌫 Air Quality Index (AQI) Tracker")

    # Input for selecting city
    city = st.selectbox("Select City", options=["Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "London", "New York", "Los Angeles", "Paris", "Tokyo", "Beijing", "Sydney", "Berlin", "Rome", "Dubai"])

    # Fetch and display AQI data
    if st.button("Fetch AQI Data"):
        latest_aqi = fetch_latest_aqi(city)
        
        if latest_aqi:
            category = categorize_aqi(latest_aqi)
            st.write(f"Current AQI in {city}: {latest_aqi}")
            st.write(f"Category: {category}")

            # Create a pie chart for AQI categories
            labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
            sizes = [0, 0, 0, 0, 0, 0]  # Initialize counts for each category

            # Classify the latest AQI value
            if category == 'Good':
                sizes[0] += 1
            elif category == 'Moderate':
                sizes[1] += 1
            elif category == 'Unhealthy for Sensitive Groups':
                sizes[2] += 1
            elif category == 'Unhealthy':
                sizes[3] += 1
            elif category == 'Very Unhealthy':
                sizes[4] += 1
            elif category == 'Hazardous':
                sizes[5] += 1

            # Create a more informative pie chart
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=sizes,
                hole=0.3,
                hoverinfo='label+percent',
                textinfo='percent+label',
                textposition='inside',
                marker=dict(colors=['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8B0000', '#7E0023'])  # Different colors for each category
            )])
            fig.update_traces(textinfo='percent+label', pull=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
            fig.update_layout(title="AQI Category Distribution")

            st.plotly_chart(fig)

        else:
            st.error(f"No data found for the city: {city}")
