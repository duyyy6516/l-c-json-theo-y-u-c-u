import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text()
    
    # 1. Tạo dải nền lý tưởng (độ ẩm/khô tối ưu)
    band = alt.Chart(df).mark_rect(opacity=0.15, color='#2E7D32').encode(
        y=alt.value(0 if vpd_min is None else vpd_min),
        y2=alt.value(3 if vpd_max is None else vpd_max)
    )
    
    # 2. Vẽ đường dữ liệu VPD dạng Line (Tránh bị bí dính giống như cột Bar)
    line = alt.Chart(df).mark_line(point=True, color='#2E7D32', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:N', title='Thời gian', sort=None),
        y=alt.Y('VPD (kPa):Q', title='VPD (kPa)', scale=alt.Scale(domain=[0, max(df['VPD (kPa)'].max() + 0.5, 3.0)])),
        tooltip=['Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    )
    
    # 3. SỬA LỖI: Dùng labelOverlap=True hoặc "greedy" để tự động thu gọn chữ bị đè trùng
    chart = (band + line).properties(height=300).configure_axisX(
        labelAngle=-45,
        labelOverlap="greedy",  # Sửa từ "hide" thành "greedy" để tương thích mọi phiên bản Altair
        labelPadding=8
    ).configure_axisY(
        labelPadding=8
    ).configure_view(
        strokeOpacity=0       # Loại bỏ khung viền thô cứng giúp mở rộng biểu đồ rộng rãi
    )
    return chart

def draw_temperature_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_text()
    chart = alt.Chart(df).mark_line(point=True, color='#FF4B4B', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:N', title='Thời gian', sort=None),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=300).configure_axisX(
        labelAngle=-45, labelOverlap="greedy", labelPadding=8
    ).configure_view(strokeOpacity=0)
    return chart

def draw_humidity_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_text()
    chart = alt.Chart(df).mark_line(point=True, color='#0068C9', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:N', title='Thời gian', sort=None),
        y=alt.Y('Độ ẩm (%):Q', title='Độ ẩm (%)'),
        tooltip=['Hiển thị Giờ', 'Độ ẩm (%)']
    ).properties(height=300).configure_axisX(
        labelAngle=-45, labelOverlap="greedy", labelPadding=8
    ).configure_view(strokeOpacity=0)
    return chart

def draw_combined_chart(df):
    if df.empty: return alt.Chart(pd.DataFrame()).mark_text()
    
    # Chuyển đổi cấu trúc bảng để vẽ đồ thị tổ hợp nhiều đường song song thoáng đãng
    df_melt = df.melt(id_vars=['Hiển thị Giờ'], value_vars=['Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)'], 
                      var_name='Chỉ số', value_name='Giá trị')
    
    chart = alt.Chart(df_melt).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('Hiển thị Giờ:N', title='Thời gian', sort=None),
        y=alt.Y('Giá trị:Q', title='Giá trị đo lường'),
        color=alt.Color('Chỉ số:N', scale=alt.Scale(domain=['Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)'], range=['#FF4B4B', '#0068C9', '#2E7D32'])),
        tooltip=['Hiển thị Giờ', 'Chỉ số', 'Giá trị']
    ).properties(height=320).configure_axisX(
        labelAngle=-45, labelOverlap="greedy", labelPadding=8
    ).configure_view(strokeOpacity=0)
    return chart
