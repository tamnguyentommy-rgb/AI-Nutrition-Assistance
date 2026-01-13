from flask import Flask, render_template, request, jsonify
import pulp
import json
from groq import Groq

app = Flask(__name__)

# =======================================================
# CẤU HÌNH GROQ AI
# =======================================================
GROQ_API_KEY = "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"

# Khởi tạo client Groq
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Lỗi Config Groq: {e}")
    client = None

def call_groq_ai(prompt):
    if not client:
        print("❌ Chưa cấu hình Groq Client")
        return None

    print("🚀 Đang gọi Groq (Llama-3.3)...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là một đầu bếp chuyên nghiệp người Việt Nam. Hãy trả lời ngắn gọn, thân thiện và trình bày đẹp mắt bằng HTML (thẻ <b>, <ul>, <li>). Không dùng Markdown (```html)."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # Model Llama 3.3 mới nhất
            model="llama-3.3-70b-versatile", 
            temperature=0.7,
            max_tokens=1024,
        )
        
        content = chat_completion.choices[0].message.content
        print("✅ Groq trả về thành công!")
        return content

    except Exception as e:
        print(f"❌ Lỗi gọi Groq: {e}")
        return None

def generate_mock_recipe(ingredients, people):
    """Fallback dự phòng"""
    main = ingredients[0] if ingredients else "Món ngon"
    return f"""
    <div style="border: 1px dashed #e17055; padding: 10px; border-radius: 8px; background: #fff0f0;">
        ⚠️ <b>Mất kết nối AI!</b><br>
        Đây là gợi ý tự động từ hệ thống dự phòng.
    </div>
    <br>
    <b>1. {main} rang cháy cạnh</b>
    <ul>
        <li>Sơ chế {main}, ướp chút nước mắm, tiêu.</li>
        <li>Phi thơm hành, đảo lửa lớn đến khi xém cạnh.</li>
    </ul>
    <b>2. Canh chua {main}</b>
    <ul>
        <li>Nấu nước sôi, thả {main} và cà chua/dứa vào.</li>
        <li>Nêm nếm vừa ăn, thêm hành ngò.</li>
    </ul>
    """

# =======================================================
# CORE LOGIC TÍNH TOÁN
# =======================================================
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
            return jsonify({"success": False, "message": "Bạn chưa chọn nguyên liệu nào cả!"})

        # --- LOGIC QUYẾT ĐỊNH SỐ MÓN ---
        if requested_dishes > 0:
            num_dishes = requested_dishes # User chọn bao nhiêu thì chiều bấy nhiêu
        else:
            # Auto: Tự tính theo số người
            num_dishes = 2
            if people >= 3: num_dishes = 3
            if people >= 6: num_dishes = 4
            if people >= 10: num_dishes = 5
        
        # Giới hạn max 10 món
        if num_dishes > 10: num_dishes = 10

        print(f"👨‍🍳 Khách: {people}, Yêu cầu: {requested_dishes} -> Chốt: {num_dishes} món")

        prompt = f"""
        Tôi có các nguyên liệu: {', '.join(ingredients)}.
        Tôi cần nấu cho {people} người ăn.
        
        Yêu cầu:
        1. Hãy lên thực đơn gồm chính xác {num_dishes} món ăn Việt Nam ngon.
        2. Cố gắng tận dụng tối đa các nguyên liệu đã liệt kê.
        3. Với mỗi món, viết cách làm thật ngắn gọn (2-3 dòng).
        4. Tuyệt đối chỉ dùng HTML (thẻ <b> tên món, <ul>, <li> cách làm) để trình bày. Không dùng Markdown.
        """

        ai_content = call_groq_ai(prompt)

        if not ai_content:
            ai_content = generate_mock_recipe(ingredients, people)

        return jsonify({"success": True, "content": ai_content})

    except Exception as e:
        print("Lỗi Server:", e)
        return jsonify({"success": True, "content": generate_mock_recipe(ingredients, people)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
