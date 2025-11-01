# controller_ws_mosquitto_fixed.py — MQTT over WSS (TLS) to test.mosquitto.org
import time
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car (Mosquitto WSS)", layout="centered")
st.title("ESP32 Car Controller — Mosquitto (WSS)")

# Connection fields
broker = st.text_input("Broker host", "test.mosquitto.org")
port = st.number_input("Port", 1, 65535, 8081)
device_id = st.text_input("Device ID", "esp32car-01").strip()
qos = st.selectbox("QoS", [0, 1], index=0)

topic_cmd = f"esp32car/{device_id}/cmd"
topic_status = f"esp32car/{device_id}/status"

# Maintain client between reruns
if "client" not in st.session_state:
    c = mqtt.Client(client_id=f"st-wss-{int(time.time())}", transport="websockets")
    st.session_state.client = c
    st.session_state.connected = False
    st.session_state.tls_configured = False  # <— new flag

client = st.session_state.client
info = st.empty()
status_box = st.empty()
echo_box = st.empty()

def on_connect(c, userdata, flags, rc):
    st.session_state.connected = (rc == 0)
    if rc == 0:
        info.success(f"✅ Connected to {broker}:{port} (WSS/TLS)")
        c.subscribe(topic_status, qos=qos)
        c.subscribe(topic_cmd, qos=qos)
    else:
        info.error(f"❌ Connect failed (rc={rc})")

def on_message(c, userdata, msg):
    payload = msg.payload.decode("utf-8", "ignore")
    if msg.topic.endswith("/status"):
        status_box.markdown(f"**Status** `{msg.topic}`\n```\n{payload}\n```")
    else:
        echo_box.markdown(f"**Command echoed** `{msg.topic}` → `{payload}`")

client.on_connect = on_connect
client.on_message = on_message

def connect():
    try:
        if not st.session_state.tls_configured:
            client.tls_set()                     # only once
            st.session_state.tls_configured = True
        if not st.session_state.connected:
            client.connect(broker, int(port), keepalive=45)
            client.loop_start()
            time.sleep(0.7)
            if not st.session_state.connected:
                info.warning("Connecting… click again if needed.")
        else:
            info.info("Already connected.")
    except Exception as e:
        info.error(f"MQTT connect error: {e}")

if st.button("Connect MQTT"):
    connect()

if not st.session_state.connected:
    connect()

# Controls
st.subheader("Controls")
speed = st.slider("Speed (0–255)", 0, 255, 160)
ms = st.slider("Duration (ms) (0 = continuous)", 0, 2000, 300)

def publish_cmd(cmd):
    if not st.session_state.connected:
        st.error("Not connected")
        return
    payload = f"{cmd},{speed},{ms}" if cmd != "S" else "S"
    try:
        pi = client.publish(topic_cmd, payload, qos=qos)
        pi.wait_for_publish(timeout=1.0)
        st.success(f"→ {topic_cmd}: {payload}")
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

st.caption(f"CMD: `{topic_cmd}` • STATUS: `{topic_status}` • Transport: WSS 8081 (TLS)")
