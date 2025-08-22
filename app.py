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
fruitsafe_b64 = img_to_base64_str("FruitSafe.jpg")
poster_b64 = img_to_base64_str("Poster.jpg")

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
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
    }
    .stApp {
        padding: 0 !important;
        margin: 0 !important;
    }
    .stApp > header {
        display: none !important;
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
      justify-content: flex-start;
      padding: 0 10px;
      height: 100vh;
      box-sizing: border-box;
      user-select: none;
      position: relative;
    }}

    .logo {{
      font-family: 'Merriweather', serif;
      font-size: 36px;
      color: #2e7d32;
      text-align: center;
      margin-bottom: 15px;
      margin-top: 0px;
    }}

    .results-label {{
      color: #e67e22;
      font-size: 22px;
      margin-bottom: 15px;
      border-top: 2px solid #c5e1a5;
      border-bottom: 2px solid #c5e1a5;
      padding: 6px 16px;
    }}

    .advice {{
      font-size: 16px;
      color: #333;
      text-align: center;
      max-width: 90vw;
      margin-top: 15px;
      min-height: 180px;
    }}

    .advice img {{
      margin-top: 10px;
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .results-value {{
      font-size: 24px;
      font-weight: bold;
      margin-bottom: 8px;
      transition: color 0.3s;
      text-align: center;
    }}

    .result {{
      text-align: center;
      margin: 30px 0;
    }}

    .meta {{
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 15px;
      margin-top: 30px;
    }}

    .percent {{
      font-size: 22px;
      font-weight: 700;
      text-align: center;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .percent small {{
      font-size: 16px;
      color: #000000;
      font-weight: 500;
    }}

    .btn {{
      width: 85%;
      max-width: 280px;
      padding: 15px;
      border-radius: 12px;
      border: 2px solid #2e7d32;
      background: #fffdf7;
      text-align: center;
      font-weight: 560;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      font-family: 'Rubik', sans-serif;
      font-size: 1.1em;
    }}

    .button-group {{
      width: 85%;
      max-width: 280px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      justify-content: center;
    }}

    .toggle-btn {{
      width: 100%;
      background: none;
      border: none;
      font-size: 1.1em;
      font-weight: 565;
      color: #2f8b3e;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0;
    }}

    .arrow {{
      display: inline-block;
      transition: transform 0.3s ease;
      font-weight: 700;
      font-size: 1.2em;
    }}

    .toggle-btn[aria-expanded="true"] .arrow {{
      transform: rotate(180deg);
    }}

    .toggle-content {{
      margin-top: 12px;
      font-size: 1em;
      line-height: 1.4;
      color: #333;
    }}

    .toggle-content img {{
      max-width: 100%;
      height: auto;
      border-radius: 10px;
    }}

    .toggle-section {{
      margin-top: 25px;
    }}
  </style>
</head>
<body>

  <div class="logo">Fruit<br>Safe</div>

  <div class="results-label">ผลการตรวจ</div>
  
  <div class="result" role="status" aria-live="polite">
    <div id="result" class="results-value"></div>
    <div id="advice" class="advice"></div>
  </div>

  <div class="meta">
    <div class="percent" id="percentDisplay"><small>สารตกค้าง</small> --%</div>
    <div class="button-group">
      <button class="btn" onclick="openLink()">วิธีการล้างฝรั่ง</button>
    </div>
  </div>

  <div class="toggle-section">
    <button class="toggle-btn" aria-expanded="false" aria-controls="info1" onclick="toggleInfo('info1', this)">
       <span style="border-bottom: 2px solid #2f8b3e;">สารเคมีผลกระทบคืออะไร</span>
      <span class="arrow">▼</span>
    </button>
    <div id="info1" class="toggle-content" hidden>
      <img src="data:image/jpeg;base64,{poster_b64}" alt="โปสเตอร์สารเคมี organophosphate และ Carbamate" style="max-width:100%; height:auto;">
    </div>
  </div>

  <script>
    function showPrediction(value) {{
      const adviceEl = document.getElementById('advice');
      const resultEl = document.getElementById('result');
      const percentEl = document.getElementById('percentDisplay');

      let color = '';
      let advice = '';
      let imgSrc = '';
      let imgAlt = '';

      if (value <= 20) {{
        color = 'green';
        advice = '<span style="font-size: 2em; color: green;">เสี่ยงต่ำ ปลอดภัย</span>';
        imgSrc = "data:image/png;base64,{img1_b64}";
        imgAlt = 'รูปความเสี่ยงต่ำ';
      }} else if (value <= 40) {{
        color = '#e67e22';
        advice = '<span style="font-size: 2em; color: #e67e22;">เสี่ยงปานกลาง</span><br> ' +
                 '<span style="font-size: 1.3em">ควรล้างผลไม้เพิ่ม และตรวจอีกครั้ง</span>';
        imgSrc = "data:image/png;base64,{img3_b64}";
        imgAlt = 'รูปความเสี่ยงปานกลาง';
      }} else {{
        color = 'red';
        advice = '<span style="font-size: 2em; color: red;">เสี่ยงสูง!</span><br>' +
                 '<span style="font-size: 1.3em;">ต้องล้างผลไม้เพิ่มหลายรอบ และตรวจอีกครั้ง</span><br>';
        imgSrc = "data:image/png;base64,{img0_b64}";
        imgAlt = 'รูปความเสี่ยงสูง';
      }}

      resultEl.textContent = '';
      percentEl.innerHTML = '<small>สารตกค้าง</small> ' + value + '%';
      percentEl.style.color = color;
      adviceEl.innerHTML = advice + `<br><img src="${{imgSrc}}" alt="${{imgAlt}}">`;
    }}

    function showDefaultState() {{
      const adviceEl = document.getElementById('advice');
      const resultEl = document.getElementById('result');
      const percentEl = document.getElementById('percentDisplay');
      
      resultEl.textContent = '';
      percentEl.innerHTML = '<small>สารตกค้าง</small> --%';
      percentEl.style.color = '#666';
      adviceEl.innerHTML = '<span style="font-size: 1.4em; color: #666;">รอข้อมูล...</span>';
    }}

    function openLink() {{
      window.open('https://youtube.com/shorts/H2OW4IHmfYM?feature=share/', '_blank');
    }}

    function toggleInfo(id, btn) {{
      const content = document.getElementById(id);
      const expanded = btn.getAttribute("aria-expanded") === "true";
      if (expanded) {{
        content.hidden = true;
        btn.setAttribute("aria-expanded", "false");
      }} else {{
        content.hidden = false;
        btn.setAttribute("aria-expanded", "true");
      }}
    }}

    {call_show_prediction_js}
  </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=1200, scrolling=False)






