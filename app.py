tab_realtime, tab_json = st.tabs([
    "🌿 REALTIME VPD",
    "📂 JSON → VPD"
])

with tab_realtime:

    st.title("🌿 VPD SMART FARM MONITOR")

    st.write("Realtime VPD Monitoring System")

    # CODE REALTIME CŨ CỦA BẠN GIỮ NGUYÊN
    # KHÔNG CẦN SỬA GÌ PHẦN REALTIME


with tab_json:

    st.markdown("""
    <h3 style='color:#114B72;'>
    📂 PHÂN TÍCH FILE JSON → TÍNH VPD
    </h3>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload file JSON chứa tempkk và humikk",
        type=["json"]
    )

    if uploaded_file:

        try:

            json_data = json.load(uploaded_file)

            # Nếu JSON là list
            if isinstance(json_data, list):

                df = pd.DataFrame(json_data)

            else:

                df = pd.DataFrame([json_data])

            # =========================
            # TỰ TÌM CỘT TEMP / HUM
            # =========================

            temp_col = None
            hum_col = None

            for col in df.columns:

                col_lower = str(col).lower()

                if "tempkk" in col_lower:
                    temp_col = col

                if "humikk" in col_lower:
                    hum_col = col

            # =========================
            # CHECK
            # =========================

            if temp_col is None or hum_col is None:

                st.error(
                    "❌ Không tìm thấy tempkk hoặc humikk trong file JSON"
                )

            else:

                # =========================
                # ÉP KIỂU
                # =========================

                df[temp_col] = pd.to_numeric(
                    df[temp_col],
                    errors="coerce"
                )

                df[hum_col] = pd.to_numeric(
                    df[hum_col],
                    errors="coerce"
                )

                # =========================
                # XÓA DÒNG LỖI
                # =========================

                df = df.dropna(
                    subset=[temp_col, hum_col]
                )

                # =========================
                # TÍNH VPD
                # =========================

                df["VPD (kPa)"] = df.apply(
                    lambda row: calculate_vpd(
                        row[temp_col],
                        row[hum_col]
                    ),
                    axis=1
                )

                # =========================
                # PHÂN LOẠI TRẠNG THÁI
                # =========================

                status_list = []

                for _, row in df.iterrows():

                    vpd = row["VPD (kPa)"]

                    if vpd < 0.4:

                        status = "🔵 Quá Ẩm"

                    elif vpd < 0.8:

                        status = "🌐 Ẩm"

                    elif vpd <= 1.2:

                        status = "🟩 Lý Tưởng"

                    elif vpd <= 1.5:

                        status = "💛 Nóng"

                    else:

                        status = "🔴 Quá Nóng"

                    status_list.append(status)

                df["Trạng thái"] = status_list

                # =========================
                # THỐNG KÊ
                # =========================

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "🌡️ Nhiệt độ TB",
                    f"{df[temp_col].mean():.1f} °C"
                )

                c2.metric(
                    "💧 Độ ẩm TB",
                    f"{df[hum_col].mean():.1f} %"
                )

                c3.metric(
                    "🌿 VPD TB",
                    f"{df['VPD (kPa)'].mean():.2f} kPa"
                )

                # =========================
                # TẠO CỘT GIỜ GIẢ
                # =========================

                df["Hiển thị Giờ"] = [
                    f"{i}"
                    for i in range(len(df))
                ]

                # =========================
                # BIỂU ĐỒ
                # =========================

                st.markdown("### 📈 BIỂU ĐỒ VPD")

                st.altair_chart(
                    draw_vpd_chart(
                        df,
                        0.8,
                        1.2
                    ),
                    use_container_width=True
                )

                # =========================
                # DATAFRAME
                # =========================

                st.markdown("### 📋 BẢNG DỮ LIỆU")

                preview_cols = [
                    temp_col,
                    hum_col,
                    "VPD (kPa)",
                    "Trạng thái"
                ]

                st.dataframe(
                    df[preview_cols],
                    use_container_width=True
                )

        except Exception as err:

            st.error(
                f"❌ Lỗi xử lý file JSON: {err}"
            )

    else:

        st.info(
            "💡 Upload file JSON chứa tempkk và humikk để bắt đầu phân tích."
        )
