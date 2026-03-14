import streamlit as st
import pandas as pd
import datetime
import os
import re
import json
from streamlit_autorefresh import st_autorefresh 
from rapidfuzz import process, utils

# Refresh the app every 30 seconds to update the "Live" tally
st_autorefresh(interval=30000, key="daterefresh")

# --- THE MASTER SYNC LOGIC ---
def sync_mission_deadline():
    # This force-updates the master variable
    st.session_state.mission_deadline = st.session_state.master_date_input
    # No st.rerun() here, it's handled by the widget's nature

# Initialize the state if it doesn't exist
if "mission_deadline" not in st.session_state:
    st.session_state.mission_deadline = datetime.date.today()

# --- 1. CONSTANTS (Add these for the Exercise Tab) ---
standard_facilities = [
    "Treadmill", "Elliptical", "Rowing Machine", "Stationary Bike",
    "Free Weights", "Squat Rack", "Cable Machine", "Pull-up Bar", 
    "Dip Station", "Kettlebells", "Medicine Balls", "Resistance Bands", 
    "Jump Rope", "Box", "Swimming Pool", "Track", "Sandbags", "TRX"
]

# --- 2. GLOBAL STATE INITIALIZATION ---
if "bmr" not in st.session_state:
    # 1. Physical Specs (Default values)
    st.session_state["gender"] = "Male"
    st.session_state["age"] = 25
    st.session_state["height_in"] = 70.0    # Set to your height in inches
    st.session_state["weight_lbs"] = 190.0 # Set to your weight in lbs
    st.session_state["setup_complete"] = False
    st.session_state["mission_lockdown"] = False

    # 2. Conversion & Calculation
    w_kg = st.session_state["weight_lbs"] * 0.453592
    h_cm = st.session_state["height_in"] * 2.54
    a = st.session_state["age"]

    # 3. Setting the REAL BMR (No more 2000 default!)
    if st.session_state["gender"] == "Male":
        st.session_state["bmr"] = (10 * w_kg) + (6.25 * h_cm) - (5 * a) + 5
    else:
        st.session_state["bmr"] = (10 * w_kg) + (6.25 * h_cm) - (5 * a) - 161

if "req_deficit" not in st.session_state:
    st.session_state["req_deficit"] = 500.0
if "burned_exercise" not in st.session_state:
    st.session_state["burned_exercise"] = 0.0
if "eaten" not in st.session_state:
    st.session_state["eaten"] = 0.0

# Add Gym Profiles to prevent the Equipment error
if "gym_profiles" not in st.session_state:
    st.session_state["gym_profiles"] = {
        "Standard Gym": ["Free Weights", "Treadmill", "Pull-up Bar"]
    }

# --- 3. MAP TO LOCAL VARIABLES ---
# This ensures lines like 219 (bmr + exercise) work on every rerun
bmr = st.session_state["bmr"]
req_deficit = st.session_state["req_deficit"]
burned_exercise = st.session_state["burned_exercise"]
eaten = st.session_state["eaten"]

# --- THE LIVE HUD MATH ---
# 1. Get the current time and calculate how much of the day has passed
now = datetime.datetime.now()
seconds_since_midnight = (now.hour * 3600) + (now.minute * 60) + now.second
percent_of_day = seconds_since_midnight / 86400

# 2. Calculate the "Passive Burn" based on the current time
# (e.g., if it's noon, you've burned 50% of your BMR)
live_bmr = int(bmr * percent_of_day)

# 3. Sum up today's "Active" entries from your history
active_today = 0
if "history" in st.session_state:
    today_date = datetime.date.today()
    active_today = sum(e["Value"] for e in st.session_state.history 
                       if e["Date"] == today_date and e["Category"] == "Active")

# 4. Final Live Total
total_live_burn = live_bmr + active_today

# --- GLOBAL CONFIGURATION ---
MODEL_ID = "gemini-2.5-flash"
DB_FILE = "gym_locker.json" 

# --- PERSISTENCE LOGIC ---
def save_gyms(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_gyms():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

STRATEGY_FILE = "mission_strategy.json"

def save_strategy(strategy_text, target_desc, start_date):
    data = {
        "plan": strategy_text,
        "target": target_desc,
        "generated_on": str(start_date)
    }
    with open(STRATEGY_FILE, "w") as f:
        json.dump(data, f)

def load_strategy():
    if os.path.exists(STRATEGY_FILE):
        try:
            with open(STRATEGY_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

# --- INITIALIZE STRATEGY IN SESSION STATE ---
# Add this right after your gym_profiles initialization
if "long_term_plan" not in st.session_state:
    saved_strat = load_strategy()
    if saved_strat:
        st.session_state["long_term_plan"] = saved_strat["plan"]
        st.session_state["perf_target"] = saved_strat["target"]
        st.session_state["strategy_generated_on"] = datetime.datetime.strptime(saved_strat["generated_on"], '%Y-%m-%d').date()

if "account_created" not in st.session_state:
    # Defaults to 30 days ago if new, or you can set a specific date
    st.session_state.account_created = datetime.date.today() - datetime.timedelta(days=30)

# --- INITIAL SETUP ---
st.set_page_config(page_title="Navy PFA Pro", layout="wide", page_icon="⚓")

# Initialize Gemini Client
try:
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("🔑 Configuration Error: Check your API Key in Streamlit Secrets.")
    st.stop()

# Initialize/Load Gym Profiles
if "gym_profiles" not in st.session_state:
    saved_data = load_gyms()
    if saved_data:
        st.session_state["gym_profiles"] = saved_data
    else:
        st.session_state["gym_profiles"] = {
            "🏠 Home Gym": ["Bodyweight/GRIT", "Dumbbells", "Pull-up Bar"],
            "⚓ Ship Gym (Afloat)": ["Bodyweight/GRIT", "Kettlebells", "Pull-up Bar"],
            "🏋️ Base Gym (Main)": ["Barbells & Bumper Plates", "Concept2 Rower", "Stairmaster"]
        }

# --- DATA FUNCTIONS ---

# --- 2. DATA FUNCTIONS ---
def get_navy_tier(score):
    """Maps 0-100 score to official Navy Tiers."""
    if score >= 90:
        if score >= 95: return "Outstanding (High)", "#00E5FF"
        if score >= 92: return "Outstanding (Medium)", "#00B8D4"
        return "Outstanding (Low)", "#0097A7"
    elif score >= 75:
        if score >= 85: return "Excellent (High)", "#00C853"
        if score >= 80: return "Excellent (Medium)", "#2E7D32"
        return "Excellent (Low)", "#388E3C"
    elif score >= 60:
        if score >= 70: return "Good (High)", "#FFAB00"
        if score >= 65: return "Good (Medium)", "#FF8F00"
        return "Good (Low)", "#EF6C00"
    elif score >= 45:
        return "Satisfactory", "#D32F2F"
    else:
        return "Probationary/Fail", "#757575"

def calculate_score(val, event_type, age, gender):
    """Calculates point values for PRT events."""
    if event_type == "Pushups":
        ref = 60 if gender == "Male" else 35
        return min(100, int((val / ref) * 80))
    elif event_type == "Plank":
        return min(100, int((val / 180) * 90))
    elif event_type == "1.5 Mile Run":
        ref_time = 630 if gender == "Male" else 750
        return min(100, int((ref_time / val) * 95))
    elif event_type == "Stationary Bike":
        ref_cals = 200 if gender == "Male" else 160
        return min(100, int((val / ref_cals) * 90))
    else:
        return 75

def update_global_deadline():
    # Safety check: Only update if the key exists in session state
    if "master_date_input" in st.session_state:
        st.session_state.mission_deadline = st.session_state.master_date_input
def load_data():
    if os.path.exists('fitness_log.csv'):
        try:
            df = pd.read_csv('fitness_log.csv')
            df['date'] = df['date'].astype(str)
            return df
        except:
            return pd.DataFrame(columns=['date', 'type', 'description', 'calories'])
    return pd.DataFrame(columns=['date', 'type', 'description', 'calories'])

def save_entry(category, activity, value, date_obj=None):
    """The ONE function to rule them all. Handles HUD, CSV, and Burn logic."""
    # 1. Default to today if no date is provided
    if date_obj is None:
        date_obj = datetime.date.today()
    
    # 2. Type Enforcement & Safety Clamping
    try:
        clean_value = float(value)
    except (ValueError, TypeError):
        return st.error(f"Invalid numeric value: {value}")
    
    safe_value = max(0.0, min(clean_value, 5000.0))
    
    # 3. Handle 'Burn' math (CSV needs negative numbers for Exercise/Passive)
    # This keeps your old spreadsheet math consistent!
    csv_value = -abs(safe_value) if category in ["Exercise", "Passive", "Active"] else abs(safe_value)

    # 4. Save to Session State (for the Live HUD)
    if "history" not in st.session_state:
        st.session_state.history = []
    
    st.session_state.history.append({
        "Date": date_obj,
        "Category": category,
        "Activity": str(activity),
        "Value": safe_value # HUD likes positive numbers
    })

    # 5. Save to CSV (The 'Permanent' log)
    file_exists = os.path.exists('fitness_log.csv')
    new_row = pd.DataFrame([[str(date_obj), category, activity, csv_value]], 
                            columns=['date', 'type', 'description', 'calories'])
    new_row.to_csv('fitness_log.csv', mode='a', header=not file_exists, index=False)

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

def global_safeguard():
    """Hard-limits all session data to humanly possible ranges."""
    # 1. Physical Limits
    if "age" in st.session_state:
        st.session_state.age = int(max(17, min(st.session_state.age, 65)))
    if "height" in st.session_state:
        st.session_state.height = float(max(48, min(st.session_state.height, 96)))
    if "current_weight" in st.session_state:
        st.session_state.current_weight = int(max(90, min(st.session_state.current_weight, 500)))

    # 2. History Integrity
    if "history" in st.session_state:
        # Prevent memory bloat (keep last 200 entries)
        if len(st.session_state.history) > 200:
            st.session_state.history = st.session_state.history[-200:]
        
        # Remove corrupted entries (None values or extreme numbers)
        st.session_state.history = [
            e for e in st.session_state.history 
            if isinstance(e.get("Value"), (int, float)) and 0 <= e["Value"] <= 5000
        ]

# Execute immediately
global_safeguard()

@st.dialog("Confirm Deletion")
def confirm_delete_dialog(indices):
    st.warning(f"⚠️ This will permanently delete {len(indices)} entries. Proceed?")
    if st.button("🔥 Confirm Bulk Purge", type="primary", use_container_width=True):
        df = load_data()
        df = df.drop(indices)
        df.to_csv('fitness_log.csv', index=False)
        st.session_state['df_key'] += 1 
        st.rerun()

# --- SIDEBAR: MISSION COMMAND & MAINTENANCE ---
with st.sidebar:
    st.header("🚢 Mission Control")
    
    # READ-ONLY DISPLAY
    deadline = st.session_state.get("mission_deadline", datetime.date.today())
    days_to_go = (deadline - datetime.date.today()).days
    
    st.metric(label="Mission Deadline", value=deadline.strftime("%d %b %Y"))
    st.caption(f"🏁 {days_to_go} Days Remaining")
    st.divider()    
    st.divider()

    # 2. DAILY BRIEFING
    st.subheader("📋 Today's Brief")
    
    if "today_workout_type" in st.session_state:
        st.info(f"**Training:** {st.session_state['today_workout_type']}")
    else:
        st.caption("No workout generated for today.")

    if "today_meal_plan" in st.session_state:
        st.success(f"**Nutrition Plan Active**")
    else:
        st.caption("No meal plan generated for today.")

    st.caption(f"Target: {st.session_state.get('perf_target', 'Not Set')}")

    # PUSH TO BOTTOM
    st.write("<br>" * 10, unsafe_allow_html=True) 
    st.divider()
    
    # 3. SYSTEM MAINTENANCE (With Confirmation Logic)
    with st.expander("🛠️ System Maintenance"):
        st.write("Manage Local Data Files")
        
        # Reset Mission Strategy with Safety Confirmation
        st.markdown("---")
        confirm_reset = st.checkbox("Confirm Strategy Reset")
        if st.button("Reset Mission Strategy", use_container_width=True, disabled=not confirm_reset):
            if os.path.exists("mission_strategy.json"):
                os.remove("mission_strategy.json")
                # Clear session state
                keys_to_clear = ["long_term_plan", "perf_target", "strategy_generated_on"]
                for key in keys_to_clear:
                    st.session_state.pop(key, None)
                st.success("Strategy Deleted.")
                st.rerun()
        
        st.markdown("---")
        if st.button("Clear Gym Locker", use_container_width=True):
            if os.path.exists("gym_locker.json"):
                os.remove("gym_locker.json")
                st.rerun()
        
        if st.button("Purge All Logs", type="primary", use_container_width=True):
            if os.path.exists("gym_data.csv"):
                os.remove("gym_data.csv")
                st.rerun()

# --- 4-COLUMN TACTICAL HUD ---
st.subheader("⚓ Real-Time Mission Energy Status")

# Create 4 columns for the full breakdown
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🧘 Passive Burn", 
        value=f"{live_bmr} kcal", 
        help="Estimated calories burned by your body so far today (BMR)."
    )

with col2:
    st.metric(
        label="🏃 Active Burn", 
        value=f"{active_today} kcal", 
        help="Sum of all exercise/active entries logged today."
    )

with col3:
    st.metric(
        label="🍽️ Consumption", 
        value=f"{int(eaten)} kcal", 
        help="Total calories consumed today."
    )

with col4:
    # Calculation: What you've eaten vs. what you've burned (Passive + Active)
    # Negative = Deficit (Weight Loss), Positive = Surplus (Weight Gain)
    current_balance = eaten - (live_bmr + active_today)
    
    # Logic to change the label based on the state
    status_label = "📈 Surplus" if current_balance > 0 else "📉 Deficit"
    
    st.metric(
        label=status_label, 
        value=f"{int(abs(current_balance))} kcal",
        delta=f"{int(current_balance)} vs Burn",
        delta_color="inverse" # Red for surplus, Green for deficit
    )

st.divider()

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
passive_burn_to_now = (st.session_state["bmr"] / 1440) * minutes_passed
actual_burn_so_far = passive_burn_to_now + burned_exercise
net_mission_balance = actual_burn_so_far - eaten
total_expected_burn_today = st.session_state.get("bmr", 2000.0) + burned_exercise
remaining_budget = (total_expected_burn_today - req_deficit) - eaten

# SESSION STATE INIT
if 'df_key' not in st.session_state: st.session_state['df_key'] = 0
if 'last_workout' not in st.session_state: st.session_state['last_workout'] = None
if 'meal_desc_fill' not in st.session_state: st.session_state['meal_desc_fill'] = ""
if 'meal_cal_fill' not in st.session_state: st.session_state['meal_cal_fill'] = 0

# --- 6. TABS ---
tab_prt, tab_perf, tab_nut, tab_analysis = st.tabs(["🏆 PRT", "🏃 Performance", "🍽️ Nutrition", "📊 Analysis"])

with tab_prt:
    st.header("📋 Profile & Performance Assessment")
    
    # --- 1. PHYSICAL PROFILE ---
    with st.container(border=True):
        st.subheader("👤 Sailor Physical Profile")
        col1, col2 = st.columns(2)
        with col1:
            gender = st.radio("Gender", ["Male", "Female"], horizontal=True, 
                             index=0 if st.session_state.get("gender") == "Male" else 1)
            age = st.number_input("Age", value=int(st.session_state.get("age", 25)), min_value=17, max_value=65)
        
        with col2: # Line 415
            # These lines MUST be indented relative to the 'with' above
            height = st.number_input("Height (inches)", value=float(st.session_state.get("height", 70.0)), min_value=48.0, max_value=96.0, step=0.1) # Line 417
            current_weight = st.number_input("Current Weight (lbs)", value=int(st.session_state.get("current_weight", 190)), min_value=80, max_value=500)

    # --- 2. BCA GATEKEEPER ---
    maw_limit = (height * 4.2) - 105 if gender == "Male" else (height * 3.8) - 110
    over_weight = current_weight > maw_limit
    bca_fail = False

    if over_weight:
        st.warning(f"⚠️ Weight exceeds standard ({int(maw_limit)} lbs). BCA Tape required.")
        waist = st.number_input("Measured Waist (inches):", value=float(st.session_state.get("waist", 35.0)), min_value=20.0, max_value=height, step=0.1)
        whtr = waist / height
        bca_fail = whtr >= 0.55
        if bca_fail:
            st.error(f"❌ BCA FAILURE: WtHR is {whtr:.2f}")
        else:
            st.info(f"✅ BCA PASS: WtHR is {whtr:.2f}")
    else:
        st.success(f"✅ Weight within Navy standards.")

    # --- 3. PERFORMANCE SCORECARD (CLEAN MANUAL ENTRY) ---
    st.divider()
    st.subheader("🏅 PRT Scorecard")
    sc1, sc2, sc3 = st.columns(3)

    with sc1:
        st.markdown("**Upper Body**")
        pushups = st.number_input("Pushups", value=45, min_value=0, max_value=250, step=1)
        st.caption("Max reps in 2 mins")

    with sc2:
        st.markdown("**Core Stability**")
        plank_input = st.number_input("Plank (M.SS)", value=2.00, min_value=0.0, max_value=10.0, help="Example: 3.20 is 3m 20s")
        p_min = int(plank_input)
        p_sec = round((plank_input - p_min) * 100)
        plank_total_sec = (p_min * 60) + p_sec
        st.caption(f"Total: {p_min}m {p_sec}s")

    with sc3:
        st.markdown("**Cardio Event**")
        cardio_method = st.selectbox("Event Type", ["1.5 Mile Run", "Stationary Bike", "2000m Row"])
        
        # Initialize performance_val immediately
        performance_val = 0 
        c_sec = 0

        if cardio_method == "Stationary Bike":
            # Guardrails: Min 40 cals (low effort) to Max 1000 cals (Elite level 12-min burn)
            performance_val = st.number_input("Calories", value=150, min_value=40, max_value=1000, step=1)
            st.caption("Total calories burned")
            
        elif cardio_method == "2000m Row":
            # Guardrails: Min 5.00 (World Class) to Max 20.00 (Failing pace)
            cardio_input = st.number_input("Time (M.SS)", value=8.30, min_value=5.00, max_value=20.00, step=0.01)
            c_min = int(cardio_input)
            c_sec = round((cardio_input - c_min) * 100)
            performance_val = (c_min * 60) + c_sec
            st.caption(f"Total: {c_min}m {c_sec}s")
            
        else: # 1.5 Mile Run
            # Guardrails: Min 6.00 (Elite) to Max 25.00 (Walking pace)
            cardio_input = st.number_input("Time (M.SS)", value=12.30, min_value=6.00, max_value=25.00, step=0.01)
            c_min = int(cardio_input)
            c_sec = round((cardio_input - c_min) * 100)
            performance_val = (c_min * 60) + c_sec
            st.caption(f"Total: {c_min}m {c_sec}s")

    # --- 4. CALCULATION & TIER DISPLAY ---
    if p_sec < 60 and (cardio_method == "Stationary Bike" or c_sec < 60):
        s_push = calculate_score(pushups, "Pushups", age, gender)
        s_plank = calculate_score(plank_total_sec, "Plank", age, gender)
        s_cardio = calculate_score(performance_val, cardio_method, age, gender)
        
        overall_score = int((s_push + s_plank + s_cardio) / 3)
        overall_tier, overall_color = get_navy_tier(overall_score)

        st.divider()
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Pushups", f"{s_push} pts")
        res_col2.metric("Plank", f"{s_plank} pts")
        res_col3.metric("Cardio", f"{s_cardio} pts")

        # The big visual label
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.05); padding:20px; border-radius:10px; border-top: 5px solid {overall_color}; text-align:center;">
            <h2 style="margin:0; color:{overall_color};">{overall_tier}</h2>
            <p style="margin:0; font-size:1.1em; opacity:0.8;">Composite Readiness Score: <strong>{overall_score}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        # --- 5. LOCKDOWN VERIFICATION ---
        # Logic: If BCA fails OR any score is less than 60 (Satisfactory/Fail), Lockdown is True
        is_failing_or_sat = s_push < 60 or s_plank < 60 or s_cardio < 60
        
        if bca_fail:
            st.error("🚨 MISSION LOCKDOWN: BCA Failure.")
        elif is_failing_or_sat:
            st.warning("⚠️ MISSION LOCKDOWN: Performance below 'Good' standard. Recovery Mode Active.")

        # --- 6. SYNC BUTTON ---
        if st.button("⚖️ Update Mission Profile", type="primary", use_container_width=True):
            # Apply the lockdown state
            st.session_state["mission_lockdown"] = bca_fail or is_failing_or_sat
            
            # Update BMR for the top HUD
            w_kg, h_cm = current_weight * 0.453592, height * 2.54
            st.session_state["bmr"] = (10 * w_kg) + (6.25 * h_cm) - (5 * age) + (5 if gender == "Male" else -161)
            st.success("✅ Profile Updated. Readiness Synced.")
    else:
        st.error("🚨 Invalid Time Format: Seconds must be .00 to .59")


with tab_perf:
    st.header("⚡ Performance Command")

    # --- SECTION 1: STRATEGIC ROLLING PLAN ---
    with st.container(border=True): # Line 537
        st.subheader("🎯 Strategic Training Plan") # Line 538 (Indented!)
        
        col_g1, col_g2 = st.columns([2, 1])
        # Make sure EVERYTHING inside this block is indented the same amount
        st.session_state.user_goal = col_g1.text_area(
            "Primary Training Goal", 
            value=st.session_state.get("user_goal", "PFA Excellence"),
            help="Describe your mission, specific weaknesses, and desired outcomes in detail."
        )
        
        # MASTER DATE INPUT: Keeping the temporal guardrail
        st.date_input(
            "Mission Deadline", 
            value=st.session_state.get("mission_deadline", datetime.date.today()),
            min_value=datetime.date.today(), # Mission cannot be in the past
            key="master_date_input",
            on_change=update_global_deadline 
        )
        
        # Local variable for the countdown logic
        mission_deadline = st.session_state.get("mission_deadline", datetime.date.today())
        days_rem = (mission_deadline - datetime.date.today()).days
        
        st.caption(f"📅 Sidebar Deadline updated to: **{mission_deadline.strftime('%d %b %Y')}**")
        if days_rem >= 0:
            st.info(f"⏳ **{days_rem} Days** until mission execution.")
        else:
            st.warning("⚠️ **Mission Deadline passed.** Update above to recalibrate.")

        # --- PRECISION READINESS LOCK ---
        current_tier = st.session_state.get("current_tier", "Good Low") 
        bca_pass = st.session_state.get("bca_pass", True)
        
        lock_tiers = ["Satisfactory High", "Satisfactory Low", "Satisfactory", "Failure"]
        lockdown = (current_tier in lock_tiers) or (not bca_pass)
        st.session_state.mission_lockdown = lockdown

        if lockdown:
            st.error(f"🚨 MISSION LOCKDOWN: {current_tier if bca_pass else 'BCA FAILURE'}.")
        else:
            st.success(f"✅ READINESS SECURED: Tier '{current_tier}' meets mission standards.")

        if st.button("🗺️ Generate Master Strategic Plan", use_container_width=True):
            with st.spinner("Calculating Rolling Horizon Plan..."):
                plan_p = f"""
                ROLE: Navy Master Fitness Coordinator.
                GOAL: {st.session_state.user_goal}. DEADLINE: {days_rem} days.
                STATUS: {'LOCKDOWN' if lockdown else 'Optimal'}.
                TASK: Provide 14 days of detailed daily focus/RPE, then a high-level overview for the remaining {max(0, days_rem-14)} days.
                """
                plan_res = client.models.generate_content(model=MODEL_ID, contents=plan_p)
                st.session_state["master_plan"] = plan_res.text
        
        if "master_plan" in st.session_state:
            with st.expander("📖 View Rolling Strategic Plan", expanded=True):
                st.markdown(st.session_state["master_plan"])

    # --- SECTION 2: DEPLOYMENT ENVIRONMENT (GYM & GEAR) ---
    with st.container(border=True):
        st.subheader("🏫 Deployment Environment")
        
        standard_gear = [
            "Bodyweight", "Standard Rack", "1.5-Mile Track", "Dumbbells", "Kettlebells", 
            "Pull-up Bar", "TRX", "Sandbags", "Rowing Machine", "Air Bike", 
            "Barbell & Plates", "Medicine Balls", "Jump Rope", "Bench", "Resistance Bands"
        ]

        if "gym_profiles" not in st.session_state:
            st.session_state.gym_profiles = {"Standard Locker": ["Bodyweight", "Standard Rack", "1.5-Mile Track"]}
        
        gym_list = list(st.session_state.gym_profiles.keys())
        if "active_gym" not in st.session_state or st.session_state.active_gym not in gym_list:
             st.session_state.active_gym = gym_list[0]
             
        active_gym = st.selectbox("Active Location", gym_list, index=gym_list.index(st.session_state.active_gym))
        st.session_state.active_gym = active_gym

        with st.expander("🛠️ Modify Gym / Gear Locker"):
            new_name = st.text_input("New Profile Name")
            if st.button("➕ Create Profile") and new_name:
                st.session_state.gym_profiles[new_name] = ["Bodyweight"]
                st.session_state.active_gym = new_name
                st.rerun()
            
            st.divider()
            add_item = st.selectbox("Add Standard Gear:", ["Select..."] + standard_gear)
            if st.button("📥 Add Standard") and add_item != "Select...":
                if add_item not in st.session_state.gym_profiles[active_gym]:
                    st.session_state.gym_profiles[active_gym].append(add_item)
                    st.rerun()

            st.session_state.gym_profiles[active_gym] = st.multiselect(
                "Verify Locker Contents:", options=st.session_state.gym_profiles[active_gym],
                default=st.session_state.gym_profiles[active_gym]
            )

    # --- SECTION 3: EVOLUTION ENGINE (DAILY WORKOUT) ---
    with st.container(border=True):
        st.subheader("🔥 Daily Evolution")
        evo_choice = st.radio("Daily Protocol:", ["Follow Strategic Plan", "Call an Audible"], horizontal=True)
        
        if st.button("🚀 Generate Daily Workout", type="primary", use_container_width=True):
            with st.spinner("Syncing Environment..."):
                gear_str = ", ".join(st.session_state.gym_profiles[active_gym])
                master_context = st.session_state.get("master_plan", "General Readiness")
                
                perf_p = f"Navy Tactical Coach. MISSION IN: {days_rem} days. GEAR: {gear_str}. CHOICE: {evo_choice}. STATUS: {'LOCKDOWN' if lockdown else 'Normal'}. TASK: Generate 1 workout."
                res = client.models.generate_content(model=MODEL_ID, contents=perf_p)
                st.session_state["daily_evo"] = res.text
                st.rerun()

        if "daily_evo" in st.session_state:
            st.markdown(st.session_state["daily_evo"])

   # --- SECTION 4: POST-WORKOUT ANALYSIS & LOGGING ---
    with st.container(border=True):
        st.subheader("📊 Performance Analysis")
        method = st.radio("Analysis:", ["AI Estimate", "Manual Tracker"], horizontal=True)
        
        if method == "AI Estimate":
            workout_desc = st.text_area("Describe the session (movements/intensity):")
            # Added date picker for AI estimates
            ai_date = st.date_input("Workout Date", value=datetime.date.today(), 
                             max_value=datetime.date.today(), key="ai_d")
            
            if st.button("🧮 Analyze"):
                # Ensure MODEL_ID and client are properly configured at the top
                analysis_res = client.models.generate_content(model=MODEL_ID, contents=f"Estimate burn for: {workout_desc}.")
                st.info(analysis_res.text)
                st.caption(f"Suggested for: {ai_date}")

        else:
            col_l1, col_l2, col_l3 = st.columns([1, 2, 1.5])
            kcal = col_l1.number_input("Kcal Burned", min_value=0, max_value=5000, step=50)
            manual_desc = col_l2.text_input("Workout Title", placeholder="e.g., 5k Run", max_chars=100)
            
            # This is the single, clean version of the date input
            manual_date = col_l3.date_input(
                "Date", 
                value=datetime.date.today(),
                min_value=datetime.date(2025, 1, 1),
                max_value=datetime.date.today(),
                key="ex_manual_d"
            )
            
            if st.button("📝 Log Work", use_container_width=True):
                if manual_desc and kcal > 0:
                    # Assuming save_entry accepts: category, activity, value, date
                    save_entry("Exercise", manual_desc, kcal, manual_date)
                    st.success(f"Logged: {manual_desc} for {manual_date}")
                    st.rerun()
                else:
                    st.error("Please provide a title and calorie amount.")

with tab_nut:
    st.header("🍽️ Nutritional Command & Logistics")

    # --- 1. PERFORMANCE & GOAL SYNC ---
    # Pulling live data from other tabs for alignment
    current_goal = st.session_state.get("user_goal", "Standard Performance")
    workout_today = st.session_state.get("daily_workout", "Rest Day")
    lockdown = st.session_state.get("mission_lockdown", False)

    # --- 2. PANTRY & GYM LOCKER INVENTORY ---
    with st.expander("📦 Gym Locker & Pantry Inventory", expanded=False):
        pantry_df = load_pantry()
        
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
        new_item = col_p1.text_input("Add Item", placeholder="e.g., Tuna, Rice", key="p_in")
        new_qty = col_p2.number_input("Qty", min_value=0, value=1, key="p_qty")
        if col_p3.button("📥 Update Stock", use_container_width=True):
            update_pantry(new_item, new_qty, action="add")
            st.rerun()

        if not pantry_df.empty:
            st.dataframe(pantry_df, use_container_width=True, hide_index=True)
            if st.button("🗑️ Purge Empty Stock"):
                pantry_df = pantry_df[pantry_df['quantity'] > 0]
                pantry_df.to_csv('pantry.csv', index=False)
                st.rerun()
        else:
            st.info("Pantry is empty. Secure supplies to optimize procurement.")

    st.divider()

    # --- 3. TACTICAL SETTINGS ---
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        dining_env = st.radio("Environment:", ["⚓ Mess Decks", "🏠 Shore / Home"], horizontal=True)
        meal_freq = st.select_slider(
            "Meal Frequency:", 
            options=["1 Meal", "2 Meals", "3 Meals", "4 Meals"], 
            value="3 Meals"
        )
        duration = st.selectbox("Plan Duration:", ["Daily Brief", "14-Day Evolution"])

    with col_n2:
        zip_code = st.text_input("📍 Zip Code", placeholder="23511", max_chars=5)
        preferred_stores = st.multiselect(
            "Target Stores:",
            ["NEX / Commissary", "Costco", "Sam's Club", "Walmart", "Aldi"],
            default=["NEX / Commissary"]
        )

    # --- 4. MISSION EXECUTION (Generation & Restock) ---
    c_gen, c_restock, c_out = st.columns(3)
    
    # ACTION A: Generate the Sync'd Meal Plan
    if c_gen.button("🍴 Generate Plan", use_container_width=True, type="primary"):
        with st.spinner("Syncing with Performance Tab..."):
            stores_str = ", ".join(preferred_stores)
            nut_p = f"""
            ROLE: Navy Tactical Dietitian.
            GOAL: {current_goal}. TODAY'S WORKOUT: {workout_today}.
            DURATION: {duration}. FREQUENCY: {meal_freq}. ZIP: {zip_code}.
            ENVIRONMENT: {dining_env}.
            
            TASK: Generate a meal plan aligned with {current_goal}. 
            Adjust macros for {workout_today}. (e.g., Higher carbs for cardio, higher protein for lifting).
            """
            res = client.models.generate_content(model=MODEL_ID, contents=nut_p)
            st.session_state["active_nut_plan"] = res.text
            st.rerun()

    # ACTION B: Restock & Forecast Popover
    with c_restock.popover("🛒 Restock & Forecast", use_container_width=True):
        st.subheader("📋 Logistics Checkpoint")
        confirm_p = st.checkbox("Pantry is up-to-date")
        loadout = st.radio("Scope:", ["Match Current Plan", "Full 2-Week Strategic Loadout"])
        
        if st.button("🚀 Execute Analysis", type="primary", use_container_width=True):
            if confirm_p:
                with st.spinner("Calculating local rates..."):
                    inventory_str = pantry_df.to_string()
                    restock_p = f"""
                    ROLE: Navy Logistics Specialist. 
                    ZIP: {zip_code}. STORES: {preferred_stores}. SCOPE: {loadout}.
                    PANTRY: {inventory_str}.
                    TASK: Provide missing items, categorized by store, and a 2026 COST FORECAST for ZIP {zip_code}.
                    Include specific store locations.
                    """
                    res_r = client.models.generate_content(model=MODEL_ID, contents=restock_p)
                    st.session_state["restock_list"] = res_r.text
                    st.rerun()

    # ACTION C: Dining Out Recon
    with c_out.popover("🍕 Dining Out", use_container_width=True):
        st.subheader("🎯 Menu Recon")
        target_res = st.text_input("Restaurant Name", placeholder="e.g., Chipotle")
        if st.button("🔍 Get Tactical Order", use_container_width=True):
            recon_p = f"GOAL: {current_goal}. RESTAURANT: {target_res}. Give 2 orders: 1 Performance, 1 Lockdown."
            res_rec = client.models.generate_content(model=MODEL_ID, contents=recon_p)
            st.session_state["active_recon"] = res_rec.text

    # --- 5. DATA OUTPUT DISPLAY ---
    if "active_nut_plan" in st.session_state:
        st.divider()
        t1, t2 = st.tabs(["📋 Tactical Plan", "💰 Restock & Forecast"])
        with t1:
            st.markdown(st.session_state["active_nut_plan"])
        with t2:
            if "restock_list" in st.session_state:
                st.markdown(st.session_state["restock_list"])
            else:
                st.info("Run 'Restock & Forecast' to see analysis.")

    if "active_recon" in st.session_state:
        st.success("Dining Recon Complete")
        st.markdown(st.session_state["active_recon"])

    # --- 6. MANUAL LOGGING ---
    st.divider()
    with st.expander("📝 Quick Calorie Log"):
        # Create four columns to fit the Date input
        c1, c2, c3, c4 = st.columns([2, 1, 1.5, 1])
    
        q_item = c1.text_input("Item", key="ql_i", placeholder="e.g. Protein Shake")
        q_cal = c2.number_input("Kcal", value=0, step=50, key="ql_c")
    
        # Historical Date Selector
        # Defaults to today, min_value pulls from account creation or a set past date
        q_date = c3.date_input("Date", 
                           value=datetime.date.today(),
                           min_value=st.session_state.get("account_created", datetime.date(2024,1,1)),
                           max_value=datetime.date.today(),
                           key="ql_d")
    
        if c4.button("➕ Log", use_container_width=True):
            if q_item and q_cal > 0:
            # Pass the selected date to your saving function
                save_entry("Nutrition", q_item, q_cal, q_date)
                st.toast(f"Logged {q_item} for {q_date}")
                st.rerun()
            else:
                st.error("Enter name and calories.")

with tab_analysis:
    st.header("📊 Tactical Analysis & Intelligence")

    # --- SECTION 1: COMMAND SITREP ---
    # Moved from the header to the top of Analysis
    with st.container(border=True):
        st.subheader("📡 Command Sitrep")
        
        # Global metrics pulled from session state
        current_tier = st.session_state.get("current_tier", "Good Low")
        bca_pass = st.session_state.get("bca_pass", True)
        lockdown = st.session_state.get("mission_lockdown", False)
        days_rem = (st.session_state.get("mission_deadline", datetime.date.today()) - datetime.date.today()).days
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mission Proximity", f"{days_rem} Days")
        col2.metric("PRT Status", current_tier)
        col3.metric("BCA Standings", "PASS" if bca_pass else "FAIL")
        col4.metric("Readiness Level", "STRIKE" if not lockdown else "RECOVERY", delta="LOCKDOWN" if lockdown else "NOMINAL", delta_color="inverse")

    # --- SECTION 2: GENERATE INTELLIGENCE (AI AUDIT) ---
    with st.container(border=True):
        st.subheader("🕵️ Generate Intelligence")
        st.write("Synthesize all mission logs, performance trends, and nutritional data into a tactical brief.")
        
        if st.button("🛰️ Initialize Tactical Audit", use_container_width=True, type="primary"):
            with st.spinner("Analyzing data streams..."):
                # Constructing the Intel Briefing
                history_data = st.session_state.get("history", [])
                recent_logs = history_data[-15:] if history_data else "No historical logs available."
                
                intel_p = f"""
                ROLE: Navy Performance Intelligence Officer.
                SITUATION: {days_rem} days to mission.
                GOAL: {st.session_state.get('user_goal', 'PFA Excellence')}.
                CURRENT STATUS: PRT {current_tier}, BCA {'Pass' if bca_pass else 'Fail'}.
                SYSTEM STATE: {'LOCKDOWN' if lockdown else 'Optimal'}.
                RECENT LOGS: {recent_logs}
                
                TASK: Generate a TACTICAL INTELLIGENCE BRIEF:
                1. TREND ANALYSIS: Are metrics improving or stagnating?
                2. LOGISTICAL GAP: Is current effort matching the mission goal?
                3. IMMEDIATE ACTION: One shift in training or nutrition for the next 72 hours.
                """
                res = client.models.generate_content(model=MODEL_ID, contents=intel_p)
                st.session_state["tactical_intel"] = res.text
                st.rerun()

        if "tactical_intel" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state["tactical_intel"])
            if st.button("🗑️ Archive Intelligence"):
                del st.session_state["tactical_intel"]
                st.rerun()

    # --- SECTION 3: VISUAL TREND ANALYSIS ---
    with st.container(border=True):
        st.subheader("📈 Performance Trajectory")
        history_data = st.session_state.get("history", [])
        
        if history_data:
            df = pd.DataFrame(history_data)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Metabolic Output
            st.write("**Metabolic Output Trends (Kcal)**")
            workout_df = df[df['Category'] == 'Exercise']
            if not workout_df.empty:
                st.line_chart(workout_df.set_index('Date')['Value'])
            
            # Nutrition Trends
            st.write("**Caloric Intake Consistency**")
            nutri_df = df[df['Category'] == 'Nutrition']
            if not nutri_df.empty:
                st.area_chart(nutri_df.set_index('Date')['Value'])
        else:
            st.info("Awaiting mission data to populate trajectory charts.")

    # --- SECTION 4: DATA MAINTENANCE ---
    with st.expander("📂 Raw Log Access"):
        if history_data:
            st.table(pd.DataFrame(history_data).sort_values(by='Date', ascending=False))
            if st.button("🗑️ Wipe Tactical History", type="secondary"):
                st.session_state.history = []
                st.rerun()
        else:
            st.write("Intelligence database is currently empty.")