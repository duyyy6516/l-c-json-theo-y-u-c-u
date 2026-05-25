import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    # 1. Trục X cấu hình dạng chuỗi danh mục (:O) giúp tự gộp điểm dữ liệu, chống lỗi giãn mốc thời gian trống
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian chu kỳ', sort=None)
    )
    
    # 2. SỬA LỖI TRÀN MÀU: Định nghĩa các dải màu nền bám chặt theo trục X của dữ liệu chính
    # Vùng Quá Ẩm (Dưới vpd_min) - Đổ nền màu xanh dương nhạt phía dưới
    rect_under = base.mark_area(color='#E3F2FD', opacity=0.85).encode(
        y=alt.value(280), # Đáy biểu đồ
        y2=alt.Y('y_min_val:Q')
    )
    
    # Vùng Lý Tưởng (Từ vpd_min đến vpd_max) - Đổ nền màu xanh lá cây nhạt ổn định
    rect_ideal = base.mark_area(color='#E8F5E9', opacity=0.85).encode(
        y=alt.Y('y_min_val:Q'),
        y2=alt.Y('y_max_val:Q')
    )
    
    # Vùng Quá Khô (Trên vpd_max) - Đổ nền màu đỏ hồng nhạt cảnh báo
    rect_over = base.mark_area(color='#FFEBEE', opacity=0.85).encode(
        y=alt.Y('y_max_val:Q'),
        y2=alt.value(0) # Đỉnh biểu đồ
    )
    
    # Tự động gán các mốc giới hạn vào dữ liệu để dải màu vẽ chuẩn xác
    df_chart = df.copy()
    df_chart['y_min_val'] = vpd_min
    df_chart['y_max_val'] = vpd_max
    
    # Re-bind lại data đã map biến giới hạn
    chart_base = alt.Chart(df_chart).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian chu kỳ', sort=None)
    )
    
    # 3. Đường đồ thị VPD chính (Đè lên trên các dải màu nền)
    line = chart_base.mark_line(color='#2E7D32', strokeWidth=3.5).encode(
        y=alt.Y('VPD (kPa):Q', title='Chỉ số VPD (kPa)', scale=alt.Scale(domain=[0, 3.0], clamp=True))
    )
    
    # 4. Các điểm nút tròn tương tác rê chuột xem thông số (Tooltip)
    points = chart_base.mark_circle(color='#1B5E20', size=70).encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    # Lồng ghép các dải nền bám biên dữ liệu + đường kẻ + điểm tròn và bật tương tác phóng to thu nhỏ
    # Sử dụng cách map dải màu này sẽ loại bỏ hoàn toàn lỗi tạo khối đặc ở Ảnh 1 và khoảng trống vô nghĩa ở Ảnh 2
    final_chart = alt.layer(
        chart_base.mark_area(color='#E3F2FD', opacity=0.8).encode(y=alt.Y('y_min_val:Q'), y2=alt.value(280)), # Dưới min
        chart_base.mark_area(color='#E8F5E9', opacity=0.8).encode(y=alt.Y('y_min_val:Q'), y2=alt.Y('y_max_val:Q')), # Khoảng giữa
        chart_base.mark_area(color='#FFEBEE', opacity=0.8).encode(y=alt.value(0), y2=alt.Y('y_max_val:Q')), # Trên max
        line,
        points
    ).properties(height=280).interactive()
    
    return final_chart.configure_axis(labelAngle=0)

def draw_temperature_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_blank()
    return alt.Chart(df).mark_line(color='#FF4B4B', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=280).interactive().configure_axis(labelAngle=0)

def draw_humidity_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_blank()
    return alt.Chart(df).mark_line(color='#0068C9', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None),
        y=alt.Y('Độ ẩm (%):Q', title='Độ ẩm (%)'),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=280).interactive().configure_axis(labelAngle=0)

def draw_combined_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None)
    )
    
    line1 = base.mark_line(color='#FF4B4B', strokeWidth=2).encode(y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ & Độ ẩm'))
    line2 = base.mark_line(color='#0068C9', strokeWidth=2).encode(y='Độ ẩm (%):Q')
    line3 = base.mark_line(color='#2E7D32', strokeWidth=3.5).encode(y='VPD (kPa):Q')
    
    return alt.layer(line1, line2, line3).properties(height=280).interactive().configure_axis(labelAngle=0)
