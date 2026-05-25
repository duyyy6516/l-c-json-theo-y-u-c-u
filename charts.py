import altair as alt
import pandas as pd

def draw_vpd_chart(df, v_min, v_max):
    """
    Vẽ biểu đồ diễn biến chỉ số VPD theo thời gian trong ngày.
    Đã được thiết kế lại theo chuẩn nghiêm ngặt của Altair v6 để loại bỏ hoàn toàn lỗi SchemaValidationError.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    # 1. Định nghĩa các vùng màu nền đại diện cho các trạng thái của môi trường (Solid background)
    # Áp dụng cấu pháp alt.datum rõ ràng kèm kiểu dữ liệu để vượt qua bộ lọc Schema của Altair v6
    
    # Vùng Quá Ẩm (0.0 -> v_min - 0.2)
    zone_too_wet = alt.Chart(df).mark_rect(opacity=0.9, color='#0B5345').encode(
        y=alt.Y(datum=0.0, type='quantitative'),
        y2=alt.Y2(datum=0.0)
    )

    # Vùng Ẩm (v_min - 0.2 -> v_min)
    v_wet_low = 0.0 if v_min - 0.2 < 0 else v_min - 0.2
    zone_wet = alt.Chart(df).mark_rect(opacity=0.9, color='#2980B9').encode(
        y=alt.Y(datum=v_wet_low, type='quantitative'),
        y2=alt.Y2(datum=v_min)
    )

    # Vùng Lý Tưởng (v_min -> v_max)
    zone_ideal = alt.Chart(df).mark_rect(opacity=0.9, color='#27AE60').encode(
        y=alt.Y(datum=v_min, type='quantitative'),
        y2=alt.Y2(datum=v_max)
    )

    # Vùng Nóng (v_max -> v_max + 0.5)
    zone_hot = alt.Chart(df).mark_rect(opacity=0.9, color='#F39C12').encode(
        y=alt.Y(datum=v_max, type='quantitative'),
        y2=alt.Y2(datum=v_max + 0.5)
    )

    # Vùng Quá Nóng (v_max + 0.5 trở lên)
    zone_too_hot = alt.Chart(df).mark_rect(opacity=0.9, color='#C0392B').encode(
        y=alt.Y(datum=v_max + 0.5, type='quantitative'),
        y2=alt.Y2(datum=2.5)
    )

    # 2. Tạo đường vẽ dữ liệu VPD thực tế (Đường Line màu trắng có node tròn)
    base_data = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', 
                title='Thời gian chi tiết trong toàn bộ ngày',
                axis=alt.Axis(labelAngle=-90, labelColor='#2C3E50', titleColor='#2C3E50'))
    )

    # Đường nối line màu trắng dày nổi bật trên nền solid
    vpd_line = base_data.mark_line(
        color='#FFFFFF', 
        strokeWidth=3.5, 
        interpolate='monotone'
    ).encode(
        y=alt.Y('VPD (kPa):Q', 
                title='Chỉ số VPD (kPa)', 
                scale=alt.Scale(domain=[0.0, 2.5]),
                axis=alt.Axis(grid=True, gridDash=[3,3], gridColor='#BDC3C7'))
    )

    # Các điểm node tròn viền đen lõi trắng trên đường line để di chuột xem Tooltip thông tin
    vpd_points = base_data.mark_point(
        color='#17202A', 
        fill='#FFFFFF', 
        size=70, 
        strokeWidth=2
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

    # 3. Gộp toàn bộ các lớp đồ thị và cấu hình không gian bảo vệ chữ chú thích
    # Tách biệt thuộc tính tiêu đề (Title) và thuộc tính cấu hình view (Configure) để an toàn tuyệt đối
    combined_chart = alt.layer(
        zone_too_wet, zone_wet, zone_ideal, zone_hot, zone_too_hot,
        vpd_line, vpd_points
    ).properties(
        width='container',
        height=350,
        title=alt.TitleParams(
            text=f"Cạn dưới: {v_min} kPa | Cạn trên: {v_max} kPa | Khoá dải màu Solid đậm | vạch dựng phân buổi",
            fontSize=13,
            fontWeight='bold',
            color='#5D6D7E',
            offset=25,         # Đẩy dòng chữ chú thích lên cao tạo khoảng trống thông thoáng
            orient='top',
            anchor='start'     # Căn lề trái thẳng hàng với trục đồ thị
        )
    )

    # Áp dụng định dạng cấu hình trục và lưới an toàn cho phiên bản mới
    return combined_chart.configure_view(padding=20).configure_axis(domain=False)


def draw_combined_temp_humidity_chart(df):
    """
    Vẽ biểu đồ lồng nhau theo dõi cặp thông số Nhiệt độ (Line) và Độ ẩm (Bar) song song trên cùng hệ trục.
    """
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()

    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc chu kỳ thời gian', axis=alt.Axis(labelAngle=-90))
    )

    # Đồ thị cột (Bar) biểu diễn Độ ẩm tương đối (%) - Liên kết trục bên phải Y2
    humidity_bar = base.mark_bar(
        color='#3498DB', 
        opacity=0.35, 
        size=15
    ).encode(
        y=alt.Y('Độ ẩm (%):Q', 
                title='Độ ẩm không khí (%)',
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(titleColor='#3498DB', orient='right'))
    )

    # Đồ thị đường (Line) biểu diễn Nhiệt độ khí hậu (°C) - Liên kết trục bên trái Y
    temp_line = base.mark_line(
        color='#E74C3C', 
        strokeWidth=3,
        interpolate='monotone'
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q', 
                title='Nhiệt độ môi trường (°C)',
                scale=alt.Scale(domain=[df['Nhiệt độ (°C)'].min() - 3, df['Nhiệt độ (°C)'].max() + 3]),
                axis=alt.Axis(titleColor='#E74C3C', orient='left'))
    )

    # Điểm tròn nhỏ định vị trên đường nhiệt độ giúp soi dữ liệu mượt mà hơn
    temp_points = base.mark_point(
        color='#E74C3C', 
        fill='#FFFFFF', 
        size=35
    ).encode(
        y=alt.Y('Nhiệt độ (°C):Q'),
        tooltip=[
            alt.Tooltip('Hiển thị Giờ:O', title='Giờ'),
            alt.Tooltip('Nhiệt độ (°C):Q', title='Nhiệt độ'),
            alt.Tooltip('Độ ẩm (%):Q', title='Độ ẩm')
        ]
    )

    # Kết hợp trục kép (Dual Axis Chart) bằng cách lồng ghép các layer độc lập dải đo
    dual_axis_chart = alt.layer(
        humidity_bar, 
        alt.layer(temp_line, temp_points)
    ).resolve_scale(
        y='independent'
    ).properties(
        width='container',
        height=220,
        title=alt.TitleParams(
            text="🌡️ Diễn biến mối tương quan trực quan giữa Nhiệt độ & Độ ẩm tương đối",
            fontSize=12,
            color='#34495E',
            anchor='start',
            offset=10
        )
    )

    return dual_axis_chart.configure_view(padding=15)
