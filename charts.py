import altair as alt

def get_biological_block_local(hour):
    if 5 <= hour < 10: return "🌅 Sáng (05h - 10h)"
    elif 10 <= hour < 15: return "☀️ Trưa (10h - 15h)"
    elif 15 <= hour < 19: return "🌇 Chiều (15h - 19h)"
    elif 19 <= hour < 23: return "🌌 Tối (19h - 23h)"
    else: return "🌙 Khuya (23h - 05h)"

def draw_vpd_chart(df, plant_matrix):
    """Vẽ biểu đồ tích hợp đường cong VPD chạy chính xác trên nền dải mục tiêu động"""
    if df.empty: return alt.Chart().mark_text()
    
    df_chart = df.copy()
    
    # Tạo dải mục tiêu động cho từng dòng dữ liệu dựa trên giờ của mốc đó
    def get_bounds(row):
        dt = row["datetime_internal"]
        block = get_biological_block_local(dt.hour)
        return plant_matrix.get(block, (0.6, 1.2))
        
    df_chart["Target_Min"] = df_chart.apply(lambda r: get_bounds(r)[0], axis=1)
    df_chart["Target_Max"] = df_chart.apply(lambda r: get_bounds(r)[1], axis=1)
    
    base = alt.Chart(df_chart).encode(
        x=alt.X('Hiển thị Giờ:N', sort=None, title='Thời gian mốc trong ngày')
    )
    
    # Dải mục tiêu xanh lá cây động bám sát trục VPD
    band = alt.Chart(df_chart).mark_area(opacity=0.18, color='#2ECC71').encode(
        x=alt.X('Hiển thị Giờ:N', sort=None),
        y=alt.Y('Target_Max:Q'),
        y2=alt.Y2('Target_Min:Q')
    )
    
    # Đường đồ thị VPD thực tế
    line = base.mark_line(strokeWidth=3.5, color='#E67E22', interpolate='monotone').encode(
        y=alt.Y('VPD (kPa):Q', title='Áp suất hơi bão hòa VPD (kPa)', scale=alt.Scale(zero=True))
    )
    
    # Điểm chấm tròn dữ liệu tương tác
    points = base.mark_circle(size=70, color='#D35400').encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    return alt.layer(band, line, points).properties(height=340).configure_axis(labelFontSize=11, titleFontSize=12)

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
