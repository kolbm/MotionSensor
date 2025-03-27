
import streamlit as st
import serial
import serial.tools.list_ports
import time
import pandas as pd
import io

st.set_page_config(page_title="ESP32 Distance Monitor", layout="wide")
st.title("📏 ESP32 Distance Sensor Dashboard")

st.markdown("""
🔌 **Instructions**
- Plug in your ESP32 **before or after** launching this app.
- If you **just plugged it in**, click the **Refresh COM Ports** button below.
- Then select the correct port from the dropdown and click **Start Sensor**.
""")

# Refresh button
if st.button("🔄 Refresh COM Ports"):
    st.rerun()

# COM Port dropdown
port_options = [port.device for port in serial.tools.list_ports.comports()]
PORT = st.selectbox("Select Serial Port", port_options)
BAUD = 115200
sample_rate_ms = st.slider("Sample Rate (ms)", min_value=10, max_value=1000, value=100, step=10)
unit = st.selectbox("Distance Unit", ["meters", "centimeters", "inches"])

ser = None
readings = []
started = False

# Start Sensor
if st.button("▶️ Start Sensor"):
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        ser.write(b's')
        st.success("Sensor started. Reading data...")
        started = True
    except Exception as e:
        st.error(f"❌ Could not open serial port: {e}")
        started = False

# Stop Sensor
if st.button("⏹ Stop Sensor"):
    if ser and ser.is_open:
        ser.write(b'x')
        ser.close()
        st.info("Sensor stopped.")
    started = False

if started and ser and ser.is_open:
    chart = st.line_chart()
    try:
        while True:
            line = ser.readline().decode().strip()
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

                    spike = ""
                    if readings and abs(distance_val - readings[-1]["Distance"]) > 10:
                        spike = "⚠️ Spike"

                    readings.append({
                        "Timestamp (ms)": timestamp,
                        "Distance": round(distance_val, 2),
                        "Note": spike
                    })
                    chart.add_rows({"Distance": [distance_val]})
                    time.sleep(sample_rate_ms / 1000.0)
                except:
                    continue
    except KeyboardInterrupt:
        st.warning("Stream stopped.")

# Show data and download
if readings:
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
