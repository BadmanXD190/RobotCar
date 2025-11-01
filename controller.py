# ESP32 Car Controller — HiveMQ Cloud (TLS, Auto Connect)
import time
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car Controller", layout="centered")
st.title("🚗 ESP32 Car Controller (HiveMQ Cloud Auto)")

# ---------- Fixed HiveMQ Cloud Config ----------
BROKER = "e03bf396880b4e10b7a6bbb5f69bdf16.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "badmanXD"           # your HiveMQ Cloud username
PASSWORD = "Siang09534" # replace with your actual HiveMQ Cloud password
DEVICE_ID = "esp32car-01"

TOPIC_CMD = f"esp32car/{DEVICE_ID}/cmd"
TOPIC_STATUS = f"esp32car/{DEVICE_ID}/status"
TOPIC_LWT = f"esp32car/{DEVICE_ID}/lwt"

QOS = 1

# ---------- MQTT Client Setup ----------
if "mqtt_client" not in st.session_state:
    c = mqtt.Client(client_id=f"st-{int(time.time())}")
    st.session_state.mqtt_client = c
    st.session_state.connected = False
    st.session_state._tls_inited = False

client = st.session_state.mqtt_client
conn_msg = st.empty()
status_box = st.empty()
cmd_echo_box = st.empty()

def on_connect(c, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        conn_msg.success(f"✅ Connected to HiveMQ Cloud ({BROKER}:{PORT})")
        c.subscribe(TOPIC_STATUS, qos=QOS)
        c.subscribe(TOPIC_CMD, qos=QOS)
    else:
        st.session_state.connected = False
        conn_msg.error(f"❌ MQTT connect failed (rc={rc})")

def on_message(c, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    if msg.topic.endswith("/status"):
        status_box.markdown(f"**Status** `{msg.topic}`\n```\n{payload}\n```")
    else:
        cmd_echo_box.markdown(f"**Broker saw command** `{msg.topic}` → `{payload}`")

client.on_connect = on_connect
client.on_message = on_message

def connect():
    try:
        if not st.session_state._tls_inited:
            client.tls_set()  # enable TLS once
            st.session_state._tls_inited = True

        client.username_pw_set(USERNAME, PASSWORD)
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        time.sleep(1)
        if not st.session_state.connected:
            conn_msg.warning("Connecting... please wait or click again.")
    except Exception as e:
        conn_msg.error(f"Connection error: {e}")

def disconnect():
    try:
        client.loop_stop()
        client.disconnect()
        st.session_state.connected = False
        conn_msg.info("Disconnected")
    except Exception as e:
        conn_msg.error(f"Disconnect error: {e}")

# ---------- Auto connect on start ----------
if not st.session_state.connected:
    connect()

st.divider()

# ---------- Car Controls ----------
st.subheader("Controls")
colA, colB = st.columns(2)
with colA:
    speed = st.slider("Speed (0–255)", 0, 255, 160)
with colB:
    ms = st.slider("Duration (ms, 0 = continuous)", 0, 2000, 300)

def publish_cmd(cmd, spd=None, dur=None):
    if not st.session_state.connected:
        st.error("MQTT not connected")
        return
    if spd is None: spd = speed
    if dur is None: dur = ms
    payload = f"{cmd},{int(spd)},{int(dur)}" if cmd != "S" else "S"
    try:
        info = client.publish(TOPIC_CMD, payload, qos=QOS)
        info.wait_for_publish(timeout=1.0)
        st.success(f"→ {TOPIC_CMD}: `{payload}`")
    except Exception as e:
        st.error(f"Publish failed: {e}")

top = st.columns(3)
with top[1]:
    if st.button("⬆️ Forward"):
        publish_cmd("F")

mid = st.columns(3)
with mid[0]:
    if st.button("⬅️ Left"):
        publish_cmd("L")
with mid[1]:
    if st.button("⏹️ Stop"):
        publish_cmd("S", 0, 0)
with mid[2]:
    if st.button("➡️ Right"):
        publish_cmd("R")

bot = st.columns(3)
with bot[1]:
    if st.button("⬇️ Backward"):
        publish_cmd("B")

st.caption(f"Connected to: `{BROKER}` • TLS: ON • Topics: `{TOPIC_CMD}` / `{TOPIC_STATUS}`")
