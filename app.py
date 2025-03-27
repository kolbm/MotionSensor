import streamlit as st
import serial
import serial.tools.list_ports
import time
import pandas as pd

st.set_page_config(page_title="ESP32 Distance Monitor", layout="wide")
st.title("📏 ESP32 Distance Sensor Dashboard")

st.markdown("""
🔌 **Instructions**
- Plug in your ESP32 (usually shows up as COM3, COM5, etc.)
- If you plugged it in after launching this app, click **🔄 Refresh COM Ports**
- Select a port and click **▶️ Start Sensor**
- Click **⏹ Stop Sensor** to stop streaming
""")

if st.button("🔄 Refresh COM Ports"):
    st.rerun()

port_options = [port.device for port in serial.tools.list_ports.comports()]
PORT = st.selectbox("Select Serial Port", port_options)
BAUD = 115200
sample_rate_ms = st.slider("Sample Rate (ms)", 10, 1000, 100, step=10)
unit = st.selectbox("Distance Unit", ["meters", "centimeters", "inches"])

ser = None
readings = []
started = False

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
                except:
                    continue
    except KeyboardInterrupt:
        st.warning("Stream stopped.")

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
