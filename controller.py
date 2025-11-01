# controller.py — Streamlit UI for ESP32 car
import requests
import streamlit as st

st.set_page_config(page_title="ESP32 Car Controller", layout="centered")

st.title("ESP32 Car Controller")

# Host: use IP shown in Serial, or mDNS name if supported
host = st.text_input("ESP32 Host (IP or mDNS)", value="esp32car.local")

colA, colB = st.columns([1,1])
with colA:
    speed = st.slider("Speed (0–255)", 0, 255, 160, 1)
with colB:
    ms = st.slider("Duration (ms) (0 = continuous)", 0, 1500, 300, 50)

def call(endpoint, params=None):
    if not host:
        st.error("Enter ESP32 host")
        return
    url = f"http://{host}/{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=2.5)
        st.write(f"→ {r.url}")
        st.success(r.text)
    except Exception as e:
        st.error(f"Request failed: {e}")

# Arrow-style layout
st.write("### Controls")
top = st.columns([1,1,1])
mid = st.columns([1,1,1])
bot = st.columns([1,1,1])

with top[1]:
    if st.button("⬆️ Up"):
        call("move", {"dir": "F", "speed": speed, "ms": ms})

with mid[0]:
    if st.button("⬅️ Left"):
        call("move", {"dir": "L", "speed": speed, "ms": ms})
with mid[1]:
    if st.button("⏹️ Stop"):
        call("stop")
with mid[2]:
    if st.button("➡️ Right"):
        call("move", {"dir": "R", "speed": speed, "ms": ms})

with bot[1]:
    if st.button("⬇️ Down"):
        call("move", {"dir": "B", "speed": speed, "ms": ms})

st.write("---")
if st.button("Get Status"):
    call("status")
