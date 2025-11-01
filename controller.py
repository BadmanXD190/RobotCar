# ESP32 Car Controller (HiveMQ Cloud TLS) — Option B (TLS configured once)
import time
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(page_title="ESP32 Car Controller (HiveMQ Cloud)", layout="centered")
st.title("🚗 ESP32 Car Controller (HiveMQ Cloud)")

# ---------- UI: Connection settings ----------
broker = st.text_input("Broker Host", "e03bf396880b4e10b7a6bbb5f69bdf16.s1.eu.hivemq.cloud")
port = st.number_input("Port", 1, 65535, 8883)
username = st.text_input("Username", "")
password = st.text_input("Password", "", type="password")
device_id = st.text_input("Device ID", "esp32car-01").strip()
qos = st.selectbox("QoS", [0, 1], index=0)

topic_cmd = f"esp32car/{device_id}/cmd"
topic_status = f"esp32car/{device_id}/status"

# ---------- Persistent MQTT client ----------
if "mqtt_client" not in st.session_state:
    c = mqtt.Client(client_id=f"st-{int(time.time())}")
    st.session_state.mqtt_client = c
    st.session_state.connected = False
    st.session_state._tls_inited = False  # custom guard flag

client: mqtt.Client = st.session_state.mqtt_client
conn_msg = st.empty()
status_box = st.empty()
cmd_echo_box = st.empty()

def on_connect(c, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        conn_msg.success(f"✅ Connected to {broker}:{port}")
        # Subscribe to status and command topics (echo)
        c.subscribe(topic_status, qos=qos)
        c.subscribe(topic_cmd, qos=qos)
    else:
        st.session_state.connected = False
        conn_msg.error(f"❌ Connection failed (rc={rc})")

def on_message(c, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    if msg.topic.endswith("/status"):
        status_box.markdown(f"**Status** `{msg.topic}`\n```\n{payload}\n```")
    else:
        cmd_echo_box.markdown(f"**Broker saw command** `{msg.topic}` → `{payload}`")

# Set callbacks once
client.on_connect = on_connect
client.on_message = on_message

def connect():
    try:
        # Guard so TLS is only set once per client instance
        if not st.session_state._tls_inited:
            client.tls_set()                 # enable SSL/TLS
            st.session_state._tls_inited = True

        client.username_pw_set(username, password)
        client.connect(broker, int(port), keepalive=60)
        client.loop_start()
        time.sleep(1)  # allow time for handshake; on_connect will update UI
        if not st.session_state.connected:
            conn_msg.warning("Connecting… click again if needed.")
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

c1, c2 = st.columns(2)
with c1:
    if st.button("Connect MQTT"):
        connect()
with c2:
    if st.button("Disconnect"):
        disconnect()

st.divider()

# ---------- Controls ----------
st.subheader("Controls")
left, right = st.columns(2)
with left:
    speed = st.slider("Speed (0–255)", 0, 255, 160, 1)
with right:
    ms = st.slider("Duration (ms) (0 = continuous)", 0, 2000, 300, 50)

def publish_cmd(cmd, spd=None, dur=None):
    if not st.session_state.connected:
        st.error("MQTT not connected")
        return
    if spd is None: spd = speed
    if dur is None: dur = ms
    payload = f"{cmd},{int(spd)},{int(dur)}" if cmd != "S" else "S"
    try:
        info = client.publish(topic_cmd, payload, qos=qos)
        info.wait_for_publish(timeout=1.0)
        st.success(f"→ {topic_cmd}: `{payload}`")
    except Exception as e:
        st.error(f"Publish failed: {e}")

row1 = st.columns(3)
with row1[1]:
    if st.button("⬆️ Forward"):
        publish_cmd("F")

row2 = st.columns(3)
with row2[0]:
    if st.button("⬅️ Left"):
        publish_cmd("L")
with row2[1]:
    if st.button("⏹️ Stop"):
        publish_cmd("S", 0, 0)
with row2[2]:
    if st.button("➡️ Right"):
        publish_cmd("R")

row3 = st.columns(3)
with row3[1]:
    if st.button("⬇️ Backward"):
        publish_cmd("B")

st.caption(f"CMD topic: `{topic_cmd}`  •  STATUS topic: `{topic_status}`  •  TLS port: {port}")
