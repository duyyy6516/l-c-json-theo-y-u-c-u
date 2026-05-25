import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD phong cách tối giản (Minimalism).
    Đã bỏ hoàn toàn các khối màu nền phân chia phân vùng theo yêu cầu.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Thêm cột phân loại vùng sinh học để làm màu cho các điểm Node chấm tròn (không làm rối nền)
    def classify_zone(vpd):
        if vpd >= 2.0: return "🔴 Stress Khô Hạn (>2.0)"
        elif vpd >= 1.6: return "🟠 Nguy cơ Khô (1.6 - 2.0)"
        elif vpd >= 0.8: return "🟢 Ngưỡng Lý Tưởng (0.8 - 1.6)"
        elif vpd >= 0.4: return "🌐 Ngưỡng Ẩm An Toàn (0.4 - 0.8)"
        else: return "🔵 Quá Ẩm - Nguy cơ Nấm (<0.4)"
        
    df['Vùng Sinh Học'] = df['VPD (kPa)'].apply(classify_zone)

    # Lấy mốc thời gian và ép kiểu về List Python thuần để tránh lỗi hệ thống
    unique_hours = df['Hiển thị Giờ'].unique()
    if len(unique_hours) > 15:
        axis_values = list(unique_hours[::2])
    else:
        axis_values = list(unique_hours)

    x_axis_config = alt.Axis(
        labelAngle=-45, 
        labelColor='#2C3E50', 
        titleColor='#114B72', 
        labelFontSize=10,
        titleFontSize=12,
        titlePadding=10,
        values=axis_values
    )

    # Khởi tạo biểu đồ nền trắng sạch sẽ
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc Thời Gian Trong Ngày', axis=x_axis_config)
    )

    # 1. Đường nét đứt động thể hiện ngưỡng tối ưu cố định của loại cây (Nếu có)
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [float(v_min)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [float(v_max)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # 2. ĐƯỜNG ĐỒ THỊ CHÍNH: Đường line màu xanh lục đậm nét, mượt mà chạy trên nền trắng
    vpd_line = base.mark_line(
        color='#27AE60', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    # 3. ĐIỂM CHẤM TRÒN: Đổi màu theo trạng thái để người xem nhìn phát biết ngay lúc nào cây gặp sự cố
    vpd_points = base.mark_point(
        size=80, 
        filled=True, 
        stroke='#2C3E50', 
        strokeWidth=1
    ).encode(
        y=alt.Y('VPD (kPa):Q'),
        color=alt.Color('Vùng Sinh Học:N', scale=alt.Scale(
            domain=[
                "🔴 Stress Khô Hạn (>2.0)", 
                "🟠 Nguy cơ Khô (1.6 - 2.0)", 
                "🟢 Ngưỡng Lý Tưởng (0.8 - 1.6)", 
                "🌐 Ngưỡng Ẩm An Toàn (0.4 - 0.8)", 
                "🔵 Quá Ẩm - Nguy cơ Nấm (<0.4)"
            ],
            range=['#C0392B', '#E67E22', '#27AE60', '#2980B9', '#1A5276']
        ), title="Trạng Thái Sinh Học")
    )

    # Lồng ghép các thành phần
    final_chart = alt.layer(vpd_line, vpd_points, *rule_charts).properties(
        title=alt.TitleParams(
            text='📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)',
            subtitle='Đường nét liền biểu thị diễn biến VPD thực tế trong nhà màng',
            anchor='start',
            fontSize=14,
            subtitleFontSize=11,
            subtitleColor='#566573',
            offset=15
        ),
        height=320
    ).configure_view(
        strokeWidth=0
    )
    
    return final_chart


def draw_combined_temp_humidity_chart(df):
    """
    Vẽ biểu đồ động học môi trường trục kép tương quan giữa Nhiệt độ và Độ ẩm.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    unique_hours = df['Hiển thị Giờ'].unique()
    if len(unique_hours) > 15:
        axis_values = list(unique_hours[::2])
    else:
        axis_values = list(unique_hours)

    x_axis_config = alt.Axis(
        labelAngle=-45, 
        labelColor='#2C3E50', 
        titleColor='#114B72', 
        labelFontSize=10,
        titleFontSize=12,
        titlePadding=10,
        values=axis_values
    )

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc Thời Gian Trong Ngày', axis=x_axis_config)
    )

    # Khối độ ẩm: Diện tích mờ màu xanh dương phẳng thoáng đãng
    humidity_area = base.mark_area(
        color='#AED6F1',
        opacity=0.45,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ Ẩm Không Khí Tương Đối (%)',
                scale=alt.Scale(domain=[20, 100]),
                axis=alt.Axis(titleColor='#2980B9', orient='right', grid=False))
    )

    humidity_line = base.mark_line(color='#3498DB', strokeWidth=1.5, strokeDash=[3, 3]).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # Khối nhiệt độ: Đường Line đỏ rực rỡ chạy đè lên trên lớp ẩm
    temp_line = base.mark_line(
        color='#E74C3C', 
        strokeWidth=3.5,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt Độ Môi Trường (°C)',
                scale=alt.Scale(domain=[float(df['Nhiệt độ (°C)'].min() - 3), float(df['Nhiệt độ (°C)'].max() + 3)]),
                axis=alt.Axis(titleColor='#C0392B', orient='left', grid=True, gridDash=[2,2], gridColor='#EAEAEA'))
    )

    temp_points = base.mark_point(
        color='#E74C3C', 
        fill='#FFFFFF', 
        size=50, 
        strokeWidth=2
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q')
    )

    final_combined = alt.layer(
        humidity_area, 
        humidity_line,
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        title=alt.TitleParams(
            text='🌡️ ĐỘNG HỌC MÔI TRƯỜNG: MỐI QUAN HỆ NHIỆT - ẨM CHU KỲ',
            subtitle='Màu đỏ đại diện cho Nhiệt độ (°C), Vùng màu xanh dương nhạt đại diện cho Độ ẩm (%)',
            anchor='start',
            fontSize=14,
            subtitleFontSize=11,
            subtitleColor='#566573',
            offset=15
        ),
        height=260
    )

    return final_combined
