import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD trực quan cao cấp, tự động tô nền cảnh báo sinh học.
    Đã sửa lỗi SchemaValidationError bằng cách ép kiểu sang List Python thuần.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Thêm cột dải màu trực quan cho từng điểm dữ liệu để vẽ bảng chú giải (Legend)
    def classify_zone(vpd):
        if vpd >= 2.0: return "🔴 Stress Khô Hạn (>2.0)"
        elif vpd >= 1.6: return "🟠 Nguy cơ Khô (1.6 - 2.0)"
        elif vpd >= 0.8: return "🟢 Ngưỡng Lý Tưởng (0.8 - 1.6)"
        elif vpd >= 0.4: return "🌐 Ngưỡng Ẩm An Toàn (0.4 - 0.8)"
        else: return "🔵 Quá Ẩm - Nguy cơ Nấm (<0.4)"
        
    df['Vùng Sinh Học'] = df['VPD (kPa)'].apply(classify_zone)

    # Lấy danh sách nhãn thời gian độc nhất
    unique_hours = df['Hiển thị Giờ'].unique()
    
    # SỬA LỖI CORE: Ép lát cắt NumPy Array sang List Python thuần bằng hàm list()
    if len(unique_hours) > 15:
        axis_values = list(unique_hours[::2])
    else:
        axis_values = list(unique_hours)

    # Cấu hình trục X an toàn
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

    # Định nghĩa các vùng màu nền đại diện cho sức khỏe cây trồng
    zones = pd.DataFrame([
        {"start": 0.0, "end": 0.4, "Color": "#EBF5FB"}, # Quá Ẩm
        {"start": 0.4, "end": 0.8, "Color": "#E8F8F5"}, # Ẩm Nhẹ
        {"start": 0.8, "end": 1.6, "Color": "#EAF2F8"}, # Lý Tưởng
        {"start": 1.6, "end": 2.0, "Color": "#FEF9E7"}, # Khô Nhẹ
        {"start": 2.0, "end": 2.5, "Color": "#FDEDEC"}  # Khô Nguy Hiểm
    ])
    
    # Vẽ các khối nền màu chỉ dẫn sinh học
    background_zones = alt.Chart(zones).mark_rect(opacity=0.6).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5])),
        y2='end:Q',
        color=alt.Color('Color:N', scale=None)
    )

    # Đường nét đứt động thể hiện dải tối ưu của loại cây đang chọn (Nếu có truyền vào)
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [float(v_min)]})).mark_rule(
            color='#C0392B', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [float(v_max)]})).mark_rule(
            color='#C0392B', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # Đường đồ thị chính của chỉ số VPD thực tế
    vpd_line = base.mark_line(
        color='#196F3D', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    # Các node chấm đổi màu linh động theo trạng thái thực tế giúp dễ quan sát
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

    # Lồng ghép các lớp đồ thị
    final_chart = alt.layer(background_zones, vpd_line, vpd_points, *rule_charts).properties(
        title=alt.TitleParams(
            text='📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)',
            subtitle='Vùng xanh lá là điều kiện hoàn hảo giúp cây mở khí khổng và hút phân bón mạnh nhất',
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
    Vẽ biểu đồ tương quan động học giữa Nhiệt độ (Line) và Độ ẩm (Area).
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

    # Lớp độ ẩm: Dạng Vùng diện tích Gradient mờ (Area)
    humidity_area = base.mark_area(
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='#AED6F1', offset=0),
                   alt.GradientStop(color='#FFFFFF', offset=1)],
            orientation='vertical'
        ),
        opacity=0.5
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ Ẩm Không Khí Tương Đối (%)',
                scale=alt.Scale(domain=[20, 100]),
                axis=alt.Axis(titleColor='#2980B9', orient='right', grid=False))
    )

    humidity_line = base.mark_line(color='#3498DB', strokeWidth=1.5, strokeDash=[2, 2]).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # Lớp nhiệt độ: Đường Line đỏ rực đi kèm Node trắng viền đỏ
    temp_line = base.mark_line(
        color='#E74C3C', 
        strokeWidth=3.5,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt Độ Môi Trường (°C)',
                scale=alt.Scale(domain=[float(df['Nhiệt độ (°C)'].min() - 3), float(df['Nhiệt độ (°C)'].max() + 3)]),
                axis=alt.Axis(titleColor='#C0392B', orient='left', grid=True, gridDash=[2,2]))
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
            subtitle='Nhìn xu hướng giao thoa: Khi Nhiệt độ (Đường Đỏ) đạt đỉnh thì Độ ẩm (Nền Xanh) sẽ tụt xuống thấp nhất',
            anchor='start',
            fontSize=14,
            subtitleFontSize=11,
            subtitleColor='#566573',
            offset=15
        ),
        height=260
    )

    return final_combined
