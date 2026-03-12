import streamlit as st
import pandas as pd
import datetime
import os
import re
import json

# --- GLOBAL CONFIGURATION ---
MODEL_ID = "gemini-2.5-flash"

# --- CALLBACKS ---
def handle_workout_submission():
    st.session_state["temp_workout_val"] = st.session_state["workout_text_box"]
    st.session_state["workout_text_box"] = ""

def handle_meal_submission():
    st.session_state["temp_meal_val"] = st.session_state["meal_text_box"]
    st.session_state["meal_text_box"] = ""

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="Navy PFA Pro", layout="wide", page_icon="⚓")

# Initialize Gemini Client
try:
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("🔑 Configuration Error: Check your API Key in Streamlit Secrets.")
    st.stop()

# --- 2. DATA FUNCTIONS ---
def load_data():
    if os.path.exists('fitness_log.csv'):
        try:
            df = pd.read_csv('fitness_log.csv')
            df['date'] = df['date'].astype(str)
            return df
        except:
            return pd.DataFrame(columns=['date', 'type', 'description', 'calories'])
    return pd.DataFrame(columns=['date', 'type', 'description', 'calories'])

def save_entry(entry_type, desc, cals, target_date=None):
    file_exists = os.path.exists('fitness_log.csv')
    adjusted_cals = -abs(cals) if entry_type in ["Exercise", "Passive"] else abs(cals)
    log_date = str(target_date) if target_date else str(datetime.date.today())
    new_data = pd.DataFrame([[log_date, entry_type, desc, adjusted_cals]], 
                            columns=['date', 'type', 'description', 'calories'])
    new_data.to_csv('fitness_log.csv', mode='a', header=not file_exists, index=False)

def load_pantry():
    if os.path.exists('pantry.csv'):
        return pd.read_csv('pantry.csv')
    return pd.DataFrame(columns=['item', 'quantity'])

def update_pantry(item, qty, action="add"):
    pantry = load_pantry()
    item = item.lower().strip()
    if item in pantry['item'].values:
        if action == "add":
            pantry.loc[pantry['item'] == item, 'quantity'] += qty
        else:
            pantry.loc[pantry['item'] == item, 'quantity'] -= qty
    elif action == "add":
        new_item = pd.DataFrame([[item, qty]], columns=['item', 'quantity'])
        pantry = pd.concat([pantry, new_item], ignore_index=True)
    pantry = pantry[pantry['quantity'] > 0]
    pantry.to_csv('pantry.csv', index=False)

@st.dialog("Confirm Deletion")
def confirm_delete_dialog(indices):
    st.warning(f"⚠️ This will permanently delete {len(indices)} entries. Proceed?")
    if st.button("🔥 Confirm Bulk Purge", type="primary", use_container_width=True):
        df = load_data()
        df = df.drop(indices)
        df.to_csv('fitness_log.csv', index=False)
        st.session_state['df_key'] += 1 
        st.rerun()

with st.sidebar:
    st.header("🚢 Mission Parameters")
    
    # THE UNIFIED DATE INPUT
    mission_deadline = st.date_input(
        "Mission Deadline (BCA/PRT/Goal Date)", 
        value=datetime.date.today() + datetime.timedelta(days=90),
        help="The unified target date for your body composition, physical test, and mission goals."
    )
    
    # SAFETY BRIDGE: Prevents 'bca_date' name errors in other parts of your script
    bca_date = mission_deadline
    
    # Calculate days remaining globally
    days_to_deadline = (mission_deadline - datetime.date.today()).days
    
    # Visual countdown for the Sailor
    if days_to_deadline > 0:
        st.metric("Time Remaining", f"{days_to_deadline} Days", help="Days until your target goal date.")
    else:
        st.error("🏁 DEADLINE REACHED")

    st.divider()
    # ... (Rest of sidebar: Gender, Age, Weight, etc.)
    st.header("👤 Sailor Profile")
    gender = st.radio("Gender", ["Male", "Female"])
    age = st.number_input("Age", value=25)
    height = st.number_input("Height (inches)", value=70.0, step=0.5)
    current_weight = st.number_input("Current Weight (lbs)", value=190)
    
    st.divider()
    st.header("📏 2026 BCA Ratio")
    # The new standard uses umbilicus (bellybutton) measurement
    waist = st.number_input("Waist Circumference (inches)", value=35.0, step=0.5)
    
    # CALCULATE WAIST-TO-HEIGHT RATIO (WHtR)
    whtr = waist / height if height > 0 else 0
    st.metric("Waist-to-Height Ratio", f"{whtr:.2f}")

    # 2026 NAVY STANDARD: WHtR must be < 0.55
    ratio_pass = whtr < 0.55
    
    # Step 1: Weight Table (Still used as initial screening)
    maw = int((height * 4.2) - 105 if gender == "Male" else (height * 3.8) - 110)
    weight_pass = current_weight <= maw

    # FINAL STATUS: You pass if you meet Weight OR Ratio
    is_bca_failing = not weight_pass and not ratio_pass

    st.divider()
    st.header("🎯 Mission Directive")
    
    if is_bca_failing:
        st.error(f"⚠️ BCA FAILURE: Ratio {whtr:.2f} (Limit: 0.55)")
        st.info("🎯 **Goal Locked:** Weight Loss")
        mission_goal = "Weight Loss"
        # Force target to get them back to passing ratio or weight
        target_waist_goal = height * 0.54
        default_target = maw
        upper_limit = maw
    elif not weight_pass and ratio_pass:
        st.success(f"✅ RATIO PASS: {whtr:.2f} (Compliant)")
        mission_goal = st.selectbox("Select Mission Objective", ["Weight Loss", "Maintenance", "Performance Build"])
        default_target = current_weight
        upper_limit = 350
    else:
        st.success(f"✅ TABLE PASS: Under {maw} lbs")
        mission_goal = st.selectbox("Select Mission Objective", ["Weight Loss", "Maintenance", "Performance Build"])
        default_target = min(current_weight - 2, maw)
        upper_limit = 350

    # ENFORCED TARGET WEIGHT
    target_weight = st.number_input(
        "Target Weight (lbs)", 
        min_value=1, 
        max_value=upper_limit, 
        value=int(default_target),
        help="Capped at MAW only if failing current BCA standards."
    )
            
    # BMR & Deficit Logic
    w_kg, h_cm = current_weight * 0.453592, height * 2.54
    bmr = (10 * w_kg) + (6.25 * h_cm) - (5 * age) + (5 if gender == "Male" else -161)
    days_left = (mission_deadline - datetime.date.today()).days
    
    if mission_goal == "Weight Loss":
        req_deficit = ((current_weight - target_weight) * 3500) / max(days_left, 1) if days_left > 0 else 0
    elif mission_goal == "Performance Build":
        req_deficit = -300 
    else:
        req_deficit = 0

    st.divider()
    with st.expander("🛠️ System Maintenance"):
        if st.button("Purge Duplicate Passive Logs"):
            df = load_data()
            if not df.empty:
                others = df[df['type'] != 'Passive']
                passives = df[df['type'] == 'Passive'].drop_duplicates(subset=['date'], keep='first')
                pd.concat([others, passives]).to_csv('fitness_log.csv', index=False)
                st.rerun()

# --- 4. THE ENGINE ---
logs = load_data()
today_date = datetime.date.today()
yesterday_date = today_date - datetime.timedelta(days=1)
yesterday_str = str(yesterday_date)

if "passive_checked" not in st.session_state:
    has_yesterday_passive = not logs[(logs['date'] == yesterday_str) & (logs['type'] == 'Passive')].empty
    if not has_yesterday_passive and not logs.empty:
        save_entry("Passive", "Daily Resting Calories (BMR)", int(bmr), target_date=yesterday_date)
        st.session_state["passive_checked"] = True
        st.rerun()
    st.session_state["passive_checked"] = True

today_logs = logs[logs['date'] == str(today_date)]
burned_exercise = abs(today_logs[today_logs['type'] == 'Exercise']['calories'].sum())
eaten = today_logs[today_logs['type'] == 'Food']['calories'].sum()
now = datetime.datetime.now()
minutes_passed = (now.hour * 60) + now.minute
passive_burn_to_now = (bmr / 1440) * minutes_passed
actual_burn_so_far = passive_burn_to_now + burned_exercise
net_mission_balance = actual_burn_so_far - eaten
total_expected_burn_today = bmr + burned_exercise
remaining_budget = (total_expected_burn_today - req_deficit) - eaten

# SESSION STATE INIT
if 'df_key' not in st.session_state: st.session_state['df_key'] = 0
if 'last_workout' not in st.session_state: st.session_state['last_workout'] = None
if 'meal_desc_fill' not in st.session_state: st.session_state['meal_desc_fill'] = ""
if 'meal_cal_fill' not in st.session_state: st.session_state['meal_cal_fill'] = 0

# --- 5. MAIN DASHBOARD ---
st.title("⚓ Navy PFA Mission Control")

with st.container(border=True):
    col_stats, col_sitrep = st.columns([2, 3])
    
    with col_stats:
        st.subheader("📊 Vital Stats")
        s1, s2 = st.columns(2)
        s1.metric("🕰️ Passive", f"{int(passive_burn_to_now)} kcal")
        s2.metric("🏃 Active", f"{int(burned_exercise)} kcal")
        s3, s4 = st.columns(2)
        s3.metric("🔥 Total", f"{int(actual_burn_so_far)} kcal")
        delta_label = "Deficit (Good)" if net_mission_balance > 0 else "Surplus"
        s4.metric("⚖️ Balance", f"{int(net_mission_balance)}", delta=delta_label)

    with col_sitrep:
        st.subheader("📡 AI Command Sitrep")
        if st.button("Generate Intelligence Brief", use_container_width=True):
            with st.spinner("Analyzing Log..."):
                try:
                    sitrep_p = f"Goal: {target_weight}lbs. Days to BCA: {days_left}. Stats: {int(actual_burn_so_far)} burned vs {int(eaten)} eaten. Budget: {int(remaining_budget)} kcal. Give a 3-bullet Sitrep using Navy jargon."
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=sitrep_p)
                    st.info(res.text)
                except Exception as e:
                    st.error(f"Comm Link Down: {e}")
        else:
            st.info("Awaiting orders. Click above for a tactical assessment.")

st.divider()
total_allowed = total_expected_burn_today - req_deficit
progress_val = min(max(eaten / max(total_allowed, 1), 0.0), 1.0)
st.markdown(f"**Daily Fuel Consumption:** {int(eaten)} / {int(total_allowed)} kcal")
st.progress(progress_val)

# --- 6. TABS ---
tab_prt, tab_ex, tab_meal, tab_hist = st.tabs(["🏆 PRT", "🏃 Exercise", "🍽️ Meals", "📊 History"])

with tab_prt:
    st.header("🏆 PRT Performance Center")
    
    # 1. LIVE STANDARDS ENGINE (2026 Navy Standards Approximation)
    # These thresholds shift based on the Sidebar Age, Gender, and Weight
    if gender == "Male":
        # Run Standards (Seconds)
        run_stnds = {"Outstanding": 578, "Excellent": 652, "Good Low": 773, "Satisfactory": 840}
        # Pushup Standards (Reps)
        push_stnds = {"Outstanding": 77, "Excellent": 67, "Good Low": 44, "Satisfactory": 35}
        # BIKE LOGIC: Weight-dependent calories (Navy formula approximation)
        # Higher weight = Higher calorie requirement
        base_bike = (current_weight * 0.75) + (age * 0.5)
        bike_stnds = {
            "Outstanding": int(base_bike + 55),
            "Excellent": int(base_bike + 35),
            "Good Low": int(base_bike + 12),
            "Satisfactory": int(base_bike)
        }
        # ROW LOGIC (Seconds for 2km)
        row_stnds = {"Outstanding": 420, "Excellent": 460, "Good Low": 510, "Satisfactory": 555}
    else:
        # Female Standards
        run_stnds = {"Outstanding": 700, "Excellent": 780, "Good Low": 930, "Satisfactory": 1020}
        push_stnds = {"Outstanding": 41, "Excellent": 31, "Good Low": 19, "Satisfactory": 12}
        base_bike = (current_weight * 0.65) + (age * 0.4)
        bike_stnds = {
            "Outstanding": int(base_bike + 45),
            "Excellent": int(base_bike + 28),
            "Good Low": int(base_bike + 8),
            "Satisfactory": int(base_bike)
        }
        row_stnds = {"Outstanding": 490, "Excellent": 550, "Good Low": 610, "Satisfactory": 680}

    # Plank is age-neutral for most brackets (Seconds)
    plank_stnds = {"Outstanding": 200, "Excellent": 180, "Good Low": 120, "Satisfactory": 90}

    # 2. INPUT SECTION
    cardio_type = st.selectbox("Select Cardio Modality", ["1.5 Mile Run", "Stationary Bike (Cals)", "2km Row", "500yd Swim"])
    
    col_p1, col_p2, col_p3 = st.columns(3)
    pushups = col_p1.number_input("Pushups (2 min)", min_value=0, value=push_stnds["Good Low"])
    plank_time = col_p2.text_input("Plank (min:sec)", value="2:00")
    
    if cardio_type == "Stationary Bike (Cals)":
        cardio_val = col_p3.number_input("Total Calories", min_value=0, value=bike_stnds["Good Low"])
    else:
        # Defaults for display
        def_time = "08:30" if "Row" in cardio_type else "12:30"
        cardio_val = col_p3.text_input(f"{cardio_type} Time", value=def_time)

    # Time Conversion Helper
    def time_to_sec(t_str):
        if isinstance(t_str, (int, float)): return t_str
        try:
            if ":" in t_str:
                m, s = map(int, t_str.split(':'))
                return (m * 60) + s
            return int(t_str)
        except: return 9999 # Treat errors as failures

    p_sec = time_to_sec(plank_time)
    c_sec = time_to_sec(cardio_val)

    # 3. SCORING LOGIC ENGINE
    def get_grade(val, stnds, reverse=False):
        # reverse=True for time (lower numbers are better grades)
        for grade, threshold in stnds.items():
            if reverse:
                if val <= threshold: return grade
            else:
                if val >= threshold: return grade
        return "Fail"

    # Calculate individual grades
    p_grade = get_grade(pushups, push_stnds)
    pl_grade = get_grade(p_sec, plank_stnds)
    
    if cardio_type == "Stationary Bike (Cals)":
        c_grade = get_grade(cardio_val, bike_stnds)
    elif cardio_type == "2km Row":
        c_grade = get_grade(c_sec, row_stnds, reverse=True)
    else: # Run or Swim
        c_grade = get_grade(c_sec, run_stnds, reverse=True)

    # 4. DETERMINING REMEDIAL STATUS
    # Status is REMEDIAL if any score is 'Satisfactory' or 'Fail' (Below Good Low)
    grades_list = [p_grade, pl_grade, c_grade]
    is_remedial = any(g in ["Fail", "Satisfactory"] for g in grades_list)
    st.session_state["prt_remedial"] = is_remedial

    # 5. DISPLAY RESULTS
    st.divider()
    if not is_remedial:
        st.success(f"### ✅ MISSION READY: {c_grade.upper()}")
    else:
        st.error("### ⚠️ STATUS: REMEDIAL (Below Good Low)")
        st.warning("Exercise and Meal plans are now force-locked to PRT Readiness.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Pushups", p_grade, f"Goal: {push_stnds['Good Low']}")
    c2.metric("Plank", pl_grade, "Goal: 2:00")
    c3.metric(cardio_type.split()[0], c_grade, f"Target: {bike_stnds['Good Low'] if 'Bike' in cardio_type else 'Pass'}")

    # 6. REMEDIAL DATE & AI ACTION
    if is_remedial:
        st.divider()
        mock_date = st.date_input(
            "Target Date for Next Mock PRT:",
            value=datetime.date.today() + datetime.timedelta(days=14)
        )
        days_to_mock = (mock_date - datetime.date.today()).days
        
        if st.button("🚀 Generate Remedial Readiness Plan", use_container_width=True):
            with st.spinner("Prioritizing weak events..."):
                p = f"""
                DEADLINE: {days_to_mock} days.
                GRADES: Pushups {p_grade}, Plank {pl_grade}, {cardio_type} {c_grade}.
                Provide a high-intensity 3-day split to ensure 'Good Low' or higher by the deadline.
                """
                res = client.models.generate_content(model="gemini-2.5-flash", contents=p)
                st.chat_message("coach", avatar="🏃").markdown(res.text)

with tab_ex:
    st.header("🏃 Performance Command")
    
    # 1. READINESS CHECK
    is_remedial = st.session_state.get("prt_remedial", False)
    
    if is_remedial:
        st.warning("🚨 **PRT REMEDIAL MODE: ACTIVE**")
    else:
        st.success(f"✅ **CURRENT MISSION:** {mission_goal}")

    # 2. THE AI STRATEGIC PLANNER
    st.subheader("📋 Strategic Training Plan")
    with st.expander("🗺️ Configure Gear & Generate Briefing", expanded=True):
        
        # --- CLEAN GEAR SELECTION (GRID STYLE) ---
        st.write("### 🛠️ Facility Equipment")
        st.caption("Check all available assets for the AI to utilize in your plan.")

        full_gym_list = [
            "Barbells & Bumper Plates", "Dumbbells", "Kettlebells", 
            "Stairmaster", "Elliptical", "Treadmill (Incline)",
            "Stationary Bike", "Concept2 Rower", "SkiErg",
            "Battling Ropes", "Climbing Ropes", "Medicine Balls", 
            "Slam Balls", "Sandbags", "Sleds/Prowlers",
            "Pull-up Bar", "TRX/Suspension Trainers", "Plyo Boxes", 
            "Swim Pool", "Track/Open Road", "Bodyweight/GRIT"
        ]

        # Container for organized layout
        assets = []
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            for i, item in enumerate(full_gym_list):
                if i % 3 == 0:
                    with col1:
                        if st.checkbox(item, value=True, key=f"ex_check_{item}"):
                            assets.append(item)
                elif i % 3 == 1:
                    with col2:
                        if st.checkbox(item, value=True, key=f"ex_check_{item}"):
                            assets.append(item)
                else:
                    with col3:
                        if st.checkbox(item, value=True, key=f"ex_check_{item}"):
                            assets.append(item)

        # 3. ADD INDIVIDUAL CUSTOM ITEMS
        custom_assets = st.text_input(
            "➕ Add specialized equipment not listed:",
            placeholder="e.g., Weighted Vest, GHD Machine, Assault Bike, Tires",
            help="Type extra gear here, separated by commas."
        )
        
        # Merge lists for the AI
        total_assets = assets + [item.strip() for item in custom_assets.split(",") if item.strip()]
        assets_str = ", ".join(total_assets)
        
        st.write("---")

        # Performance Target
        perf_goal_desc = st.text_area(
            "What is your specific performance target?",
            placeholder="e.g., Increase pushups by 20 and shave 1 minute off my 1.5-mile run.",
            help="The AI uses this to build your phases and fuel your meal plan."
        )

        if st.button("🗺️ Generate Long-Term Training Strategy", use_container_width=True):
            # Calculate days to deadline
            days_to_deadline = (mission_deadline - datetime.date.today()).days
            
            with st.spinner(f"Consulting Tactical Coach for a {days_to_deadline}-day evolution..."):
                try:
                    # UPDATED: Dynamic Focus Prompt (2-Week Dive + Long Term Overview)
                    coach_p = f"""
                    ROLE: Tactical Strength & Conditioning Coach.
                    MISSION: {mission_goal if not is_remedial else 'REMEDIAL PRT RECOVERY'}.
                    TARGET: {perf_goal_desc}.
                    TIMELINE: {days_to_deadline} days remaining.
                    ASSETS: {assets_str}.

                    TASK: Provide a periodized plan with this structure:
                    1. 🛡️ THE 14-DAY DEEP DIVE: Specific daily workouts for the next 2 weeks. 
                       Incorporate equipment like {assets_str[:50]}...
                    2. 📈 THE MONTHLY HORIZON: Weekly focus and frequency for days 15-30.
                    3. 🔭 LONG-TERM STRATEGY: High-level overview of training phases until the deadline.
                    
                    TONE: Professional and motivating.
                    """
                    
                    res = client.models.generate_content(model=MODEL_ID, contents=coach_p)
                    st.chat_message("coach", avatar="🏃").markdown(res.text)

                    # --- BRIDGE TO MEAL TAB ---
                    st.session_state["current_perf_strategy"] = perf_goal_desc
                    
                except Exception as e:
                    st.error(f"Comm Link lost: {e}")

    st.divider()

    # 4. DAILY ACTIVITY LOGGING
    st.subheader("📝 Daily Log")
    workout_desc = st.text_area("Describe today's training:", placeholder="e.g., 20 mins Stairmaster, then 5 rounds of Kettlebell swings.")
    
    if st.button("Analyze and Log Workout", use_container_width=True):
        if workout_desc:
            with st.spinner("Analyzing performance..."):
                try:
                    p = f"Weight: {current_weight}lbs. Workout: {workout_desc}. Calculate kcal burn. Return integer only."
                    res = client.models.generate_content(model=MODEL_ID, contents=p)
                    import re
                    val = int(re.search(r'\d+', res.text).group())
                    save_entry("Exercise", workout_desc, val)
                    st.success(f"Logged: {val} kcal burned.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Logging failed: {e}")

with tab_meal:
    st.header("🍽️ Performance Fueling")

    # 1. INITIALIZE CACHE & RETRIEVE CONTEXT
    perf_goal = st.session_state.get("current_perf_strategy", "General Health & Maintenance")
    if "cached_shopping_list" not in st.session_state:
        st.session_state["cached_shopping_list"] = None

    # 2. STRATEGIC SOURCING PROFILE
    with st.container(border=True):
        st.write("### 📍 Logistics & Sourcing")
        
        # Manual Zip Code Input - Privacy First
        zip_code = st.text_input(
            "Enter Zip Code:", 
            placeholder="e.g., 32212",
            max_chars=5,
            help="The AI uses your zip code to identify the closest Costco, Commissary, or local grocery chains."
        )
        
        shop_prefs = st.multiselect(
            "Preferred Retailers:",
            options=["Commissary", "Costco", "Sam's Club", "Walmart", "Target", "Publix/Safeway", "Aldi"],
            default=["Commissary", "Costco"]
        )

        pantry_items = st.text_area(
            "🥫 Pantry Inventory (What's already in the locker?)",
            placeholder="e.g., White rice, Olive oil, Salt/Pepper, Whey Protein"
        )

    st.write("---")

    # 3. THE "I'M GOING SHOPPING" ENGINE
    if st.button("🛒 I'm Going Shopping (14-Day Tactical Plan)", use_container_width=True, type="primary"):
        if not zip_code or len(zip_code) < 5:
            st.error("⚠️ Please enter a valid 5-digit Zip Code to optimize your route.")
        else:
            with st.spinner(f"Scouting provisioning options near {zip_code}..."):
                try:
                    shopping_p = f"""
                    ROLE: Tactical Logistics & Sports Dietitian.
                    LOCATION: Zip Code {zip_code}.
                    TARGET RETAILERS: {', '.join(shop_prefs)}.
                    TIMELINE: 14-Day Evolution.
                    PERFORMANCE GOAL: {perf_goal}.
                    EXISTING PANTRY: {pantry_items if pantry_items else 'None listed'}.

                    TASK:
                    1. LOCALIZE: Based on zip {zip_code}, identify which of the {', '.join(shop_prefs)} are likely available.
                    2. STRATEGIZE: Provide a 14-day meal plan overview that matches the performance goal of {perf_goal}.
                    3. SOURCE: Create a 14-day shopping list. 
                       - Group items by store (e.g., 'Bulk items to get at Costco', 'Fresh items at the Commissary').
                       - Do NOT include items already in the pantry.
                    
                    FORMAT: Use [ ] checkboxes and bold category headers.
                    """
                    res = client.models.generate_content(model=MODEL_ID, contents=shopping_p)
                    st.session_state["cached_shopping_list"] = res.text
                except Exception as e:
                    st.error(f"Logistics Link lost: {e}")

    # 4. DISPLAY SHOPPING LIST & LOGGING
    if st.session_state["cached_shopping_list"]:
        with st.expander("📦 View My 14-Day Tactical Shopping Plan", expanded=True):
            st.markdown(st.session_state["cached_shopping_list"])
            st.download_button("📲 Save to Phone", st.session_state["cached_shopping_list"], file_name=f"Shopping_List_{zip_code}.txt", use_container_width=True)

    st.divider()
    
    # 5. RESTORED NUTRITION LOG (Ensuring it stays at the bottom)
    st.subheader("📝 Daily Nutrition Log")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        meal_desc = st.text_input("What did you eat?", placeholder="e.g., 2 Chicken Tacos, Black beans")
    with col_b:
        manual_cal = st.number_input("Calories (0 = AI Guess)", min_value=0)

    if st.button("Log Meal Entry", use_container_width=True):
        if meal_desc:
            try:
                p = f"Estimate calories for: {meal_desc}. Return integer only."
                res = client.models.generate_content(model=MODEL_ID, contents=p)
                import re
                match = re.search(r'\d+', res.text)
                val = int(match.group()) if match else 0
                save_entry("Food", meal_desc, val)
                st.success(f"Logged {val} kcal.")
                st.rerun()
            except Exception as e:
                st.error(f"Log failed: {e}")
with tab_hist:
    st.header("History")
    if not logs.empty:
        logs_display = logs.sort_values(by='date', ascending=False)
        selection = st.dataframe(logs_display, use_container_width=True, on_select="rerun", selection_mode="multi-row", key=f"hist_{st.session_state['df_key']}")
        rows = selection.get("selection", {}).get("rows", [])
        if rows:
            selected_indices = [logs_display.index[i] for i in rows]
            if st.button("🗑️ Delete Selected"): confirm_delete_dialog(selected_indices)
    else: st.info("No logs.")