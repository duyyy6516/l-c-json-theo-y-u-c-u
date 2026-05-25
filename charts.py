import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD phong cách tối giản tuyệt đối (Minimalism).
    Đã tích hợp tính năng Phóng to / Thu nhỏ / Di chuyển linh hoạt (Interactive).
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Lấy mốc thời gian và ép kiểu về List Python để tránh lỗi hệ thống trục X
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

    # 1. Đường nét đứt thể hiện ngưỡng tối ưu (Nếu có truyền vào)
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [float(v_min)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [float(v_max)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # 2. Đường đồ thị chính: Màu xanh lục đậm mượt mà
    vpd_line = base.mark_line(
        color='#27AE60', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    # 3. Các chấm tròn giao điểm: Đồng nhất viền xanh ruột trắng tinh tế
    vpd_points = base.mark_point(
        size=60, 
        filled=True, 
        color='#27AE60',
        fill='#FFFFFF',
        strokeWidth=2
    ).encode(
        y=alt.Y('VPD (kPa):Q')
    )

    # Lồng ghép và tối ưu căn lề tiêu đề + Kích hoạt tính năng INTERACTIVE (Phóng to/Thu nhỏ)
    final_chart = alt.layer(vpd_line, vpd_points, *rule_charts).properties(
        title=alt.TitleParams(
            text='📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)',
            subtitle='Đường nét liền biểu thị diễn biến chỉ số VPD thực tế trong ngày (Cuộn chuột để Phóng to/Thu nhỏ)',
            anchor='start',
            offset=15
        ),
        height=320
    ).interactive().configure_title(
        fontSize=14,
        subtitleFontSize=11,
        subtitleColor='#566573',
        dy=-5  # Đẩy khoảng cách chữ lên trên để không bị dính vào đồ thị
    ).configure_view(
        strokeWidth=0
    )
    
    return final_chart


def draw_combined_temp_humidity_chart(df):
    """
    Vẽ biểu đồ tương quan Nhiệt - Ẩm trục kép song song dạng Đường (Line Chart).
    Sửa triệt để lỗi che khuất chữ tiêu đề và kích hoạt zoom tương tác toàn diện.
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

    # LỚP ĐỘ ẨM: Tự động co giãn theo biên độ thực tế
    h_min = float(df['Độ ẩm (%)'].min() - 5)
    h_max = float(df['Độ ẩm (%)'].max() + 5)
    h_min = max(0.0, h_min)
    h_max = min(100.0, h_max)

    humidity_line = base.mark_line(
        color='#3498DB', 
        strokeWidth=3, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ Ẩm Không Khí Tương Đối (%)',
                scale=alt.Scale(domain=[h_min, h_max]),
                axis=alt.Axis(titleColor='#2980B9', orient='right', grid=False))
    )

    humidity_points = base.mark_point(
        color='#3498DB', 
        fill='#FFFFFF', 
        size=40, 
        strokeWidth=1.5
    ).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # LỚP NHIỆT ĐỘ: Đường màu đỏ trục trái
    t_min = float(df['Nhiệt độ (°C)'].min() - 2)
    t_max = float(df['Nhiệt độ (°C)'].max() + 2)

    temp_line = base.mark_line(
        color='#E74C3C', 
        strokeWidth=3,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt Độ Môi Trường (°C)',
                scale=alt.Scale(domain=[t_min, t_max]),
                axis=alt.Axis(titleColor='#C0392B', orient='left', grid=True, gridDash=[2,2], gridColor='#EAEAEA'))
    )

    temp_points = base.mark_point(
        color='#E74C3C', 
        fill='#FFFFFF', 
        size=40, 
        strokeWidth=1.5
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q')
    )

    # Tích hợp trục kép độc lập, gán cấu hình lề tiêu đề an toàn và cho phép Zoom
    final_combined = alt.layer(
        alt.layer(humidity_line, humidity_points),
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        title=alt.TitleParams(
            text='🌡️ ĐỘNG HỌC MÔI TRƯỜNG: MỐI QUAN HỆ NHIỆT - ẨM CHU KỲ',
            subtitle='Đường Đỏ: Nhiệt độ (°C) [Trục trái]  |  Đường Xanh: Độ ẩm (%) [Trục phải] (Cuộn chuột để thu phóng)',
            anchor='start',
            offset=25  # Tăng khoảng cách lề bao quanh để bảo vệ phần chữ tiêu đề trục kép
        ),
        height=260
    ).interactive().configure_title(
        fontSize=14,
        subtitleFontSize=11,
        subtitleColor='#566573',
        dy=-8  # Đẩy hẳn tiêu đề lên trên, tạo không gian thoáng 100% không lo che chữ
    )

    return final_combined
