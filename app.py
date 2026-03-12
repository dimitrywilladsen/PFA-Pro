import streamlit as st

# --- CONFIG ---
st.set_page_config(page_title="PFA Pro", page_icon="⚓", layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stMetric { background-color: #1A1C23; padding: 20px; border-radius: 10px; border-left: 5px solid #0077b6; }
    div[data-testid="stMetricValue"] { color: #00a8ff; }
    .stTable { background-color: #1A1C23; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("⚓ PFA Pro: Mission Dashboard")
st.caption("Official 2026 Navy BCA Standards & Performance Tracking")
st.divider()

# --- INPUT SECTION: STAGE 1 (Metrics) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Body Metrics")
    height = st.number_input("Height (inches)", min_value=50, max_value=90, value=70, step=1)
    weight = st.number_input("Weight (lbs)", min_value=90, max_value=400, value=185, step=1)
    waist = st.number_input("Waist (inches)", min_value=20.0, max_value=60.0, value=35.0, step=0.5)

# --- BCA LOGIC ---
wthr = waist / height
is_passing = wthr <= 0.55
status_text = "PASSED" if is_passing else "ABOVE LIMIT"
status_color = "normal" if is_passing else "inverse"

# --- INPUT SECTION: STAGE 2 (Goals & Lock Logic) ---
with col2:
    st.subheader("🎯 Mission Goal")
    
    if not is_passing:
        goal = st.selectbox(
            "Objective", 
            ["Weight Loss", "Maintenance", "Performance Bulk"], 
            index=0, 
            disabled=True,
            help="BCA limits exceeded. Goal locked to Weight Loss."
        )
        st.caption("⚠️ **BCA OVERRIDE ACTIVE**")
    else:
        goal = st.selectbox(
            "Objective", 
            ["Weight Loss", "Maintenance", "Performance Bulk"],
            index=1 
        )
        
    activity = st.select_slider("Daily Activity Level", 
                               options=["Low (Office)", "Moderate (Shipboard)", "High (Field/Special Ops)"])

# --- METRICS DISPLAY ---
st.divider()
m1, m2 = st.columns(2)
with m1:
    st.metric(label="Waist-to-Height Ratio", value=f"{wthr:.2f}", delta="Target: ≤ 0.55", delta_color=status_color)
with m2:
    st.metric(label="BCA Status", value=status_text)

# --- MOTIVATIONAL CALLOUTS ---
st.write("") # Spacer
if not is_passing:
    st.error("📉 Stay Disciplined, Shipmate.")
elif goal == "Performance Bulk":
    st.success("💪 Get Some!")
elif goal == "Weight Loss":
    st.info("🔥 Eyes on the prize—keep grinding.")
else:
    st.info("⚓ Steady as she goes.")

# --- NUTRITION TARGETS ---
st.header(f"🍴 Today's Fuel Plan: {goal}")

if goal == "Weight Loss":
    target_cals = 1800
elif goal == "Maintenance":
    target_cals = 2300
else:
    target_cals = 2800

protein = (target_cals * 0.30) / 4
carbs = (target_cals * 0.40) / 4
fats = (target_cals * 0.30) / 9

st.table({
    "Nutrient": ["Total Calories", "Protein (g)", "Carbs (g)", "Fats (g)"],
    "Target": [f"{target_cals} kcal", f"{protein:.0f}g", f"{carbs:.0f}g", f"{fats:.0f}g"]
})

# --- FOOTER ---
st.divider()
st.subheader("Always Mission Ready")
st.caption(f"© 2026 Dimitry Willadsen | PFA Pro™")