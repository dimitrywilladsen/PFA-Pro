import math

def run_pfa_pro():
    print("--- PFA Pro: Always Mission Ready ---")
    
    # --- 1. USER DATA ---
    gender = input("Enter Gender (Male/Female): ").strip().lower()
    age = int(input("Enter Age: "))
    height_in = float(input("Enter Height (inches): "))
    weight_lbs = float(input("Enter Current Weight (lbs): "))
    
    # --- 2. THE SMARTER BCA CHECK ---
    max_weight = 191 # Placeholder for 70in Sailor

    if weight_lbs <= max_weight:
        passed_bca = True
        whtr_display = "Passed (Weight Table)"
        print(f"\n>>> Weight {weight_lbs} lbs is within standards. No tape required.")
    else:
        print(f"\n>>> Over weight standard ({max_weight} lbs).")
        waist_in = float(input("Enter Waist (inches): "))
        whtr = round(waist_in / height_in, 3)
        passed_bca = whtr < 0.55
        whtr_display = f"{whtr} (Waist-to-Height)"

    # --- 3. GOAL SELECTION (Your Progress!) ---
    print("\nSelect your Goal:")
    print("1. Lose Weight")
    print("2. Maintain")
    print("3. Gain Muscle")
    goal = input("Enter 1, 2, or 3: ")

    # --- 4. NUTRITION LOGIC ---
    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "male" else -161)
    maintenance = bmr * 1.55
    
    # Adjust calories based on your choice
    if goal == "1":
        daily_calories = maintenance - 500
        goal_text = "Fat Loss"
    elif goal == "3":
        daily_calories = maintenance + 300
        goal_text = "Muscle Gain"
    else:
        daily_calories = maintenance
        goal_text = "Maintenance"

    protein_g = round(weight_lbs)
    fat_g = round((daily_calories * 0.25) / 9)
    carb_g = round((daily_calories - (protein_g * 4) - (fat_g * 9)) / 4)

    # --- 5. RUN PACE ---
    run_target = 650 if gender == "male" else 780
    pace_min = int((run_target / 1.5) // 60)
    pace_sec = int((run_target / 1.5) % 60)

    # --- 6. FINAL OUTPUT ---
    print("\n" + "="*40)
    print(f"BCA STATUS:     {'PASS' if passed_bca else 'FAIL'}")
    print(f"BCA Method:     {whtr_display}")
    print(f"Goal:           {goal_text}")
    print(f"Daily Targets:  {round(daily_calories)} kcal")
    print(f"Macros (P/C/F): {protein_g}g | {carb_g}g | {fat_g}g")
    print(f"Run Pace Goal:  {pace_min}:{pace_sec:02d} /mile")
    print("="*40)
    print("Always mission ready.")

if __name__ == "__main__":
    run_pfa_pro()