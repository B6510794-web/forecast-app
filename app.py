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

try:
    logo_image = Image.open("logo.png")
    st.logo(logo_image)
except FileNotFoundError:
    pass

st.title("🏭 ระบบพยากรณ์และวางแผนการผลิต (Smart Factory Dashboard)")

# 2. จัดระเบียบ Sidebar และเพิ่มปุ่มเลือกโมเดลพยากรณ์
with st.sidebar:
    st.header("⚙️ แผงควบคุม (Control Panel)")
    capacity_limit = st.number_input("กำลังการผลิตสูงสุด (Units/เดือน)", min_value=100, value=450, step=10)
    forecast_horizon = st.slider("พยากรณ์ล่วงหน้า (เดือน)", min_value=1, max_value=12, value=12)
    
    st.markdown("---")
    # 🌟 ไฮไลต์ฟีเจอร์ใหม่: ให้ผู้ใช้เลือกโมเดลพยากรณ์ตามความเหมาะสมของระยะเวลา
    st.subheader("🧠 เลือกโมเดลการพยากรณ์")
    selected_model = st.radio(
        "กรุณาเลือกวิธีการคำนวณ:",
        [
            "📊 WMA 3 เดือน (แม่นยำสำหรับระยะสั้น 1-3 เดือน)", 
            "📈 Linear Regression (จับเทรนด์ระยะยาว 4-12 เดือน)",
            "🌊 Seasonal Trend (จับเทรนด์ + ฤดูกาลรายไตรมาส)"
        ]
    )
    
    st.markdown("---")
    st.caption("เครื่องมือสนับสนุนการตัดสินใจ: Aggregate Planning")

# 3. ฐานข้อมูลเริ่มต้น
default_data = {
    'เดือน': ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'],
    'ยอดขายจริง': [280, 310, 360, 295, 340, 490, 410, 390, 440, 525, 515, 480]
}
df_current = pd.DataFrame(default_data)

# 4. ส่วนแท็บการทำงาน
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
        st.info("💡 ปัจจุบันระบบกำลังใช้: ข้อมูลดิบตั้งต้น 12 เดือนจากรูปภาพแรก")
    
    st.write("---")
    st.write("📊 **ตารางตรวจสอบ/แก้ไขข้อมูลล่าสุด:**")
    edited_df = st.data_editor(df_current, num_rows="dynamic", use_container_width=True, key="data_editor")

# 5. กระบวนการประมวลผลคำนวณพยากรณ์ล่วงหน้า (แยกลอจิกตามที่ผู้ใช้เลือก)
edited_df = edited_df.dropna()
col_month = edited_df.columns[0]
col_sales = edited_df.columns[1]

historical_sales = edited_df[col_sales].astype(float).tolist()
historical_months = edited_df[col_month].astype(str).tolist()

last_month_name = historical_months[-1] if len(historical_months) > 0 else "ปัจจุบัน"
future_months = [f"พยากรณ์ (+{i+1}) หลัง {last_month_name}" for i in range(forecast_horizon)]

forecast_values = []

# 🌟 การตัดสินใจเลือกใช้สูตร (If-Else Logic)
if "WMA" in selected_model:
    # --- สูตรที่ 1: WMA (ระยะสั้น) ---
    weights = np.array([0.2, 0.3, 0.5])
    temp_sales = historical_sales.copy()
    for i in range(forecast_horizon):
        if len(temp_sales) >= 3:
            next_forecast = np.dot(temp_sales[-3:], weights)
        else:
            next_forecast = np.mean(temp_sales) if len(temp_sales) > 0 else 0
        forecast_values.append(int(round(next_forecast, 0)))
        temp_sales.append(next_forecast)

elif "Seasonal" in selected_model:
    # --- สูตรที่ 3: Seasonal (อิงฐานข้อมูลล่าสุด ไม่ใช้เส้นความชันซ้ำซ้อน) ---
    if len(historical_sales) >= 12: # ต้องมีข้อมูลอย่างน้อย 1 ปีเพื่อหาฤดูกาล
        # 1. หาค่าเฉลี่ยยอดขายรวมของปีที่แล้ว เพื่อทำดัชนี
        avg_sales = np.mean(historical_sales)
        
        # 2. สร้างดัชนีฤดูกาล (Seasonal Index)
        seasonal_indices = [sale / avg_sales for sale in historical_sales]
        
        # 3. 🌟 สร้างแกนฐาน (Base Level) จาก "ค่าเฉลี่ย 3 เดือนล่าสุด"
        # เพื่อยกกราฟให้เริ่มจากระดับยอดขายปัจจุบัน โดยไม่พุ่งทะยานเป็นทวีคูณ
        current_base_level = np.mean(historical_sales[-3:]) 
        
        for i in range(forecast_horizon):
            # 4. วนหาดัชนีของเดือนนั้นๆ
            month_index = (len(historical_sales) + i) % 12
            
            # 5. เอาแกนฐานล่าสุด * ดัชนีฤดูกาล ได้เลย!
            next_forecast = current_base_level * seasonal_indices[month_index]
            
            forecast_values.append(max(0, int(round(next_forecast, 0))))
    else:
        st.warning("⚠️ การพยากรณ์แบบ Seasonal ต้องใช้ข้อมูลย้อนหลังอย่างน้อย 12 เดือน")
        avg_val = np.mean(historical_sales) if len(historical_sales) > 0 else 0
        forecast_values = [int(round(avg_val, 0))] * forecast_horizon
        
else:
    # --- สูตรที่ 2: Polynomial Regression (เส้นโค้ง จับเทรนด์อย่างเดียว) ---
    if len(historical_sales) >= 3:
        x = np.arange(len(historical_sales))
        y = np.array(historical_sales)
        coefficients = np.polyfit(x, y, 2) 
        a, b, c = coefficients
        
        for i in range(forecast_horizon):
            next_x = len(historical_sales) + i
            next_forecast = (a * (next_x ** 2)) + (b * next_x) + c
            forecast_values.append(max(0, int(round(next_forecast, 0))))
    else:
        avg_val = np.mean(historical_sales) if len(historical_sales) > 0 else 0
        forecast_values = [int(round(avg_val, 0))] * forecast_horizon

forecast_df = pd.DataFrame({'เดือน': future_months, 'พยากรณ์ความต้องการ (Units)': forecast_values})
forecast_df.index = forecast_df.index + 1

# 6. แสดงผลลัพธ์กราฟและแดชบอร์ดในแท็บที่ 1
with tab1:
    if forecast_values:
        st.markdown(f"### 🎯 สรุปสถานการณ์เดือนถัดไป ({future_months[0]})")
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดคำสั่งซื้อที่คาดการณ์", f"{forecast_values[0]:,} Units", f"ด้วยวิธี {selected_model.split()[1]}")
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
        chart_data['เดือน'] = pd.Categorical(chart_data['MONTH'] if 'MONTH' in chart_data.columns else chart_data['เดือน'], categories=ordered_months, ordered=True)
        st.line_chart(chart_data.set_index('เดือน'), height=350)

    st.subheader("📋 ตารางตัวเลขพยากรณ์ล่วงหน้า")
    st.table(forecast_df.T)

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

# 🌟 ฟีเจอร์ใหม่: ระบบวิเคราะห์กลยุทธ์ด้วยค่า VC (Variance Coefficient)
    st.subheader("🧠 วิเคราะห์กลยุทธ์การผลิตอัจฉริยะ (อ้างอิงทฤษฎี IE)")
    
    if len(forecast_values) > 1:
        # 1. คำนวณค่าเฉลี่ย (d_bar) และ ความแปรปรวน (Est. var D)
        mean_demand = np.mean(forecast_values)
        var_demand = np.var(forecast_values, ddof=1) # ddof=1 คือ Sample Variance
        
        # 2. เข้าสูตร VC = Est.var D / (d_bar)^2
        mean_sq = mean_demand ** 2
        vc_value = var_demand / mean_sq if mean_sq > 0 else 0
        
        # แสดงผลตัวเลขให้ผู้บริหารดู
        col1, col2 = st.columns(2)
        col1.metric("ค่าสัมประสิทธิ์ความแปรปรวน (VC)", f"{vc_value:.4f}")
        col2.caption("สูตรคำนวณ: VC = Est. var D / d̄²")
        
        # 3. สร้างเงื่อนไขตัดสินใจตามตำรา
        if vc_value < 0.20:
            st.success(
                f"✅ **ผลวิเคราะห์ (VC < 0.20):** ความต้องการมีความผันผวนต่ำ-ปานกลาง\n\n"
                f"**คำแนะนำ:** มีความเหมาะสมอย่างยิ่งที่จะนำ **กลยุทธ์การปรับเรียบกำลังการผลิต (Level Strategy)** หรือโมเดล **EOQ** มาใช้ โดยโรงงานควรเดินเครื่องผลิตคงที่เฉลี่ยเดือนละ **{int(mean_demand)} Units** เพื่อลดปัญหาสินค้าขาดมือในช่วง Peak Season ครับ"
            )
        else:
            st.warning(
                f"⚠️ **ผลวิเคราะห์ (VC > 0.20):** ความต้องการมีความผันผวนและความไม่แน่นอนสูงมาก\n\n"
                f"**คำแนะนำ:** ไม่เหมาะสมที่จะใช้วิธีปรับเรียบ (Level) เพียงอย่างเดียว เนื่องจากอาจทำให้ต้นทุนสินค้าจมทุนสูงเกินไป ควรพิจารณาใช้ **กลยุทธ์ผลิตตามความต้องการ (Chase Strategy)** หรือใช้โมเดลระดับสูงเช่น ฮิวริสติกของซิลเวอร์-มีล (Silver-Meal) หรือ โปรแกรมเชิงพลวัต (Dynamic Programming) เพื่อปรับการผลิตให้ยืดหยุ่นตามยอดครับ"
            )
