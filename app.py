import streamlit as st
import pandas as pd
import numpy as np

# 1. ตั้งค่าหน้าเว็บให้กว้างเต็มจอ
st.set_page_config(page_title="Smart Factory Forecast", page_icon="🏭", layout="wide")
st.title("🏭 ระบบพยากรณ์และวางแผนการผลิต (Smart Factory Dashboard)")

# 2. จัดระเบียบ Sidebar ให้สะอาดตา
with st.sidebar:
    st.header("⚙️ แผงควบคุม (Control Panel)")
    capacity_limit = st.number_input("กำลังการผลิตสูงสุด (Units/เดือน)", min_value=100, value=450, step=10)
    forecast_horizon = st.slider("พยากรณ์ล่วงหน้า (เดือน)", min_value=1, max_value=6, value=3)
    st.markdown("---")
    st.caption("เครื่องมือสนับสนุนการตัดสินใจ: Aggregate Planning")

# 3. ข้อมูลและการคำนวณ (ซ่อนไว้ประมวลผลเบื้องหลัง)
data = {
    'เดือน': ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'],
    'ยอดขายจริง': [280, 310, 360, 295, 340, 490, 410, 390, 440, 525, 515, 480]
}
df = pd.DataFrame(data)

historical_sales = df['ยอดขายจริง'].tolist()
weights = np.array([0.2, 0.3, 0.5])
forecast_values = []
temp_sales = historical_sales.copy()
future_months = ['ม.ค. 68', 'ก.พ. 68', 'มี.ค. 68', 'เม.ย. 68', 'พ.ค. 68', 'มิ.ย. 68']

for i in range(forecast_horizon):
    next_forecast = np.dot(temp_sales[-3:], weights)
    forecast_values.append(int(round(next_forecast, 0)))
    temp_sales.append(next_forecast)

# ---------------------------------------------------------
# 🌟 4. ส่วนหน้าจอแสดงผลแบบใหม่ (Modern Dashboard Layout)
# ---------------------------------------------------------

st.markdown("### 🎯 สรุปสถานการณ์เดือนถัดไป (มกราคม 2568)")

col1, col2, col3 = st.columns(3)
col1.metric("ยอดคำสั่งซื้อที่คาดการณ์", f"{forecast_values[0]:,} Units", "อัปเดตล่าสุด")
col2.metric("กำลังการผลิตปกติ", f"{capacity_limit:,} Units", "คงที่", delta_color="off")

if forecast_values[0] > capacity_limit:
    over = forecast_values[0] - capacity_limit
    col3.metric("สถานะระบบ", "🔴 เสี่ยงคอขวด", f"ทะลุขีดจำกัด {over} Units", delta_color="inverse")
else:
    col3.metric("สถานะระบบ", "🟢 ปกติ", "กำลังผลิตเพียงพอ")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📈 กราฟแสดงแนวโน้ม", "📋 ตารางข้อมูลเชิงลึก", "💡 แผนรับมือ (Action Plan)"])

with tab1:
    st.caption("เปรียบเทียบยอดขายจริง ยอดพยากรณ์ และเส้นขีดจำกัดกำลังการผลิต")
    
    # 🌟 จุดที่แก้ไข: กำหนดลำดับเดือนให้ถูกต้องตามเวลา
    ordered_months = df['เดือน'].tolist() + future_months[:forecast_horizon]
    
    chart_data = pd.DataFrame({
        'เดือน': ordered_months,
        'ยอดขายจริง': df['ยอดขายจริง'].tolist() + [None] * forecast_horizon,
        'ยอดพยากรณ์': [None] * 11 + [df['ยอดขายจริง'].iloc[-1]] + forecast_values, 
        'เส้น Capacity': capacity_limit
    })
    
    # 🌟 จุดที่แก้ไข: สั่งล็อคคอลัมน์ 'เดือน' ให้เป็น Categorical Data ไม่ให้เรียงตามตัวอักษร
    chart_data['เดือน'] = pd.Categorical(chart_data['เดือน'], categories=ordered_months, ordered=True)
    
    st.line_chart(chart_data.set_index('เดือน'), height=350)

with tab2:
    st.caption("สรุปตัวเลขการพยากรณ์ล่วงหน้า")
    forecast_df = pd.DataFrame({'เดือน': future_months[:forecast_horizon], 'พยากรณ์ความต้องการ (Units)': forecast_values})
    st.dataframe(forecast_df.T, use_container_width=True)

with tab3:
    over_capacity_months = forecast_df[forecast_df['พยากรณ์ความต้องการ (Units)'] > capacity_limit]
    if not over_capacity_months.empty:
        st.error("🚨 **ระบบตรวจพบเดือนที่มีแนวโน้มเกิดคอขวด (Over Capacity):**")
        for index, row in over_capacity_months.iterrows():
            st.write(f"- 🗓️ **{row['เดือน']}**: ความต้องการล้นระบบอยู่ **{row['พยากรณ์ความต้องการ (Units)'] - capacity_limit} Units**")
        
        st.info("🔧 **ข้อเสนอแนะสำหรับการจัดตารางการผลิตหลัก (Master Production Schedule):** เพื่อหลีกเลี่ยงค่าล่วงเวลา (OT) ควรใช้กลยุทธ์ **Build Inventory** โดยเริ่มเดินเครื่องเต็มกำลังที่ 450 Units ตั้งแต่ช่วงต้นปีที่เครื่องจักรว่าง เพื่อกักตุนเป็น Inventory ไว้ส่งมอบในเดือนเหล่านี้ครับ")
    else:
        st.success("✨ **เยี่ยมมาก!** ปริมาณการผลิตสอดคล้องกับความต้องการ ไม่พบปัญหาคอขวดในกรอบเวลาที่ประเมิน")