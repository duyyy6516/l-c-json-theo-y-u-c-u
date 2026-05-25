import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD phong cách tối giản tuyệt đối (Minimalism).
    Đã lược bỏ phần text tiêu đề phức tạp để tránh lỗi biên dịch Altair.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Tạo bản sao dữ liệu và cấu hình trục X dạng thời gian chuẩn để cuộn zoom tự do
    df_chart = df.copy()
    df_chart['Thời Gian Chuẩn'] = pd.to_datetime(df_chart['Hiển thị Giờ'], format='%H:%M', errors='coerce')
    df_chart = df_chart.dropna(subset=['Thời Gian Chuẩn']).sort_values('Thời Gian Chuẩn')

    base = alt.Chart(df_chart).encode(
        x=alt.X('Thời Gian Chuẩn:T', 
                title='Mốc Thời Gian Trong Ngày', 
                axis=alt.Axis(format='%H:%M', labelAngle=-45, labelColor='#2C3E50', titleColor='#114B72'))
    )

    # Ngưỡng tối ưu nét đứt (Nếu có)
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [float(v_min)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [float(v_max)]})).mark_rule(
            color='#7F8C8D', strokeWidth=1.2, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # Đường chỉ số VPD chính màu xanh lục
    vpd_line = base.mark_line(color='#27AE60', strokeWidth=3.5, interpolate='monotone').encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    vpd_points = base.mark_point(size=60, filled=True, color='#27AE60', fill='#FFFFFF', strokeWidth=2).encode(
        y=alt.Y('VPD (kPa):Q')
    )

    final_chart = alt.layer(vpd_line, vpd_points, *rule_charts).properties(
        height=320
    ).interactive().configure_view(
        strokeWidth=0
    )
    
    return final_chart


def draw_combined_temp_humidity_chart(df):
    """
    Vẽ biểu đồ tương quan Nhiệt - Ẩm trục kép dạng Đường (Line Chart).
    Tối ưu hóa gọn gàng trục Y độc lập, hỗ trợ thu phóng cuộn chuột.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Tạo bản sao dữ liệu và cấu hình trục X dạng thời gian chuẩn
    df_chart = df.copy()
    df_chart['Thời Gian Chuẩn'] = pd.to_datetime(df_chart['Hiển thị Giờ'], format='%H:%M', errors='coerce')
    df_chart = df_chart.dropna(subset=['Thời Gian Chuẩn']).sort_values('Thời Gian Chuẩn')

    base = alt.Chart(df_chart).encode(
        x=alt.X('Thời Gian Chuẩn:T', 
                title='Mốc Thời Gian Trong Ngày', 
                axis=alt.Axis(format='%H:%M', labelAngle=-45, labelColor='#2C3E50', titleColor='#114B72'))
    )

    # Cấu hình tự động co giãn trục Độ ẩm (%) độc lập
    h_min = max(0.0, float(df_chart['Độ ẩm (%)'].min() - 5))
    h_max = min(100.0, float(df_chart['Độ ẩm (%)'].max() + 5))

    humidity_line = base.mark_line(color='#3498DB', strokeWidth=3, interpolate='monotone').encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ Ẩm Không Khí Tương Đối (%)',
                scale=alt.Scale(domain=[h_min, h_max]),
                axis=alt.Axis(titleColor='#2980B9', orient='right', grid=False))
    )

    humidity_points = base.mark_point(color='#3498DB', fill='#FFFFFF', size=40, strokeWidth=1.5).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # Cấu hình tự động co giãn trục Nhiệt độ (°C) độc lập
    t_min = float(df_chart['Nhiệt độ (°C)'].min() - 2)
    t_max = float(df_chart['Nhiệt độ (°C)'].max() + 2)

    temp_line = base.mark_line(color='#E74C3C', strokeWidth=3, interpolate='monotone').encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt Độ Môi Trường (°C)',
                scale=alt.Scale(domain=[t_min, t_max]),
                axis=alt.Axis(titleColor='#C0392B', orient='left', grid=True, gridDash=[2,2], gridColor='#EAEAEA'))
    )

    temp_points = base.mark_point(color='#E74C3C', fill='#FFFFFF', size=40, strokeWidth=1.5).encode(
        y=alt.Y('Nhiệt độ (°C):Q')
    )

    # Hợp nhất trục độc lập và bật tính năng tương tác thu phóng
    final_combined = alt.layer(
        alt.layer(humidity_line, humidity_points),
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        height=280
    ).interactive().configure_view(
        strokeWidth=0
    )

    return final_combined
