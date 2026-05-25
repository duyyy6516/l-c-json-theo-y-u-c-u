import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min=None, v_max=None):
    """
    Vẽ đường diễn biến VPD trực quan cao cấp.
    Tự động tô màu nền theo các ngưỡng giúp người xem biết ngay lúc nào cây đang AN TOÀN hay STRESS.
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

    # Trục X: Giới hạn số lượng nhãn hiển thị nếu dữ liệu quá dày để tránh đè chữ
    x_axis_config = alt.Axis(
        labelAngle=-45, 
        labelColor='#2C3E50', 
        titleColor='#114B72', 
        labelFontSize=10,
        titleFontSize=12,
        titlePadding=10,
        values=df['Hiển thị Giờ'].unique()[::2] if len(df['Hiển thị Giờ'].unique()) > 15 else None
    )

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc Thời Gian Trong Ngày', axis=x_axis_config)
    )

    # 1. TÔ NỀN CẢNH BÁO BẰNG RECT (Nhìn phát biết ngay vùng an toàn/nguy hiểm)
    zones = pd.DataFrame([
        {"start": 0.0, "end": 0.4, "Color": "#EBF5FB", "Zone": "Quá Ẩm (Nấm Bệnh)"},
        {"start": 0.4, "end": 0.8, "Color": "#E8F8F5", "Zone": "Ẩm Nhẹ (An Toàn)"},
        {"start": 0.8, "end": 1.6, "Color": "#EAF2F8", "Zone": "Lý Tưởng (Quang Hợp)"},
        {"start": 1.6, "end": 2.0, "Color": "#FEF9E7", "Zone": "Khô Nhẹ (Cảnh Báo)"},
        {"start": 2.0, "end": 3.0, "Color": "#FDEDEC", "Zone": "Stress Khô (Nguy Hiểm)"}
    ])
    
    background_zones = alt.Chart(zones).mark_rect(opacity=0.6).encode(
        y=alt.Y('start:Q', scale=alt.Scale(domain=[0.0, 2.5])),
        y2='end:Q',
        color=alt.Color('Color:N', scale=None) # Lấy mã màu trực tiếp từ dataframe
    )

    # 2. ĐƯỜNG NÉT ĐỨT THỂ HIỆN NGƯỠNG LÝ TƯỞNG CỦA LOẠI CÂY (Nếu có truyền vào)
    rule_charts = []
    if v_min is not None and v_max is not None:
        rule_min = alt.Chart(pd.DataFrame({'y': [v_min]})).mark_rule(
            color='#E74C3C', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_max = alt.Chart(pd.DataFrame({'y': [v_max]})).mark_rule(
            color='#E74C3C', strokeWidth=1.5, strokeDash=[4, 4]
        ).encode(y='y:Q')
        rule_charts = [rule_min, rule_max]

    # 3. ĐƯỜNG ĐỒ THỊ CHÍNH (VPD Thực Tế)
    vpd_line = base.mark_line(
        color='#196F3D', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', title='Áp Suất Thâm Hụt Hơi VPD (kPa)', scale=alt.Scale(domain=[0.0, 2.5]))
    )

    # 4. CÁC ĐIỂM NODE TRÒN ĐỔI MÀU THEO TRẠNG THÁI SINH HỌC
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

    # Gom tất cả các lớp lại thành một biểu đồ thống nhất
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
    Vẽ biểu đồ tương quan động học giữa Nhiệt độ và Độ ẩm.
    Sử dụng giải pháp diện tích (Area) mờ phía dưới và đường Line sắc nét phía trên giúp biểu đồ thanh thoát, không đè lấp.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # Trục X đồng bộ cấu hình ẩn bớt nhãn thừa
    x_axis_config = alt.Axis(
        labelAngle=-45, 
        labelColor='#2C3E50', 
        titleColor='#114B72', 
        labelFontSize=10,
        titleFontSize=12,
        titlePadding=10,
        values=df['Hiển thị Giờ'].unique()[::2] if len(df['Hiển thị Giờ'].unique()) > 15 else None
    )

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc Thời Gian Trong Ngày', axis=x_axis_config)
    )

    # 1. LỚP ĐỘ ẨM: Chuyển từ cột Bar thô cứng sang đồ thị VÙNG DIỆN TÍCH (Area) mềm mại, màu xanh nước biển mát mắt
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

    # Đường viền đỉnh cho vùng độ ẩm
    humidity_line = base.mark_line(color='#3498DB', strokeWidth=1.5, strokeDash=[2, 2]).encode(
        y=alt.Y('Độ ẩm (%):Q')
    )

    # 2. LỚP NHIỆT ĐỘ: Đường Line màu đỏ Neon đậm rực rỡ, đi kèm các Node tròn màu trắng viền đỏ
    temp_line = base.mark_line(
        color='#E74C3C', 
        strokeWidth=3.5,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt Độ Môi Trường (°C)',
                scale=alt.Scale(domain=[df['Nhiệt độ (°C)'].min() - 3, df['Nhiệt độ (°C)'].max() + 3]),
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

    # Kết hợp trục kép độc lập (Nhiệt độ bên trái, Độ ẩm bên phải)
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
