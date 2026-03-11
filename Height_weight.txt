import math

def run_pfa_pro():
    print("--- PFA Pro: Always Mission Ready ---")
    print("Navy PFA & Nutrition Assistant (2026 Standards)\n")

    # --- 1. USER DATA COLLECTION ---
    gender = input("Enter Gender (Male/Female): ").strip().lower()
    age = int(input("Enter Age: "))
    height_in = float(input("Enter Height (inches): "))
    weight_lbs = float(input("Enter Current Weight (lbs): "))
    waist_in = float(input("Enter Waist Circumference (inches): "))
    
    print("\nSelect your Goal:")
    print("1. Lose Weight (BCA Focus)")
    print("2. Gain Muscle/Strength (Lifting Focus)")
    goal_choice = input("Enter 1 or 2: ")

    # --- 2. BCA CALCULATOR (OPNAV 6110.1L) ---
    whtr = round(waist_in / height_in, 3)
    passed_bca = whtr < 0.55

    # --- 3. NUTRITION & MACROS ---
    # Convert to Metric for Mifflin-St Jeor Equation
    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    
    if gender == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    
    maintenance = bmr * 1.55  # Moderate activity multiplier
    
    if goal_choice == "1":
        daily_calories = maintenance - 500
        plan_name = "Weight Loss (Healthy Deficit)"
    else:
        daily_calories = maintenance + 300
        plan_name = "Muscle Gain (Lean Bulk)"

    # Macro Breakdown
    protein_g = round(weight_lbs)  # 1g per lb
    fat_g = round((daily_calories * 0.25) / 9)
    carb_g = round((daily_calories - (protein_g * 4) - (fat_g * 9)) / 4)

    # --- 4. PRT RUN PACE (Example for 25-29 Age Group) ---
    # Target: Excellent Low for 1.5 miles
    run_target_seconds = 650 if gender == "male" else 780
    pace_seconds_per_mile = run_target_seconds / 1.5
    pace_min = int(pace_seconds_per_mile // 60)
    pace_sec = int(pace_seconds_per_mile % 60)

    # --- 5. FINAL OUTPUT DISPLAY ---
    print("\n" + "="*40)
    print("             RESULTS")
    print("="*40)
    print(f"BCA STATUS:     {'PASS' if passed_bca else 'FAIL (Over 0.55)'}")
    print(f"Waist-to-Height: {whtr}")
    print(f"Current Plan:   {plan_name}")
    print(f"Daily Calories: {round(daily_calories)} kcal")
    print(f"Daily Macros:   {protein_g}P | {carb_g}C | {fat_g}F")
    print("-" * 40)
    print(f"PRT RUN GOAL (Excellent): {run_target_seconds // 60}:{run_target_seconds % 60:02d}")
    print(f"REQUIRED TRAINING PACE:   {pace_min}:{pace_sec:02d} /mile")
    print("="*40)
    print("Always mission ready.")

# This starts the program
if __name__ == "__main__":
    run_pfa_pro()