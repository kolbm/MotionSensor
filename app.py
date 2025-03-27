import streamlit as st
import serial
import time
import pandas as pd
import io

st.set_page_config(page_title="ESP32 Distance Monitor", layout="wide")
st.title("📏 ESP32 Distance Sensor Dashboard")

PORT = st.text_input("Serial Port", "/dev/ttyUSB0" if not st.runtime.exists() else "COM3")
BAUD = 115200
sample_rate_ms = st.slider("Sample Rate (ms)", min_value=10, max_value=1000, value=100, step=10)
unit = st.selectbox("Distance Unit", ["meters", "centimeters", "inches"])

@st.cache_resource
def get_serial():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        return ser
    except:
        st.error("Could not open serial port.")
        return None

ser = get_serial()

if ser:
    col1, col2 = st.columns(2)
    if col1.button("▶️ Start Sensor"):
        ser.write(b's')
        st.success("Sensor started")
    if col2.button("⏹ Stop Sensor"):
        ser.write(b'x')
        st.info("Sensor stopped")

    readings = []
    chart = st.line_chart()

    try:
        while True:
            line = ser.readline().decode().strip()
            if line:
                try:
                    timestamp, distance = line.split(",")[:2]
                    timestamp = int(timestamp)
                    distance_m = float(distance)

                    # Convert unit
                    if unit == "centimeters":
                        distance_val = distance_m * 100
                    elif unit == "inches":
                        distance_val = distance_m * 39.3701
                    else:
                        distance_val = distance_m

                    spike = ""
                    if readings and abs(distance_val - readings[-1]["Distance"]) > 10:
                        spike = "⚠️ Spike"

                    readings.append({"Timestamp (ms)": timestamp, "Distance": round(distance_val, 2), "Note": spike})
                    chart.add_rows({"Distance": [distance_val]})
                    time.sleep(sample_rate_ms / 1000.0)
                except:
                    continue
    except KeyboardInterrupt:
        pass

    st.subheader("📊 Recorded Readings")
    df = pd.DataFrame(readings)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="distance_log.csv",
        mime="text/csv"
    )
