document.addEventListener("DOMContentLoaded", () => {
    
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

            try {
                const formData = new FormData(calcForm);
                const res = await fetch("/solve", { method: "POST", body: formData });
                const data = await res.json();

                if (!data.success) {
                    alert(data.message);
                } else {
                    renderResults(data);
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
            
            // Thêm nút SWAP (Thay thế)
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

        // Gắn sự kiện cho các nút Swap
        document.querySelectorAll(".btn-swap").forEach(btn => {
            btn.addEventListener("click", function(e) {
                e.stopPropagation(); // Ngăn sự kiện click lan ra ngoài (để không kích hoạt popup công thức)
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

        // Gọi API
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
    // 3. TÍNH NĂNG QUÉT TỦ LẠNH (VISION)
    // ==========================================
    const fridgeInput = document.getElementById("fridge-upload");
    const uploadStatus = document.getElementById("upload-status");
    const ingredientListDiv = document.getElementById("ingredient-list");

    if (fridgeInput) {
        fridgeInput.addEventListener("change", async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            uploadStatus.textContent = "⏳ Đang quét ảnh...";
            uploadStatus.style.color = "#0984e3";

            const formData = new FormData();
            formData.append("image", file);

            try {
                const res = await fetch("/scan-fridge", {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();

                if (data.success) {
                    uploadStatus.textContent = "✅ Đã nhận diện xong!";
                    uploadStatus.style.color = "#00b894";
                    
                    data.ingredients.forEach(ing => {
                        const cleanName = ing.trim();
                        let found = false;

                        const checkboxes = ingredientListDiv.querySelectorAll("input[type='checkbox']");
                        checkboxes.forEach(cb => {
                            if (cb.value.toLowerCase().includes(cleanName.toLowerCase()) || 
                                cleanName.toLowerCase().includes(cb.value.toLowerCase())) {
                                cb.checked = true;
                                found = true;
                                cb.parentElement.scrollIntoView({ block: "center", behavior: "smooth" });
                            }
                        });

                        if (!found) {
                            const label = document.createElement("label");
                            label.className = "tag-check";
                            label.style.border = "2px solid #6c5ce7"; 
                            label.innerHTML = `<input type="checkbox" value="${cleanName}" checked> ${cleanName} (Scan)`;
                            ingredientListDiv.prepend(label);
                        }
                    });
                } else {
                    uploadStatus.textContent = "❌ " + data.message;
                    uploadStatus.style.color = "#d63031";
                }
            } catch (err) {
                console.error(err);
                uploadStatus.textContent = "❌ Lỗi hệ thống";
            }
        });
    }

    // ==========================================
    // 4. BẾP TRƯỞNG AI (SCAN TỦ LẠNH)
    // ==========================================
    const btnSuggest = document.getElementById("btn-suggest");
    const chefResult = document.getElementById("chef-result");
    const chefContent = document.getElementById("chef-content"); // Cái này của phần Fridge Chef

    if (btnSuggest) {
        btnSuggest.addEventListener("click", async () => {
            const checkedBoxes = document.querySelectorAll("#ingredient-list input:checked");
            const selectedIngs = Array.from(checkedBoxes).map(cb => cb.value);
            const people = document.getElementById("people-count").value;
            const dishCount = document.getElementById("dish-count").value;

            const allergyInput = document.getElementById("allergy-input"); 
            const allergyValue = allergyInput ? allergyInput.value : "";

            if (selectedIngs.length === 0) {
                alert("Bạn ơi, chọn nguyên liệu đi (hoặc Scan ảnh)!");
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
                        allergies: allergyValue
                    })
                });
                
                const data = await res.json();
                
                if (data.success) {
                    chefContent.innerHTML = data.content;
                    chefResult.classList.remove("hidden");
                    chefResult.scrollIntoView({ behavior: "smooth" });
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
            msgDiv.textContent = text;
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
    // 6. [MỚI] CLICK MÓN ĂN -> POPUP CÔNG THỨC
    // ==========================================
    const menuListEl = document.getElementById("menu-list");
    const recipeModal = document.getElementById("chef-modal"); // Modal Popup
    const closeRecipeModal = recipeModal ? recipeModal.querySelector(".close-modal") : null;
    
    // SỬA: Lấy đúng ID mới trong modal để không đè lên phần Fridge Chef
    const recipeContentEl = document.getElementById("recipe-popup-content");

    if (menuListEl && recipeModal) {
        menuListEl.addEventListener("click", async (e) => {
            // Tìm thẻ li gần nhất
            const item = e.target.closest("li");
            // Kiểm tra xem có click vào nút swap không (nếu swap thì bỏ qua)
            const isSwapBtn = e.target.closest(".btn-swap");

            if (!item || isSwapBtn) return;

            // Lấy tên món từ class .food-name (đã thêm ở phần renderResults trên)
            // Hoặc fallback lấy text cũ
            const nameEl = item.querySelector(".food-name");
            let foodName = nameEl ? nameEl.textContent.trim() : "";
            
            // Nếu không tìm thấy class, thử lấy text node đầu tiên
            if (!foodName) {
                let rawText = item.textContent;
                foodName = rawText.split("(")[0].trim();
            }

            if (!foodName) return;

            // Hiển thị Modal
            recipeModal.classList.remove("hidden");
            if(recipeContentEl) {
                recipeContentEl.innerHTML = '<div style="text-align:center; padding:20px"><i class="fas fa-spinner fa-spin fa-2x"></i><br>Đang hỏi bếp trưởng công thức...</div>';
            }

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

        // Đóng Modal Công thức
        if (closeRecipeModal) {
            closeRecipeModal.addEventListener("click", () => {
                recipeModal.classList.add("hidden");
            });
        }
        
        // Click ra ngoài thì đóng
        window.addEventListener("click", (e) => {
            if (e.target === recipeModal) {
                recipeModal.classList.add("hidden");
            }
        });
    }
    
});
