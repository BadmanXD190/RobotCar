
# controller_mqtt.py — Streamlit MQTT controller for ESP32 car
import json
import time
import threading
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car (MQTT)", layout="centered")
st.title("ESP32 Car Controller (MQTT)")

# --- Settings ---
col = st.columns(2)
with col[0]:
    broker = st.text_input("MQTT Broker", "broker.hivemq.com")
    port = st.number_input("Port", 1, 65535, 1883, step=1)
with col[1]:
    device_id = st.text_input("Device ID", "esp32car-01").strip()
    qos = st.selectbox("QoS", [0,1,2], index=0)

topic_cmd = f"esp32car/{device_id}/cmd"
topic_status = f"esp32car/{device_id}/status"

# --- MQTT Client ---
client = mqtt.Client()
connected = st.empty()
status_box = st.empty()

def on_connect(c, userdata, flags, rc):
    connected.info(f"Connected (rc={rc})")
    # subscribe to status
    c.subscribe(topic_status, qos=qos)

def on_message(c, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
    except:
        payload = str(msg.payload)
    status_box.markdown(f"**Status** `{msg.topic}`\n```\n{payload}\n```")

client.on_connect = on_connect
client.on_message = on_message

def ensure_connected():
    try:
        client.connect(broker, int(port), keepalive=30)
        client.loop_start()
        time.sleep(0.5)
        connected.success(f"MQTT to {broker}:{port} | CMD topic: `{topic_cmd}`")
    except Exception as e:
        connected.error(f"MQTT connect failed: {e}")

if st.button("Connect MQTT"):
    ensure_connected()

# --- Controls ---
cA, cB = st.columns(2)
with cA:
    speed = st.slider("Speed (0–255)", 0, 255, 160, 1)
with cB:
    ms = st.slider("Duration (ms) (0 = continuous)", 0, 1500, 300, 50)

def publish_cmd(cmd, spd=None, dur=None):
    if spd is None: spd = speed
    if dur is None: dur = ms
    payload = f"{cmd},{int(spd)},{int(dur)}" if cmd != "S" else "S"
    try:
        client.publish(topic_cmd, payload, qos=qos)
        st.success(f"→ {topic_cmd}: {payload}")
    except Exception as e:
        st.error(f"Publish failed: {e}")

st.write("### Controls")
top = st.columns([1,1,1])
mid = st.columns([1,1,1])
bot = st.columns([1,1,1])

with top[1]:
    if st.button("⬆️ Up (F)"):
        publish_cmd("F")

with mid[0]:
    if st.button("⬅️ Left (L)"):
        publish_cmd("L")
with mid[1]:
    if st.button("⏹️ Stop (S)"):
        publish_cmd("S", 0, 0)
with mid[2]:
    if st.button("➡️ Right (R)"):
        publish_cmd("R")

with bot[1]:
    if st.button("⬇️ Down (B)"):
        publish_cmd("B")

st.write("---")
st.caption(f"Command topic: `{topic_cmd}`  •  Status topic: `{topic_status}`")
