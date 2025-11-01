# controller_mqtt_tls.py — Streamlit controller (HiveMQ Cloud TLS)
import time
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car Controller (HiveMQ Cloud)", layout="centered")
st.title("🚗 ESP32 Car Controller (HiveMQ Cloud)")

# --- Configuration fields ---
broker = st.text_input("Broker Host", "e03bf396880b4e10b7a6bbb5f69bdf16.s1.eu.hivemq.cloud")
port = st.number_input("Port", 1, 65535, 8883)
username = st.text_input("Username", "")
password = st.text_input("Password", "", type="password")
device_id = st.text_input("Device ID", "esp32car-01").strip()
qos = st.selectbox("QoS", [0, 1], index=0)

topic_cmd = f"esp32car/{device_id}/cmd"
topic_status = f"esp32car/{device_id}/status"

# --- MQTT Client (persistent) ---
if "mqtt_client" not in st.session_state:
    c = mqtt.Client(client_id=f"st-{int(time.time())}")
    st.session_state.mqtt_client = c
    st.session_state.connected = False

client = st.session_state.mqtt_client
msg_status = st.empty()

def on_connect(c, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        msg_status.success(f"✅ Connected to HiveMQ Cloud ({broker}:{port})")
        c.subscribe(topic_status, qos=qos)
        c.subscribe(topic_cmd, qos=qos)
    else:
        msg_status.error(f"❌ Connection failed: {rc}")

def on_message(c, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    st.write(f"📩 `{msg.topic}` → `{payload}`")

client.on_connect = on_connect
client.on_message = on_message

def connect():
    try:
        client.username_pw_set(username, password)
        client.tls_set()  # enables SSL/TLS
        client.connect(broker, int(port), keepalive=60)
        client.loop_start()
        time.sleep(1)
    except Exception as e:
        msg_status.error(f"Connection error: {e}")

if st.button("Connect MQTT"):
    connect()

# Auto-connect once
if not st.session_state.connected:
    connect()

# --- Car Controls ---
st.subheader("Controls")
speed = st.slider("Speed (0–255)", 0, 255, 160)
ms = st.slider("Duration (ms) (0 = continuous)", 0, 2000, 300)

def publish_cmd(cmd):
    if not st.session_state.connected:
        st.error("MQTT not connected")
        return
    payload = f"{cmd},{speed},{ms}"
    try:
        client.publish(topic_cmd, payload, qos=qos)
        st.success(f"Sent → `{topic_cmd}` : `{payload}`")
    except Exception as e:
        st.error(f"Publish failed: {e}")

cols1 = st.columns(3)
with cols1[1]:
    if st.button("⬆️ Forward"): publish_cmd("F")
cols2 = st.columns(3)
with cols2[0]:
    if st.button("⬅️ Left"): publish_cmd("L")
with cols2[1]:
    if st.button("⏹️ Stop"): publish_cmd("S")
with cols2[2]:
    if st.button("➡️ Right"): publish_cmd("R")
cols3 = st.columns(3)
with cols3[1]:
    if st.button("⬇️ Backward"): publish_cmd("B")
