import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Vẽ biểu đồ VPD có chia 5 phân vùng màu nền sinh học theo yêu cầu:
    - [0 -> vpd_min - 0.2]: Màu Quá ẩm (Xanh đậm)
    - [vpd_min - 0.2 -> vpd_min]: Màu Ẩm (Xanh lục nhạt)
    - [vpd_min -> vpd_max]: Màu Lý tưởng (Xanh lá)
    - [vpd_max -> vpd_max + 0.5]: Màu Nóng (Màu Cam)
    - [vpd_max + 0.5 -> 3.0]: Màu Quá Nóng (Đỏ rực)
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Vùng": "💙 Quá Ẩm (Too Wet)", "color": "#BBDEFB"},
        {"start": wet_limit, "end": vpd_min, "Vùng": "🔵 Ẩm (Wet)", "color": "#E8F5E9"},
        {"start": vpd_min, "end": vpd_max, "Vùng": "🟩 Lý Tưởng (Ideal)", "color": "#C8E6C9"},
        {"start": vpd_max, "end": hot_limit, "Vùng": "🟠 Nóng (Hot)", "color": "#FFE0B2"},
        {"start": hot_limit, "end": 3.0, "Vùng": "🔴 Quá Nóng (Danger)", "color": "#FFCDD2"}
    ])

    background = alt.Chart(zones).mark_rect(opacity=0.55).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 3.0]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Vùng:N', 
                        scale=alt.Scale(
                            domain=["💙 Quá Ẩm (Too Wet)", "🔵 Ẩm (Wet)", "🟩 Lý Tưởng (Ideal)", "🟠 Nóng (Hot)", "🔴 Quá Nóng (Danger)"],
                            range=["#BBDEFB", "#E6EE9C", "#C8E6C9", "#FFE0B2", "#FFCDD2"]
                        ),
                        legend=alt.Legend(title="Phân vùng Ma Trận Màu", orient="top"))
    )

    line = alt.Chart(df).mark_line(point=True, color="#2E7D32", strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('VPD (kPa):Q'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    rules_data = pd.DataFrame([
        {"y": vpd_min, "label": "Cận dưới ẩm", "color": "#1E88E5"},
        {"y": vpd_max, "label": "Cận trên nóng", "color": "#FB8C00"},
        {"y": hot_limit, "label": "Ngưỡng đỏ rực", "color": "#E53935"}
    ])
    
    rules = alt.Chart(rules_data).mark_rule(strokeDash=[4, 4], strokeWidth=1.5).encode(
        y='y:Q',
        color=alt.Color('color:N', scale=None)
    )

    chart = alt.layer(background, rules, line).properties(
        height=380,
        title=alt.TitleParams(
            text="Biểu đồ Phân Tích Ma Trận VPD Sinh Học Đa Vùng",
            subtitle=f"Cam Nóng (> {vpd_max} kPa) | Đỏ Rực Quá Nóng (> {hot_limit} kPa)",
            anchor="start"
        )
    ).configure_axis(
        grid=False
    )

    return chart

def draw_temperature_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#FF4B4B").encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Nhiệt độ (°C):Q', title="Nhiệt độ (°C)"),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=300)

def draw_humidity_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#0068C9").encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Độ ẩm (%):Q', title="Độ ẩm (%)"),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=300)
