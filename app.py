import streamlit as st
import serial
import serial.tools.list_ports
import time
import pandas as pd

st.set_page_config(page_title="ESP32 Distance Monitor", layout="wide")
st.title("📏 ESP32 Distance Sensor Dashboard")

st.markdown("""
🔌 **Instructions**
- Make sure your ESP32 is plugged into COM5.
- Click ▶️ to start streaming distance data.
- Click ⏹ to stop the stream and release the port.
""")

PORT = "COM5"
BAUD = 115200
sample_rate_ms = st.slider("Sample Rate (ms)", 10, 1000, 100, step=10)
unit = st.selectbox("Distance Unit", ["meters", "centimeters", "inches"])

# Setup session state
if "ser" not in st.session_state:
    st.session_state.ser = None
if "running" not in st.session_state:
    st.session_state.running = False

readings = []

col1, col2 = st.columns(2)

# ▶️ Start Sensor
if col1.button("▶️ Start Sensor"):
    try:
        # Close any old connection
        if st.session_state.ser and st.session_state.ser.is_open:
            st.session_state.ser.close()
        st.session_state.ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)  # Allow time for serial to stabilize
        st.session_state.ser.write(b's')
        st.session_state.running = True
        st.success(f"✅ Connected and started on {PORT}")
    except Exception as e:
        st.session_state.ser = None
        st.session_state.running = False
        st.error(f"❌ Could not open serial port: {e}")

# ⏹ Stop Sensor
if col2.button("⏹ Stop Sensor"):
    try:
        if st.session_state.ser and st.session_state.ser.is_open:
            st.session_state.ser.write(b'x')
            st.session_state.ser.close()
            st.success("Sensor stopped and port closed.")
        st.session_state.running = False
    except Exception as e:
        st.error(f"Error closing serial port: {e}")

# 📈 Live data chart
if st.session_state.running and st.session_state.ser and st.session_state.ser.is_open:
    chart = st.line_chart()
    try:
        while True:
            line = st.session_state.ser.readline().decode().strip()
            if line:
                try:
                    timestamp, distance = line.split(",")[:2]
                    timestamp = int(timestamp)
                    distance_m = float(distance)

                    # Convert units
                    if unit == "centimeters":
                        distance_val = distance_m * 100
                    elif unit == "inches":
                        distance_val = distance_m * 39.3701
                    else:
                        distance_val = distance_m

                    readings.append({
                        "Timestamp (ms)": timestamp,
                        "Distance": round(distance_val, 2)
                    })

                    chart.add_rows({"Distance": [distance_val]})
                    time.sleep(sample_rate_ms / 1000.0)

                except Exception as e:
                    st.warning(f"⚠️ Parse error: {e}")
                    continue
    except KeyboardInterrupt:
        st.warning("⏹ Stream stopped manually.")

# 📥 Download CSV
if readings:
    st.subheader("📊 Recorded Readings")
    df = pd.DataFrame(readings)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="distance_log.csv",
        mime="text/csv"
    )
