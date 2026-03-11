import math

def get_valid_input(prompt, min_val, max_val):
    """Silent validation: Re-asks if input is unrealistic or not a number."""
    while True:
        try:
            val = float(input(prompt))
            if min_val <= val <= max_val:
                return val
            else:
                print("[!] Invalid entry. Please try again.")
        except ValueError:
            print("[!] Invalid entry. Please try again.")

def run_pfa_pro():
    print("--- PFA Pro: Always Mission Ready ---")
    
    # --- 1. USER DATA ---
    gender = input("Enter Gender (Male/Female): ").strip().lower()
    while gender not in ["male", "female"]:
        print("[!] Invalid entry.")
        gender = input("Enter Gender (Male/Female): ").strip().lower()

    # Validated without printing ranges
    age = get_valid_input("Enter Age: ", 17, 65)
    height_in = get_valid_input("Enter Height (inches): ", 50, 95)
    weight_lbs = get_valid_input("Enter Weight (lbs): ", 90, 500)
    
    # --- 2. THE BCA CHECK ---
    max_weight = 191 

    if weight_lbs <= max_weight:
        passed_bca = True
        whtr_display = "Passed (Weight Table)"
        print(f"\n>>> Weight {weight_lbs} lbs is within standards. No tape required.")
    else:
        print(f"\n>>> Over weight standard ({max_weight} lbs).")
        waist_in = get_valid_input("Enter Waist Circumference (inches): ", 20, 80)
        
        whtr = round(waist_in / height_in, 3)
        passed_bca = whtr < 0.55
        whtr_display = f"{whtr} (Waist-to-Height)"

        if not passed_bca:
            target_waist = round(height_in * 0.549, 1)
            waist_loss_needed = round(waist_in - target_waist, 1)
            est_weight_loss_for_tape = round(waist_loss_needed * 7)
            weight_loss_needed = round(weight_lbs - max_weight, 1)
            
            print(f"\n[!] MISSION READINESS PLAN:")
            print(f"    OPTION 1 (The Tape): Lose {waist_loss_needed}\" (Approx. {est_weight_loss_for_tape} lbs)")
            print(f"    - Target Waist: {target_waist}\"")
            print(f"    OPTION 2 (The Scale): Lose {weight_loss_needed} lbs")
            print(f"    - Target Weight: {max_weight} lbs")

    # --- 3. AUTO-GOAL SELECTION ---
    if not passed_bca:
        print("\n>>> BCA Not Met: Goal locked to 'Weight Loss'.")
        goal = "1"
        goal_text = "BCA Correction"
    else:
        print("\nSelect your Goal:")
        print("1. Lose Weight | 2. Maintain | 3. Gain Muscle")
        goal = input("Enter 1, 2, or 3: ")
        goal_text = "Weight Loss" if goal == "1" else ("Muscle Gain" if goal == "3" else "Maintenance")

    # --- 4. NUTRITION LOGIC ---
    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "male" else -161)
    maintenance = bmr * 1.55
    daily_calories = maintenance - 500 if goal == "1" else (maintenance + 300 if goal == "3" else maintenance)

    # --- 5. FINAL OUTPUT ---
    print("\n" + "="*45)
    print(f"BCA STATUS:     {'PASS' if passed_bca else 'FAIL'}")
    print(f"BCA Method:     {whtr_display}")
    print(f"Current Goal:   {goal_text}")
    print(f"Daily Target:   {round(daily_calories)} kcal")
    print("="*45)
    print("Shipmate, stay disciplined.")

if __name__ == "__main__":
    try:
        while True: # This starts the loop
            run_pfa_pro()
            
            # Ask the user if they want to go again
            repeat = input("\nRun another calculation? (y/n): ").strip().lower()
            if repeat != 'y':
                print("Secure the watch. Goodbye.")
                break # This exits the loop
            print("\n" + "-"*30 + "\n") # Visual separator for the next run
            
    except KeyboardInterrupt:
        print("\n\n[!] Program closed. Stay ready, Shipmate.")