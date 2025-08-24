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
fruitsafe_b64 = img_to_base64_str("FruitSafe.png")
poster_b64 = img_to_base64_str("Poster.jpg")

predicted_percent = 0  # ค่าเริ่มต้น

# Check if there is a new row
if len(row_data) >= 10:
    try:
        input_data = [float(x) for x in row_data[:10]]
        prob_safe = model.predict_proba([input_data])[0][1]
        predicted_percent = int(prob_safe * 100)

        # Update session state ONLY when new row exists
        st.session_state.last_prediction = predicted_percent

        # Delete processed row
        sheet.delete_rows(2)

        # Call JS to update result
        call_show_prediction_js = f"showPrediction({predicted_percent});"

    except Exception as e:
        st.error(f"Prediction error: {e}")

else:
    # If no new row, keep the last prediction displayed
    if 'last_prediction' in st.session_state:
        call_show_prediction_js = f"showPrediction({st.session_state.last_prediction});"
    else:
        call_show_prediction_js = "showDefaultState();"


# 🔹 ซ่อน Header / Footer / Menu ของ Streamlit และลบ container padding
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
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
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

# HTML with modal for poster
html_code = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>FruitSafe</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@500&family=Merriweather:wght@700&display=swap');

html, body {{
  margin: 0;
  padding: 0;
  height: 100%;
  overflow-x: hidden;
}}

body {{
  font-family: 'Rubik', sans-serif;
  background-color: #fefae0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 0 10px;
  box-sizing: border-box;
  user-select: none;
}}

.logo {{
  text-align: center;
  margin: 0;
}}
.logo img {{
  max-width: 220px;
  height: auto;
}}

.results-label {{
  color: #e67e22;
  font-size: 22px;
  margin-bottom: 10px;
  border-top: 2px solid #c5e1a5;
  border-bottom: 2px solid #c5e1a5;
  padding: 6px 16px;
}}

.result {{
  text-align: center;
  margin: 20px 0;
  min-height: 150px; /* keep space for result images/advice */
}}

.results-value {{
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
  transition: color 0.3s;
  text-align: center;
}}

.advice {{
  font-size: 16px;
  color: #333;
  text-align: center;
  max-width: 90vw;
  margin-top: 10px;
  min-height: 120px;
}}

.advice img {{
  margin-top: 10px;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.meta {{
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
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
  color: #000;
  font-weight: 500;
}}

.btn {{
  width: 85%;
  max-width: 280px;
  padding: 12px;
  border-radius: 12px;
  border: 2px solid #2e7d32;
  background: #fffdf7;
  text-align: center;
  font-weight: 560;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  font-family: 'Rubik', sans-serif;
  font-size: 1em;
}}

.button-group {{
  width: 85%;
  max-width: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  justify-content: center;
}}

/* Modal styles */
.modal {{
  display: none;
  position: fixed;
  z-index: 9999;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgba(0,0,0,0.5);
  justify-content: center;
  align-items: center;
}}

.modal-content {{
  background-color: #fff;
  padding: 10px;
  border-radius: 10px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  text-align: center;
}}

.close-btn {{
  background-color: #2e7d32;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 8px;
}}

.toggle-section {{
  margin-top: 10px;
}}
</style>
</head>
<body>

<div class="logo">
  <img src="data:image/jpeg;base64,{fruitsafe_b64}" alt="FruitSafe Logo" />
</div>

<div class="results-label">ผลการตรวจ</div>

<div class="result" role="status" aria-live="polite">
  <div id="result" class="results-value"></div>
  <div id="advice" class="advice"></div>
</div>

<div class="meta">
  <div class="percent" id="percentDisplay"><small>สารตกค้าง</small> --%</div>
  <div class="button-group">
    <button class="btn" onclick="openLink()">วิธีล้างฝรั่ง</button>
    <button class="btn" onclick="openModal()">ผลกระทบของสารเคมี</button>
  </div>
</div>

<!-- Modal popup -->
<div id="posterModal" class="modal">
  <div class="modal-content">
    <img src="data:image/jpeg;base64,{poster_b64}" alt="Poster" style="max-width:100%; height:auto; border-radius:10px;">
    <br>
    <button class="close-btn" onclick="closeModal()">ปิด</button>
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

  // push elements down same as result state
  resultEl.textContent = '';
  percentEl.innerHTML = '<small>สารตกค้าง</small> --%';
  percentEl.style.color = '#666';
  adviceEl.innerHTML = '';
}}

// Modal functions
function openModal() {{
  document.getElementById('posterModal').style.display = 'flex';
}}

function closeModal() {{
  document.getElementById('posterModal').style.display = 'none';
}}

function openLink() {{
  window.open('https://youtube.com/shorts/H2OW4IHmfYM?feature=share/', '_blank');
}}

{call_show_prediction_js}
</script>

</body>
</html>
"""

st.components.v1.html(html_code, height=800, scrolling=True)







