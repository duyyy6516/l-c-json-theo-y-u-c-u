def draw_vpd_chart(df, vpd_min, vpd_max):
    if len(df) == 0:
        return alt.Chart(df).mark_blank()
        
    try:
        actual_max_vpd = float(df['VPD (kPa)'].max())
    except:
        actual_max_vpd = 2.0
        
    Y_LIMIT = max(actual_max_vpd + 0.3, 2.0)
    
    # Khối nền màu xanh biểu thị khu vực Quá ẩm
    rect_blue = alt.Chart(df).mark_rect(color='#0068C9', opacity=0.15).encode(
        y=alt.Y(datum=0.0),
        y2=alt.Y2(datum=vpd_min)
    )
    
    # Khối nền màu đỏ biểu thị khu vực Quá khô
    rect_red = alt.Chart(df).mark_rect(color='#FF4B4B', opacity=0.15).encode(
        y=alt.Y(datum=vpd_max),
        y2=alt.Y2(datum=Y_LIMIT)
    )
    
    # Đường đồ thị chính mượt mà màu xanh lá cây đậm (Bỏ .interactive() ở cuối biến này)
    line_vpd = alt.Chart(df).mark_line(color="#2E7D32", size=2.5, point=len(df) < 100).encode(
        x=alt.X('Hiển thị Giờ:N', title="Mốc thời gian", sort=None),
        y=alt.Y('VPD (kPa):Q', 
               scale=alt.Scale(domain=[0.0, Y_LIMIT], clamp=True), 
               axis=alt.Axis(title="Chỉ số VPD (kPa)", grid=True)),
        tooltip=['Ngày', 'Hiển thị Giờ', 'VPD (kPa)', 'Trạng thái']
    )
    
    # ĐƯỢC SỬA TẠI ĐÂY: Đưa .interactive() ra ngoài cùng sau khi gộp 3 lớp dữ liệu
    chart = (rect_blue + rect_red + line_vpd).properties(
        height=260
    ).interactive().configure_axisX(  # Thêm .interactive() tại đây giúp kích hoạt phóng to toàn bộ biểu đồ
        labelAngle=-45,
        labelOverlap="greedy",
        labelPadding=8
    ).configure_view(
        strokeOpacity=0
    )
    
    return chart
