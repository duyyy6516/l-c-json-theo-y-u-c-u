import altair as alt
import pandas as pd

def draw_temperature_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_text()
        
    chart = alt.Chart(df).mark_line(color="#FF4B4B", point=alt.OverlayMarkDef(color="#FF4B4B", size=40)).encode(
        x=alt.X('datetime_internal:T', title="Mốc thời gian", axis=alt.Axis(format="%H:%M", labelAngle=-45, grid=True)), 
        y=alt.Y("Nhiệt độ (°C):Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Nhiệt độ (°C)")),
        tooltip=['Ngày', 'Hiển thị Giờ', "Nhiệt độ (°C)"]
    ).properties(height=280).interactive().configure_view(strokeOpacity=0)
    return chart

def draw_humidity_chart(df):
    if df.empty: 
        return alt.Chart(pd.DataFrame()).mark_text()
        
    chart = alt.Chart(df).mark_line(color="#0068C9", point=alt.OverlayMarkDef(color="#0068C9", size=40)).encode(
        x=alt.X('datetime_internal:T', title="Mốc thời gian", axis=alt.Axis(format="%H:%M", labelAngle=-45, grid=True)),
        y=alt.Y("Độ ẩm (%):Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Độ ẩm (%)")),
        tooltip=['Ngày', 'Hiển thị Giờ', "Độ ẩm (%)"]
    ).properties(height=280).interactive().configure_view(strokeOpacity=0)
    return chart

def draw_vpd_chart(df, vpd_min, vpd_max):
    if len(df) == 0:
        return alt.Chart(df).mark_blank()
        
    try:
        actual_max_vpd = float(df['VPD (kPa)'].max())
    except:
        actual_max_vpd = 2.0
        
    # Xác định đỉnh trục Y linh hoạt dựa trên dữ liệu, tối thiểu là mức 2.5 kPa
    Y_LIMIT = max(actual_max_vpd + 0.5, 2.5)
    
    # Lớp nền 1: Vùng quá ẩm (Màu xanh dương lót bên dưới đáy)
    rect_blue = alt.Chart(df).mark_rect(color='#0068C9', opacity=0.12).encode(
        y=alt.Y(datum=0.0),
        y2=alt.Y2(datum=vpd_min)
    )
    
    # Lớp nền 2: Vùng quá khô (Màu đỏ lót từ vpd_max lên tới kịch đỉnh đồ thị)
    rect_red = alt.Chart(df).mark_rect(color='#FF4B4B', opacity=0.12).encode(
        y=alt.Y(datum=vpd_max),
        y2=alt.Y2(datum=Y_LIMIT)
    )
    
    # Lớp chủ đạo 3: Đường biểu đồ chính màu xanh lá cây đậm có nút thắt dữ liệu trực quan
    # Trục X sử dụng định dạng thời gian chuẩn để loại bỏ lỗi lặp nhãn "00:00"
    # Trục Y ép domainMin=0 để loại bỏ hoàn toàn các dải số âm vô lý
    line_vpd = alt.Chart(df).mark_line(color="#2E7D32", size=3, point=alt.OverlayMarkDef(color="#0068C9", size=45), clip=True).encode(
        x=alt.X('datetime_internal:T', 
                title="Mốc thời gian", 
                axis=alt.Axis(format="%H:%M", labelAngle=-45, tickCount=12, grid=True)),
        y=alt.Y('VPD (kPa):Q', 
               scale=alt.Scale(domainMin=0, domainMax=Y_LIMIT, zero=True), 
               axis=alt.Axis(title="Chỉ số VPD (kPa)", grid=True)),
        tooltip=['Ngày', 'Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    ).interactive() # Bật tương tác phóng to/thu nhỏ trực tiếp trên lớp đường truyền dữ liệu thực
    
    # Gộp các tầng biểu đồ: Đưa các khối màu lót xuống đáy, đường nét dữ liệu nằm hiên ngang ở trên cùng
    chart = alt.layer(
        rect_blue, rect_red, line_vpd
    ).properties(
        height=280
    ).configure_view(
        strokeOpacity=0
    )
    
    return chart

def draw_combined_chart(df):
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text()

    base = alt.Chart(df).encode(
        x=alt.X('datetime_internal:T', title="Mốc thời gian", axis=alt.Axis(format="%H:%M", labelAngle=-45, grid=True))
    )
    
    line_t = base.mark_line(color='#FF4B4B', strokeDash=[4,3]).encode(
        y=alt.Y("Nhiệt độ (°C):Q", axis=alt.Axis(title="Nhiệt độ (°C) / Độ ẩm (%)", titleColor='#FF4B4B')),
        tooltip=['Hiển thị Giờ', "Nhiệt độ (°C)"]
    )
    
    line_r = base.mark_line(color='#0068C9').encode(
        y=alt.Y("Độ ẩm (%):Q"),
        tooltip=['Hiển thị Giờ', "Độ ẩm (%)"]
    )
    
    weather_layer = alt.layer(line_t, line_r)
    
    line_v = base.mark_line(color="#2E7D32", size=3).encode(
        y=alt.Y('VPD (kPa):Q', axis=alt.Axis(title="Áp suất VPD (kPa)", titleColor='#2E7D32'), scale=alt.Scale(domainMin=0, clamp=True)),
        tooltip=['Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    )
    
    chart = alt.layer(weather_layer, line_v).properties(height=280).resolve_scale(
        y='independent'
    ).interactive().configure_view(
        strokeOpacity=0
    )
    
    return chart
