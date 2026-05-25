import altair as alt
import pandas as pd

def draw_vpd_chart(df, vpd_min, vpd_max):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    # 1. Trục X cấu hình dạng chuỗi danh mục (:O) để triệt tiêu lỗi giãn cách, tự gộp điểm gọn gàng
    base = alt.Chart(df).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian chu kỳ', sort=None)
    )
    
    # 2. KHÔI PHỤC CÁC DẢI MÀU NỀN TRỰC QUAN (Xanh / Đỏ / Xanh dương)
    # Vùng Quá Ẩm (Dưới vpd_min)
    rect_under = alt.Chart(pd.DataFrame({'y1': [0], 'y2': [vpd_min]})).mark_rect(fill='#E3F2FD', opacity=0.8).encode(y='y1:Q', y2='y2:Q')
    
    # Vùng Lý Tưởng (Từ vpd_min đến vpd_max)
    rect_ideal = alt.Chart(pd.DataFrame({'y1': [vpd_min], 'y2': [vpd_max]})).mark_rect(fill='#E8F5E9', opacity=0.8).encode(y='y1:Q', y2='y2:Q')
    
    # Vùng Quá Khô (Trên vpd_max đến kịch trần 3.0)
    rect_over = alt.Chart(pd.DataFrame({'y1': [vpd_max], 'y2': [3.0]})).mark_rect(fill='#FFEBEE', opacity=0.8).encode(y='y1:Q', y2='y2:Q')
    
    # 3. Đường đồ thị VPD chính
    line = base.mark_line(color='#2E7D32', strokeWidth=3.5).encode(
        y=alt.Y('VPD (kPa):Q', title='Chỉ số VPD (kPa)', scale=alt.Scale(domain=[0, 3.0]))
    )
    
    # 4. Các điểm nút dữ liệu hình tròn để rê chuột xem Tooltip thông số chi tiết
    points = base.mark_circle(color='#1B5E20', size=70).encode(
        y='VPD (kPa):Q',
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'VPD (kPa)', 'Trạng thái']
    )
    
    # KÍCH HOẠT TÍNH NĂNG .interactive() ĐỂ PHÓNG TO / THU NHỎ VÀ KÉO TRƯỢT BIỂU ĐỒ
    main_chart = (rect_under + rect_ideal + rect_over + line + points).properties(height=280).interactive()
    
    return main_chart.configure_axis(labelAngle=0)

def draw_temperature_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    # Bật .interactive() để cho phép phóng to thu nhỏ đồ thị nhiệt độ
    return alt.Chart(df).mark_line(color='#FF4B4B', strokeWidth=2.5).encode(
        x=alt.X('Hiển thị Giờ:O', title='Mốc thời gian', sort=None),
        y=alt.Y('Nhiệt độ (°C):Q', title='Nhiệt độ (°C)'),
        tooltip=['Hiển thị Giờ', 'Nhiệt độ (°C)']
    ).properties(height=280).interactive().configure_axis(labelAngle=0)

def draw_humidity_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_blank()
    
    # Bật .interactive() để cho phép phóng to thu nhỏ đồ thị độ ẩm
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
    
    # Bật .interactive() cho đồ thị tổ hợp nhiều đường kẻ
    return alt.layer(line1, line2, line3).properties(height=280).interactive().configure_axis(labelAngle=0)
