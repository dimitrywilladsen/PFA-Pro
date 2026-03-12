import streamlit as st
from datetime import date

# --- CONFIG ---
st.set_page_config(page_title="PFA Pro", page_icon="⚓", layout="wide")

# --- GLOBAL MEMORY (Session State) ---
if 'water' not in st.session_state: st.session_state.water = 0
if 'food_cals' not in st.session_state: st.session_state.food_cals = 0
if 'exercise_burn' not in st.session_state: st.session_state.exercise_burn = 0

# --- UI STYLING & HIGH-CONTRAST BUTTONS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] { color: #00a8ff; font-size: 32px; font-weight: bold; }
    
    /* BUTTON STYLING - High Contrast Navy */
    div.stButton > button {
        background-color: #0077b6;
        color: white !important;
        border-radius: 5px;
        border: 1px solid #00b4d8;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background-color: #00b4d8;
        border: 1px solid white;
        color: #0E1117 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1C23;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MISSION COMMAND ---
with st.sidebar:
    st.title("⚓ PFA Command")
    st.divider()
    
    # PFA COUNTDOWN
    st.subheader("🗓️ Target Date")
    pfa_date = st.date_input("Scheduled PFA", value=date(2026, 5, 15))
    days_left = (pfa_date - date.today()).days
    
    if days_left > 0:
        st.metric("Days to Mission", f"{days_left}")
    else:
        st.error("🏁 PFA COMPLETE / OVERDUE")

    st.divider()

    # BODY METRICS
    st.subheader("📋 Body Metrics")
    height = st.number_input("Height (in)", 50, 90, 70)
    waist = st.number_input("Waist (in)", 20.0, 60.0, 35.0, step=0.5)
    
    wthr = waist / height
    is_passing = wthr <= 0.55
    
    if is_passing:
        st.success(f"BCA: PASSED ({wthr:.2f})")
        goal = st.selectbox("Objective", ["Maintenance", "Weight Loss", "Performance Bulk"], index=1)
    else:
        st.error(f"BCA: ABOVE LIMIT ({wthr:.2f})")
        st.warning("⚠️ Locked to Weight Loss")
        goal = "Weight Loss"

    # AUTO-TARGETS
    if goal == "Weight Loss": target_cals = 1800
    elif goal == "Maintenance": target_cals = 2300
    else: target_cals = 2800

    st.divider()
    st.caption("PFA Pro™ | Always Mission Ready")
    st.caption("© 2026 Dimitry Willadsen")

# --- MAIN DASHBOARD ---
st.title(f"⚓ Daily Mission: {goal}")

tab1, tab2, tab3 = st.tabs(["🍴 Nutrition", "🏃 Exercise", "📊 Mission Summary"])

# --- TAB 1: NUTRITION & SMART FUEL ---
with tab1:
    st.header("Smart Mess Deck")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💧 Hydration")
        unit = st.radio("Unit", ["oz", "mL"], horizontal=True)
        water_input = st.number_input(f"Amount to add ({unit})", min_value=0.0, step=1.0, key="water_in")
        
        if st.button("📥 Log Hydration"):
            final_oz = water_input if unit == "oz" else water_input * 0.033814
            st.session_state.water += final_oz
            st.toast(f"Added {water_input} {unit} to the canteen!")

        st.info(f"Total: **{st.session_state.water:.1f} oz** ({st.session_state.water * 29.57:.0f} mL)")
        if st.button("Reset Water"): st.session_state.water = 0

    with c2:
        st.subheader("🍳 Fuel Intake")
        log_mode = st.radio("Log Method", ["Direct Cal", "Servings/Weight", "AI Describe"], horizontal=True)

        if log_mode == "Direct Cal":
            food_val = st.number_input("Enter kcal", step=50)
            if st.button("Log Calories"): st.session_state.food_cals += food_val

        elif log_mode == "Servings/Weight":
            qty = st.number_input("Quantity", min_value=0.1, step=0.1)
            unit_type = st.selectbox("Unit", ["Servings", "oz", "grams", "cups"])
            est_per_unit = st.number_input("Calories per unit", value=100)
            if st.button("Calculate & Log"): st.session_state.food_cals += (qty * est_per_unit)

        elif log_mode == "AI Describe":
            user_desc = st.text_input("What did you eat?", placeholder="e.g., 2 slices of pizza and a salad")
            if st.button("🤖 AI Estimate"):
                # Keyword logic for v4.0 simulation
                desc = user_desc.lower()
                if "pizza" in desc: est = 600
                elif "chicken" in desc: est = 400
                elif "salad" in desc: est = 200
                elif "burger" in desc: est = 800
                else: est = 500
                st.session_state.food_cals += est
                st.success(f"AI Estimated: {est} kcal for '{user_desc}'")

        st.info(f"Total Fuel: **{st.session_state.food_cals} kcal**")
        if st.button("Reset Daily Fuel"): st.session_state.food_cals = 0

# --- TAB 2: EXERCISE ---
with tab2:
    st.header("Daily Burn")
    ex_type = st.selectbox("Activity Type", ["Running (1.5 mi)", "Swimming", "Plank Session", "Custom"])
    
    if ex_type == "Running (1.5 mi)": auto_burn = 150
    elif ex_type == "Swimming": auto_burn = 300
    else: auto_burn = st.number_input("Custom Burn Calories", step=50)

    if st.button("Log Activity"):
        st.session_state.exercise_burn += auto_burn
        st.toast(f"Logged {auto_burn} calories!")
    
    st.metric("Total Burned Today", f"{st.session_state.exercise_burn} kcal")
    if st.button("Reset Exercise"): st.session_state.exercise_burn = 0

# --- TAB 3: SUMMARY ---
with tab3:
    st.header("Net Mission Progress")
    net_cals = st.session_state.food_cals - st.session_state.exercise_burn
    remaining = target_cals - net_cals
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Net Calories", f"{net_cals}", delta=f"{remaining} Left", delta_color="normal" if remaining >= 0 else "inverse")
    
    with col_b:
        progress_val = min(max(net_cals/target_cals, 0.0), 1.0) if target_cals > 0 else 0
        st.write(f"Fuel Gauge: {int(progress_val * 100)}%")
        st.progress(progress_val)
    
    st.divider()
    if not is_passing:
        st.error(f"📉 **Stay Disciplined, Shipmate.** You have {days_left} days to hit your target.")
    elif goal == "Performance Bulk":
        st.success("💪 **Get Some!** Build that engine.")
    else:
        st.info("⚓ **Steady as she goes.** Mission is on track.")

# --- GLOBAL FOOTER ---
st.write("")
st.divider()
st.caption("All calculations are based on 2026 Navy Physical Readiness Program standards.")
st.markdown("<p style='font-size: 0.8rem; color: gray;'>PFA Pro™ is a trademark of Dimitry Willadsen. All rights reserved.</p>", unsafe_allow_html=True)