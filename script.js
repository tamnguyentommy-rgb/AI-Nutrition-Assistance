document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // [CODE MỚI] 0. TỰ ĐỘNG GHI NHỚ NGƯỜI DÙNG
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
            
            li.innerHTML = `
                <div style="display:flex; justify-content:space-between; width:100%; align-items:center;">
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

        document.querySelectorAll(".btn-swap").forEach(btn => {
            btn.addEventListener("click", function(e) {
                e.stopPropagation(); 
                const foodName = this.getAttribute("data-name");
                openSubModal(foodName);
            });
        });

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
    const subTitle = document.getElementById("sub-title");
    const subResult = document.getElementById("sub-result");
    const subLoading = document.getElementById("sub-loading");
    const closeModal = document.querySelector(".close-modal");

    function openSubModal(foodName) {
        if (!subModal) return;
        subModal.classList.remove("hidden");
        if (subTitle) subTitle.textContent = `Tìm thay thế cho: ${foodName}`;
        if (subResult) subResult.innerHTML = "";
        if (subLoading) subLoading.classList.remove("hidden");

        showMascotMessage(`Để xem có gì thay thế cho ${foodName} nhé... 🤔`);

        fetch("/suggest-substitute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ food_name: foodName })
        })
        .then(res => res.json())
        .then(data => {
            if(data.success) {
                subResult.innerHTML = data.content;
            } else {
                subResult.innerHTML = "Không tìm thấy gợi ý.";
            }
        })
        .catch(err => {
            subResult.innerHTML = "Lỗi kết nối AI.";
        })
        .finally(() => {
            if (subLoading) subLoading.classList.add("hidden");
        });
    }

    if(closeModal) {
        closeModal.addEventListener("click", () => subModal.classList.add("hidden"));
    }
    window.onclick = function(event) {
        if (event.target == subModal) subModal.classList.add("hidden");
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
    // 6. POPUP CÔNG THỨC
    // ==========================================
    const menuListEl = document.getElementById("menu-list");
    const recipeModal = document.getElementById("chef-modal");
    const closeRecipeModal = recipeModal ? recipeModal.querySelector(".close-modal") : null;
    const recipeContentEl = document.getElementById("recipe-popup-content");

    if (menuListEl && recipeModal) {
        menuListEl.addEventListener("click", async (e) => {
            const item = e.target.closest("li");
            const isSwapBtn = e.target.closest(".btn-swap");

            if (!item || isSwapBtn) return;

            const nameEl = item.querySelector(".food-name");
            let foodName = nameEl ? nameEl.textContent.trim() : "";
            
            if (!foodName) {
                let rawText = item.textContent;
                foodName = rawText.split("(")[0].trim();
            }

            if (!foodName) return;

            recipeModal.classList.remove("hidden");
            if(recipeContentEl) {
                recipeContentEl.innerHTML = '<div style="text-align:center; padding:20px"><i class="fas fa-spinner fa-spin fa-2x"></i><br>Đang hỏi bếp trưởng công thức...</div>';
            }
            
            showMascotMessage(`Món ${foodName} nấu dễ lắm, xem nhé! 📖`);

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
        window.addEventListener("click", (e) => {
            if (e.target === recipeModal) {
                recipeModal.classList.add("hidden");
            }
        });
    }

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
    // 8. TÍNH NĂNG PHÂN TÍCH BỮA ĂN (ĐÃ SỬA LỖI)
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

    // ==========================================
    // [FIX] CÔNG KHAI HÀM RA NGOÀI (GLOBAL SCOPE)
    // Để nút bấm HTML onclick="analyzeMeal()" nhìn thấy nó
    // ==========================================
    window.analyzeMeal = analyzeMeal;

});
