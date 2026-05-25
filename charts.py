import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    # Xác định loại trục X dựa trên dữ liệu (nếu có dấu "/" tức là định dạng Ngày dd/mm, ngược lại là Giờ %H:%M)
    # Sử dụng kiểu ":O" (Ordinal) giúp Altair xếp các điểm sát nhau, không tự giãn cách theo giờ thô.
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian chu kỳ', sort=None)
    )
    
    line = base.mark_line(color='#2E7D32', strokeWidth=3).encode(
        y=alt.Y('VPD (kPa):Q', title='Chỉ số VPD (kPa)', scale=alt.Scale(domain=[0, 3.0]))
    )
    
    points = base.mark_circle(color='#1B5E20', size=60).encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    # Vùng tối ưu
    rule_min = alt.Chart(pd.DataFrame({'y': [vpd_min]})).mark_rule(color='rgba(46, 125, 50, 0.4)', strokeDash=[5, 5]).encode(y='y:Q')
    rule_max = alt.Chart(pd.DataFrame({'y': [vpd_max]})).mark_rule(color='rgba(46, 125, 50, 0.4)', strokeDash=[5, 5]).encode(y='y:Q')
    
    return (line + points + rule_min + rule_max).properties(height=280).configure_axis(labelAngle=0)

def draw_temperature_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_blank()
    return alt.Chart(df).mark_line(color='#FF4B4B', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=280).configure_axis(labelAngle=0)

def draw_humidity_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_blank()
    return alt.Chart(df).mark_line(color='#0068C9', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None),
        y=alt.Y('Độ ẩm (%):Q', title='Độ ẩm (%)'),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=280).configure_axis(labelAngle=0)

def draw_combined_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_blank()
    
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None)
    )
    
    line1 = base.mark_line(color='#FF4B4B', strokeWidth=2).encode(y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ & Độ ẩm'))
    line2 = base.mark_line(color='#0068C9', strokeWidth=2).encode(y='Độ ẩm (%):Q')
    line3 = base.mark_line(color='#2E7D32', strokeWidth=3).encode(y='VPD (kPa):Q')
    
    return alt.layer(line1, line2, line3).properties(height=280).configure_axis(labelAngle=0)
