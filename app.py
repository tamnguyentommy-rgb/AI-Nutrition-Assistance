from flask import Flask, render_template, request, jsonify
import pulp
import json
import base64
from groq import Groq
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import threading

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

# ... [GIỮ NGUYÊN PHẦN FOOD DATA VÀ HÀM calc_tdee] ...
foodData = {
    "Thịt heo nạc":  {"cal":2.42, "pro":0.27, "carb":0,    "fat":0.14,  "price":0.008, "type": "meat"},
    "Gan gà":       {"cal":1.67, "pro":0.24, "carb":0.01, "fat":0.05,  "price":0.004, "type": "meat"},
    "Ức Gà":        {"cal":1.65, "pro":0.31, "carb":0,    "fat":0.036, "price":0.015, "type": "meat"},
    "Cá nục":       {"cal":1.50, "pro":0.25, "carb":0,    "fat":0.05,  "price":0.007, "type": "fish"},
    "Trứng Gà":     {"cal":1.55, "pro":0.13, "carb":0.011,"fat":0.11,  "price":0.005, "type": "egg"},
    "Đậu hũ":       {"cal":0.76, "pro":0.08, "carb":0.019,"fat":0.048, "price":0.004, "type": "vegan"},
    "Cơm trắng":    {"cal":1.30, "pro":0.027,"carb":0.28, "fat":0.003, "price":0.002, "type": "starch"},
    "Khoai lang":   {"cal":0.86, "pro":0.016,"carb":0.20, "fat":0.001, "price":0.003, "type": "starch"},
    "Bánh mì":      {"cal":2.60, "pro":0.09, "carb":0.49, "fat":0.03,  "price":0.004, "type": "starch"},
    "Rau Muống":    {"cal":0.20, "pro":0.03, "carb":0.03, "fat":0,     "price":0.001, "type": "veg"},
    "Bí đỏ":        {"cal":0.26, "pro":0.01, "carb":0.07, "fat":0.001, "price":0.002, "type": "veg"},
    "Cà rốt":       {"cal":0.41, "pro":0.01, "carb":0.10, "fat":0.002, "price":0.003, "type": "veg"},
    "Súp lơ xanh":  {"cal":0.34, "pro":0.028,"carb":0.07, "fat":0.004, "price":0.003, "type": "veg"},
    "Dầu ăn":       {"cal":8.84, "pro":0,    "carb":0,    "fat":1.0,   "price":0.015, "type": "fat"},
    "Chuối":        {"cal":0.89, "pro":0.011,"carb":0.23, "fat":0.003, "price":0.003, "type": "fruit"},
    "Thịt bò nạc":   {"cal":2.50, "pro":0.26, "carb":0,    "fat":0.15,  "price":0.020, "type":"meat"},
    "Thịt vịt":      {"cal":3.37, "pro":0.19, "carb":0,    "fat":0.28,  "price":0.012, "type":"meat"},
    "Cá hồi":        {"cal":2.08, "pro":0.20, "carb":0,    "fat":0.13,  "price":0.030, "type":"fish"},
    "Cá basa":       {"cal":1.20, "pro":0.18, "carb":0,    "fat":0.04,  "price":0.006, "type":"fish"},
    "Tôm":           {"cal":0.99, "pro":0.24, "carb":0.002,"fat":0.003, "price":0.018, "type":"seafood"},
    "Mực":           {"cal":0.92, "pro":0.15, "carb":0.03, "fat":0.01,  "price":0.015, "type":"seafood"},
    "Sữa tươi":      {"cal":0.64, "pro":0.033,"carb":0.05, "fat":0.036, "price":0.004, "type":"dairy"},
    "Sữa đậu nành":  {"cal":0.45, "pro":0.036,"carb":0.04, "fat":0.02,  "price":0.003, "type":"dairy"},
    "Phô mai":       {"cal":4.02, "pro":0.25, "carb":0.013,"fat":0.33,  "price":0.025, "type":"dairy"},
    "Yến mạch":      {"cal":3.89, "pro":0.17, "carb":0.66, "fat":0.07,  "price":0.006, "type":"starch"},
    "Bún tươi":      {"cal":1.10, "pro":0.02, "carb":0.25, "fat":0.002, "price":0.002, "type":"starch"},
    "Miến":          {"cal":3.50, "pro":0.01, "carb":0.85, "fat":0.001, "price":0.004, "type":"starch"},
    "Đậu phộng":     {"cal":5.67, "pro":0.26, "carb":0.16, "fat":0.49,  "price":0.008, "type":"fat"},
    "Hạt điều":      {"cal":5.53, "pro":0.18, "carb":0.30, "fat":0.44,  "price":0.020, "type":"fat"},
    "Táo":           {"cal":0.52, "pro":0.003,"carb":0.14, "fat":0.002, "price":0.004, "type":"fruit"},
    "Cam":           {"cal":0.47, "pro":0.009,"carb":0.12, "fat":0.001, "price":0.003, "type":"fruit"},
    "Xoài":          {"cal":0.60, "pro":0.008,"carb":0.15, "fat":0.004, "price":0.005, "type":"fruit"},
    "Hành tây":      {"cal":0.40, "pro":0.011,"carb":0.09, "fat":0.001, "price":0.002, "type":"veg"},
    "Cà chua":       {"cal":0.18, "pro":0.009,"carb":0.04, "fat":0.002, "price":0.002, "type":"veg"},
    "Nấm rơm":       {"cal":0.22, "pro":0.03, "carb":0.03, "fat":0.003, "price":0.004, "type":"veg"},
    "Rau cải xanh":   {"cal":0.23, "pro":0.03, "carb":0.04, "fat":0.002, "price":0.001, "type":"veg"},
    "Mồng tơi":       {"cal":0.19, "pro":0.028,"carb":0.03, "fat":0.003, "price":0.001, "type":"veg"},
    "Bắp cải":       {"cal":0.25, "pro":0.013,"carb":0.06, "fat":0.001, "price":0.001, "type":"veg"},
    "Cải thìa":      {"cal":0.13, "pro":0.015,"carb":0.02, "fat":0.002, "price":0.002, "type":"veg"},
    "Rau dền":       {"cal":0.23, "pro":0.025,"carb":0.04, "fat":0.003, "price":0.001, "type":"veg"},
    "Rau ngót":      {"cal":0.26, "pro":0.04, "carb":0.05, "fat":0.002, "price":0.001, "type":"veg"},
    "Cải bó xôi":    {"cal":0.23, "pro":0.029,"carb":0.04, "fat":0.004, "price":0.003, "type":"veg"},
    "Đậu bắp":       {"cal":0.33, "pro":0.019,"carb":0.07, "fat":0.002, "price":0.003, "type":"veg"},
    "Cua biển":        {"cal":0.83, "pro":0.18, "carb":0.01, "fat":0.01,  "price":0.030, "type":"seafood"},
    "Ghẹ":             {"cal":0.87, "pro":0.19, "carb":0,    "fat":0.01,  "price":0.028, "type":"seafood"},
    "Sò huyết":        {"cal":1.43, "pro":0.25, "carb":0.03, "fat":0.02,  "price":0.018, "type":"seafood"},
    "Nghêu":           {"cal":0.74, "pro":0.12, "carb":0.03, "fat":0.01,  "price":0.010, "type":"seafood"},
    "Hàu":             {"cal":0.68, "pro":0.09, "carb":0.04, "fat":0.02,  "price":0.020, "type":"seafood"},
    "Bạch tuộc":       {"cal":0.82, "pro":0.15, "carb":0.02, "fat":0.01,  "price":0.017, "type":"seafood"},
    "Cá tráp":         {"cal":1.28, "pro":0.21, "carb":0,    "fat":0.04,  "price":0.016, "type":"fish"},
    "Cá chim":         {"cal":1.40, "pro":0.20, "carb":0,    "fat":0.06,  "price":0.018, "type":"fish"},
    "Thịt cừu":        {"cal":2.94, "pro":0.25, "carb":0, "fat":0.21, "price":0.030, "type":"meat"},
    "Thịt dê":         {"cal":1.43, "pro":0.27, "carb":0, "fat":0.03, "price":0.018, "type":"meat"},
    "Thịt trâu":       {"cal":1.31, "pro":0.26, "carb":0, "fat":0.02, "price":0.016, "type":"meat"},
    "Bắp bò":          {"cal":2.01, "pro":0.28, "carb":0, "fat":0.08, "price":0.022, "type":"meat"},
    "Sườn bò":         {"cal":3.40, "pro":0.21, "carb":0, "fat":0.29, "price":0.025, "type":"meat"},
    "Gạo lứt":        {"cal":1.11, "pro":0.026,"carb":0.23, "fat":0.009, "price":0.003, "type":"starch"},
    "Khoai tây":      {"cal":0.77, "pro":0.020,"carb":0.17, "fat":0.001, "price":0.003, "type":"starch"},
    "Khoai môn":      {"cal":1.12, "pro":0.015,"carb":0.27, "fat":0.002, "price":0.004, "type":"starch"},
    "Bột mì":         {"cal":3.64, "pro":0.10, "carb":0.76, "fat":0.01,  "price":0.003, "type":"starch"},
    "Bún gạo lứt":    {"cal":1.18, "pro":0.021,"carb":0.27, "fat":0.002, "price":0.003, "type":"starch"},
    "Ngô nếp":        {"cal":1.09, "pro":0.036,"carb":0.23, "fat":0.015, "price":0.004, "type":"starch"},
    "Miến dong":      {"cal":3.32, "pro":0.004,"carb":0.83, "fat":0.001, "price":0.005, "type":"starch"}
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

@app.route("/solve", methods=["POST"])
def solve():
    try:
        d = request.form
        weight, height, age = float(d["weight"]), float(d["height"]), int(d["age"])
        budget = float(d["budget"])
        goal = d["goal"]
        
        # --- XỬ LÝ DỊ ỨNG ---
        allergies = d.get("allergies", "").lower().strip()
        blocked_foods = []
        if allergies:
            keywords = [k.strip() for k in allergies.split(',')]
            for food_name, food_info in foodData.items():
                fname_lower = food_name.lower()
                ftype = food_info['type']
                for k in keywords:
                    if k and (k in fname_lower): blocked_foods.append(food_name)
                    elif k == "hải sản" and ftype in ["seafood", "fish"]: blocked_foods.append(food_name)
                    elif k == "sữa" and ftype == "dairy": blocked_foods.append(food_name)

        # =======================================================
        # [CODE MỚI] XỬ LÝ CHẾ ĐỘ ĂN (DIET TYPE)
        # =======================================================
        diet_type = d.get("diet_type", "normal")
        
        # Nếu ăn chay: Block toàn bộ thịt, cá, trứng, sữa
        if diet_type == "vegan":
            for fname, fval in foodData.items():
                if fval['type'] in ['meat', 'fish', 'seafood', 'egg', 'dairy']:
                    blocked_foods.append(fname)
        # =======================================================

        available_foods = [f for f in foodData if f not in blocked_foods]
        # --------------------

        bmi = weight / ((height/100)**2)
        tdee = calc_tdee(weight, height, age, d["gender"], d["job_type"], d["exercise_freq"])
        
        target = tdee
        if goal == "lose": target = tdee - (500 if bmi > 25 else 300)
        elif goal == "gain": target = tdee + 400

        prob = pulp.LpProblem("Menu_Optimize", pulp.LpMaximize)
        vars = {f: pulp.LpVariable(f.replace(" ","_"), 0, None) for f in available_foods}

        total_cal = pulp.lpSum([foodData[f]["cal"]*vars[f] for f in available_foods])
        total_veg = pulp.lpSum([vars[f] for f in available_foods if "veg" in foodData[f]["type"]])
        total_meat = pulp.lpSum([vars[f] for f in available_foods if foodData[f]["type"] in ["meat", "fish", "egg", "seafood"]])

        prob += total_cal >= target * 0.9
        prob += total_cal <= target * 1.1
        prob += pulp.lpSum([foodData[f]["price"]*vars[f] for f in available_foods]) <= budget
        prob += total_veg <= 2.5 * total_meat
        prob += total_veg >= 100

        # =======================================================
        # [CODE MỚI] RÀNG BUỘC DINH DƯỠNG NÂNG CAO
        # =======================================================
        # Lowcarb: Giới hạn tinh bột dưới 150g thực phẩm (ước lượng)
        if diet_type == "lowcarb":
            starch_items = [vars[f] for f in available_foods if foodData[f]["type"] == "starch"]
            if starch_items:
                prob += pulp.lpSum(starch_items) <= 150

        # High Protein: Bắt buộc ăn nhiều thịt/cá (trên 300g)
        if diet_type == "highpro":
            protein_items = [vars[f] for f in available_foods if foodData[f]["type"] in ["meat", "fish"]]
            if protein_items:
                prob += pulp.lpSum(protein_items) >= 300
        # =======================================================

        for f in available_foods:
            limit = 400
            if foodData[f]["type"] == "fat": limit = 30
            prob += vars[f] <= limit

        prob += pulp.lpSum([vars[f] for f in available_foods]) 
        status = prob.solve() 
        
        if pulp.LpStatus[status] != "Optimal":
            return jsonify({"success": False, "message": "Không tìm thấy thực đơn phù hợp. Hãy thử tăng ngân sách."})

        menu = []
        totals = {"cal":0, "pro":0, "carb":0, "fat":0, "cost":0}
        
        for f in available_foods:
            val = vars[f].varValue
            if val and val > 10:
                menu.append({"name": f, "gram": round(val), "type": foodData[f]["type"]})
                totals["cal"] += foodData[f]["cal"] * val
                totals["pro"] += foodData[f]["pro"] * val
                totals["carb"] += foodData[f]["carb"] * val
                totals["fat"] += foodData[f]["fat"] * val
                totals["cost"] += foodData[f]["price"] * val

        return jsonify({
            "success": True,
            "menu": menu,
            "totals": {k: round(v,1) for k,v in totals.items()},
            "info": {"bmi": round(bmi, 2), "tdee": round(tdee), "target": round(target)}
        })

    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi tính toán: " + str(e)})

@app.route("/suggest-recipe", methods=["POST"])
def suggest_recipe():
    try:
        data = request.json
        ingredients = data.get("ingredients", [])
        allergies = data.get("allergies", "")
        
        try:
            p_val = data.get("people")
            people = int(p_val) if p_val else 2
            d_val = data.get("num_dishes")
            requested_dishes = int(d_val) if d_val else 0
        except ValueError:
            people = 2
            requested_dishes = 0

        if not ingredients:
            return jsonify({"success": False, "message": "Chưa có nguyên liệu!"})

        if requested_dishes > 0: 
            num_dishes = requested_dishes
        else:
            num_dishes = 2
            if people >= 3: num_dishes = 3
            if people >= 5: num_dishes = 4

        allergy_note = f"LƯU Ý QUAN TRỌNG: Người dùng bị dị ứng/kiêng kỵ: {allergies}. Tuyệt đối không dùng thành phần này." if allergies else ""
        
        # =======================================================
        # [CODE MỚI] XỬ LÝ VÙNG MIỀN & ĐỘ CAY
        # =======================================================
        region = data.get("region", "general")
        spicy = data.get("spicy_level", "none")
        style_text = f"Phong cách nấu: Chuẩn vị {region}. Độ cay: {spicy}."
        # =======================================================

        prompt = f"""
        Nguyên liệu: {', '.join(ingredients)}. Nấu cho {people} người. {allergy_note}
        {style_text}
        Yêu cầu: Gợi ý {num_dishes} món Việt Nam, kèm cách làm ngắn gọn.
        Trả về định dạng HTML (<b>, <ul>, <li>).
        """
        
        content = call_groq_chat(prompt)
        return jsonify({"success": True, "content": content if content else "AI đang bận."})

    except Exception as e:
        print(f"Lỗi Suggest Recipe: {e}") 
        return jsonify({"success": False, "message": "Lỗi server: " + str(e)})
    
@app.route("/suggest-substitute", methods=["POST"])
def suggest_substitute():
    food_name = request.json.get("food_name")
    prompt = f"Gợi ý 2 món thay thế cho '{food_name}' (1 rẻ hơn, 1 dinh dưỡng ngang bằng). Trả về định dạng HTML ngắn gọn."
    content = call_groq_chat(prompt)
    return jsonify({"success": True, "content": content})

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
def get_recipe():
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
