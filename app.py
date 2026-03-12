import streamlit as st
from datetime import date
import google.generativeai as genai

# --- CONFIG ---
st.set_page_config(page_title="PFA Pro", page_icon="⚓", layout="wide")

# --- GEMINI AI SETUP (Diagnostic Mode) ---
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    
    try:
        # Get all models that support generating content
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if models:
            # We will use the first one found, but remove the 'models/' prefix if it's there
            selected_model = models[0].replace('models/', '')
            model = genai.GenerativeModel(selected_model)
            
            # This will show a temporary message so you know which one worked!
            st.toast(f"Connected to: {selected_model}", icon="✅")
        else:
            st.error("No models found for this API key.")
            model = None
            
    except Exception as e:
        st.error(f"Failed to connect to Google: {e}")
        model = None
else:
    st.error("⚠️ AI Key Not Found! Check .streamlit/secrets.toml")
    model = None

# --- GLOBAL MEMORY ---
if 'water' not in st.session_state: st.session_state.water = 0
if 'food_cals' not in st.session_state: st.session_state.food_cals = 0
if 'exercise_burn' not in st.session_state: st.session_state.exercise_burn = 0

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stMetricValue"] { color: #00a8ff; font-size: 32px; font-weight: bold; }
    div.stButton > button {
        background-color: #0077b6; color: white !important;
        border-radius: 5px; border: 1px solid #00b4d8; font-weight: bold; width: 100%;
    }
    div.stButton > button:hover { background-color: #00b4d8; color: #0E1117 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚓ PFA Command")
    pfa_date = st.date_input("Scheduled PFA", value=date(2026, 5, 15))
    days_left = (pfa_date - date.today()).days
    st.metric("Days to Mission", f"{days_left}")
    
    st.divider()
    height = st.number_input("Height (in)", 50, 90, 70)
    waist = st.number_input("Waist (in)", 20.0, 60.0, 35.0, step=0.5)
    wthr = waist / height
    is_passing = wthr <= 0.55
    
    if is_passing:
        st.success(f"BCA: PASSED ({wthr:.2f})")
        goal = st.selectbox("Objective", ["Maintenance", "Weight Loss", "Bulk"], index=1)
    else:
        st.error(f"BCA: ABOVE LIMIT ({wthr:.2f})")
        goal = "Weight Loss"

    target_cals = 1800 if goal == "Weight Loss" else (2300 if goal == "Maintenance" else 2800)
    st.caption("PFA Pro™ | © 2026 Dimitry Willadsen")

# --- MAIN DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["🍴 Nutrition", "🏃 Exercise", "📊 Summary"])

with tab1:
    st.header("Smart Mess Deck")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💧 Hydration")
        unit = st.radio("Unit", ["oz", "mL"], horizontal=True)
        water_in = st.number_input("Amount", min_value=0.0, key="w_in")
        if st.button("Log Water"):
            st.session_state.water += water_in if unit == "oz" else water_in * 0.0338
        st.info(f"Total: {st.session_state.water:.1f} oz")

with c2:
        st.subheader("🍳 AI Fuel Log")
        user_desc = st.text_area("Describe your meal:", placeholder="e.g. 6oz steak, sweet potato, and asparagus")
        
        if st.button("🤖 Analyze Meal with Gemini"):
            if model is None:
                st.error("AI is not configured. Check .streamlit/secrets.toml")
            elif user_desc:
                try:
                    with st.spinner("Analyzing..."):
                        # This sends the request to Google
                        response = model.generate_content(f"How many calories in {user_desc}? Give number only.")
                        
                        # This finds the number in the response
                        import re
                        numbers = re.findall(r'\d+', response.text)
                        
                        if numbers:
                            est_cals = int(numbers[0])
                            st.session_state.food_cals += est_cals
                            st.success(f"Log Updated: +{est_cals} kcal")
                        else:
                            st.warning(f"AI responded but no number found: {response.text}")
                
                except Exception as e:
                    # --- THIS IS THE DEBUG SECTION ---
                    st.error("🚨 Found the problem! See the technical error below:")
                    st.exception(e) 
                    # ----------------------------------
            else:
                st.warning("Please describe what you ate first.")

        st.info(f"Total Fuel: {st.session_state.food_cals} kcal")

with tab2:
    st.header("Daily Burn")
    ex_val = st.number_input("Exercise Calories Burned", step=50)
    if st.button("Log Burn"): 
        st.session_state.exercise_burn += ex_val
    st.metric("Total Burned", f"{st.session_state.exercise_burn}")

with tab3:
    st.header("Mission Summary")
    net = st.session_state.food_cals - st.session_state.exercise_burn
    remaining = target_cals - net
    
    st.metric("Net Calories", f"{net}", delta=f"{remaining} Left", delta_color="inverse")
    st.progress(min(max(net/target_cals, 0.0), 1.0))
    
    if net > target_cals:
        st.warning("⚠️ You've exceeded your daily target for your objective.")
    else:
        st.success("✅ You are currently on track for your mission objective.")