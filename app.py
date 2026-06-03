import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# 1. ตั้งค่าหน้าเว็บให้กว้างเต็มจอ
try:
    icon_image = Image.open("logo.png")
    st.set_page_config(page_title="B6510794 Smart Forecast", page_icon=icon_image, layout="wide")
except FileNotFoundError:
    st.set_page_config(page_title="B6510794 Smart Forecast", page_icon="🏭", layout="wide")

# แสดงโลโก้จริงบนหน้าเว็บ
try:
    logo_image = Image.open("logo.png")
    st.logo(logo_image)
except FileNotFoundError:
    pass

st.title("🏭 ระบบพยากรณ์และวางแผนการผลิต (Smart Factory Dashboard)")

# 2. จัดระเบียบ Sidebar
with st.sidebar:
    st.header("⚙️ แผงควบคุม (Control Panel)")
    capacity_limit = st.number_input("กำลังการผลิตสูงสุด (Units/เดือน)", min_value=100, value=450, step=10)
    forecast_horizon = st.slider("พยากรณ์ล่วงหน้า (เดือน)", min_value=1, max_value=6, value=3)
    st.markdown("---")
    st.caption("เครื่องมือสนับสนุนการตัดสินใจ: Aggregate Planning")

# 🌟 3. ฐานข้อมูลเริ่มต้นดึงมาจากรูปแรกที่เคยส่งมา (ครบทั้ง 12 เดือน)
default_data = {
    'เดือน': ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'],
    'ยอดขายจริง': [280, 310, 360, 295, 340, 490, 410, 390, 440, 525, 515, 480]
}
df_current = pd.DataFrame(default_data)

# ---------------------------------------------------------
# 4. ส่วนแท็บการทำงาน
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 กราฟและตารางพยากรณ์", "📂 นำเข้าข้อมูล (Excel)", "💡 แผนรับมือ (Action Plan)"])

with tab2:
    st.subheader("📥 นำเข้าข้อมูลยอดขายจาก Excel")
    
    uploaded_file = st.file_uploader("ลากไฟล์ Excel (.xlsx) มาวางที่นี่ หรือคลิกเพื่อค้นหา", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            df_current = pd.read_excel(uploaded_file)
            st.success("✅ โหลดข้อมูลจาก Excel ใหม่สำเร็จ!")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
    else:
        st.info("💡 ปัจจุบันระบบกำลังใช้: ข้อมูลดิบตั้งต้น 12 เดือนจากรูปภาพแรก (หากต้องการเปลี่ยน สามารถอัปโหลดไฟล์ Excel ของคุณทับได้เลย)")
    
    st.write("---")
    st.write("📊 **ตารางตรวจสอบ/แก้ไขข้อมูลล่าสุด:**")
    
    edited_df = st.data_editor(
        df_current,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )

# 5. กระบวนการประมวลผลคำนวณพยากรณ์ล่วงหน้า
edited_df = edited_df.dropna()
col_month = edited_df.columns[0]
col_sales = edited_df.columns[1]

historical_sales = edited_df[col_sales].astype(float).tolist()
historical_months = edited_df[col_month].astype(str).tolist()

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

# 6. แสดงผลลัพธ์กราฟและแดชบอร์ดในแท็บที่ 1
with tab1:
    if forecast_values:
        st.markdown(f"### 🎯 สรุปสถานการณ์เดือนถัดไป ({future_months[0]})")
        col1, col2, col3 = st.columns(3)
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
        # 🌟 แก้ไขจุดนี้ให้เป็น 'เดือน' เรียบร้อยแล้ว กราฟจะเรียงถูกและเส้นประหลาดจะหายไป
        chart_data['เดือน'] = pd.Categorical(chart_data['เดือน'], categories=ordered_months, ordered=True)
        st.line_chart(chart_data.set_index('เดือน'), height=350)

    st.subheader("📋 ตารางตัวเลขพยากรณ์ล่วงหน้า")
    st.dataframe(forecast_df.T, use_container_width=True)

# 7. แผนรับมือในแท็บที่ 3
with tab3:
    over_capacity_months = forecast_df[forecast_df['พยากรณ์ความต้องการ (Units)'] > capacity_limit]
    if not over_capacity_months.empty:
        st.error("🚨 **ระบบตรวจพบช่วงเวลาที่มีแนวโน้มเกิดคอขวด (Over Capacity):**")
        for index, row in over_capacity_months.iterrows():
            st.write(f"- 🗓️ **{row['เดือน']}**: ความต้องการล้นระบบอยู่ **{row['พยากรณ์ความต้องการ (Units)'] - capacity_limit} Units**")
        st.info("🔧 **ข้อเสนอแนะ:** ควรกักตุนสินค้าคงคลัง (Build Inventory) ไว้ล่วงหน้าตั้งแต่ช่วงเดือนที่ยอดขายยังไม่ล้นกำลังผลิต เพื่อนำมาส่งมอบในเดือนเหล่านี้โดยไม่ต้องจ่ายค่าล่วงเวลา (OT) ครับ")
    else:
        st.success("✨ **เยี่ยมมาก!** ปริมาณการผลิตสอดคล้องกับความต้องการ ไม่พบปัญหาคอขวดในกรอบเวลาที่ประเมิน")
