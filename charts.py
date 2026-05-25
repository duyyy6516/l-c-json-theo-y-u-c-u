import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    """
    Biểu đồ VPD liền mạch 1 trục thời gian duy nhất.
    Có các đường nét đứt dọc phân chia ranh giới Sáng - Trưa - Chiều - Tối - Khuya kèm nhãn chữ.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu đồ thị")

    df_chart = df.copy()

    # 1. ĐỊNH NGHĨA CÁC VÙNG CẢNH BÁO MÀU NỀN NGANG (Trục Y)
    wet_limit = max(0.0, vpd_min - 0.2)
    hot_limit = vpd_max + 0.5
    
    zones = pd.DataFrame([
        {"start": 0.0, "end": wet_limit, "Trạng thái": "🔵 Quá Ẩm"},      
        {"start": wet_limit, "end": vpd_min, "Trạng thái": "🌐 Ẩm"},       
        {"start": vpd_min, "end": vpd_max, "Trạng thái": "🟩 Lý Tưởng"},     
        {"start": vpd_max, "end": hot_limit, "Trạng thái": "💛 Nóng"},          
        {"start": hot_limit, "end": 2.5, "Trạng thái": "🔴 Quá Nóng"}            
    ])

    background = alt.Chart(zones).mark_rect(opacity=1.0).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5]), title="Chỉ số VPD (kPa)"),
        y2='end:Q',
        color=alt.Color('Trạng thái:N', 
                        scale=alt.Scale(
                            domain=["🔵 Quá Ẩm", "🌐 Ẩm", "🟩 Lý Tưởng", "💛 Nóng", "🔴 Quá Nóng"],
                            range=["#0B5345", "#2980B9", "#27AE60", "#F39C12", "#C0392B"]
                        ),
                        legend=alt.Legend(title="Màu Cảnh Báo", orient="top", direction="horizontal"))
    )

    horiz_rules_data = pd.DataFrame([{"y": wet_limit}, {"y": vpd_min}, {"y": vpd_max}, {"y": hot_limit}])
    horiz_rules = alt.Chart(horiz_rules_data).mark_rule(stroke="#17202A", strokeDash=[4, 3], strokeWidth=1.2).encode(y='y:Q')

    # 2. ĐƯỜNG NÉT ĐỨT DỌC PHÂN CHIA CÁC BUỔI TRÊN TRỤC X
    time_lines = pd.DataFrame([
        {"Giờ": "05:00", "Nhãn": "🌅 SÁNG (5h)"},
        {"Giờ": "10:00", "Nhãn": "☀️ TRƯA (10h)"},
        {"Giờ": "15:00", "Nhãn": "🌇 CHIỀU (15h)"},
        {"Giờ": "19:00", "Nhãn": "🌌 TỐI (19h)"},
        {"Giờ": "23:00", "Nhãn": "🌙 KHUYA (23h)"}
    ])
    
    existing_hours = df_chart['Hiển thị Giờ'].unique()
    time_lines_filtered = time_lines[time_lines['Giờ'].isin(existing_hours)].copy()

    vert_rules = alt.Chart(time_lines_filtered).mark_rule(
        stroke="#2C3E50", 
        strokeDash=[6, 4], 
        strokeWidth=2.0
    ).encode(
        x=alt.X('Giờ:N', sort=None)
    )

    vert_texts = alt.Chart(time_lines_filtered).mark_text(
        align='left',
        dx=5,
        dy=-175, 
        fontSize=11,
        fontWeight='bold',
        color='#17202A',
        angle=0
    ).encode(
        x=alt.X('Giờ:N', sort=None),
        text='Nhãn:N'
    )

    # 3. ĐƯỜNG TUYẾN TÍNH LIỀN MẠCH VPD
    line = alt.Chart(df_chart).mark_line(
        point=alt.OverlayMarkDef(color="#FFFFFF", size=65, filled=True, stroke="#17202A", strokeWidth=1.5), 
        color="#FFFFFF", 
        strokeWidth=4.0
    ).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian chi tiết trong toàn bộ ngày"),
        y=alt.Y('VPD (kPa):Q'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )

    final_chart = alt.layer(background, horiz_rules, vert_rules, vert_texts, line, data=df_chart).properties(
        width=850, 
        height=390,
        title=alt.TitleParams(
            text="BIỂU ĐỒ CHỈ SỐ VPD LIỀN MẠCH THEO CHU KỲ SINH HỌC TOÀN NGÀY",
            subtitle=f"Cận dưới: {vpd_min} kPa | Cận trên: {vpd_max} kPa | Khóa dải màu Solid đậm | Vạch đứng phân buổi",
            anchor="start",
            fontSize=16,
            font="Segoe UI",
            subtitleColor="#2C3E50"
        )
    ).configure_axis(
        grid=False,
        labelColor="#17202A",
        titleColor="#17202A",
        labelFontSize=11,
        titleFontSize=12
    ).configure_view(
        strokeWidth=1,
        stroke="#BDC3C7" 
    )

    return final_chart

def draw_combined_temp_humidity_chart(df):
    """
    Biểu đồ lồng nhau (Dual Axes): 
    - Trục Y bên trái: Nhiệt độ (°C) - Màu đỏ thẫm rực rỡ
    - Trục Y bên phải: Độ ẩm (%) - Màu xanh dương dịu mát
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Chưa có dữ liệu")

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title="Thời gian")
    )

    # Lớp 1: Đường Nhiệt độ (Trục Y bên trái)
    temp_line = base.mark_line(
        point=alt.OverlayMarkDef(color="#E74C3C", size=40, filled=True),
        color="#E74C3C", 
        strokeWidth=3
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='🌡️ Nhiệt độ khí (°C)',
                axis=alt.Axis(titleColor='#E74C3C', labelColor='#E74C3C')),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    )

    # Lớp 2: Đường Độ ẩm (Trục Y bên phải độc lập)
    humidity_line = base.mark_line(
        point=alt.OverlayMarkDef(color="#3498DB", size=40, filled=True),
        color="#3498DB", 
        strokeWidth=3
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='💧 Độ ẩm khí (%)',
                axis=alt.Axis(titleColor='#3498DB', labelColor='#3498DB'),
                scale=alt.Scale(domain=[0, 100])),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    )

    # Gộp 2 trục Y nằm lồng nhau trên cùng 1 biểu đồ trục X
    combined = alt.layer(temp_line, humidity_line).resolve_scale(
        y='independent'
    ).properties(
        width=850,
        height=260,
        title=alt.TitleParams(
            text="BIỂU ĐỒ ĐỐI CHIẾU SONG SONG GIỮA NHIỆT ĐỘ & ĐỘ ẨM KHÔNG KHÍ",
            anchor="start",
            fontSize=13,
            fontWeight='bold',
            color='#2C3E50'
        )
    ).configure_view(
        strokeWidth=1,
        stroke="#BDC3C7"
    )

    return combined
