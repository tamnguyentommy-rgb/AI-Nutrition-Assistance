from flask import Flask, render_template, request, jsonify
import pulp
import json
import base64
from groq import Groq
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import threading
import random

app = Flask(__name__)

# =======================================================
# CẤU HÌNH GROQ AI
# =======================================================
GROQ_API_KEY = "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"

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Lỗi Config Groq: {e}")
    client = None

# =======================================================
# HỆ THỐNG CẬP NHẬT DATABASE HÀNG NGÀY
# =======================================================
class DailyFoodDatabase:
    def __init__(self):
        self.market_info = "Chưa có dữ liệu thị trường mới."
        self.last_updated = None

    def update(self):
        print("🔄 System: Đang chạy cập nhật dữ liệu thực phẩm hàng ngày...")
        try:
            url = "https://vnexpress.net/doi-song/am-thuc"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                titles = [a.get('title') for a in soup.find_all('h3', class_='title-news')[:5]]
                clean_titles = [t for t in titles if t]
                self.market_info = "Tin tức thực phẩm hôm nay: " + "; ".join(clean_titles)
                self.last_updated = datetime.now()
                print(f"✅ Đã cập nhật DB: {self.market_info}")
            else:
                print("⚠️ Không kết nối được nguồn tin tức.")
        except Exception as e:
            print(f"❌ Lỗi cập nhật: {e}")

daily_db = DailyFoodDatabase()

@app.before_request
def check_daily_update():
    should_update = False
    if daily_db.last_updated is None:
        should_update = True
    elif (datetime.now() - daily_db.last_updated) > timedelta(hours=24):
        should_update = True

    if should_update:
        t = threading.Thread(target=daily_db.update)
        t.start()

# =======================================================
# CÁC HÀM AI (ĐÃ FIX LỖI FORMAT)
# =======================================================

def call_groq_chat(prompt, model="llama-3.3-70b-versatile", custom_system=None):
    """
    Hàm chat text thông minh.
    - custom_system: Cho phép truyền vai trò cụ thể (Bếp trưởng, Bác sĩ...)
    """
    if not client: return None
    
    current_market = daily_db.market_info
    
    # Nếu không có vai trò cụ thể, dùng mặc định
    if custom_system:
        system_instruction = f"{custom_system}. \nLƯU Ý THỊ TRƯỜNG: {current_market}."
    else:
        system_instruction = f"Bạn là chuyên gia dinh dưỡng và đầu bếp Việt Nam. Thông tin thị trường: {current_market}. Trả về định dạng HTML (<b>, <ul>, <li>) ngắn gọn. KHÔNG dùng Markdown."

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )
        content = chat_completion.choices[0].message.content
        
        # --- [FIX QUAN TRỌNG] LÀM SẠCH DỮ LIỆU ---
        # Xoá các ký tự Markdown thừa nếu AI lỡ thêm vào
        content = content.replace("```html", "").replace("```", "").strip()
        # Xoá dấu } hoặc { nếu lỡ xuất hiện ở đầu/cuối
        if content.startswith("}"): content = content[1:].strip()
        if content.startswith("{"): content = content[1:].strip()
        
        return content
    except Exception as e:
        print(f"Lỗi Groq Chat: {e}")
        return None

# Đơn vị Price: k VNĐ / 1 gram (VD: 0.15 = 150k/kg)
foodData = {
    # --- THỊT (MEAT) ---
    "Thịt heo nạc":  {"cal":2.42, "pro":0.27, "carb":0,    "fat":0.14,  "price":0.14, "type": "meat"}, # 140k/kg
    "Gan gà":       {"cal":1.67, "pro":0.24, "carb":0.01, "fat":0.05,  "price":0.04, "type": "meat"}, # 40k/kg
    "Ức Gà":        {"cal":1.65, "pro":0.31, "carb":0,    "fat":0.036, "price":0.08, "type": "meat"}, # 80k/kg
    "Thịt bò nạc":   {"cal":2.50, "pro":0.26, "carb":0,    "fat":0.15,  "price":0.28, "type": "meat"}, # 280k/kg
    "Thịt vịt":      {"cal":3.37, "pro":0.19, "carb":0,    "fat":0.28,  "price":0.11, "type": "meat"}, # 110k/kg
    "Thịt cừu":      {"cal":2.94, "pro":0.25, "carb":0,    "fat":0.21,  "price":0.35, "type": "meat"}, # 350k/kg
    "Thịt dê":       {"cal":1.43, "pro":0.27, "carb":0,    "fat":0.03,  "price":0.32, "type": "meat"}, # 320k/kg
    "Thịt trâu":     {"cal":1.31, "pro":0.26, "carb":0,    "fat":0.02,  "price":0.26, "type": "meat"}, # 260k/kg
    "Bắp bò":        {"cal":2.01, "pro":0.28, "carb":0,    "fat":0.08,  "price":0.30, "type": "meat"}, # 300k/kg
    "Sườn bò":       {"cal":3.40, "pro":0.21, "carb":0,    "fat":0.29,  "price":0.29, "type": "meat"}, # 290k/kg
    "Gan heo":       {"cal":1.34, "pro":0.21, "carb":0.02, "fat":0.03,  "price":0.03, "type": "meat"}, # 30k/kg (Rẻ)
    "Huyết heo":     {"cal":0.27, "pro":0.05, "carb":0,    "fat":0.001, "price":0.01, "type": "meat"}, # 10k/kg (Siêu rẻ)
    "Mề gà":         {"cal":0.94, "pro":0.18, "carb":0,    "fat":0.02,  "price":0.05, "type": "meat"}, # 50k/kg

    # --- HẢI SẢN (FISH/SEAFOOD) ---
    "Cá nục":       {"cal":1.50, "pro":0.25, "carb":0,    "fat":0.05,  "price":0.06, "type": "fish"}, # 60k/kg
    "Cá hồi":        {"cal":2.08, "pro":0.20, "carb":0,    "fat":0.13,  "price":0.55, "type": "fish"}, # 550k/kg
    "Cá basa":       {"cal":1.20, "pro":0.18, "carb":0,    "fat":0.04,  "price":0.05, "type": "fish"}, # 50k/kg
    "Tôm":           {"cal":0.99, "pro":0.24, "carb":0.002,"fat":0.003, "price":0.22, "type": "seafood"}, # 220k/kg
    "Mực":           {"cal":0.92, "pro":0.15, "carb":0.03, "fat":0.01,  "price":0.25, "type": "seafood"}, # 250k/kg
    "Cua biển":      {"cal":0.83, "pro":0.18, "carb":0.01, "fat":0.01,  "price":0.45, "type": "seafood"}, # 450k/kg
    "Ghẹ":           {"cal":0.87, "pro":0.19, "carb":0,    "fat":0.01,  "price":0.35, "type": "seafood"}, # 350k/kg
    "Sò huyết":      {"cal":1.43, "pro":0.25, "carb":0.03, "fat":0.02,  "price":0.15, "type": "seafood"}, # 150k/kg
    "Nghêu":         {"cal":0.74, "pro":0.12, "carb":0.03, "fat":0.01,  "price":0.04, "type": "seafood"}, # 40k/kg
    "Hàu":           {"cal":0.68, "pro":0.09, "carb":0.04, "fat":0.02,  "price":0.05, "type": "seafood"}, # 50k/kg
    "Bạch tuộc":     {"cal":0.82, "pro":0.15, "carb":0.02, "fat":0.01,  "price":0.18, "type": "seafood"}, # 180k/kg
    "Cá tráp":       {"cal":1.28, "pro":0.21, "carb":0,    "fat":0.04,  "price":0.12, "type": "fish"},
    "Cá chim":       {"cal":1.40, "pro":0.20, "carb":0,    "fat":0.06,  "price":0.14, "type": "fish"},
    "Cá cơm khô":    {"cal":2.62, "pro":0.59, "carb":0,    "fat":0.03,  "price":0.18, "type": "fish"}, # 180k/kg
    "Cá nục bông":   {"cal":1.10, "pro":0.21, "carb":0,    "fat":0.03,  "price":0.05, "type": "fish"}, # 50k/kg

    # --- TRỨNG & VEGAN (ĐẠM THỰC VẬT) ---
    "Trứng Gà":     {"cal":1.55, "pro":0.13, "carb":0.011,"fat":0.11,  "price":0.06, "type": "egg"},   # ~3.5k/trứng 55g
    "Trứng cút":     {"cal":1.58, "pro":0.13, "carb":0.01, "fat":0.11,  "price":0.07, "type": "egg"},
    "Đậu hũ":       {"cal":0.76, "pro":0.08, "carb":0.019,"fat":0.048, "price":0.03, "type": "vegan"}, # 3k/miếng 100g
    "Đậu xanh":      {"cal":3.47, "pro":0.23, "carb":0.62, "fat":0.01,  "price":0.05, "type": "vegan"}, # 50k/kg
    "Đậu đen":       {"cal":3.41, "pro":0.24, "carb":0.60, "fat":0.01,  "price":0.06, "type": "vegan"},
    "Đậu đỏ":        {"cal":3.29, "pro":0.22, "carb":0.61, "fat":0.01,  "price":0.06, "type": "vegan"},
    "Đậu hũ ky":     {"cal":4.00, "pro":0.45, "carb":0.10, "fat":0.20,  "price":0.15, "type": "vegan"}, # 150k/kg

    # --- TINH BỘT (STARCH) ---
    "Cơm trắng":    {"cal":1.30, "pro":0.027,"carb":0.28, "fat":0.003, "price":0.02, "type": "starch"}, # Gạo 20k/kg
    "Khoai lang":   {"cal":0.86, "pro":0.016,"carb":0.20, "fat":0.001, "price":0.025,"type": "starch"}, # 25k/kg
    "Bánh mì":      {"cal":2.60, "pro":0.09, "carb":0.49, "fat":0.03,  "price":0.04, "type": "starch"}, # 4k/ổ
    "Yến mạch":      {"cal":3.89, "pro":0.17, "carb":0.66, "fat":0.07,  "price":0.08, "type": "starch"}, # 80k/kg
    "Bún tươi":      {"cal":1.10, "pro":0.02, "carb":0.25, "fat":0.002, "price":0.015,"type": "starch"}, # 15k/kg
    "Miến":          {"cal":3.50, "pro":0.01, "carb":0.85, "fat":0.001, "price":0.06, "type": "starch"},
    "Gạo lứt":       {"cal":1.11, "pro":0.026,"carb":0.23, "fat":0.009, "price":0.035,"type": "starch"}, # 35k/kg
    "Khoai tây":     {"cal":0.77, "pro":0.020,"carb":0.17, "fat":0.001, "price":0.025,"type": "starch"},
    "Khoai môn":     {"cal":1.12, "pro":0.015,"carb":0.27, "fat":0.002, "price":0.04, "type": "starch"},
    "Bột mì":        {"cal":3.64, "pro":0.10, "carb":0.76, "fat":0.01,  "price":0.02, "type": "starch"},
    "Bún gạo lứt":   {"cal":1.18, "pro":0.021,"carb":0.27, "fat":0.002, "price":0.04, "type": "starch"},
    "Ngô nếp":       {"cal":1.09, "pro":0.036,"carb":0.23, "fat":0.015, "price":0.03, "type": "starch"},
    "Miến dong":     {"cal":3.32, "pro":0.004,"carb":0.83, "fat":0.001, "price":0.07, "type": "starch"},

    # --- RAU (VEG) - Giá trung bình 15k - 40k/kg ---
    "Rau Muống":    {"cal":0.20, "pro":0.03, "carb":0.03, "fat":0,     "price":0.015, "type": "veg"}, 
    "Bí đỏ":        {"cal":0.26, "pro":0.01, "carb":0.07, "fat":0.001, "price":0.02, "type": "veg"},
    "Cà rốt":       {"cal":0.41, "pro":0.01, "carb":0.10, "fat":0.002, "price":0.02, "type": "veg"},
    "Súp lơ xanh":  {"cal":0.34, "pro":0.028,"carb":0.07, "fat":0.004, "price":0.05, "type": "veg"}, # 50k/kg
    "Hành tây":      {"cal":0.40, "pro":0.011,"carb":0.09, "fat":0.001, "price":0.025,"type": "veg"},
    "Cà chua":       {"cal":0.18, "pro":0.009,"carb":0.04, "fat":0.002, "price":0.03, "type": "veg"},
    "Nấm rơm":       {"cal":0.22, "pro":0.03, "carb":0.03, "fat":0.003, "price":0.08, "type": "veg"}, # 80k/kg
    "Rau cải xanh":  {"cal":0.23, "pro":0.03, "carb":0.04, "fat":0.002, "price":0.02, "type": "veg"},
    "Mồng tơi":      {"cal":0.19, "pro":0.028,"carb":0.03, "fat":0.003, "price":0.015,"type": "veg"},
    "Bắp cải":       {"cal":0.25, "pro":0.013,"carb":0.06, "fat":0.001, "price":0.015,"type": "veg"},
    "Cải thìa":      {"cal":0.13, "pro":0.015,"carb":0.02, "fat":0.002, "price":0.02, "type": "veg"},
    "Rau dền":       {"cal":0.23, "pro":0.025,"carb":0.04, "fat":0.003, "price":0.015,"type": "veg"},
    "Rau ngót":      {"cal":0.26, "pro":0.04, "carb":0.05, "fat":0.002, "price":0.02, "type": "veg"},
    "Cải bó xôi":    {"cal":0.23, "pro":0.029,"carb":0.04, "fat":0.004, "price":0.035,"type": "veg"},
    "Đậu bắp":       {"cal":0.33, "pro":0.019,"carb":0.07, "fat":0.002, "price":0.03, "type": "veg"},
    "Đậu cove":      {"cal":0.31, "pro":0.018,"carb":0.07, "fat":0.002, "price":0.03, "type": "veg"},

    # --- KHÁC (FAT/DAIRY/FRUIT) ---
    "Dầu ăn":       {"cal":8.84, "pro":0,    "carb":0,    "fat":1.0,   "price":0.05, "type": "fat"}, # 50k/lít
    "Chuối":        {"cal":0.89, "pro":0.011,"carb":0.23, "fat":0.003, "price":0.02, "type": "fruit"}, # 20k/kg
    "Sữa tươi":      {"cal":0.64, "pro":0.033,"carb":0.05, "fat":0.036, "price":0.035,"type": "dairy"}, # 35k/lít
    "Sữa đậu nành":  {"cal":0.45, "pro":0.036,"carb":0.04, "fat":0.02,  "price":0.02, "type": "dairy"},
    "Phô mai":       {"cal":4.02, "pro":0.25, "carb":0.013,"fat":0.33,  "price":0.30, "type": "dairy"}, # 300k/kg
    "Đậu phộng":     {"cal":5.67, "pro":0.26, "carb":0.16, "fat":0.49,  "price":0.06, "type": "fat"}, # 60k/kg
    "Hạt điều":      {"cal":5.53, "pro":0.18, "carb":0.30, "fat":0.44,  "price":0.30, "type": "fat"}, # 300k/kg
    "Táo":           {"cal":0.52, "pro":0.003,"carb":0.14, "fat":0.002, "price":0.06, "type": "fruit"}, # 60k/kg
    "Cam":           {"cal":0.47, "pro":0.009,"carb":0.12, "fat":0.001, "price":0.03, "type": "fruit"}, # 30k/kg
    "Xoài":          {"cal":0.60, "pro":0.008,"carb":0.15, "fat":0.004, "price":0.04, "type": "fruit"}, # 40k/kg
}

def calc_tdee(weight, height, age, gender, job, exercise_freq):
    if gender == "male": bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else: bmr = 10 * weight + 6.25 * height - 5 * age - 161
    factors = {"student": 1.2, "office": 1.2, "service": 1.375, "manual": 1.55}
    act_base = factors.get(job, 1.2)
    ex_add = {"0":0, "1-3":0.1, "4-5":0.25, "5+":0.4}.get(exercise_freq, 0)
    return bmr * (act_base + ex_add)

# =======================================================
# ROUTES
# =======================================================

@app.route("/")
def index():
    return render_template("index.html", foodList=list(foodData.keys()))

# =======================================================
# ROUTE GIẢI QUYẾT BẰNG AI (KHÔNG DÙNG PULP)
# =======================================================
@app.route("/solve", methods=["POST"])
def solve():
    try:
        # 1. Lấy dữ liệu
        d = request.form
        weight, height, age = float(d["weight"]), float(d["height"]), int(d["age"])
        budget = float(d["budget"]) 
        goal = d["goal"]
        diet_type = d.get("diet_type", "normal")
        gender = d["gender"]
        job = d["job_type"]
        exercise = d["exercise_freq"]

        # 2. Tính TDEE & Target
        tdee = calc_tdee(weight, height, age, gender, job, exercise)
        bmi = weight / ((height/100)**2)
        target_cal = tdee
        if goal == "lose": target_cal = tdee - 500
        elif goal == "gain": target_cal = tdee + 400
        
        # Chặn ngưỡng calo tối thiểu để không bị đói
        if target_cal < 1300: target_cal = 1300 

        # 3. Lọc & Shuffle Nguyên liệu
        groups = {"starch": [], "protein": [], "veg": [], "fruit": [], "fat": []}
        
        for name, info in foodData.items():
            item = {"n": name, "c": info["cal"], "p": info["price"], "t": info["type"]}
            
            if info["type"] == "starch": groups["starch"].append(item)
            elif info["type"] in ["meat", "fish", "seafood", "egg", "vegan"]: groups["protein"].append(item)
            elif info["type"] == "veg": groups["veg"].append(item)
            elif info["type"] in ["fruit", "dairy"]: groups["fruit"].append(item)
            else: groups["fat"].append(item)

        # Shuffle
        for k in groups: random.shuffle(groups[k])

        # LẤY NHIỀU HƠN ĐỂ AI CÓ LỰA CHỌN (Đặc biệt khi budget cao)
        final_list = []
        final_list.extend(groups["starch"][:5]) 
        final_list.extend(groups["protein"][:10]) # Tăng lên 10 loại đạm
        final_list.extend(groups["veg"][:8])
        final_list.extend(groups["fruit"][:5])
        
        # Nếu budget cao (> 500k), ưu tiên đẩy các món đắt tiền lên đầu list gửi cho AI
        if budget > 500:
            final_list.sort(key=lambda x: x['p'], reverse=True)

        if diet_type == "vegan":
            final_list = [f for f in final_list if f['t'] in ['vegan', 'starch', 'veg', 'fruit', 'fat']]

        # 4. Prompt "Nghiêm khắc" hơn
        system_prompt = f"""
        Bạn là Chuyên gia Dinh dưỡng cao cấp.
        
        NHIỆM VỤ: Lên thực đơn 1 ngày (Sáng, Trưa, Tối, Phụ).
        
        THÔNG SỐ BẮT BUỘC:
        - Calo Mục tiêu: {int(target_cal)} kcal (Phải đạt trong khoảng +/- 100kcal).
        - Ngân sách: {budget} k VNĐ.
        
        DANH SÁCH NGUYÊN LIỆU (Chọn từ đây):
        {json.dumps(final_list, ensure_ascii=False)}

        YÊU CẦU LOGIC:
        1. **KHÔNG ĐƯỢC ĐỂ ĐÓI**: Tổng lượng thức ăn phải đủ 3 bữa chính. 
           - Tinh bột: Tổng > 300g/ngày (nếu không phải low-carb).
           - Đạm: Tổng > 300g/ngày (chia ra các bữa).
        2. **SỬ DỤNG NGÂN SÁCH**: 
           - Nếu ngân sách cao ({budget}k), HÃY CHỌN Cua, Ghẹ, Bò, Cá Hồi và tăng số lượng (gram) lên. Đừng chọn món rẻ tiền.
           - Nếu ngân sách thấp, chọn trứng, ức gà.
        3. **KẾT HỢP MÓN**: Phải gợi ý cách nấu (Ví dụ: Bò xào cần tỏi, Canh chua...).

        OUTPUT FORMAT (JSON ONLY):
        {{
            "menu": [
                {{"name": "tên_nguyên_liệu", "gram": số_gram_nguyên}}
            ],
            "meal_plan": "Gợi ý thực đơn: Sáng ăn gì... Trưa ăn món gì (kết hợp từ nguyên liệu trên)... Tối ăn gì..."
        }}
        """

        # 5. Gọi AI
        if not client: return jsonify({"success": False, "message": "Lỗi config AI."})

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Tạo JSON thực đơn đầy đủ calo ngay."}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        result_content = chat_completion.choices[0].message.content
        ai_data = json.loads(result_content)

        # 6. Tính toán lại
        final_menu = []
        totals = {"cal":0, "pro":0, "carb":0, "fat":0, "cost":0}

        for item in ai_data.get("menu", []):
            fname = item["name"]
            try:
                fgram = float(item["gram"])
            except:
                fgram = 100

            if fname in foodData:
                info = foodData[fname]
                
                # Nới lỏng Hard Limit để AI được phép cho ăn nhiều hơn nếu cần Calo
                if info["type"] in ["meat", "fish"] and fgram > 500: fgram = 500 
                if info["type"] == "starch" and fgram > 600: fgram = 600

                final_menu.append({
                    "name": fname,
                    "gram": int(fgram),
                    "type": info["type"],
                    "item_cost": round(info["price"] * fgram, 1) # Thêm giá tiền từng món để check
                })
                
                totals["cal"] += info["cal"] * fgram
                totals["pro"] += info["pro"] * fgram
                totals["carb"] += info["carb"] * fgram
                totals["fat"] += info["fat"] * fgram
                totals["cost"] += info["price"] * fgram

        # Lấy gợi ý kết hợp món
        meal_plan_text = ai_data.get("meal_plan", "AI chưa kịp viết gợi ý món ăn.")

        return jsonify({
            "success": True,
            "menu": final_menu,
            "meal_plan": meal_plan_text, # Trả về frontend hiển thị
            "totals": {k: round(v, 1) for k, v in totals.items()},
            "info": {
                "bmi": round(bmi, 2),
                "tdee": int(tdee),
                "target": int(target_cal),
                "budget": budget
            }
        })

    except Exception as e:
        print(f"Lỗi Server: {e}")
        return jsonify({"success": False, "message": str(e)})
    
@app.route("/suggest-substitute", methods=["POST"])
def suggest_substitute():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "content": "Dữ liệu rỗng."})
            
        food_name = data.get("food_name")
        if not food_name:
            return jsonify({"success": False, "content": "Không tìm thấy tên món cần đổi."})

        # Lấy giá của món gốc để so sánh (nếu có trong DB)
        origin_price_info = ""
        if food_name in foodData:
            p = foodData[food_name]['price'] * 1000 # Đổi về VND/kg cho dễ hiểu
            origin_price_info = f"(Món này giá khoảng {p:,.0f} đ/kg)"

        prompt = f"""
        Người dùng muốn đổi món: "{food_name}" {origin_price_info}.
        Hãy gợi ý 2 lựa chọn thay thế:
        1. Một lựa chọn RẺ HƠN (tiết kiệm).
        2. Một lựa chọn DINH DƯỠNG TƯƠNG ĐƯƠNG (hoặc healthy hơn).
        
        Trả về định dạng HTML (<ul>, <li>, <b>). Ngắn gọn, không rườm rà.
        """
        
        content = call_groq_chat(prompt)
        return jsonify({"success": True, "content": content if content else "AI đang bận."})
        
    except Exception as e:
        print(f"Lỗi Substitute: {e}")
        return jsonify({"success": False, "content": "Lỗi xử lý yêu cầu thay thế."})

# --- ĐÃ SỬA LẠI ROUTE CHAT NUTRITION ---
@app.route("/chat-nutrition", methods=["POST"])
def chat_nutrition():
    data = request.json
    user_msg = data.get("message", "")
    
    if not user_msg:
        return jsonify({"success": False, "reply": "Bạn chưa nhập câu hỏi!"})

    # Định nghĩa Prompt chuyên biệt cho Mascot
    system_prompt = """
    Bạn là Trợ lý Dinh dưỡng & Đầu bếp AI thân thiện.
    Nhiệm vụ: Trả lời câu hỏi về calo, thực phẩm, chế độ ăn, hoặc cách nấu ăn.
    Phong cách: Ngắn gọn (dưới 100 từ), vui vẻ, dùng emoji 🥗.
    QUAN TRỌNG: Chỉ trả về nội dung HTML (<b>, <br>). KHÔNG ĐƯỢC trả về JSON hoặc Markdown code block.
    """
    
    # Truyền system_prompt riêng vào hàm chat
    reply = call_groq_chat(user_msg, model="llama-3.3-70b-versatile", custom_system=system_prompt)
    
    if reply:
         return jsonify({"success": True, "reply": reply})
    else:
        return jsonify({"success": False, "reply": "Xin lỗi, server đang bận!"})

@app.route("/get-recipe", methods=["POST"])
def suggest_recipe():
    data = request.json
    food_name = data.get("food_name")
    
    if not food_name:
        return jsonify({"success": False, "message": "Thiếu tên món ăn"})

    # Dùng hàm chat có tích hợp market update và vai trò Bếp trưởng
    prompt = f"Hướng dẫn nấu món: {food_name}"
    
    chef_prompt = """
    Bạn là Bếp trưởng 5 sao Michelin. 
    Nhiệm vụ: Viết công thức nấu ăn chi tiết.
    Định dạng trả về: HTML (sử dụng các thẻ <h4>, <ul>, <li>, <b>). KHÔNG dùng Markdown.
    """
    
    content = call_groq_chat(prompt, custom_system=chef_prompt)
    
    if content:
        return jsonify({"success": True, "content": content})
    else:
        return jsonify({"success": False, "message": "Lỗi AI"})

# =======================================================
# [FIX] THÊM ROUTE NÀY VÀO APP.PY
# =======================================================
@app.route("/suggest-recipe", methods=["POST"])
def suggest_recipe_from_ingredients():
    try:
        data = request.json
        # Lấy dữ liệu từ frontend gửi lên
        ingredients = data.get("ingredients", [])
        people = data.get("people", "2")
        num_dishes = data.get("num_dishes", "tùy ý")
        allergies = data.get("allergies", "")
        region = data.get("region", "general")
        spicy_level = data.get("spicy_level", "none")

        if not ingredients:
            return jsonify({"success": False, "message": "Chưa chọn nguyên liệu!"})

        # Xử lý text hiển thị cho prompt
        region_map = {"bac": "Miền Bắc", "trung": "Miền Trung", "nam": "Miền Nam", "general": "3 miền"}
        spicy_map = {"none": "Không cay", "little": "Cay vừa", "hot": "Siêu cay"}
        
        region_text = region_map.get(region, "3 miền")
        spicy_text = spicy_map.get(spicy_level, "Không cay")

        # Tạo prompt cho Bếp trưởng AI
        prompt = f"""
        Tôi có các nguyên liệu: {', '.join(ingredients)}.
        Hãy sáng tạo thực đơn cho {people} người ăn.
        Số món mong muốn: {num_dishes}.
        Dị ứng/Kiêng kỵ: {allergies if allergies else "Không"}.
        Khẩu vị: {region_text}. Độ cay: {spicy_text}.

        YÊU CẦU:
        1. Đặt tên các món ăn thật hấp dẫn.
        2. Giải thích ngắn gọn cách nấu (hoặc sơ chế) từ các nguyên liệu trên.
        3. Nếu thiếu gia vị cơ bản (mắm, muối...) cứ coi như nhà có sẵn.
        
        Trả về định dạng HTML (dùng thẻ <h4> cho tên món, <ul><li> cho các bước hoặc nguyên liệu). KHÔNG dùng Markdown.
        """

        chef_system = "Bạn là Bếp trưởng chuyên nghiệp, giỏi biến tấu món ăn từ nguyên liệu có sẵn trong tủ lạnh."

        # Gọi AI
        content = call_groq_chat(prompt, custom_system=chef_system)

        if content:
            return jsonify({"success": True, "content": content})
        else:
            return jsonify({"success": False, "message": "Bếp trưởng AI đang nghỉ tay, thử lại sau nhé!"})

    except Exception as e:
        print(f"Lỗi Suggest Recipe: {e}")
        return jsonify({"success": False, "message": "Lỗi server khi gọi Bếp trưởng."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
