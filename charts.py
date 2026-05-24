import altair as alt

def draw_temperature_chart(df):
    return alt.Chart(df).mark_line(color="#FF4B4B", point=True).encode(
        x=alt.X('Hiển thị Giờ:O', axis=alt.Axis(title="Mốc thời gian", labelAngle=-45)), 
        y=alt.Y("Nhiệt độ (°C):Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Nhiệt độ (°C)")),
        tooltip=['Ngày', 'Hiển thị Giờ', "Nhiệt độ (°C)"]
    ).properties(height=200).interactive() # Đã hạ xuống 200px để vừa khít màn hình

def draw_humidity_chart(df):
    return alt.Chart(df).mark_line(color="#0068C9", point=True).encode(
        x=alt.X('Hiển thị Giờ:O', axis=alt.Axis(title="Mốc thời gian", labelAngle=-45)),
        y=alt.Y("Độ ẩm (%):Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Độ ẩm (%)")),
        tooltip=['Ngày', 'Hiển thị Giờ', "Độ ẩm (%)"]
    ).properties(height=200).interactive() # Đã hạ xuống 200px để vừa khít màn hình

def draw_vpd_chart(df, vpd_min, vpd_max):
    # Giải pháp đổ màu tràn viền cố định khung Y từ 0 đến 2.0 kPa
    rect_blue = alt.Chart(df).mark_rect(color='#0068C9', opacity=0.12).encode(
        y=alt.Y(datum=0.0),
        y2=alt.Y2(datum=vpd_min)
    )
    rect_red = alt.Chart(df).mark_rect(color='#FF4B4B', opacity=0.12).encode(
        y=alt.Y(datum=vpd_max),
        y2=alt.Y2(datum=2.0)
    )
    line_vpd = alt.Chart(df).mark_line(color="#2E7D32", point=True).encode(
        x=alt.X('Hiển thị Giờ:O', axis=alt.Axis(title="Mốc thời gian", labelAngle=-45)),
        y=alt.Y('VPD (kPa):Q', scale=alt.Scale(domain=[0, 2.0]), axis=alt.Axis(title="Chỉ số VPD (kPa)", grid=True)),
        tooltip=['Ngày', 'Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    ).interactive() 
    
    return (rect_blue + rect_red + line_vpd).properties(height=210) # Chiều cao tối ưu cho Tab 1

def draw_combined_chart(df):
    base = alt.Chart(df).encode(x=alt.X('Hiển thị Giờ:O', axis=alt.Axis(title="Mốc thời gian", labelAngle=-45)))
    line_t = base.mark_line(color='#FF4B4B', strokeDash=[3,3], point=alt.OverlayMarkDef(color='#FF4B4B')).encode(
        y=alt.Y("Nhiệt độ (°C):Q", axis=alt.Axis(title="Nhiệt độ / Độ ẩm", titleColor='#0068C9')),
        tooltip=['Hiển thị Giờ', "Nhiệt độ (°C)"]
    )
    line_r = base.mark_line(color='#0068C9', point=alt.OverlayMarkDef(color='#0068C9')).encode(
        y=alt.Y("Độ ẩm (%):Q"),
        tooltip=['Hiển thị Giờ', "Độ ẩm (%)"]
    )
    weather_layer = alt.layer(line_t, line_r)
    line_v = base.mark_line(color="#2E7D32", size=3, point=alt.OverlayMarkDef(color='#2E7D32')).encode(
        y=alt.Y('VPD (kPa):Q', axis=alt.Axis(title="Áp suất VPD (kPa)", titleColor='#2E7D32'), scale=alt.Scale(domain=[0, 2.0])),
        tooltip=['Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    )
    return alt.layer(weather_layer, line_v).properties(height=200).resolve_scale(y='independent').interactive()
