import streamlit as st
import serial
import serial.tools.list_ports
import time
import pandas as pd

st.set_page_config(page_title="ESP32 Distance Monitor", layout="wide")
st.title("📏 ESP32 Distance Sensor Dashboard")

st.markdown("""
🔌 **Instructions**
- Plug in your ESP32 before or after launching this app.
- Click 🔄 to refresh the COM port list if needed.
- Select the correct port and click ▶️ to start streaming.
""")

# 🔄 Refresh COM port list
if st.button("🔄 Refresh COM Ports"):
    st.rerun()

# 🛠 List available ports
ports = [port.device for port in serial.tools.list_ports.comports()]
PORT = st.selectbox("Select Serial Port", ports)
BAUD = 115200
sample_rate_ms = st.slider("Sample Rate (ms)", 10, 1000, 100)
unit = st.selectbox("Distance Unit", ["meters", "centimeters", "inches"])

if "ser" not in st.session_state:
    st.session_state.ser = None
if "running" not in st.session_state:
    st.session_state.running = False

readings = []

col1, col2 = st.columns(2)

# ▶️ Start Sensor
if col1.button("▶️ Start Sensor"):
    try:
        if st.session_state.ser and st.session_state.ser.is_open:
            st.session_state.ser.close()
        st.session_state.ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        st.session_state.ser.write(b's')
        st.session_state.running = True
        st.success(f"✅ Connected to {PORT}")
    except Exception as e:
        st.session_state.ser = None
        st.session_state.running = False
        st.error(f"❌ Could not open serial port {PORT}: {e}")

# ⏹ Stop Sensor
if col2.button("⏹ Stop Sensor"):
    try:
        if st.session_state.ser and st.session_state.ser.is_open:
            st.session_state.ser.write(b'x')
            st.session_state.ser.close()
            st.success("Sensor stopped.")
        st.session_state.running = False
    except Exception as e:
        st.error(f"Error closing serial port: {e}")

# 📈 Live Stream
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
                    st.warning(f"⚠️ Read error: {e}")
                    continue
    except KeyboardInterrupt:
        st.warning("⏹ Stream stopped.")

# 📥 CSV Download
if readings:
    st.subheader("📊 Recorded Readings")
    df = pd.DataFrame(readings)
    st.dataframe(df)
    st.download_button(
        "📥 Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="distance_log.csv",
        mime="text/csv"
    )
