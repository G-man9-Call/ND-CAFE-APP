import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz

# ฟังก์ชันสำหรับดึงเวลาปัจจุบันของซิดนีย์
def get_sydney_time():
    sydney_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(sydney_tz)

# --- การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="ND Cafe Log", page_icon="☕", layout="centered")

# --- การจัดการฐานข้อมูล ---
DB_NAME = "work_log_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # เพิ่มคอลัมน์ status เพื่อเช็คว่างานเสร็จหรือยัง
    c.execute('''CREATE TABLE IF NOT EXISTS shifts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  start_time TEXT, 
                  end_time TEXT, 
                  hours REAL, 
                  pay REAL,
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- ส่วนหัวแอป ---
st.markdown("<h1 style='text-align: center; color: #8B4513;'>☕ ND CAFE LOG</h1>", unsafe_allow_html=True)
now_sydney = get_sydney_time()
curr_time = now_sydney.strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<p style='text-align: center;'>🇦🇺 Sydney Time: {curr_time}</p>", unsafe_allow_html=True)

# --- ตรวจสอบสถานะการทำงานจากฐานข้อมูล ---
def get_active_shift():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM shifts WHERE status = 'active' LIMIT 1", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

active_shift = get_active_shift()

st.divider()

col1, col2 = st.columns(2)

with col1:
    # ปุ่ม CLOCK IN จะกดได้เมื่อไม่มีงานที่ค้างอยู่
    if st.button("🚀 CLOCK IN", use_container_width=True, disabled=active_shift is not None):
        start_dt = get_sydney_time()
        date_str = start_dt.strftime("%d/%m/%Y")
        start_str = start_dt.strftime("%H:%M:%S")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO shifts (date, start_time, status) VALUES (?, ?, ?)",
                  (date_str, start_str, 'active'))
        conn.commit()
        conn.close()
        st.rerun()

with col2:
    # ปุ่ม CLOCK OUT จะกดได้เมื่อมีการ CLOCK IN ไว้ก่อนหน้า
    if st.button("🛑 CLOCK OUT", use_container_width=True, disabled=active_shift is None):
        end_dt = get_sydney_time()
        start_time_str = active_shift['start_time']
        date_str = active_shift['date']
        
        # คำนวณเวลา
        start_dt = datetime.strptime(f"{date_str} {start_time_str}", "%d/%m/%Y %H:%M:%S")
        start_dt = pytz.timezone('Australia/Sydney').localize(start_dt)
        
        duration = end_dt - start_dt
        hours = round(duration.total_seconds() / 3600, 2)
        
        hourly_rate = 30 
        pay = round(hours * hourly_rate, 2)
        end_str = end_dt.strftime("%H:%M:%S")
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''UPDATE shifts 
                     SET end_time = ?, hours = ?, pay = ?, status = 'completed' 
                     WHERE id = ?''', (end_str, hours, pay, int(active_shift['id'])))
        conn.commit()
        conn.close()
        
        st.balloons()
        st.success(f"บันทึกสำเร็จ! ทำงานไป {hours} ชม. รับเงิน ${pay}")
        st.rerun()

# แสดงสถานะปัจจุบัน
if active_shift is not None:
    st.info(f"⏳ กำลังทำงาน: เริ่มตั้งแต่วันที่ {active_shift['date']} เวลา {active_shift['start_time']}")
else:
    st.write("🟢 สถานะ: พร้อมเริ่มงาน")

# --- ส่วนแสดงประวัติ ---
st.divider()
st.subheader("📊 ประวัติการทำงาน")

conn = sqlite3.connect(DB_NAME)
df_history = pd.read_sql_query("""
    SELECT date as 'วันที่', 
           start_time as 'เริ่ม', 
           end_time as 'เลิก', 
           hours as 'ชม.', 
           pay as 'เงิน ($)' 
    FROM shifts 
    WHERE status = 'completed' 
    ORDER BY id DESC
""", conn)
conn.close()

if not df_history.empty:
    st.dataframe(df_history, use_container_width=True, hide_index=True)
    
    csv = df_history.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ดาวน์โหลดประวัติเป็น CSV",
        data=csv,
        file_name=f'work_log_{get_sydney_time().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
else:
    st.write("ยังไม่มีประวัติที่สมบูรณ์")

# --- ตั้งค่าเพิ่มเติม ---
if st.expander("ตั้งค่าเพิ่มเติม"):
    if st.button("ลบประวัติทั้งหมด"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM shifts")
        conn.commit()
        conn.close()
        st.rerun()
