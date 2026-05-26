import altair as alt

def draw_vpd_chart(df, vpd_min, vpd_max):
    """Vẽ biểu đồ tích hợp đường cong VPD chạy trên nền dải mục tiêu"""
    if df.empty: return alt.Chart().mark_text()
    
    base = alt.Chart(df).encode(x=alt.X('Hiển thị Giờ:N', sort=None, title='Thời gian mốc trong ngày'))
    
    # Tạo dải màu nền xanh lý tưởng bao quanh mục tiêu
    band = alt.Chart(df).mark_area(opacity=0.15, color='#2ECC71').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None),
        y=alt.value(vpd_max * 120),  
        y2=alt.value(vpd_min * 120)
    )
    
    line = base.mark_line(strokeWidth=3.5, color='#E67E22', interpolate='monotone').encode(
        y=alt.Y('VPD (kPa):Q', title='Áp suất hơi bão hòa VPD (kPa)')
    )
    
    points = base.mark_circle(size=70, color='#D35400').encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    return alt.layer(band, line, points).properties(height=320).configure_axis(labelFontSize=11, titleFontSize=12)

def draw_temperature_chart(df):
    """Vẽ biểu đồ lịch sử nhiệt độ riêng biệt tại Tab 2"""
    if df.empty: return alt.Chart().mark_text()
    return alt.Chart(df).mark_line(color='#E74C3C', strokeWidth=2.5, interpolate='monotone').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title='Giờ'),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=180)

def draw_humidity_chart(df):
    """Vẽ biểu đồ lịch sử độ ẩm không khí riêng biệt tại Tab 2"""
    if df.empty: return alt.Chart().mark_text()
    return alt.Chart(df).mark_line(color='#3498DB', strokeWidth=2.5, interpolate='monotone').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title='Giờ'),
        y=alt.Y('Độ ẩm (%):Q', title='Độ ẩm (%)'),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=180)
