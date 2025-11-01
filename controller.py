# controller_mqtt.py — Streamlit MQTT controller (WebSockets + persistent client)
import time
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car (MQTT)", layout="centered")
st.title("ESP32 Car Controller (MQTT)")

# --- Settings ---
col = st.columns(2)
with col[0]:
    broker = st.text_input("MQTT Broker", "broker.hivemq.com")
    # Use 8000 for WebSockets on HiveMQ public broker
    port = st.number_input("Port", 1, 65535, 8000, step=1)
with col[1]:
    device_id = st.text_input("Device ID", "esp32car-01").strip()
    qos = st.selectbox("QoS", [0, 1], index=0)

topic_cmd = f"esp32car/{device_id}/cmd"
topic_status = f"esp32car/{device_id}/status"

# --- Persist MQTT client across reruns ---
if "mqtt_client" not in st.session_state:
    # transport="websockets" for cloud compatibility
    c = mqtt.Client(client_id=f"st-{int(time.time())}", transport="websockets")
    # HiveMQ WS path
    c.ws_set_options(path="/mqtt")
    st.session_state.mqtt_client = c
    st.session_state.connected = False

client = st.session_state.mqtt_client
connected_msg = st.empty()
status_box = st.empty()
cmd_echo = st.empty()

def on_connect(c, userdata, flags, rc):
    st.session_state.connected = (rc == 0)
    if rc == 0:
        connected_msg.success(f"Connected to {broker}:{port} (WebSockets)")
        # Subscribe to status and cmd so you can SEE your own publishes too
        c.subscribe(topic_status, qos=qos)
        c.subscribe(topic_cmd, qos=qos)
    else:
        connected_msg.error(f"Connect failed (rc={rc})")

def on_message(c, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    if msg.topic.endswith("/status"):
        status_box.markdown(f"**Status** `{msg.topic}`\n```\n{payload}\n```")
    else:
        cmd_echo.markdown(f"**Command seen on broker** `{msg.topic}` → `{payload}`")

client.on_connect = on_connect
client.on_message = on_message

def connect():
    try:
        # For WS brokers like HiveMQ public:  broker.hivemq.com:8000 + /mqtt
        client.connect(broker, int(port), keepalive=30)
        client.loop_start()
        time.sleep(0.6)  # give time to finish handshake
        if not st.session_state.connected:
            connected_msg.warning("Connecting... click again if needed.")
    except Exception as e:
        connected_msg.error(f"MQTT connect failed: {e}")

if st.button("Connect MQTT"):
    connect()

# Auto-connect once when page opens
if not st.session_state.connected:
    connect()

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
    if not st.session_state.connected:
        st.error("Not connected to MQTT")
        return
    try:
        info = client.publish(topic_cmd, payload, qos=qos)
        # Wait briefly for network loop to actually send
        info.wait_for_publish(timeout=1.0)
        st.success(f"→ {topic_cmd}: {payload}")
    except Exception as e:
        st.error(f"Publish failed: {e}")

st.write("### Controls")
top = st.columns([1,1,1]); mid = st.columns([1,1,1]); bot = st.columns([1,1,1])
with top[1]:
    if st.button("⬆️ Up (F)"):    publish_cmd("F")
with mid[0]:
    if st.button("⬅️ Left (L)"):  publish_cmd("L")
with mid[1]:
    if st.button("⏹️ Stop (S)"):  publish_cmd("S", 0, 0)
with mid[2]:
    if st.button("➡️ Right (R)"): publish_cmd("R")
with bot[1]:
    if st.button("⬇️ Down (B)"):  publish_cmd("B")

st.caption(f"CMD topic: `{topic_cmd}`  •  STATUS topic: `{topic_status}`  •  Transport: WebSockets")
