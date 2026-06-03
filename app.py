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

# 3. ฐานข้อมูลเริ่มต้น (ปี 2567)
initial_data = {
    'เดือน': ['ม.ค. 67', 'ก.พ. 67', 'มี.ค. 67', 'เม.ย. 67', 'พ.ค. 67', 'มิ.ย. 67', 'ก.ค. 67', 'ส.ค. 67', 'ก.ย. 67', 'ต.ค. 67', 'พ.ย. 67', 'ธ.ค. 67'],
    'ยอดขายจริง': [280, 310, 360, 295, 340, 490, 410, 390, 440, 525, 515, 480]
}
df_initial = pd.DataFrame(initial_data)

# ---------------------------------------------------------
# 🌟 4. ส่วนแท็บจัดการข้อมูลและประมวลผลพยากรณ์ (สลับลำดับแท็บแล้ว)
# ---------------------------------------------------------

# เปลี่ยนชื่อแท็บ 1 เป็นกราฟ และ แท็บ 2 เป็นตารางข้อมูล
tab1, tab2, tab3 = st.tabs(["📈 กราฟและตารางพยากรณ์", "📝 จัดการข้อมูลยอดขายจริง", "💡 แผนรับมือ (Action Plan)"])

# ⚠️ เทคนิค: ต้องสั่งรันพื้นที่แท็บ 2 ก่อน เพื่อดึงข้อมูลที่ผู้ใช้พิมพ์ มาใช้คำนวณกราฟ
with tab2:
    st.subheader("✏️ ตารางบันทึกยอดขายจริง (เพิ่มหรือแก้ไขข้อมูลได้ที่นี่)")
    st.markdown("💡 **วิธีใช้งาน:** \n"
                "1. สามารถดับเบิลคลิกที่ช่องตัวเลขเพื่อแก้ไขข้อมูลได้ทันที\n"
                "2. หากต้องการเพิ่มข้อมูลเดือนถัดไป ให้เลื่อนเมาส์ไปที่ด้านล่างสุดของตาราง แล้วกดปุ่ม **(➕ Add row)** จากนั้นพิมพ์ชื่อเดือนและยอดขายจริงลงไปได้เลยครับ")
    
    edited_df = st.data_editor(
        df_initial,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )

# 5. ประมวลผลและคำนวณ (รับข้อมูลมาจาก tab2)
edited_df = edited_df.dropna(subset=['เดือน', 'ยอดขายจริง'])

historical_sales = edited_df['ยอดขายจริง'].astype(float).tolist()
historical_months = edited_df['เดือน'].tolist()

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

forecast_df = pd.DataFrame({
    'เดือน': future_months,
    'พยากรณ์ความต้องการ (Units)': forecast_values
})

# ---------------------------------------------------------
# 6. แสดงผลลัพธ์ในแท็บ 1 (Dashboard) และ แท็บ 3
# ---------------------------------------------------------

# นำกราฟและตัวเลขสรุปมาแสดงใน tab1 (ผู้ใช้จะเห็นหน้านี้เป็นหน้าแรก)
with tab1:
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
        'ยอดพยากรณ์': [None] * (len(historical_sales)-1) + [historical_sales[-1]] + forecast_values, 
        'เส้น Capacity': capacity_limit
    })
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
        
        st.info("🔧 **ข้อเสนอแนะสำหรับการจัดตารางการผลิตหลัก (Master Production Schedule):** เพื่อหลีกเลี่ยงค่าล่วงเวลา (OT) ควรใช้กลยุทธ์ **Build Inventory** โดยเริ่มเดินเครื่องเต็มกำลังตั้งแต่วันนี้ในช่วงที่ยอดสั่งซื้อยังต่ำกว่ากำลังการผลิต เพื่อกักตุนเป็น Inventory ไว้ส่งมอบในช่วงเดือนที่เกิดคอขวดครับ")
    else:
        st.success("✨ **เยี่ยมมาก!** กำลังการผลิตสอดคล้องกับความต้องการ ไม่พบปัญหาคอขวดในกรอบเวลาที่ประเมิน")
