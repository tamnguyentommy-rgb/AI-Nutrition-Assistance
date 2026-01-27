document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // 0. TỰ ĐỘNG GHI NHỚ NGƯỜI DÙNG
    // ==========================================
    const autoFillInputs = document.querySelectorAll("input[type='text'], input[type='number'], select");
    autoFillInputs.forEach(input => {
        if (!input.name) return;
        const savedValue = localStorage.getItem("user_pref_" + input.name);
        if (savedValue) input.value = savedValue;

        input.addEventListener("change", () => {
            localStorage.setItem("user_pref_" + input.name, input.value);
        });
    });

    // Biến toàn cục để lưu thông tin món đang xem
    let currentRecipeTitle = ""; 
    let currentRecipeHTML = "";

    // ==========================================
    // HÀM HỖ TRỢ: ĐIỀU KHIỂN MASCOT NÓI CHUYỆN
    // ==========================================
    function showMascotMessage(text, duration = 4000) {
        const bubble = document.getElementById("mascot-bubble");
        const mascotImg = document.getElementById("mascot-image");
        
        if (bubble) {
            bubble.textContent = text;
            bubble.classList.remove("hidden");
            
            if (mascotImg) {
                mascotImg.style.animation = "shake 0.5s ease-in-out";
                setTimeout(() => {
                    mascotImg.style.animation = "floatMascot 3s ease-in-out infinite";
                }, 500);
            }

            if (window.mascotTimeout) clearTimeout(window.mascotTimeout);
            
            window.mascotTimeout = setTimeout(() => {
                bubble.classList.add("hidden");
            }, duration);
        }
    }

    // ==========================================
    // 1. TÍNH NĂNG TÍNH CALO & MENU
    // ==========================================
    const calcForm = document.getElementById("app-form");
    const loading = document.getElementById("loading");
    const resultArea = document.getElementById("result-area");
    let nutritionChart = null;

    if (calcForm) {
        calcForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            loading.classList.remove("hidden");
            resultArea.classList.add("hidden");
            
            showMascotMessage("Đợi xíu nhé, mình đang tính toán... 🍳");

            try {
                const formData = new FormData(calcForm);
                const res = await fetch("/solve", { method: "POST", body: formData });
                const data = await res.json();

                if (!data.success) {
                    alert(data.message);
                    showMascotMessage("Úi! Có lỗi rồi: " + data.message);
                } else {
                    renderResults(data);
                    
                    if (data.mascot_explanation) {
                        setTimeout(() => {
                            showMascotMessage(data.mascot_explanation, 10000);
                        }, 500);
                    } else {
                        showMascotMessage("Tèn ten! Thực đơn đã sẵn sàng! 🥗");
                    }
                }
            } catch (err) {
                alert("Lỗi: " + err.message);
            } finally {
                loading.classList.add("hidden");
            }
        });
    }

    function renderResults(data) {
        document.getElementById("res-bmi").textContent = data.info.bmi;
        document.getElementById("res-target").textContent = data.info.target;
        document.getElementById("t-cost").textContent = data.totals.cost;

        const list = document.getElementById("menu-list");
        list.innerHTML = "";
        
        data.menu.forEach((item, index) => {
            const li = document.createElement("li");
            let color = "#ccc";
            if (item.type.includes("meat")) color = "#ff7675";
            else if (item.type.includes("veg")) color = "#00b894";
            else if (item.type.includes("starch")) color = "#fdcb6e";

            li.style.borderLeftColor = color;
            li.style.animation = `fadeInUp 0.3s forwards ${index * 0.05}s`;
            
            // Thêm data-name vào thẻ div để dễ lấy tên
            li.innerHTML = `
                <div style="display:flex; justify-content:space-between; width:100%; align-items:center;" class="menu-item-content">
                    <div class="food-info" style="cursor:pointer;">
                        <span class="food-name" style="font-weight:500;">${item.name}</span> 
                        <span style="font-size:0.8rem; color:#888;">(${item.gram}g)</span>
                    </div>
                    <button class="btn-swap" data-name="${item.name}" title="Tìm món thay thế">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            `;
            list.appendChild(li);
        });

        // Nút Swap
        document.querySelectorAll(".btn-swap").forEach(btn => {
            btn.addEventListener("click", function(e) {
                e.stopPropagation(); 
                const foodName = this.getAttribute("data-name");
                openSubModal(foodName);
            });
        });

        // Vẽ biểu đồ
        const ctx = document.getElementById('nutritionChart').getContext('2d');
        if (nutritionChart) nutritionChart.destroy();
        nutritionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Đạm', 'Tinh bột', 'Béo'],
                datasets: [{
                    data: [data.totals.pro * 4, data.totals.carb * 4, data.totals.fat * 9],
                    backgroundColor: ['#ff7675', '#fdcb6e', '#00b894'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });

        resultArea.classList.remove("hidden");
        resultArea.scrollIntoView({ behavior: "smooth" });
    }

    // ==========================================
    // 2. MODAL SUBSTITUTION (THAY THẾ)
    // ==========================================
    const subModal = document.getElementById("sub-modal");
    const subTitle = document.getElementById("sub-title"); // Đảm bảo HTML có id này nếu dùng
    const subResult = document.getElementById("modal-body"); // Sửa lại id cho khớp với HTML
    const closeModal = document.querySelector(".close-modal");

    function openSubModal(foodName) {
        if (!subModal) return;
        subModal.classList.remove("hidden");
        const titleEl = document.getElementById("modal-title");
        if(titleEl) titleEl.textContent = `Tìm thay thế cho: ${foodName}`;
        
        if (subResult) subResult.innerHTML = '<div style="text-align:center"><i class="fas fa-spinner fa-spin"></i> Đang tìm...</div>';

        showMascotMessage(`Để xem có gì thay thế cho ${foodName} nhé... 🤔`);

        fetch("/suggest-substitute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ food_name: foodName })
        })
        .then(res => res.json())
        .then(data => {
            if(data.success && subResult) {
                subResult.innerHTML = data.content;
            } else if (subResult) {
                subResult.innerHTML = "Không tìm thấy gợi ý.";
            }
        })
        .catch(err => {
            if (subResult) subResult.innerHTML = "Lỗi kết nối AI.";
        });
    }

    if(closeModal) {
        closeModal.addEventListener("click", () => subModal.classList.add("hidden"));
    }
    
    // ==========================================
    // 4. BẾP TRƯỞNG AI
    // ==========================================
    const btnSuggest = document.getElementById("btn-suggest");
    const chefResult = document.getElementById("chef-result");
    const chefContent = document.getElementById("chef-content");

    if (btnSuggest) {
        btnSuggest.addEventListener("click", async () => {
            const checkedBoxes = document.querySelectorAll("#ingredient-list input:checked");
            const selectedIngs = Array.from(checkedBoxes).map(cb => cb.value);
            const people = document.getElementById("people-count").value;
            const dishCount = document.getElementById("dish-count").value;
            const allergyInput = document.getElementById("allergy-input"); 
            const allergyValue = allergyInput ? allergyInput.value : "";
            
            const regionSelect = document.querySelector('select[name="region"]');
            const spicySelect = document.querySelector('select[name="spicy_level"]');
            const regionValue = regionSelect ? regionSelect.value : "general";
            const spicyValue = spicySelect ? spicySelect.value : "none";

            if (selectedIngs.length === 0) {
                showMascotMessage("Chọn nguyên liệu đi đã bạn ơi! 😅");
                return;
            }

            const originalText = btnSuggest.innerHTML;
            btnSuggest.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đầu bếp đang suy nghĩ...';
            btnSuggest.disabled = true;
            btnSuggest.style.opacity = "0.8";
            chefResult.classList.add("hidden");

            try {
                const res = await fetch("/suggest-recipe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        ingredients: selectedIngs, 
                        people: people,
                        num_dishes: dishCount,
                        allergies: allergyValue,
                        region: regionValue,
                        spicy_level: spicyValue
                    })
                });
                const data = await res.json();
                
                if (data.success) {
                    chefContent.innerHTML = data.content;
                    chefResult.classList.remove("hidden");
                    chefResult.scrollIntoView({ behavior: "smooth" });
                    showMascotMessage("Xong! Mời bạn xem thực đơn Bếp Trưởng 👨‍🍳");
                } else {
                    alert(data.message);
                }
            } catch (err) {
                alert("Lỗi kết nối: " + err.message);
            } finally {
                btnSuggest.innerHTML = originalText;
                btnSuggest.disabled = false;
                btnSuggest.style.opacity = "1";
            }
        });
    }

    // ==========================================
    // 5. TÍNH NĂNG CHATBOT
    // ==========================================
    const chatLauncher = document.getElementById("chat-launcher");
    const chatWindow = document.getElementById("chat-window");
    const closeChat = document.getElementById("close-chat");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const chatMsgs = document.getElementById("chat-messages");

    if (chatLauncher) {
        chatLauncher.addEventListener("click", () => chatWindow.classList.remove("hidden"));
        closeChat.addEventListener("click", () => chatWindow.classList.add("hidden"));

        function addMessage(text, isUser) {
            const msgDiv = document.createElement("div");
            msgDiv.className = isUser ? "message user-msg" : "message bot-msg";
            if (isUser) msgDiv.textContent = text;
            else msgDiv.innerHTML = text; 
            chatMsgs.appendChild(msgDiv);
            chatMsgs.scrollTop = chatMsgs.scrollHeight;
        }

        async function handleChat() {
            const text = chatInput.value.trim();
            if (!text) return;

            addMessage(text, true);
            chatInput.value = "";
            chatInput.focus();

            const loadingDiv = document.createElement("div");
            loadingDiv.className = "message bot-msg";
            loadingDiv.innerHTML = '<i class="fas fa-ellipsis-h fa-fade"></i>';
            loadingDiv.id = "chat-loading";
            chatMsgs.appendChild(loadingDiv);

            try {
                const res = await fetch("/chat-nutrition", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                
                loadingDiv.remove();
                if (data.success) {
                    addMessage(data.reply, false);
                } else {
                    addMessage("Lỗi: " + data.reply, false);
                }
            } catch (err) {
                loadingDiv.remove();
                addMessage("Lỗi kết nối server!", false);
            }
        }

        sendBtn.addEventListener("click", handleChat);
        chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") handleChat();
        });
    }

    // ==========================================
    // 6. POPUP CÔNG THỨC (ĐÃ SỬA LỖI CLICK)
    // ==========================================
    const menuListEl = document.getElementById("menu-list");
    const recipeModal = document.getElementById("chef-modal");
    const closeRecipeModal = recipeModal ? recipeModal.querySelector(".close-modal") : null;
    const recipeContentEl = document.getElementById("recipe-popup-content");

    if (menuListEl && recipeModal) {
        menuListEl.addEventListener("click", async (e) => {
            // 1. Bắt sự kiện khi click vào dòng (thẻ li)
            const liItem = e.target.closest("li");
            
            // 2. Nếu click trúng nút Swap hoặc không phải li thì bỏ qua
            if (!liItem || e.target.closest(".btn-swap")) return;

            // 3. Tìm tên món ăn bên trong thẻ li đó
            const nameEl = liItem.querySelector(".food-name");
            const foodName = nameEl ? nameEl.textContent.trim() : "";
            
            if (!foodName) return;

            // [QUAN TRỌNG] Cập nhật tiêu đề để lưu không bị lỗi
            currentRecipeTitle = foodName;
            
            const modalTitle = recipeModal.querySelector("h2");
            if(modalTitle) {
                modalTitle.innerHTML = `<i class="fas fa-hat-chef"></i> ${foodName}`;
            }

            // 4. Mở Modal và hiện Loading
            recipeModal.classList.remove("hidden");
            if(recipeContentEl) {
                recipeContentEl.innerHTML = '<div style="text-align:center; padding:20px"><i class="fas fa-spinner fa-spin fa-2x"></i><br>Đang hỏi bếp trưởng công thức...</div>';
            }
            
            showMascotMessage(`Món ${foodName} nấu dễ lắm, xem nhé! 📖`);

            // 5. Gọi API lấy công thức
            try {
                const res = await fetch("/get-recipe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ food_name: foodName })
                });
                const data = await res.json();

                if (recipeContentEl) {
                    if (data.success) {
                        recipeContentEl.innerHTML = data.content;
                        currentRecipeHTML = data.content; // Lưu nội dung vào biến toàn cục
                    } else {
                        recipeContentEl.innerHTML = `<p style="color:red">Lỗi: ${data.message}</p>`;
                    }
                }
            } catch (err) {
                if(recipeContentEl) recipeContentEl.innerHTML = `<p style="color:red">Lỗi kết nối: ${err.message}</p>`;
            }
        });

        if (closeRecipeModal) {
            closeRecipeModal.addEventListener("click", () => {
                recipeModal.classList.add("hidden");
            });
        }
    }

    // Đóng Modal khi click ra ngoài
    window.addEventListener("click", (e) => {
        if (e.target === recipeModal) recipeModal.classList.add("hidden");
        if (e.target === subModal) subModal.classList.add("hidden");
        if (e.target === document.getElementById("auth-modal")) document.getElementById("auth-modal").style.display = "none";
    });

    // ==========================================
    // 7. XỬ LÝ MASCOT
    // ==========================================
    const mascotImg = document.getElementById("mascot-image");
    
    const weightInput = document.querySelector('input[name="weight"]');
    if (weightInput) {
        weightInput.addEventListener('focus', () => {
            showMascotMessage("Khai thật đi, dạo này có tăng cân không? ⚖️");
        });
    }
    const heightInput = document.querySelector('input[name="height"]');
    if (heightInput) {
        heightInput.addEventListener('focus', () => {
            showMascotMessage("Cao bao nhiêu rồi? Đừng ăn gian nha! 📏");
        });
    }
    
    if (mascotImg) {
        setTimeout(() => {
            showMascotMessage("Chào! Mình là Trợ lý Dinh dưỡng 🥕");
        }, 1000);

        mascotImg.addEventListener("click", () => {
            const launcher = document.getElementById("chat-launcher");
            if (launcher) launcher.click();
            const funnyQuotes = ["Cần thực đơn healthy không? 🥗", "Đừng lo béo, có tớ lo! 🍬", "Tớ là Bếp trưởng AI đây! 👨‍🍳"];
            const randomQuote = funnyQuotes[Math.floor(Math.random() * funnyQuotes.length)];
            showMascotMessage(randomQuote);
        });
    }

    // ==========================================
    // 8. TÍNH NĂNG PHÂN TÍCH BỮA ĂN
    // ==========================================
    let mealChartInstance = null;

    async function analyzeMeal() {
        const input = document.getElementById("meal-input").value;
        if (!input.trim()) {
            showMascotMessage("Ơ kìa, bạn chưa nhập món ăn nào cả! 🥕");
            return;
        }

        document.getElementById("loading-calc").classList.remove("hidden");
        document.getElementById("result-calc").classList.add("hidden");
        showMascotMessage("Đợi xíu, tớ đang soi calo giúp bạn... 🔍");

        try {
            const response = await fetch('/api/analyze-meal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meal_input: input })
            });

            const res = await response.json();
            document.getElementById("loading-calc").classList.add("hidden");

            if (res.success) {
                renderMealResult(res.data);
                showMascotMessage("Xong rồi! Xem kết quả bên dưới nhé 👇");
            } else {
                alert(res.message);
            }
        } catch (err) {
            console.error(err);
            document.getElementById("loading-calc").classList.add("hidden");
            alert("Lỗi kết nối server!");
        }
    }

    function renderMealResult(data) {
        const resultDiv = document.getElementById("result-calc");
        const tbody = document.getElementById("meal-list-body");
        const totalDisplay = document.getElementById("total-cals-display");
        const adviceDisplay = document.getElementById("ai-advice");

        resultDiv.classList.remove("hidden");
        totalDisplay.innerText = data.total_calories;
        adviceDisplay.innerText = `"${data.advice}"`;

        tbody.innerHTML = "";
        const labels = [];
        const caloriesData = [];

        data.items.forEach(item => {
            const row = `
                <tr style="border-bottom: 1px solid #f0f0f0;">
                    <td style="padding: 12px 10px;">
                        <div style="font-weight: 600;">${item.name}</div>
                        <div style="font-size: 0.8rem; color: #888;">
                            P: ${item.protein}g | C: ${item.carbs}g | F: ${item.fat}g
                        </div>
                    </td>
                    <td style="padding: 12px 10px;">${item.portion}</td>
                    <td style="padding: 12px 10px; text-align: right; font-weight: bold; color: var(--primary-dark);">
                        ${item.calories}
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
            labels.push(item.name);
            caloriesData.push(item.calories);
        });

        const ctx = document.getElementById('mealChart').getContext('2d');
        if (mealChartInstance) mealChartInstance.destroy();

        mealChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: caloriesData,
                    backgroundColor: ['#00b894', '#0984e3', '#fd79a8', '#fab1a0', '#6c5ce7'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } },
                    title: { display: true, text: 'Tỉ lệ Calo', font: { size: 14 } }
                }
            }
        });
    }

    // EXPOSE Hàm ra ngoài window
    window.analyzeMeal = analyzeMeal;

    // ==========================================
    // 9. HỆ THỐNG ĐĂNG NHẬP
    // ==========================================
    let isRegister = false;

    async function checkLoginStatus() {
        try {
            const res = await fetch('/api/current_user');
            const data = await res.json();
            if (data.is_logged_in) {
                const userDisplay = document.getElementById("user-display-name");
                if (userDisplay) userDisplay.innerText = data.username;
            }
        } catch (e) { console.log("Chưa đăng nhập"); }
    }
    
    checkLoginStatus();

    window.openAuthModal = function() {
        const currentName = document.getElementById("user-display-name").innerText;
        if (currentName !== "Đăng nhập" && currentName !== "Login") {
            if(confirm("Bạn muốn đăng xuất?")) {
                fetch('/api/logout').then(() => {
                    location.reload();
                });
            }
            return;
        }
        document.getElementById("auth-modal").style.display = "flex";
    };

    window.toggleAuthMode = function() {
        isRegister = !isRegister;
        const title = document.getElementById("auth-title");
        const healthGroup = document.getElementById("health-check-group");
        const toggleText = document.getElementById("toggle-auth-text");

        if (isRegister) {
            title.innerText = "Đăng Ký Tài Khoản";
            healthGroup.style.display = "block";
            toggleText.innerText = "Đã có nick? Đăng nhập";
        } else {
            title.innerText = "Đăng Nhập";
            healthGroup.style.display = "none";
            toggleText.innerText = "Chưa có nick? Đăng ký ngay";
        }
    };

    window.submitAuth = async function() {
        const userInp = document.getElementById("inp-user");
        const passInp = document.getElementById("inp-pass");
        
        if(!userInp || !passInp) return;
        const user = userInp.value;
        const pass = passInp.value;
        
        let healthCondition = "";
        if (isRegister) {
            const checks = document.querySelectorAll("#health-check-group input:checked");
            let arr = [];
            checks.forEach(c => arr.push(c.value));
            healthCondition = arr.join(", ");
        }

        const url = isRegister ? '/api/register' : '/api/login';
        const payload = isRegister 
            ? { username: user, password: pass, health_condition: healthCondition }
            : { username: user, password: pass };

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                alert(data.message || "Thành công!");
                document.getElementById("auth-modal").style.display = "none";
                
                if (!isRegister) {
                    document.getElementById("user-display-name").innerText = data.username;
                    const msg = data.health_profile 
                        ? `Chào ${data.username}-kun! Đã bật chế độ bảo vệ: ${data.health_profile} 🛡️` 
                        : `Chào ${data.username}-kun! Chúc bạn một ngày healthy!`;
                    showMascotMessage(msg);
                }
            } else {
                alert(data.message);
            }
        } catch (err) {
            alert("Lỗi kết nối server");
        }
    };

    // ==========================================
    // 10. QUẢN LÝ CÔNG THỨC YÊU THÍCH [ĐÃ FIX]
    // ==========================================
    
    // Hàm Lưu Công Thức - Sử dụng biến toàn cục currentRecipeTitle
    window.saveCurrentRecipe = async function() {
        // Lấy nội dung trực tiếp từ Popup nếu biến chưa có
        if (!currentRecipeHTML) {
             const contentEl = document.getElementById("recipe-popup-content");
             if(contentEl) currentRecipeHTML = contentEl.innerHTML;
        }

        if (!currentRecipeTitle || !currentRecipeHTML) {
            alert("Chưa có nội dung hoặc tên món để lưu!");
            return;
        }

        try {
            const res = await fetch('/api/save-recipe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    title: currentRecipeTitle,
                    content: currentRecipeHTML
                })
            });
            const data = await res.json();
            
            if(data.success) {
                alert(data.message);
                const btnIcon = document.querySelector("#btn-save-recipe i");
                if(btnIcon) btnIcon.className = "fas fa-heart"; // Đổi tim đặc
            } else {
                alert(data.message); 
                if(data.message && data.message.includes("Login")) window.openAuthModal();
            }
        } catch(err) {
            alert("Lỗi kết nối hoặc chưa đăng nhập!");
        }
    };


// Biến toàn cục để lưu danh sách tải về (dùng để tra cứu khi bấm Xem lại)
let savedRecipesData = [];

window.loadSavedRecipes = async function() {
    const listDiv = document.getElementById("saved-list");
    listDiv.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:30px;"><i class="fas fa-spinner fa-spin fa-2x" style="color:var(--primary)"></i><br>Đang tải bộ sưu tập...</div>';

    try {
        const res = await fetch('/api/get-saved-recipes');
        const data = await res.json();

        if (data.success) {
            savedRecipesData = data.data; // Lưu data vào biến toàn cục

            if (data.data.length === 0) {
                listDiv.innerHTML = `
                    <div style="grid-column: 1/-1; text-align:center; color: #636e72;">
                        <i class="far fa-folder-open" style="font-size: 2rem; margin-bottom: 10px; display:block;"></i>
                        Bạn chưa lưu món nào cả.
                    </div>`;
                return;
            }

            listDiv.innerHTML = "";
            
            // Render từng thẻ món ăn
            data.data.forEach(item => {
                const card = document.createElement("div");
                card.className = "recipe-card"; 
                card.innerHTML = `
                    <h3 style="color:var(--primary); margin-top:0;">${item.title}</h3>
                    <div style="font-size:0.8rem; color:#888; margin-bottom:10px;">
                        <i class="far fa-calendar-alt"></i> ${item.date}
                    </div>
                    
                    <div style="max-height:100px; overflow:hidden; opacity:0.7; font-size:0.9rem; margin-bottom:10px;">
                        ${item.content} 
                    </div>
                    
                    <div style="margin-top:10px; border-top:1px solid #eee; padding-top:10px; display:flex; justify-content:space-between;">
                        <button onclick="viewRecipe(${item.id})" style="border:none; background:none; color:var(--secondary); cursor:pointer; font-weight:bold;">
                            <i class="fas fa-eye"></i> Xem lại
                        </button>
                        
                        <button onclick="deleteRecipe(${item.id})" style="border:none; background:none; color:#ff7675; cursor:pointer;">
                            <i class="fas fa-trash-alt"></i> Xóa
                        </button>
                    </div>
                `;
                listDiv.appendChild(card);
            });
        } else {
            listDiv.innerHTML = `<p style="text-align:center">Vui lòng đăng nhập để xem.</p>`;
        }
    } catch (err) {
        console.error(err);
        listDiv.innerHTML = `<p style="text-align:center; color:red;">Lỗi kết nối server!</p>`;
    }
};

    // --- HÀM XỬ LÝ XEM LẠI ---
    window.viewRecipe = function(id) {
        // 1. Tìm món ăn trong biến savedRecipesData dựa vào ID
        const recipe = savedRecipesData.find(item => item.id === id);
        if (!recipe) return;

        // 2. Mở Modal hiển thị
        const recipeModal = document.getElementById("chef-modal");
        const modalTitle = recipeModal.querySelector("h2");
        const contentEl = document.getElementById("recipe-popup-content");

        if (modalTitle) modalTitle.innerHTML = `<i class="fas fa-book-open"></i> ${recipe.title}`;
        if (contentEl) contentEl.innerHTML = recipe.content; // Đổ nội dung HTML đã lưu vào đây

        recipeModal.classList.remove("hidden");
    };

    // --- HÀM XỬ LÝ XÓA ---
    window.deleteRecipe = async function(id) {
        if (!confirm("Bạn có chắc muốn xóa công thức này không?")) return;

        try {
            const res = await fetch('/api/delete-recipe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id })
            });
            const data = await res.json();

            if (data.success) {
                alert(data.message);
                // Tải lại danh sách để mất cái thẻ vừa xóa
                loadSavedRecipes();
            } else {
                alert("Lỗi: " + data.message);
            }
        } catch (err) {
            alert("Lỗi kết nối server khi xóa!");
        }
    };
});
