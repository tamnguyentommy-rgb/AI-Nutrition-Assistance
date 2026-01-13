document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // 1. TÍNH NĂNG TÍNH CALO
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
            li.innerHTML = `<span>${item.name}</span><b>${item.gram}g</b>`;
            list.appendChild(li);
        });

        // Vẽ biểu đồ Chart.js
        const ctx = document.getElementById('myChart').getContext('2d');
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
    // 2. TÍNH NĂNG BẾP TRƯỞNG AI (Đã update)
    // ==========================================
    const btnSuggest = document.getElementById("btn-suggest");
    const chefResult = document.getElementById("chef-result");
    const chefContent = document.getElementById("chef-content");

    if (btnSuggest) {
        btnSuggest.addEventListener("click", async () => {
            // Lấy nguyên liệu
            const checkedBoxes = document.querySelectorAll("#ingredient-list input:checked");
            const selectedIngs = Array.from(checkedBoxes).map(cb => cb.value);
            
            // Lấy thông tin người và số món
            const people = document.getElementById("people-count").value;
            const dishCount = document.getElementById("dish-count").value;

            // Validate
            if (selectedIngs.length === 0) {
                alert("Bạn ơi, chọn ít nhất 1 nguyên liệu trong tủ lạnh đi!");
                return;
            }

            // Hiệu ứng Loading
            const originalText = btnSuggest.innerHTML;
            btnSuggest.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đầu bếp đang suy nghĩ...';
            btnSuggest.disabled = true;
            btnSuggest.style.opacity = "0.8";
            chefResult.classList.add("hidden");

            try {
                const res = await fetch("/suggest-recipe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    // Gửi thêm num_dishes
                    body: JSON.stringify({ 
                        ingredients: selectedIngs, 
                        people: people,
                        num_dishes: dishCount
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
                // Reset nút
                btnSuggest.innerHTML = originalText;
                btnSuggest.disabled = false;
                btnSuggest.style.opacity = "1";
            }
        });
    }
});
