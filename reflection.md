# Reflection

## Why this system might be wrong

This system produces recommendations based on estimated nutritional data and assumed user behavior. As a result, its outputs should be interpreted as decision support rather than exact prescriptions. Several sources of uncertainty and modeling assumptions may lead to deviations between the system’s recommendations and real-world outcomes.

---

## ***Sources of uncertainty***

### 1. Calorie estimation from food descriptions

Calorie estimation is inherently uncertain because dishes with identical names can vary significantly in ingredients, portion sizes, and cooking methods.  
For example, a dish such as *bún bò* may be estimated at approximately 450 kcal based on standard assumptions about noodles and beef. In practice, vendors may add pork, pork leg, additional toppings, or varying amounts of oil, resulting in substantial deviations from the estimated calorie value.

This highlights a fundamental limitation of relying on average food databases and textual descriptions to infer precise nutritional values.

---

### 2. Budget-constrained meal generation

Early versions of the system applied linear optimization techniques to minimize cost while satisfying calorie constraints. While mathematically optimal, this approach often produced unrealistic meal plans, such as repeatedly suggesting low-cost foods (e.g., eggs) to meet calorie requirements.

To improve realism, the system was later transitioned to AI-based generation through prompt engineering. This increased diversity and practicality but introduced new forms of uncertainty, including repetitive meals and conservative spending behavior.

Additional heuristics—such as ingredient randomization and budget-sensitive spending encouragement—were introduced to mitigate these issues. However, these changes revealed a broader limitation: optimizing for cost and nutrition does not guarantee alignment with human eating preferences or behavior.

---

### 3. ***Cultural and gastronomic realism***

When generating meals from user-selected ingredients, the system may produce combinations that are nutritionally valid but culturally or gastronomically unrealistic (e.g., unconventional ingredient pairings).

This reflects the model’s lack of an explicit understanding of taste, cultural norms, and ingredient compatibility unless such constraints are explicitly encoded.

---

## ***Key trade-offs***

- Mathematical optimization ensured cost efficiency and calorie sufficiency but often sacrificed realism.
- AI-based generation improved meal plausibility at the expense of optimality and consistency.
- Increasing randomness enhanced diversity but occasionally produced unconventional or impractical dishes.
- Budget-aware heuristics improved perceived quality but risked misalignment with individual user preferences.

---

## ***What I learned about AI limits***

This project demonstrated that AI systems can generate plausible outputs under constraints, but they do not inherently understand context, culture, or human intent.  
Effective AI system design therefore requires not only improving model outputs, but also explicitly acknowledging uncertainty, modeling assumptions, and enforcing guardrails to prevent technically valid yet impractical recommendations.
