import altair as alt
import pandas as pd

def draw_temperature_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_text()
        
    chart = alt.Chart(df).mark_line(color="#FF4B4B", point=True).encode(
        x=alt.X('Hiển thị Giờ:N', title="Mốc thời gian", sort=None), # Chuyển từ :O sang :N giúp giãn khoảng cách
        y=alt.Y("Nhiệt độ (°C):Q", scale=alt.Scale(zero=False), title="Nhiệt độ (°C)"),
        tooltip=['Ngày', 'Hiển thị Giờ', "Nhiệt độ (°C)"]
    ).properties(height=250).interactive().configure_axisX(
        labelAngle=-45,
        labelOverlap="greedy",  # Tự động ẩn bớt chữ nếu mốc thời gian trong file quá dày
        labelPadding=8
    ).configure_view(
        strokeOpacity=0       # Loại bỏ khung viền giúp biểu đồ thoáng hơn
    )
    return chart

def draw_humidity_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_text()
        
    chart = alt.Chart(df).mark_line(color="#0068C9", point=True).encode(
        x=alt.X('Hiển thị Giờ:N', title="Mốc thời gian", sort=None),
        y=alt.Y("Độ ẩm (%):Q", scale=alt.Scale(zero=False), title="Độ ẩm (%)"),
        tooltip=['Ngày', 'Hiển thị Giờ', "Độ ẩm (%)"]
    ).properties(height=250).interactive().configure_axisX(
        labelAngle=-45,
        labelOverlap="greedy",
        labelPadding=8
    ).configure_view(
        strokeOpacity=0
    )
    return chart

def draw_vpd_chart(df, vpd_min, vpd_max):
    if len(df) == 0:
        return alt.Chart(df).mark_blank()
        
    try:
        actual_
