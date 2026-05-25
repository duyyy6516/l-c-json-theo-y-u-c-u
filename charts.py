import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Vẽ biểu đồ VPD phân tách rõ ràng 5 vùng màu đặc, đậm đà (Solid Deep Colors):
    - [0.0 -> vpd_min - 0.2]: 🔵 Quá Ẩm -> Xanh Dương Đậm (Ocean Blue)
    - [vpd_min - 0.2 -> vpd_min]: 🌐 Ẩm -> Xanh Da Trời Rõ (Sky Blue)
    - [vpd_min -> vpd_max]: 🟩 Lý Tưởng -> Xanh Lá Cây Đậm (Pure Green)
    - [vpd_max -> vpd_max + 0.5]: 💛 Nóng -> Vàng Nghệ/Vàng Đậm (Amber Yellow)
    - [vpd_max + 0.5 -> 3.0]: 🔴 Quá Nóng -> Đỏ Cờ Báo Động (Signal Red)
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    # Định nghĩa dữ liệu 5 vùng màu nền
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Vùng": "🔵 Quá Ẩm (Xanh Đậm)", "color": "#0B5345"},      # Xanh biển sâu/Xanh đậm rành mạch
        {"start": wet_limit, "end": vpd_min, "Vùng": "🌐 Ẩm (Xanh Nhạt)", "color": "#2980B9"},       # Xanh dương rực rỡ
        {"start": vpd_min, "end": vpd_max, "Vùng": "🟩 Lý Tưởng (Xanh Lá)", "color": "#27AE60"},     # Xanh lá cây chuẩn
        {"start": vpd_max, "end": hot_limit, "Vùng": "💛 Nóng (Vàng)", "color": "#F39C12"},          # Vàng nghệ đậm
        {"start": hot_limit, "end": 3.0, "Vùng": "🔴 Quá Nóng (Đỏ)", "color": "#C0392B"}            # Đỏ cờ đậm rực
    ])

    # Khóa độ đậm của nền ở mức tối đa opacity=1.0 để màu sắc đập thẳng vào mắt, không bị mờ
    background = alt.Chart(zones).mark_rect(opacity=1.0).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Vùng:N', 
                        scale=alt.Scale(
                            domain=["🔵 Quá Ẩm (Xanh Đậm)", "🌐 Ẩm (Xanh Nhạt)", "🟩 Lý Tưởng (Xanh Lá)", "💛 Nóng (Vàng)", "🔴 Quá Nóng (Đỏ)"],
                            range=["#0B5345", "#2980B9", "#27AE60", "#F39C12", "#C0392B"]
                        ),
                        legend=alt.Legend(
                            title="Phân Vùng Khí Hậu", 
                            orient="top",
                            direction="horizontal",
                            labelFontSize=11,
                            titleFontSize=12
                        ))
    )

    # Các đường giới hạn nét đứt màu đen đậm để cắt phân khu rõ hơn
    rules_data = pd.DataFrame([{"y": wet_limit}, {"y": vpd_min}, {"y": vpd_max}, {"y": hot_limit}])
    rules = alt.Chart(rules_data).mark_rule(stroke="#17202A", strokeDash=[4, 3], strokeWidth=1.5).encode(y='y:Q')

    # Dùng đường màu TRẮNG NGUYÊN BẢN (#FFFFFF) để làm nổi bật dữ liệu trên nền các khối màu đậm
    line = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(color="#FFFFFF", size=60, filled=True, stroke="#17202A", strokeWidth=1.5), 
        color="#FFFFFF", 
        strokeWidth=3.5
    ).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Mốc thời gian quét dữ liệu"),
        y=alt.Y('VPD (kPa):Q'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    chart = alt.layer(background, rules, line).properties(
        height=390,
        title=alt.TitleParams(
            text="MA TRẬN ĐỐI CHIẾU 5 VÙNG SINH HỌC VPD",
            subtitle=f"Cận dưới: {vpd_min} kPa | Cận trên: {vpd_max} kPa | Ngưỡng quá nóng: {hot_limit} kPa",
            anchor="start",
            fontSize=15,
            font="Segoe UI",
            subtitleColor="#2C3E50"
        )
    ).configure_axis(
        grid=False,
        labelFont="Segoe UI",
        titleFont="Segoe UI",
        labelColor="#17202A",
        titleColor="#17202A",
        labelFontSize=11,
        titleFontSize=12
    ).configure_view(
        strokeWidth=0
    )

    return chart

def draw_temperature_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#E74C3C", strokeWidth=3).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Nhiệt độ (°C):Q', title="Nhiệt độ (°C)"),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=260).configure_view(strokeWidth=0)

def draw_humidity_chart(df):
    return alt.Chart(df).mark_line(point=True, color="#3498DB", strokeWidth=3).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian"),
        y=alt.Y('Độ ẩm (%):Q', title="Độ ẩm (%)"),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=260).configure_view(strokeWidth=0)
