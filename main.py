from datetime import datetime
import math

# --- 1. NUTRITION DATA (Reference Values for Automation) ---
PRO_CAL_OZ = 35  # Average for Chicken/Lean Turkey/Fish
CARB_CAL_OZ = 32 # Average for Cooked Rice/Potato
FAT_CAL_OZ = 150 # Average for Oils/Nuts/Avocado

# Official Navy Max Weight Table
NAVY_MAX_WEIGHTS = {
    60: 141, 61: 145, 62: 150, 63: 155, 64: 160, 65: 165, 66: 170, 67: 175, 68: 181, 
    69: 186, 70: 191, 71: 197, 72: 202, 73: 208, 74: 214, 75: 220, 76: 225, 77: 231, 
    78: 237, 79: 244, 80: 250
}

# --- 2. THE TAILORED PLAN GENERATOR ---
def generate_tailored_plan(target_calories, env, goal_name, weeks):
    """Calculates and prints the exact meal and workout plan."""
    meal_cals = target_calories / 4
    p_oz = round((meal_cals * 0.40) / PRO_CAL_OZ, 1)
    c_oz = round((meal_cals * 0.35) / CARB_CAL_OZ, 1)
    f_oz = round((meal_cals * 0.25) / FAT_CAL_OZ, 1)

    print("\n" + "!"*20 + " YOUR TAILORED MISSION PLAN " + "!"*20)
    
    if env == "2": # OFF-BASE AUTOMATION
        print(f"LOCATION: OFF-BASE | GOAL: {goal_name.upper()}")
        print(f"DAILY TARGET: {round(target_calories)} CALORIES")
        print(f"\n[EXACT MEASUREMENTS PER MEAL (4x DAILY)]")
        print(f"- PROTEIN: {p_oz} oz (Cooked) - Chicken, Turkey, or White Fish.")
        print(f"- CARBS:   {c_oz} oz (Cooked) - Rice, Sweet Potato, or Quinoa.")
        print(f"- FATS:    {f_oz} oz - Healthy Fats (Almonds, Avocado) or 1 tbsp Olive Oil.")
        print("- VOLUME:  Minimum 1.5 cups of Green Veggies (Broccoli, Spinach, etc.).")
    else: # BARRACKS
        print(f"LOCATION: BARRACKS | GOAL: {goal_name.upper()}")
        print(f"DAILY TARGET: {round(target_calories)} CALORIES")
        print(f"\n[VISUAL PORTION GUIDE PER MEAL]")
        print(f"- PROTEIN: {round(p_oz/3.5, 1)} 'Palms' of Lean Protein. (Ask for Double).")
        print(f"- CARBS:   1 Rounded Scoop of Rice or 1 Medium Potato.")
        print("- VEGGIES: Fill the rest of the tray with Greens.")

    print("\n[TRAINING MISSION]")
    if "lose" in goal_name.lower() or "cut" in goal_name.lower():
        print(f"- CARDIO: 30 min Fasted Walk daily for the next {int(weeks)} weeks.")
        print("- PFA: 15 min Push-ups and Planks.")
    elif "gain" in goal_name.lower() or "bulk" in goal_name.lower():
        print("- STRENGTH: 45 min Heavy Resistance Training (Squat/Bench/Deadlift).")
        print("- RECOVERY: 15 min Light Movement/Mobility.")
    else:
        print("- MAINTENANCE: 30 min Mixed Activity (Run/Swim/Lift) 4x per week.")
    
    print("- SLEEP: 7.5+ Hours of sleep is mandatory for proper recovery.")
    
    print("="*64)
    print("           STAY DISCIPLINED, SHIPMATE.")
    print("="*64)

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
    print("      PFA PRO: MISSION READINESS COACH (V1.5)")
    print("="*50)
    
    while True:
        date_str = input("\nEnter the date of your next BCA (MM/DD/YYYY): ")
        try:
            bca_date = datetime.strptime(date_str, "%m/%d/%Y")
            today = datetime.now().date()
            target_day = bca_date.date()

            if target_day < today:
                print(f"[!] Error: {date_str} is in the past.")
                continue
            else:
                days_until = (target_day - today).days
                weeks_until = max(1, days_until // 7)
                print(f"[*] Timeline: {days_until} days remaining ({weeks_until} weeks).")
                break
        except ValueError:
            print("[!] Invalid format. Please use MM/DD/YYYY.")

    gender = input("Gender (Male/Female): ").strip().lower()
    while gender not in ["male", "female"]:
        gender = input("[!] Enter 'male' or 'female': ").strip().lower()

    age = get_valid_input("Age: ", 17, 65)
    height_in = round(get_valid_input("Height (inches): ", 50, 95))
    weight_lbs = get_valid_input("Current Weight (lbs): ", 90, 500)
    max_weight = NAVY_MAX_WEIGHTS.get(height_in, 191)

    passed_bca = weight_lbs <= max_weight
    if not passed_bca:
        print(f"\n[!] Weight ({weight_lbs} lbs) is above Navy Max ({max_weight} lbs).")
        waist_in = get_valid_input("Enter Waist Circumference (inches): ", 20, 80)
        whtr = waist_in / height_in
        passed_bca = whtr < 0.55

    weight_kg = weight_lbs * 0.453592
    height_cm = height_in * 2.54
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "male" else -161)
    tdee = bmr * 1.3 

    if not passed_bca:
        target_calories = tdee - 500
        goal_name = "Weight Loss (BCA Prep)"
    else:
        print(f"\nBCA STATUS: PASS\n" + "-"*30)
        print("1. Lose (Cut)\n2. Maintain\n3. Gain (Bulk)")
        goal_choice = input("Select (1/2/3): ")
        
        if goal_choice == "1":
            target_calories = tdee - 500
            goal_name = "Weight Loss (Cutting)"
        elif goal_choice == "3":
            target_calories = tdee + 300
            goal_name = "Weight Gain (Bulking)"
        else:
            target_calories = tdee
            goal_name = "Maintenance"

    print("\n[ENVIRONMENT]\n1. Barracks\n2. Off-Base")
    env_choice = input("Select (1/2): ")

    generate_tailored_plan(target_calories, env_choice, goal_name, weeks_until)

if __name__ == "__main__":
    try:
        while True:
            run_pfa_pro()
            if input("\nRun another analysis? (y/n): ").lower() != 'y':
                print("Secure the watch. Goodbye.")
                break
    except KeyboardInterrupt:
        print("\n\n[!] Program closed.")