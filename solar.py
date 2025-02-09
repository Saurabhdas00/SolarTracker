import streamlit as st
import requests
import geocoder

# Set Streamlit app title
st.title("🌞 Solar Feasibility Checker")

# Initialize session state variables
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "session_ended" not in st.session_state:
    st.session_state.session_ended = False

# Show Start Session button only if session hasn't started or ended
if not st.session_state.session_active and not st.session_state.session_ended:
    if st.button("🔍 Start Session"):
        st.session_state.session_active = True
        st.session_state.panel_selected = False  # To ensure only feasibility shows first
        st.experimental_rerun()

# Proceed only if session has started and not ended
if st.session_state.session_active:

    # Step 1: Get location based on IP
    st.write("📍 Fetching your location...")

    location = geocoder.ip('me')
    if location.latlng:
        latitude, longitude = location.latlng
    else:
        st.error("❌ Error: Could not determine location!")
        st.stop()

    # Reverse geocoding to get city & state
    geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    geo_response = requests.get(geocode_url, headers=headers).json()

    if "address" in geo_response:
        city = geo_response["address"].get("city", "Unknown City")
        state = geo_response["address"].get("state", "Unknown State")
    else:
        city, state = "Unknown City", "Unknown State"

    st.subheader(f"📍 Location: {city}, {state}")

    # Step 2: Fetch Solar & Weather Data
    st.write("🌤️ Fetching solar & weather data...")

    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=shortwave_radiation_sum,temperature_2m_max,cloudcover_mean,wind_speed_10m_max&timezone=Asia/Kolkata"
    response = requests.get(weather_url)
    weather_data = response.json()

    nasa_url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN,T2M,CLRSKY_SFC_SW_DWN,WS10M&community=RE&longitude={longitude}&latitude={latitude}&start=20230101&end=20231231&format=JSON"
    response_nasa = requests.get(nasa_url)
    nasa_data = response_nasa.json()

    # Step 3: Extract relevant data (taking annual average)
    try:
        avg_solar_irradiance = sum(nasa_data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"].values()) / 365
        avg_temperature = sum(nasa_data["properties"]["parameter"]["T2M"].values()) / 365
        avg_cloud_cover = sum(weather_data["daily"]["cloudcover_mean"]) / len(weather_data["daily"]["cloudcover_mean"])
        avg_wind_speed = sum(weather_data["daily"]["wind_speed_10m_max"]) / len(weather_data["daily"]["wind_speed_10m_max"])
    except KeyError:
        st.error("❌ Error: Unable to fetch weather data!")
        st.stop()

    # Step 4: Check Solar Feasibility
    st.subheader("📊 Solar Feasibility Analysis")

    solar_feasible = True
    reasons = []

    # Solar Irradiance Condition
    if avg_solar_irradiance < 4:
        reasons.append("❌ Not Enough Sunlight: Solar energy might be inefficient here.")
        solar_feasible = False
    else:
        st.write("✅ Solar Irradiance is good for solar panels.")

    # Temperature Condition
    if avg_temperature > 45:
        reasons.append("⚠️ High Temperature: May reduce solar panel efficiency.")
    else:
        st.write("✅ Temperature is suitable for solar panels.")

    # Cloud Cover Condition
    if avg_cloud_cover > 50:
        reasons.append("⚠️ High Cloud Cover: May reduce power output.")
    else:
        st.write("✅ Cloud cover is within acceptable limits.")

    # Wind Speed Condition
    if avg_wind_speed > 20:
        reasons.append("⚠️ High Wind Speed: Might require stronger mounting.")
    else:
        st.write("✅ Wind speed is safe for solar panel installation.")

    # Step 5: Display Final Decision
    if solar_feasible:
        st.success("✅ **This location is SUITABLE for Solar Panel Installation!** 🌞⚡")

        # Step 6: Predict Solar Power Generation
        panel_efficiency = 0.18  # 18% efficiency standard for solar panels
        panel_area = 1.6  # Each panel is ~1.6 m²
        panel_output_per_day = avg_solar_irradiance * panel_area * panel_efficiency  # kWh/day per panel

        st.subheader("🔋 Predicted Solar Power Generation")
        st.write(f"**Estimated daily output per panel:** {panel_output_per_day:.2f} kWh/day")

        # Panel slider that updates dynamically
        if not st.session_state.panel_selected:
            num_panels = st.slider("Select number of panels:", 1, 20, 5, key="num_panels")
            st.session_state.total_power = panel_output_per_day * num_panels
            st.session_state.panel_selected = True
            st.experimental_rerun()

        st.write(f"⚡ **Total estimated power output:** {st.session_state.total_power:.2f} kWh/day for {st.session_state.num_panels} panels")

    else:
        st.error("❌ **This location is NOT suitable for solar energy.**")
        st.subheader("⚠️ Reasons:")
        for reason in reasons:
            st.write(reason)

    # End Session: Disable all inputs and show final message
    st.session_state.session_active = False
    st.session_state.session_ended = True

# Step 7: Show "Session Ended" and Restart Button
if st.session_state.session_ended:
    st.divider()
    st.write("🛑 **Session Ended**")
    if st.button("🔄 Start New Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
