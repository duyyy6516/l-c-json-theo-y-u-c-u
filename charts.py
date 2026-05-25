import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD phong cách tối giản tuyệt đối (Minimalism).
    Sửa tận gốc lỗi TypeError bằng cách cấu hình view ở lớp ngoài cùng của vconcat.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Tạo bản sao dữ liệu và cấu hình trục X dạng thời gian chuẩn để cuộn zoom tự do
    df_chart = df.copy()
    df_chart['Thời Gian Chuẩn'] = pd.to_datetime(df_chart['Hiển thị Giờ'], format='%H:%M', errors='coerce')
    df_chart = df_chart.dropna(subset=['Thời Gian Chuẩn']).sort_values('Thời Gian Chuẩn')

    # 1. TẠO TIÊU ĐỀ ĐỘC LẬP: Đảm bảo hiển thị FULL 100% chữ, đứng riêng ở tầng trên
    title_text = alt.Chart(pd.DataFrame([{}])).mark_text(
        text='📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)',
        dx=0, dy=0, fontSize=14, fontWeight='bold', color='#2C3E50', align='left'
    ).properties(width='container', height=15)

    subtitle_text = alt.Chart(pd.DataFrame([{}])).mark_text(
        text='Cuộn chuột để phóng to/thu nhỏ, nhấn giữ chuột trái kéo qua lại để xem chi tiết',
        dx=0, dy=0, fontSize=11, color='#566573', align='left'
    ).properties(width='container', height=15)

    # 2. XÂY DỰNG THÂN ĐỒ THỊ THÔ (Chưa cấu hình view để không gây lỗi vconcat)
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

    body_chart = alt.layer(vpd_line, vpd_points, *rule_charts).properties(
        height=300
    ).interactive()

    # 3. GỘP BIỂU ĐỒ VÀ TIÊU ĐỀ, SAU ĐÓ MỚI CẤU HÌNH VIEW NGOÀI CÙNG (Sửa lỗi hoàn toàn)
    final_chart = alt.vconcat(title_text, subtitle_text, body_chart).spacing(5).configure_view(
        strokeWidth=0
    )
    return final_chart


def draw_combined_temp_humidity_chart(df):
    """
    Vẽ biểu đồ tương quan Nhiệt - Ẩm trục kép dạng Đường (Line Chart).
    Giải quyết triệt để lỗi ăn mất tiêu đề và tương thích tuyệt đối với Altair v6.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Tạo bản sao dữ liệu và cấu hình trục X dạng thời gian chuẩn
    df_chart = df.copy()
    df_chart['Thời Gian Chuẩn'] = pd.to_datetime(df_chart['Hiển thị Giờ'], format='%H:%M', errors='coerce')
    df_chart = df_chart.dropna(subset=['Thời Gian Chuẩn']).sort_values('Thời Gian Chuẩn')

    # 1. TẠO TIÊU ĐỀ ĐỘC LẬP: Hiển thị trọn vẹn 100% không lo bị nuốt chữ
    title_text = alt.Chart(pd.DataFrame([{}])).mark_text(
        text='🌡️ ĐỘNG HỌC MÔI TRƯỜNG: MỐI QUAN HỆ NHIỆT - ẨM CHU KỲ',
        dx=0, dy=0, fontSize=14, fontWeight='bold', color='#2C3E50', align='left'
    ).properties(width='container', height=15)

    subtitle_text = alt.Chart(pd.DataFrame([{}])).mark_text(
        text='Đường Đỏ: Nhiệt độ (°C) [Trục trái]  |  Đường Xanh: Độ ẩm (%) [Trục phải] (Cuộn chuột để thu phóng)',
        dx=0, dy=0, fontSize=11, color='#566573', align='left'
    ).properties(width='container', height=15)

    # 2. XÂY DỰNG THÂN ĐỒ THỊ TRỤC KÉP THÔ
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
    body_chart = alt.layer(
        alt.layer(humidity_line, humidity_points),
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        height=260
    ).interactive()

    # 3. KẾT HỢP VÀ ĐỂ HÀM CẤU HÌNH GIAO DIỆN Ở NGOÀI CÙNG
    final_combined = alt.vconcat(title_text, subtitle_text, body_chart).spacing(5).configure_view(
        strokeWidth=0
    )
    return final_combined
