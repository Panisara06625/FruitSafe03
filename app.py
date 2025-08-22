import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import joblib
from streamlit_autorefresh import st_autorefresh
import base64

# รีเฟรชทุก 10 วินาที (10000 ms)
st_autorefresh(interval=10_000, key="refresh")

# โหลดโมเดล
model = joblib.load('Model.pkl')

# กำหนด scope และโหลดข้อมูล service account จาก secrets ของ Streamlit Cloud
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)

# เชื่อมต่อ Google Sheet
client = gspread.authorize(creds)
sheet = client.open("FruitSafe03").sheet1

# ดึงข้อมูลแถวที่ 2 จาก Sheet
try:
    row_data = sheet.row_values(2)
except Exception as e:
    st.error(f"Cannot access Google Sheet: {e}")
    st.stop()

# ฟังก์ชันแปลงรูปภาพเป็น base64 string
def img_to_base64_str(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# โหลดภาพและแปลงเป็น base64
img0_b64 = img_to_base64_str("guava0.png")
img1_b64 = img_to_base64_str("guava1.png")
img3_b64 = img_to_base64_str("guava3.png")

predicted_percent = 0  # ค่าเริ่มต้น

if len(row_data) >= 10:
    try:
        input_data = [float(x) for x in row_data[:10]]
        prob_safe = model.predict_proba([input_data])[0][1]
        predicted_percent = int(prob_safe * 100)

        # ลบแถวที่ 1 หลังประมวลผล
        sheet.delete_rows(2)

    except Exception as e:
        st.error(f"Prediction error: {e}")

# เรียก JS ฟังก์ชันเมื่อมีผลลัพธ์ หรือแสดงสถานะเริ่มต้น
if len(row_data) >= 10:
    # มีข้อมูลใหม่ - แสดงผลลัพธ์ใหม่และบันทึก
    call_show_prediction_js = f"showPrediction({predicted_percent});"
    st.session_state.last_prediction = predicted_percent
elif 'last_prediction' in st.session_state and st.session_state.last_prediction > 0:
    # ไม่มีข้อมูลใหม่ แต่มีผลลัพธ์ล่าสุด - แสดงผลลัพธ์ล่าสุด
    call_show_prediction_js = f"showPrediction({st.session_state.last_prediction});"
else:
    # ไม่มีข้อมูลและไม่มีผลลัพธ์ล่าสุด - แสดงสถานะรอ
    call_show_prediction_js = "showDefaultState();"

# ซ่อน Header / Footer / Menu ของ Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] {
        background-color: #fefae0;
    }
    </style>
""", unsafe_allow_html=True)

# HTML ฝังผลลัพธ์
html_code = f"""
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
  <title>FruitSafe</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@500&family=Merriweather:wght@700&display=swap');

    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      overflow: hidden;
    }}

    body {{
      font-family: 'Rubik', sans-serif;
      background-color: #fefae0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 10px;
      height: 100vh;
      box-sizing: border-box;
      user-select: none;
      position: relative;
    }}

    .logo {{
      font-family: 'Merriweather', serif;
      font-size: 28px;
      color: #2e7d32;
      text-align: center;
      margin-bottom: 15px;
    }}

    .results-label {{
      color: #e67e22;
      font-size: 18px;
      margin-bottom: 8px;
      border-top: 2px solid #c5e1a5;
      border-bottom: 2px solid #c5e1a5;
      padding: 4px 12px;
    }}

    .advice {{
      font-size: 14px;
      color: #333;
      text-align: center;
      max-width: 90vw;
      margin-top: 10px;
      min-height: 140px;
    }}

    .advice img {{
      margin-top: 10px;
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .confidence {{
      position: absolute;
      bottom: 10px;
      right: 12px;
      font-size: 12px;
      color: #666;
      font-style: italic;
    }}
  </style>
</head>
<body>

  <div class="logo">Fruit<br>Safe</div>

  <div class="results-label">ผลการตรวจ</div>
  <div id="advice" class="advice"></div>
  <div id="confidence" class="confidence"></div>

  <script>
    function showPrediction(value) {{
      const adviceEl = document.getElementById('advice');
      const confEl = document.getElementById('confidence');

      let advice = '';
      let imgSrc = '';
      let imgAlt = '';

      if (value <= 20) {{
        advice = '<span style="font-size: 1.6em; color: green;">ปลอดภัย</span>';
        imgSrc = "data:image/png;base64,{img1_b64}";
        imgAlt = 'รูปปลอดภัย';
      }} else if (value <= 40) {{
        advice = '<span style="font-size: 1.6em; color: #e67e22;">เสี่ยงปานกลาง</span><br>' +
                 '<span style="font-size: 1.1em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img3_b64}";
        imgAlt = 'รูปเสี่ยงปานกลาง';
      }} else {{
        advice = '<span style="font-size: 1.6em; color: red;">เสี่ยงสูง!</span><br>' +
                 '<span style="font-size: 1.1em;">ควรล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img0_b64}";
        imgAlt = 'รูปเสี่ยงสูง';
      }}

      advice += `<br><img src="${{imgSrc}}" alt="${{imgAlt}}">`;

             adviceEl.innerHTML = advice;
       confEl.innerHTML = `Confidence: ${{value}}%`;
     }}

     function showDefaultState() {{
       const adviceEl = document.getElementById('advice');
       const confEl = document.getElementById('confidence');
       
       adviceEl.innerHTML = '<span style="font-size: 1.4em; color: #666;">รอข้อมูล...</span>';
       confEl.innerHTML = '';
     }}

     {call_show_prediction_js}
  </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=100, scrolling=False)



