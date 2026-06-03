import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# 1. ตั้งค่าหน้าเว็บ
try:
    icon_image = Image.open("logo.png")
    st.set_page_config(page_title="B6510794 Smart Forecast", page_icon=icon_image, layout="wide")
except FileNotFoundError:
    st.set_page_config(page_title="B6510794 Smart Forecast", page_icon="🏭", layout="wide")

try:
    logo_image = Image.open("logo.png")
    st.logo(logo_image)
except FileNotFoundError:
    pass

st.title("🏭 ระบบพยากรณ์และวางแผนการผลิต (Smart Factory Dashboard)")

with st.sidebar:
    st.header("⚙️ แผงควบคุม (Control Panel)")
    capacity_limit = st.number_input("กำลังการผลิตสูงสุด (Units/เดือน)", min_value=100, value=450, step=10)
    forecast_horizon = st.slider("พยากรณ์ล่วงหน้า (เดือน)", min_value=1, max_value=6, value=3)
    st.markdown("---")
    st.caption("เครื่องมือสนับสนุนการตัดสินใจ: Aggregate Planning")

# ข้อมูลสำรอง (กรณีผู้ใช้ยังไม่อัปโหลดไฟล์)
default_data = {
    'เดือน': ['ม.ค. 67', 'ก.พ. 67', 'มี.ค. 67', 'เม.ย. 67', 'พ.ค. 67', 'มิ.ย. 67'],
    'ยอดขายจริง': [280, 310, 360, 295, 340, 490]
}
df_initial = pd.DataFrame(default_data)

# ---------------------------------------------------------
# 🌟 แท็บการทำงาน (ดึงข้อมูล -> คำนวณ -> แสดงผล)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 กราฟและตารางพยากรณ์", "📂 นำเข้าข้อมูล (Excel)", "💡 แผนรับมือ (Action Plan)"])

with tab2:
    st.subheader("📥 นำเข้าข้อมูลยอดขายจาก Excel")
    
    # 🌟 ฟีเจอร์อัปโหลดไฟล์ Excel
    uploaded_file = st.file_uploader("ลากไฟล์ Excel (.xlsx) มาวางที่นี่ หรือคลิกเพื่อค้นหา", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # ถ้ามีการอัปโหลด ให้ใช้ข้อมูลจาก Excel
        try:
            df_initial = pd.read_excel(uploaded_file)
            st.success("✅ โหลดข้อมูลจาก Excel สำเร็จ!")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
    else:
        st.info("💡 ข้อแนะนำ: ไฟล์ Excel ควรมีหัวคอลัมน์ชื่อ 'เดือน' และ 'ยอดขายจริง'")
        st.write("---")
        st.write("ข้อมูลตัวอย่าง (แก้ไขเพิ่มลดข้อมูลด้านล่างนี้ได้โดยตรงหากไม่อัปโหลดไฟล์):")

    # นำข้อมูลที่ได้ (จาก Excel หรือ Default) มาแสดงให้แก้ได้อีกรอบ
    edited_df = st.data_editor(
        df_initial,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )

# กระบวนการคำนวณพยากรณ์
edited_df = edited_df.dropna(subset=['เดือน', 'ยอดขายจริง'])
historical_sales = edited_df['ยอดขายจริง'].astype(float).tolist()
historical_months = edited_df['เดือน'].astype(str).tolist()

weights = np.array([0.2, 0.3, 0.5])
forecast_values = []
temp_sales = historical_sales.copy()

last_month_name = historical_months[-1] if len(historical_months) > 0 else "ปัจจุบัน"
future_months = [f"พยากรณ์ (+{i+1}) หลัง {last_month_name}" for i in range(forecast_horizon)]

for i in range(forecast_horizon):
    if len(temp_sales) >= 3:
        next_forecast = np.dot(temp_sales[-3:], weights)
    else:
        next_forecast = np.mean(temp_sales) if len(temp_sales) > 0 else 0
    forecast_values.append(int(round(next_forecast, 0)))
    temp_sales.append(next_forecast)

forecast_df = pd.DataFrame({'เดือน': future_months, 'พยากรณ์ความต้องการ (Units)': forecast_values})

# การแสดงผลกราฟในแท็บที่ 1
with tab1:
    st.markdown(f"### 🎯 สรุปสถานการณ์เดือนถัดไป ({future_months[0] if future_months else ''})")
    col1, col2, col3 = st.columns(3)
    if forecast_values:
        col1.metric("ยอดคำสั่งซื้อที่คาดการณ์", f"{forecast_values[0]:,} Units", "คำนวณจากข้อมูลล่าสุด")
        col2.metric("กำลังการผลิตปกติ", f"{capacity_limit:,} Units", "คงที่", delta_color="off")

        if forecast_values[0] > capacity_limit:
            over = forecast_values[0] - capacity_limit
            col3.metric("สถานะระบบ", "🔴 เสี่ยงคอขวด", f"ทะลุขีดจำกัด {over} Units", delta_color="inverse")
        else:
            col3.metric("สถานะระบบ", "🟢 ปกติ", "กำลังผลิตเพียงพอ")
    
    st.markdown("---")
    st.subheader("📈 แนวโน้มข้อมูลยอดขายจริงเปรียบเทียบกับผลพยากรณ์")
    
    ordered_months = historical_months + future_months
    chart_data = pd.DataFrame({
        'เดือน': ordered_months,
        'ยอดขายจริง': historical_sales + [None] * forecast_horizon,
        'ยอดพยากรณ์': [None] * (len(historical_sales)-1) + [historical_sales[-1]] + forecast_values if len(historical_sales) > 0 else forecast_values, 
        'เส้น Capacity': capacity_limit
    })
    if not chart_data.empty:
        chart_data['เดือน'] = pd.Categorical(chart_data['เดือน'], categories=ordered_months, ordered=True)
        st.line_chart(chart_data.set_index('เดือน'), height=350)

    st.subheader("📋 ตารางตัวเลขพยากรณ์ล่วงหน้า")
    st.dataframe(forecast_df.T, use_container_width=True)

with tab3:
    over_capacity_months = forecast_df[forecast_df['พยากรณ์ความต้องการ (Units)'] > capacity_limit]
    if not over_capacity_months.empty:
        st.error("🚨 **ระบบตรวจพบช่วงเวลาที่มีแนวโน้มเกิดคอขวด (Over Capacity):**")
        for index, row in over_capacity_months.iterrows():
            st.write(f"- 🗓️ **{row['เดือน']}**: ความต้องการล้นระบบอยู่ **{row['พยากรณ์ความต้องการ (Units)'] - capacity_limit} Units**")
    else:
        st.success("✨ **เยี่ยมมาก!** กำลังการผลิตสอดคล้องกับความต้องการ ไม่พบปัญหาคอขวด")
