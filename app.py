import streamlit as pd
import streamlit as st
import pandas as pd
import json
from charts import draw_vpd_chart, draw_combined_temp_humidity_chart

# 1. Cấu hình trang Streamlit giao diện rộng
st.set_page_config(
    page_title="Hệ Thống Theo Dõi Chỉ Số VPD Nhà Màng",
    page_icon="🌿",
    layout="wide"
)

# Thêm CSS tùy biến để giao diện nhìn thoáng và sạch sẽ hơn
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h3 { margin-bottom: 5px !important; }
    hr { margin: 25px 0 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Tiêu đề chính ứng dụng
st.title("🌿 ỨNG DỤNG GIÁM SÁT MÔI TRƯỜNG & SỨC KHỎE CÂY TRỒNG")
st.caption("Hệ thống tự động tính toán và phân tích chỉ số Áp suất thâm hụt hơi (VPD) thời gian thực")

# 3. Khu vực Tải dữ liệu JSON (Sidebar bên trái)
st.sidebar.header("📂 Cấu Hình & Dữ Liệu")
uploaded_file = st.sidebar.file_uploader("Tải lên file dữ liệu (JSON)", type=["json"])

# Hàm khởi tạo dữ liệu mẫu nếu người dùng chưa tải file lên
def load_sample_data():
    # Tạo chuỗi thời gian giả lập từ 00:00 đến 23:00
    hours = [f"{str(i).zfill(2)}:00" for i in range(24)]
    # Dữ liệu mẫu mô phỏng chu kỳ nhiệt độ, độ ẩm trong ngày
    sample_data = {
        "Hiển thị Giờ": hours,
        "Nhiệt độ (°C)": [22.1, 21.5, 20.8, 20.2, 19.8, 20.5, 22.3, 25.1, 28.4, 30.2, 32.5, 33.1, 
                           32.8, 31.5, 29.7, 28.0, 26.5, 25.2, 24.5, 23.8, 23.2, 22.9, 22.5, 22.2],
        "Độ ẩm (%)": [85, 88, 90, 92, 94, 91, 85, 78, 68, 62, 55, 52, 
                       54, 58, 65, 70, 75, 78, 80, 82, 84, 85, 86, 85],
        "VPD (kPa)": [0.40, 0.31, 0.25, 0.19, 0.14, 0.22, 0.40, 0.70, 1.23, 1.62, 2.20, 2.42,
                      2.31, 1.95, 1.46, 1.13, 0.86, 0.70, 0.61, 0.53, 0.46, 0.42, 0.38, 0.37]
    }
    return pd.DataFrame(sample_data)

# Xử lý đọc file người dùng đăng lên hoặc nạp dữ liệu mẫu
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        # Hỗ trợ nếu dữ liệu tải lên ở dạng danh sách các dict hoặc dict dạng cột
        if isinstance(data, list):
            df_f = pd.DataFrame(data)
        else:
            df_f = pd.DataFrame(data)
        st.sidebar.success(" Loaded dữ liệu thành công!")
    except Exception as e:
        st.sidebar.error(f"Lỗi cấu trúc file JSON: {e}")
        df_f = load_sample_data()
else:
    st.sidebar.info("💡 Đang hiển thị dữ liệu mô phỏng mặc định.")
    df_f = load_sample_data()

# 4. Khu vực tùy chỉnh Ngưỡng tối ưu của cây trồng (Dải nét đứt)
st.sidebar.subheader("🎯 Thiết Lập Ngưỡng VPD Mục Tiêu")
use_threshold = st.sidebar.checkbox("Hiển thị dải ngưỡng tối ưu cho cây", value=True)

if use_threshold:
    v_min = st.sidebar.slider("Ngưỡng dưới VPD tối ưu (kPa)", 0.0, 2.0, 0.8, step=0.1)
    v_max = st.sidebar.slider("Ngưỡng trên VPD tối ưu (kPa)", 0.5, 3.0, 1.6, step=0.1)
else:
    v_min, v_max = None, None

# Bộ lọc thời gian nhanh (Nếu dữ liệu lớn)
if not df_f.empty and "Hiển thị Giờ" in df_f.columns:
    st.sidebar.subheader("🔍 Bộ Lọc Khoảng Thời Gian")
    all_hours = list(df_f["Hiển thị Giờ"].unique())
    time_range = st.sidebar.select_slider(
        "Chọn khoảng thời gian theo dõi:",
        options=all_hours,
        value=(all_hours[0], all_hours[-1])
    )
    # Lọc lại dataframe theo khoảng thời gian được chọn
    start_idx = all_hours.index(time_range[0])
    end_idx = all_hours.index(time_range[1])
    selected_hours = all_hours[start_idx:end_idx+1]
    df_f = df_f[df_f["Hiển thị Giờ"].isin(selected_hours)]

# 5. HIỂN THỊ KHỐI BIỂU ĐỒ CHÍNH TRÊN GIAO DIỆN MÀN HÌNH
st.write("### 📊 THÔNG SỐ PHÂN TÍCH MÔI TRƯỜNG GREENHOUSE")

if df_f.empty:
    st.warning("⚠️ Không có dữ liệu phù hợp để hiển thị đồ thị. Vui lòng kiểm tra lại bộ lọc.")
else:
    # --- BIỂU ĐỒ SỐ 1: VPD THỰC TẾ ---
    st.markdown("### 📉 BIỂU ĐỒ THEO DÕI SỨC KHỎE CÂY TRỒNG (VPD THỰC TẾ)")
    st.markdown("<p style='color: #566573; font-size: 13px; margin-top: -10px;'>Cuộn lăn chuột để phóng to/thu nhỏ, nhấn giữ chuột trái kéo qua lại để xem chi tiết dữ liệu thời gian</p>", unsafe_allow_html=True)
    
    # Gọi hàm vẽ biểu đồ VPD từ charts.py
    st.altair_chart(draw_vpd_chart(df_f, v_min, v_max), use_container_width=True)

    # Thanh phân cách thẩm mỹ giữa 2 biểu đồ
    st.markdown("<hr style='margin: 25px 0; border: 0; border-top: 1px solid #EAEAEA;'/>", unsafe_allow_html=True)

    # --- BIỂU ĐỒ SỐ 2: NHIỆT - ẨM CHU KỲ ---
    st.markdown("### 🌡️ ĐỘNG HỌC MÔI TRƯỜNG: MỐI QUAN HỆ NHIỆT - ẨM CHU KỲ")
    st.markdown("<p style='color: #566573; font-size: 13px; margin-top: -10px;'><span style='color: #E74C3C; font-weight: bold;'>Đường Đỏ</span>: Nhiệt độ (°C) [Trục trái]  |  <span style='color: #3498DB; font-weight: bold;'>Đường Xanh</span>: Độ ẩm (%) [Trục phải] (Đặt chuột vào để cuộn thu phóng)</p>", unsafe_allow_html=True)
    
    # Gọi hàm vẽ biểu đồ Nhiệt - Ẩm trục kép từ charts.py
    st.altair_chart(draw_combined_temp_humidity_chart(df_f), use_container_width=True)

# 6. Khu vực bảng dữ liệu thô đi kèm bên dưới (Tùy chọn xem)
with st.expander("👁️ Xem chi tiết bảng dữ liệu thô (Data Table)"):
    st.dataframe(df_f, use_container_width=True)
