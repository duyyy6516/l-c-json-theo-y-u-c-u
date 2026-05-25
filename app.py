# app.py
import streamlit as st
from ui_tab1 import render_tab1
from ui_tab2 import render_tab2

st.set_page_config(page_title="VPD Farm System", layout="wide")

# CSS chung
st.markdown("""<style> .stTabs [data-baseweb="tab-list"] { gap: 24px; } </style>""", unsafe_allow_html=True)

st.title("🌿 Hệ thống Quản trị Nhà kính Đà Lạt")

tab1, tab2 = st.tabs(["🔮 TRẠM ĐIỀU HÀNH", "📁 LỊCH SỬ DỮ LIỆU"])

with tab1:
    render_tab1()
with tab2:
    render_tab2()
