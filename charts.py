import altair as alt

def draw_vpd_chart(df, vpd_min, vpd_max):
    """Vẽ biểu đồ tích hợp đường cong VPD chạy chính xác trên nền dải mục tiêu"""
    if df.empty: return alt.Chart().mark_text()
    
    # Tạo thêm 2 cột dữ liệu động trong dataframe phục vụ việc vẽ dải mục tiêu theo trục Y thật
    df_chart = df.copy()
    df_chart["VPD_Mục_Tiêu_Min"] = vpd_min
    df_chart["VPD_Mục_Tiêu_Max"] = vpd_max
    
    base = alt.Chart(df_chart).encode(x=alt.X('Hiển thị Giờ:N', sort=None, title='Thời gian mốc trong ngày'))
    
    # SỬA LỖI TẠI ĐÂY: Ép dải màu đi theo đúng trục giá trị kPa thực tế của hệ thống
    band = alt.Chart(df_chart).mark_area(opacity=0.18, color='#2ECC71').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None),
        y=alt.Y('VPD_Mục_Tiêu_Max:Q'),
        y2=alt.Y2('VPD_Mục_Tiêu_Min:Q')
    )
    
    # Đường line đồ thị VPD thực tế
    line = base.mark_line(strokeWidth=3.5, color='#E67E22', interpolate='monotone').encode(
        y=alt.Y('VPD (kPa):Q', title='Áp suất hơi bão hòa VPD (kPa)', scale=alt.Scale(zero=True))
    )
    
    # Điểm chấm tròn dữ liệu
    points = base.mark_circle(size=70, color='#D35400').encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    return alt.layer(band, line, points).properties(height=320).configure_axis(labelFontSize=11, titleFontSize=12)

def draw_temperature_chart(df):
    if df.empty: return alt.Chart().mark_text()
    return alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=2.5, interpolate='monotone').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title='Giờ'),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=180)

def draw_humidity_chart(df):
    if df.empty: return alt.Chart().mark_text()
    return alt.Chart(df).mark_line(color='#3498DB', strokeWidth=2.5, interpolate='monotone').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title='Giờ'),
        y=alt.Y('Độ ẩm (%):Q', title='Độ ẩm (%)'),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=180)
