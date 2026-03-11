from datetime import datetime
import math

# Official Navy Max Weight Table
NAVY_MAX_WEIGHTS = {
    60: 141, 61: 145, 62: 150, 63: 155, 64: 160, 65: 165, 66: 170, 67: 175, 68: 181, 
    69: 186, 70: 191, 71: 197, 72: 202, 73: 208, 74: 214, 75: 220, 76: 225, 77: 231, 
    78: 237, 79: 244, 80: 250
}

def get_valid_input(prompt, min_val, max_val):
    while True:
        try:
            val = float(input(prompt))
            if min_val <= val <= max_val: return val
            print(f"[!] Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("[!] Invalid numeric entry. Try again.")

def run_pfa_pro():
    print("\n" + "="*50)
    print("      PFA PRO: MISSION READINESS COACH (V1.4)")
    print("="*50)
    
    # --- 1. MISSION TIMELINE ---
    while True:
        date_str = input("\nEnter the date of your next BCA (MM/DD/YYYY): ")
        try:
            bca_date = datetime.strptime(date_str, "%m/%d/%Y")
            today = datetime.now().date()
            target_day = bca_date.date()

            if target_day < today:
                print(f"[!] Error: {date_str} is in the past. Time travel not yet supported.")
                continue
            elif target_day == today:
                print("[!] Mission Day: The BCA is TODAY. No time for weight loss. Stay hydrated.")
                weeks_until = 0.1 # Minimal value to avoid division by zero
                break
            else:
                days_until = (target_day - today).days
                weeks_until = max(1, days_until // 7)
                print(f"[*] Timeline: {days_until} days remaining ({weeks_until} weeks).")
                break
        except ValueError:
            print("[!] Invalid format. Please use MM/DD/YYYY (e.g., 07/04/2026).")

    # --- 2. PHYSICAL DATA ---
    gender = input("Gender (Male/Female): ").strip().lower()
    while gender not in ["male", "female"]:
        gender = input("[!] Enter 'male' or 'female': ").strip().lower()

    age = get_valid_input("Age: ", 17, 65)
    height_in = round(get_valid_input("Height (inches): ", 50, 95))
    weight_lbs = get_valid_input("Current Weight (lbs): ", 90, 500)
    max_weight = NAVY_MAX_WEIGHTS.get(height_in, 191)

    # --- 3. BCA ANALYSIS ---
    passed_bca = weight_lbs <= max_weight
    
    if not passed_bca:
        print(f"\n[!] Weight ({weight_lbs} lbs) is above Navy Max ({max_weight} lbs).")
        waist_in = get_valid_input("Enter Waist Circumference (inches): ", 20, 80)
        whtr = waist_in / height_in
        passed_bca = whtr < 0.55
        
        # --- 4. WEIGHT LOSS METHODOLOGY ---
        if not passed_bca:
            weight_to_lose = weight_lbs - max_weight
            lbs_per_week = round(weight_to_lose / weeks_until, 1)
            
            print(f"\n" + "-"*30)
            print(f"COACHING STRATEGY:")
            print(f"Goal: Lose {weight_to_lose} lbs to meet the scale standard.")
            print(f"Required Rate: {lbs_per_week} lbs/week.")
            
            if lbs_per_week > 2.0:
                print("\n[!] HIGH INTENSITY REQUIRED")
                print("Advice: This rate is aggressive. Focus on the 'Tape' path:")
                print("1. High Protein diet to maintain muscle.")
                print("2. HIIT workouts for fat loss.")
                print("3. Cut sodium 48 hours before BCA to reduce waist bloat.")
            else:
                print("\n[+] SUSTAINABLE PATH")
                print(f"Advice: A deficit of {round(lbs_per_week * 500)} calories/day is recommended.")
            print("-"*30)

    # --- 5. GOAL SELECTION & NUTRITION ---
    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "male" else -161)
    tdee = bmr * 1.3  # Maintenance level

    if not passed_bca:
        # User is over standards; mission is clear
        target_calories = tdee - 500
        print(f"\nBCA STATUS: FAIL")
        print(f"Goal: Weight Loss (Mandatory for BCA)")
    else:
        # User is in standards; they get to choose
        print(f"\nBCA STATUS: PASS")
        print("-" * 30)
        print("What is your current performance goal?")
        print("1. Lose (Cut for definition)")
        print("2. Maintain (Stay the course)")
        print("3. Gain (Bulk for strength)")
        
        goal_choice = input("Select (1/2/3): ")
        
        if goal_choice == "1":
            target_calories = tdee - 500
            print("Goal: Weight Loss (Cutting)")
        elif goal_choice == "3":
            target_calories = tdee + 300
            print("Goal: Weight Gain (Bulking)")
        else:
            target_calories = tdee
            print("Goal: Maintenance")

    print(f"Daily Energy Target: {round(target_calories)} calories")
    print("="*50)

if __name__ == "__main__":
    try:
        while True:
            run_pfa_pro()
            if input("\nRun another analysis? (y/n): ").lower() != 'y':
                print("Secure the watch. Goodbye.")
                break
    except KeyboardInterrupt:
        print("\n\n[!] Program closed by user. Stay ready.")