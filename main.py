import math

def run_pfa_pro():
    print("--- PFA Pro: Always Mission Ready ---")
    
    # --- 1. USER DATA ---
    gender = input("Enter Gender (Male/Female): ").strip().lower()
    age = int(input("Enter Age: "))
    height_in = float(input("Enter Height (inches): "))
    weight_lbs = float(input("Enter Current Weight (lbs): "))
    
    # --- 2. THE BCA CHECK ---
    # Placeholder: 191 lbs is the Navy max for a 70-inch male
    max_weight = 191 

    if weight_lbs <= max_weight:
        passed_bca = True
        whtr_display = "Passed (Weight Table)"
        print(f"\n>>> Weight {weight_lbs} lbs is within standards. No tape required.")
    else:
        print(f"\n>>> Over weight standard ({max_weight} lbs).")
        waist_in = float(input("Enter Waist Circumference (inches): "))
        whtr = round(waist_in / height_in, 3)
        passed_bca = whtr < 0.55
        whtr_display = f"{whtr} (Waist-to-Height)"

        # --- IMPROVEMENT PLAN (Triggered if BCA Fail) ---
        if not passed_bca:
            # Option 1: The Tape Path (0.549 safety margin)
            target_waist = round(height_in * 0.549, 1)
            waist_loss_needed = round(waist_in - target_waist, 1)
            # 1 inch ≈ 7 lbs estimate
            est_weight_loss_for_tape = round(waist_loss_needed * 7)
            
            # Option 2: The Scale Path
            weight_loss_needed = round(weight_lbs - max_weight, 1)
            
            print(f"\n[!] MISSION READINESS PLAN:")
            print(f"    OPTION 1 (The Tape): Lose {waist_loss_needed}\" (Approx. {est_weight_loss_for_tape} lbs)")
            print(f"    - Target Waist: {target_waist}\"")
            
            print(f"    OPTION 2 (The Scale): Lose {weight_loss_needed} lbs")
            print(f"    - Target Weight: {max_weight} lbs")
            print(f"    *Note: Option 1 is often the faster path to readiness.*")

    # --- 3. AUTO-GOAL SELECTION ---
    if not passed_bca:
        print("\n>>> BCA Not Met: Goal locked to 'Weight Loss' for readiness.")
        goal = "1"
        goal_text = "BCA Correction (Deficit)"
    else:
        print("\nSelect your Goal:")
        print("1. Lose Weight")
        print("2. Maintain")
        print("3. Gain Muscle")
        goal = input("Enter 1, 2, or 3: ")
        
        if goal == "1":
            goal_text = "Weight Loss"
        elif goal == "3":
            goal_text = "Muscle Gain"
        else:
            goal_text = "Maintenance"

    # --- 4. NUTRITION LOGIC ---
    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    # Mifflin-St Jeor Equation
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "male" else -161)
    maintenance = bmr * 1.55 # Activity multiplier
    
    if goal == "1":
        daily_calories = maintenance - 500
    elif goal == "3":
        daily_calories = maintenance + 300
    else:
        daily_calories = maintenance

    # Macros
    protein_g = round(weight_lbs)
    fat_g = round((daily_calories * 0.25) / 9)
    carb_g = round((daily_calories - (protein_g * 4) - (fat_g * 9)) / 4)

    # --- 5. FINAL OUTPUT ---
    print("\n" + "="*45)
    print(f"BCA STATUS:     {'PASS' if passed_bca else 'FAIL'}")
    print(f"BCA Method:     {whtr_display}")
    print(f"Current Goal:   {goal_text}")
    print("-" * 45)
    print(f"Daily Targets:  {round(daily_calories)} kcal")
    print(f"Macros (P/C/F): {protein_g}g | {carb_g}g | {fat_g}g")
    print("="*45)
    print("Shipmate, stay disciplined.")

if __name__ == "__main__":
    run_pfa_pro()