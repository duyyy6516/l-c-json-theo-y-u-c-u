import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="JSON Data Pro", layout="wide")
st.title("📊 Công cụ Phân tích Dữ liệu JSON")

# Hàm làm phẳng mạnh mẽ nhất
def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x: flatten(x[a], name + a + '.')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else: out[name[:-1]] = x
    flatten(y)
    return out

uploaded_file = st.file_uploader("Tải lên file JSON", type=['json'])

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        if isinstance(data, dict): data = [data]
        df = pd.DataFrame([flatten_json(row) for row in data])
        
        # Làm sạch cột (giữ lại các cột có dữ liệu)
        df = df.dropna(axis=1, how='all')
        
        # BẢNG DỮ LIỆU GỐC
        st.subheader("📋 Bảng dữ liệu gốc")
        st.data_editor(df, use_container_width=True)
        st.divider()

        # THIẾT LẬP BIỂU ĐỒ
        st.subheader("⚙️ Thiết lập biểu đồ")
        # Tìm cột thời gian
        time_col = next((col for col in df.columns if 'time' in col.lower() or 'thời gian' in col.lower()), None)
        
        # Chọn cột số (loại trừ cột thời gian và ID)
        all_cols = [c for c in df.columns if c != time_col and '_id' not in c]
        selected_keys = st.multiselect("Chọn chỉ số để vẽ biểu đồ:", all_cols)

        if st.button("🚀 TẠO BIỂU ĐỒ", type="primary"):
            if not selected_keys:
                st.warning("Chọn ít nhất 1 cột!")
            else:
                # Ép kiểu dữ liệu từng cột được chọn thành số
                plot_data = df.copy()
                if time_col:
                    plot_data[time_col] = pd.to_datetime(plot_data[time_col].astype(str).str.replace('-', ':').str.replace(':', '-', 2), errors='coerce')
                    plot_data = plot_data.dropna(subset=[time_col])
                    plot_data = plot_data.set_index(time_col)
                
                # Vẽ từng biểu đồ
                for col in selected_keys:
                    st.write(f"**Biểu đồ: {col}**")
                    # Chuyển đổi dữ liệu cột sang số, lỗi thì thành 0
                    series = pd.to_numeric(plot_data[col], errors='coerce').fillna(0)
                    st.line_chart(series)
                    st.write("---")

    except Exception as e:
        st.error(f"Lỗi: {e}")
