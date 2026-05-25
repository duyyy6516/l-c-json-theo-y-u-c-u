import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD trực quan cao cấp, tự động tô nền cảnh báo sinh học.
    Chuẩn hóa 100% kiểu dữ liệu cho Altair v6 trên Python 3.14+.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Thêm cột phân loại vùng sinh học để hiển thị bảng chú giải rõ ràng
    def classify_zone(vpd):
        if vpd >= 2.0: return "🔴 Stress Khô Hạn (>2.0)"
        elif vpd >= 1.6: return "🟠 Nguy cơ Khô (1.6 - 2.0)"
        elif vpd >= 0.8: return "🟢 Ngưỡng Lý Tưởng (0.8 - 1.6)"
        elif vpd >= 0.4: return "🌐 Ngưỡng Ẩm An Toàn (0.4 - 0.8)"
        else: return "🔵 Quá Ẩm - Nguy cơ Nấm (<0.4)"
        
    df['Vùng Sinh Học'] = df['VPD (kPa)'].apply(classify_zone)

    # Lấy mốc thời gian và ép kiểu về List Python thuần (Sửa lỗi Schema)
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

    # Tạo dữ liệu vùng nền trực quan bằng các khoảng tĩnh phẳng độc lập
    zones = pd.DataFrame([
        {"start": 0.0, "end": 0.4, "Color": "#EBF5FB"}, # Quá Ẩm
        {"start": 0.4, "end": 0.8, "Color": "#E8F8F5"}, # Ẩm Nhẹ
        {"start": 0.8, "end": 1.6, "Color": "#EAF2F8"}, # Lý Tưởng
        {"start": 1.6, "end": 2.0, "Color": "#FEF9E7"}, # Khô Nhẹ
        {"start": 2.0, "end": 2.5, "Color": "#FDEDEC"}  # Khô Nguy Hiểm
    ])
    
    background_zones = alt.Chart(zones).mark_rect(opacity=0.6).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5])),
        y2='end:Q',
        color=alt.Color('Color:N', scale=None)
    )

    # Khối vẽ đường nét đứt biểu diễn dải tối ưu của loại cây trồng
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [float(v_min)]})).mark_rule(
            color='#C0392B', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [float(v_max)]})).mark_rule(
            color='#C0392B', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # Vẽ đường chỉ số VPD thực tế của nhà kính
    vpd_line = base.mark_line(
        color='#196F3D', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    # Vẽ các chấm tròn giao điểm dữ liệu đổi màu linh động
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
        ), title="Chú Giải Trạng Thái Khí Khổng")
    )

    final_chart = alt.layer(background_zones, vpd_line, vpd_points, *rule_charts).properties(
        title=alt.TitleParams(
            text='📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)',
            subtitle='Vùng nền màu giúp bạn nhận biết ngay cây có đang ở dải quang hợp tối ưu hay không',
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
    Sửa lỗi Schema bằng cách sử dụng mã màu Hex phẳng nhẹ Thay vì Gradient không tương thích.
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

    # SỬA LỖI CORE: Loại bỏ alt.Gradient phức tạp, thay bằng màu Hex phẳng kết hợp độ trong suốt cao (opacity)
    # Giúp vùng diện tích Độ ẩm trở nên mềm mại, sang trọng giống phong cách ứng dụng iOS/Android chuyên nghiệp
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

    # Đường viền đỉnh nét đứt cho khối độ ẩm để tăng tính thẩm mỹ
    humidity_line = base.mark_line(color='#3498DB', strokeWidth=1.5, strokeDash=[3, 3]).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # Lớp biểu diễn Nhiệt độ: Đường Line đỏ rực gắt nổi bật hẳn lên phía trên lớp nền ẩm
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

    # Giải quyết tích hợp trục kép độc lập
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
