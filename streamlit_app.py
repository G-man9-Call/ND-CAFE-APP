import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz

# ฟังก์ชันสำหรับดึงเวลาปัจจุบันของ ซิดนีย์

def get_sydney_time():

sydney_tz =

pytz.timezone('Australia/Sydney') return datetime.now(sydney_tz)

# --- การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="ND Cafe Log", page_icon="☕", layout="centered")

# --- การจัดการฐานข้อมูล ---
DB_NAME = "work_log_streamlit.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shifts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  start_time TEXT, 
                  end_time TEXT, 
                  hours REAL, 
                  pay REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- ส่วนหัวแอป ---
# ดึงเวลาซิดนีย์มาแสดง
 curr_time = get_sydney_time().strftime("%d/ %m/%Y %H:%M:%S") st.markdown(f"<p style='text-align: center;'> Sydney Time: {curr_time} </p>", unsafe_allow_html=True)

# --- ส่วนของการ Clock In/Out ---
st.divider()

# ใช้ Session State เพื่อเก็บเวลาเริ่มงาน
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

col1, col2 = st.columns(2)

with col1:
    # --- แก้ไขส่วน 
    Clock In --- if st.button(" CLOCK IN", use_container_width=True):

# ใช้เวลาซิดนีย์แทน datetime.now()

st.session_state.start_time = get_sydney_time()

st.success(f"เริ่มงานตอน: {st.sessi on_state.start_time.strftime('%H: %M')}")

with col2:
   # --- แก้ไขส่วน Clock Out ---
if st.button("🛑 CLOCK OUT", use_container_width=True):
    if st.session_state.start_time:
        end_time = get_sydney_time() # ใช้เวลาซิดนีย์
        
            # ปรับอัตราค่าจ้างตรงนี้
            hourly_rate = 30 
            pay = round(hours * hourly_rate, 2)
            
            date_str = end_time.strftime("%d/%m/%Y")
            start_str = st.session_state.start_time.strftime("%H:%M")
            end_str = end_time.strftime("%H:%M")
            
            # บันทึกลงฐานข้อมูล
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO shifts (date, start_time, end_time, hours, pay) VALUES (?, ?, ?, ?, ?)",
                      (date_str, start_str, end_str, hours, pay))
            conn.commit()
            conn.close()
            
            st.balloons()
            st.info(f"บันทึกแล้ว: {hours} ชม. | รับเงิน ${pay}")
            st.session_state.start_time = None # Reset เวลา
        else:
            st.warning("คุณยังไม่ได้กด Clock In!")

# --- ส่วนแสดงประวัติ ---
st.divider()
st.subheader("📊 ประวัติการทำงาน")

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT date as 'วันที่', start_time as 'เริ่ม', end_time as 'เลิก', hours as 'ชม.', pay as 'เงิน ($)' FROM shifts ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ฟังก์ชันส่งออกเป็นไฟล์
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ดาวน์โหลดประวัติเป็น CSV",
        data=csv,
        file_name=f'work_log_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
else:
    st.write("ยังไม่มีประวัติการทำงาน")

# --- ปุ่มล้างข้อมูล ---
if st.expander("ตั้งค่าเพิ่มเติม"):
    if st.button("ลบประวัติทั้งหมด"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM shifts")
        conn.commit()
        conn.close()
        st.rerun()
