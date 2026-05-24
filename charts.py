import altair as alt

def draw_vpd_chart(df, vpd_min, vpd_max):
    # ... (giữ nguyên phần logic tạo biểu đồ `chart` hiện tại của bạn) ...
    
    # Bổ sung cấu hình dưới đây vào trước khi return để làm thoáng biểu đồ:
    styled_chart = chart.properties(
        height=320 # Tăng độ cao một chút cho thoáng
    ).configure_axisX(
        labelAngle=-45,      # Xoay nghiêng nhãn ngày/giờ 45 độ để không bị đè chữ
        labelOverlap="hide",  # Tự động ẩn bớt nhãn nếu dữ liệu quá dày để tránh chồng chéo
        labelPadding=10       # Tạo khoảng cách giữa chữ và trục tọa độ
    ).configure_axisY(
        labelPadding=10
    ).configure_view(
        strokeOpacity=0       # Ẩn khung viền thô cứng để biểu đồ mở rộng tự nhiên
    )
    
    return styled_chart
