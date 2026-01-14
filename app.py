from flask import Flask, render_template, request, jsonify
import pulp
import json
import base64
from groq import Groq

app = Flask(__name__)

# =======================================================
# CẤU HÌNH GROQ AI
# =======================================================
# Lưu ý: Hãy thay đổi API KEY của bạn nếu cần bảo mật
GROQ_API_KEY = "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"

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Lỗi Config Groq: {e}")
    client = None

def call_groq_vision(image_file):
    """Hàm xử lý hình ảnh Scan tủ lạnh"""
    if not client: return []
    
    # Encode ảnh sang Base64
    image_content = image_file.read()
    encoded_image = base64.b64encode(image_content).decode('utf-8')
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview", # Model Vision của Groq
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hãy nhìn vào bức ảnh này và liệt kê các loại thực phẩm/nguyên liệu bạn nhìn thấy. Chỉ trả về danh sách tên tiếng Việt ngăn cách bởi dấu phẩy. Ví dụ: Trứng gà, Thịt bò, Cà chua. Không nói thêm gì khác."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=512,
        )
        # Xử lý text trả về thành list
        result_text = completion.choices[0].message.content
        ingredients = [x.strip() for x in result_text.split(',')]
        return ingredients
    except Exception as e:
        print(f"Lỗi Vision: {e}")
        return []

def call_groq_chat(prompt, model="llama-3.3-70b-versatile"):
    """Hàm chat text thông thường"""
    if not client: return None
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia dinh dưỡng và đầu bếp Việt Nam. Trả về định dạng HTML ngắn gọn."},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Lỗi Groq Chat: {e}")
        return None

# ... [GIỮ NGUYÊN PHẦN FOOD DATA VÀ HÀM calc_tdee] ...
# (Copy lại phần foodData và calc_tdee từ file cũ của bạn vào đây)
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
    "Nấm rơm":       {"cal":0.22, "pro":0.03, "carb":0.03, "fat":0.003, "price":0.004, "type":"veg"}
}

def calc_tdee(weight, height, age, gender, job, exercise_freq):
    if gender == "male": bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else: bmr = 10 * weight + 6.25 * height - 5 * age - 161
    factors = {"student": 1.2, "office": 1.2, "service": 1.375, "manual": 1.55}
    act_base = factors.get(job, 1.2)
    ex_add = {"0":0, "1-3":0.1, "4-5":0.25, "5+":0.4}.get(exercise_freq, 0)
    return bmr * (act_base + ex_add)

@app.route("/")
def index():
    return render_template("index.html", foodList=foodData.keys())

# ... [GIỮ NGUYÊN ROUTE /solve] ...
@app.route("/solve", methods=["POST"])
def solve():
    try:
        d = request.form
        weight, height, age = float(d["weight"]), float(d["height"]), int(d["age"])
        budget = float(d["budget"])
        goal = d["goal"]
        bmi = weight / ((height/100)**2)
        tdee = calc_tdee(weight, height, age, d["gender"], d["job_type"], d["exercise_freq"])
        
        target = tdee
        if goal == "lose": target = tdee - (500 if bmi > 25 else 300)
        elif goal == "gain": target = tdee + 400

        prob = pulp.LpProblem("Menu_Optimize", pulp.LpMaximize)
        vars = {f: pulp.LpVariable(f.replace(" ","_"), 0, None) for f in foodData}

        total_cal = pulp.lpSum([foodData[f]["cal"]*vars[f] for f in foodData])
        total_veg = pulp.lpSum([vars[f] for f in foodData if "veg" in foodData[f]["type"]])
        total_meat = pulp.lpSum([vars[f] for f in foodData if foodData[f]["type"] in ["meat", "fish", "egg"]])

        prob += total_cal >= target * 0.9
        prob += total_cal <= target * 1.1
        prob += pulp.lpSum([foodData[f]["price"]*vars[f] for f in foodData]) <= budget
        prob += total_veg <= 2.0 * total_meat
        prob += total_veg >= 150

        for f in foodData:
            limit = 300
            if foodData[f]["type"] == "fat": limit = 30
            prob += vars[f] <= limit

        prob += pulp.lpSum([vars[f] for f in foodData]) 
        status = prob.solve() 
        
        if pulp.LpStatus[status] != "Optimal":
            return jsonify({"success": False, "message": f"Với {budget}$, không đủ tiền ăn! Hãy tăng ngân sách."})

        menu = []
        totals = {"cal":0, "pro":0, "carb":0, "fat":0, "cost":0}
        
        for f in foodData:
            val = vars[f].varValue
            if val and val > 15:
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

# --- NEW: ROUTE XỬ LÝ SCAN ẢNH ---
@app.route("/scan-fridge", methods=["POST"])
def scan_fridge():
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "Không tìm thấy file ảnh"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "message": "Chưa chọn file"})

    print("📸 Đang quét ảnh tủ lạnh...")
    ingredients = call_groq_vision(file)
    
    if ingredients:
        return jsonify({"success": True, "ingredients": ingredients})
    else:
        return jsonify({"success": False, "message": "AI không nhận diện được thực phẩm nào."})

# --- NEW: ROUTE TƯ VẤN THAY THẾ (SUBSTITUTION) ---
@app.route("/suggest-substitute", methods=["POST"])
def suggest_substitute():
    data = request.json
    food_name = data.get("food_name")
    
    # Tìm thông tin dinh dưỡng nếu có trong DB
    food_info = foodData.get(food_name, {})
    food_context = ""
    if food_info:
        food_context = f"(Calo: {food_info.get('cal')}, Giá: {food_info.get('price')})"

    prompt = f"""
    Người dùng muốn tìm món thay thế cho: <b>{food_name}</b> {food_context}.
    Hãy gợi ý 2 lựa chọn thay thế khả thi ở Việt Nam theo tiêu chí:
    1. Một lựa chọn giá rẻ hơn (tiết kiệm).
    2. Một lựa chọn dinh dưỡng tương đương (cùng nhóm chất).
    
    Định dạng trả về HTML (không markdown):
    <div class='sub-opt'>
        <b>Option 1 (Tiết kiệm):</b> [Tên món] - [Lý do ngắn gọn]
    </div>
    <div class='sub-opt'>
        <b>Option 2 (Dinh dưỡng):</b> [Tên món] - [Lý do ngắn gọn]
    </div>
    """
    
    content = call_groq_chat(prompt)
    if not content:
        content = "Xin lỗi, AI đang bận. Hãy thử thay bằng món tương tự."
        
    return jsonify({"success": True, "content": content})

# --- UPDATED: ROUTE GỢI Ý CÔNG THỨC ---
@app.route("/suggest-recipe", methods=["POST"])
def suggest_recipe():
    try:
        data = request.json
        ingredients = data.get("ingredients", [])
        try:
            people = int(data.get("people", 1))
            requested_dishes = int(data.get("num_dishes", 0))
        except:
            people = 1
            requested_dishes = 0
            
        if not ingredients:
            return jsonify({"success": False, "message": "Chưa có nguyên liệu!"})

        if requested_dishes > 0: num_dishes = requested_dishes
        else:
            num_dishes = 2
            if people >= 3: num_dishes = 3
            if people >= 6: num_dishes = 4

        prompt = f"""
        Nguyên liệu: {', '.join(ingredients)}.
        Nấu cho {people} người.
        Yêu cầu: Lên thực đơn {num_dishes} món Việt Nam.
        Chỉ dùng HTML (<b>, <ul>, <li>), không Markdown.
        """
        ai_content = call_groq_chat(prompt)
        
        return jsonify({"success": True, "content": ai_content if ai_content else "Lỗi AI"})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Lỗi server"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
