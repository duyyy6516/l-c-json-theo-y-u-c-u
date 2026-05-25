import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min, v_max):
    """
    Biểu đồ 1: Diễn biến chỉ số VPD trong ngày (image_00029c.png / image_09f6aa.png)
    Đã được tối ưu giao diện, dải màu chuẩn hóa và không bị lỗi Schema.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # 1. Tạo các vùng màu nền Solid theo đúng dải thuật toán của bạn
    # Sử dụng cấu trúc dữ liệu Type 'quantitative' để Altair v6 không báo lỗi
    zone_too_wet = alt.Chart(df).mark_rect(opacity=0.85, color='#206f6e').encode(
        y=alt.Y(datum=0.0, type='quantitative'),
        y2=alt.Y2(datum=0.0)
    )

    v_wet_low = 0.0 if v_min - 0.2 < 0 else v_min - 0.2
    zone_wet = alt.Chart(df).mark_rect(opacity=0.85, color='#37a2c7').encode(
        y=alt.Y(datum=v_wet_low, type='quantitative'),
        y2=alt.Y2(datum=v_min)
    )

    zone_ideal = alt.Chart(df).mark_rect(opacity=0.85, color='#5cc45f').encode(
        y=alt.Y(datum=v_min, type='quantitative'),
        y2=alt.Y2(datum=v_max)
    )

    zone_hot = alt.Chart(df).mark_rect(opacity=0.85, color='#f4a261').encode(
        y=alt.Y(datum=v_max, type='quantitative'),
        y2=alt.Y2(datum=v_max + 0.5)
    )

    zone_too_hot = alt.Chart(df).mark_rect(opacity=0.85, color='#e76f51').encode(
        y=alt.Y(datum=v_max + 0.5, type='quantitative'),
        y2=alt.Y2(datum=2.5)
    )

    # 2. Tạo đường dữ liệu thực tế màu trắng nổi bật
    base_data = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', 
                title='Thời gian chi tiết trong toàn bộ ngày',
                axis=alt.Axis(labelAngle=-90, labelColor='#2C3E50', titleColor='#2C3E50', labelFontSize=11))
    )

    vpd_line = base_data.mark_line(
        color='#FFFFFF', 
        strokeWidth=3, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', 
                title='Chỉ số VPD (kPa)', 
                scale=alt.Scale(domain=[0.0, 2.5]),
                axis=alt.Axis(grid=True, gridDash=[3,3], gridColor='#EAEAEA'))
    )

    vpd_points = base_data.mark_point(
        color='#17202A', 
        fill='#FFFFFF', 
        size=60, 
        strokeWidth=1.5
    ).encode(
        y=alt.Y('VPD (kPa):Q'),
        tooltip=[
            alt.Tooltip('Hiển thị Giờ:O', title='Thời gian'),
            alt.Tooltip('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
            alt.Tooltip('Độ ẩm (%):Q', title='Độ ẩm (%)'),
            alt.Tooltip('VPD (kPa):Q', title='Chỉ số VPD'),
            alt.Tooltip('Trạng thái:N', title='Đánh giá')
        ]
    )

    # Gộp toàn bộ layer lại thành biểu đồ hoàn chỉnh
    combined_chart = alt.layer(
        zone_too_wet, zone_wet, zone_ideal, zone_hot, zone_too_hot,
        vpd_line, vpd_points
    ).properties(
        width='container',
        height=340
    )

    return combined_chart.configure_view(padding=15).configure_axis(domain=False)


def draw_combined_temp_humidity_chart(df):
    """
    Biểu đồ 2: Trục kép lồng ghép Nhiệt độ & Độ ẩm song song (image_09f6ca.png)
    Đã được làm mờ cột ẩm mịn màng và cân bằng màu trục sắc nét.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc chu kỳ thời gian', axis=alt.Axis(labelAngle=-90, labelFontSize=11))
    )

    # Cột độ ẩm màu xanh sky_blue mát mắt, độ mờ nhẹ (opacity=0.4) tránh đè đường nhiệt độ
    humidity_bar = base.mark_bar(
        color='#3498DB', 
        opacity=0.4, 
        size=14
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ ẩm không khí (%)',
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(titleColor='#3498DB', orient='right', grid=False))
    )

    # Đường nhiệt độ màu đỏ Crimson cân bằng, sắc nét
    temp_line = base.mark_line(
        color='#DC143C', 
        strokeWidth=3,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt độ môi trường (°C)',
                scale=alt.Scale(domain=[df['Nhiệt độ (°C)'].min() - 2, df['Nhiệt độ (°C)'].max() + 2]),
                axis=alt.Axis(titleColor='#DC143C', orient='left', grid=True, gridDash=[3,3]))
    )

    temp_points = base.mark_point(
        color='#DC143C', 
        fill='#FFFFFF', 
        size=35
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q'),
        tooltip=[
            alt.Tooltip('Hiển thị Giờ:O', title='Giờ'),
            alt.Tooltip('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
            alt.Tooltip('Độ ẩm (%):Q', title='Độ ẩm (%)')
        ]
    )

    # Kết hợp trục kép độc lập
    dual_axis_chart = alt.layer(
        humidity_bar, 
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        width='container',
        height=220
    )

    return dual_axis_chart.configure_view(padding=15)
