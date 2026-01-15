<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Nutrition Pro</title>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="main-wrapper">
        <header>
            <h1><i class="fas fa-bolt"></i> AI Nutrition Assistance</h1>
            <p>Trợ lý dinh dưỡng & Đầu bếp ảo thông minh</p>
        </header>

        <div class="glass-panel">
            <div class="section-title"><h3><i class="fas fa-calculator"></i> Tính Toán Khẩu Phần</h3></div>
            <form id="app-form">
                <div class="grid-2-col">
                    <div class="section">
                        <label>Thông tin cơ bản:</label>
                        <div class="input-row">
                            <input type="number" name="age" placeholder="Tuổi" required>
                            <select name="gender"><option value="male">Nam</option><option value="female">Nữ</option></select>
                        </div>
                        <div class="input-row">
                            <input type="number" name="weight" placeholder="Cân (kg)" required>
                            <input type="number" name="height" placeholder="Cao (cm)" required>
                        </div>
                        <label>Vận động:</label>
                        <select name="job_type">
                            <option value="student">Học sinh</option>
                            <option value="office">Văn phòng</option>
                            <option value="manual">Lao động</option>
                        </select>
                        <select name="exercise_freq">
                            <option value="0">Không tập</option>
                            <option value="1-3">1-3 buổi/tuần</option>
                            <option value="4-5">4-5 buổi/tuần</option>
                        </select>
                    </div>

                    <div class="section">
                        <label>Mục tiêu & Ngân sách:</label>
                        <div class="input-row">
                            <select name="goal" style="flex:2">
                                <option value="maintain">Giữ cân</option>
                                <option value="lose">Giảm cân</option>
                                <option value="gain">Tăng cân</option>
                            </select>
                            <input type="number" name="budget" placeholder="$ Ngân sách" value="5.0" step="0.5" style="flex:1">
                        </div>
                        <div class="tags-group">
                            <label class="tag-check"><input type="checkbox" name="conditions[]" value="diabetes"> Tiểu đường</label>
                            <label class="tag-check"><input type="checkbox" name="conditions[]" value="hypertension"> Huyết áp</label>
                        </div>
                        <label>Mục tiêu & Ngân sách:</label>
                        <label>Dị ứng / Kiêng kỵ (nếu có):</label>
                        <input type="text" id="allergy-input" name="allergies" placeholder="VD: Tôm, Đậu phộng, Sữa..." style="margin-bottom: 20px;">
                    </div>
                </div>
                <button type="submit" class="submit-btn">TÍNH TOÁN NGAY</button>
            </form>
        </div>

        <div id="loading" class="hidden"><div class="spinner"></div><p>AI đang tính toán...</p></div>
        
        <div id="result-area" class="hidden glass-panel">
            <div class="stats-row">
                <div class="stat-box">BMI: <b id="res-bmi">--</b></div>
                <div class="stat-box">Target: <b id="res-target">--</b> kcal</div>
                <div class="stat-box highlight">Giá: $<b id="t-cost">--</b></div>
            </div>
            <div class="result-grid">
                <div class="menu-col">
                    <h4>Thực đơn tối ưu (Bấm icon <i class="fas fa-sync-alt"></i> để tìm món thay thế):</h4>
                    <ul id="menu-list"></ul>
                </div>
                <div class="chart-col">
                    <canvas id="myChart"></canvas>
                </div>
            </div>
        </div>

        <div class="glass-panel" style="margin-top: 30px; border-top: 4px solid #6c5ce7;">
            <div class="section-title"><h3><i class="fas fa-utensils"></i> Bếp Trưởng AI</h3></div>
            <p>Chọn nguyên liệu hoặc <b>Chụp ảnh tủ lạnh</b> để AI nhận diện!</p>
            
            <div id="chef-form">
                <div class="upload-area">
                    <label for="fridge-upload" class="upload-label">
                        <i class="fas fa-camera"></i> Scan Tủ Lạnh (Beta)
                    </label>
                    <input type="file" id="fridge-upload" accept="image/*" class="hidden">
                    <span id="upload-status"></span>
                </div>

                <div style="display: flex; gap: 15px; margin-bottom: 15px; margin-top: 15px;">
                    <div style="flex: 1;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Số người ăn:</label>
                        <input type="number" id="people-count" value="2" min="1" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc;">
                    </div>
                    <div style="flex: 1;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Số món:</label>
                        <input type="number" id="dish-count" value="0" min="0" placeholder="Auto" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc;">
                    </div>
                </div>
                
                <label style="font-weight: bold;">Nguyên liệu (Tích chọn hoặc Scan):</label>
                <div class="tags-group" id="ingredient-list">
                    {% for food in foodList %}
                    <label class="tag-check">
                        <input type="checkbox" value="{{ food }}"> {{ food }}
                    </label>
                    {% endfor %}
                </div>

                <button type="button" id="btn-suggest" class="submit-btn" style="background: linear-gradient(135deg, #6c5ce7, #a29bfe); margin-top: 20px;">
                    <i class="fas fa-magic"></i> Sáng tạo công thức
                </button>
            </div>

            <div id="chef-result" class="hidden" style="margin-top: 25px; background: #fff; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h4 style="color: #6c5ce7; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px;">🧑‍🍳 Gợi ý từ Bếp Trưởng:</h4>
                <div id="chef-content" style="line-height: 1.8; color: #2d3436; font-size: 15px;"></div>
            </div>
        </div>

    </div>

    <div id="sub-modal" class="modal hidden">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h3 id="sub-title">Tìm món thay thế</h3>
            <div id="sub-loading" class="hidden"><div class="spinner" style="width: 30px; height: 30px;"></div></div>
            <div id="sub-result"></div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>
