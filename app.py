import streamlit as st
import pandas as pd
import datetime
import os
import re

# --- CALLBACKS ---
def handle_workout_submission():
    # These two lines MUST be indented exactly 4 spaces (one Tab)
    st.session_state["temp_workout_val"] = st.session_state["workout_text_box"]
    st.session_state["workout_text_box"] = ""

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="Navy PFA Pro", layout="wide", page_icon="⚓")

# Initialize Gemini 2.5 Client
try:
    from google import genai
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("🔑 Configuration Error: Check your API Key or SDK installation.")
    st.stop()

# --- 2. DATA FUNCTIONS ---
def load_data():
    if os.path.exists('fitness_log.csv'):
        df = pd.read_csv('fitness_log.csv')
        df['date'] = df['date'].astype(str)
        return df
    return pd.DataFrame(columns=['date', 'type', 'description', 'calories'])

def save_entry(entry_type, desc, cals):
    new_data = pd.DataFrame([[str(datetime.date.today()), entry_type, desc, cals]], 
                            columns=['date', 'type', 'description', 'calories'])
    new_data.to_csv('fitness_log.csv', mode='a', header=not os.path.exists('fitness_log.csv'), index=False)

@st.dialog("Confirm Deletion")
def confirm_delete_dialog(indices):
    st.warning(f"⚠️ This will permanently delete {len(indices)} entries. Proceed?")
    if st.button("🔥 Confirm Bulk Purge", type="primary", use_container_width=True):
        delete_entries(indices)
        st.session_state['df_key'] += 1 # Reset table view
        st.rerun()

def delete_entries(indices):
    df = pd.read_csv('fitness_logs.csv')
    df = df.drop(indices)
    df.to_csv('fitness_logs.csv', index=False)

# Helper to format data for sharing
def get_shareable_text(row):
    return f"🚀 Mission Update: {row['type']} - {row['description']} ({row['calories']} kcal) on {row['date']}"

# --- 3. THE "ENGINE" (Calculating variables BEFORE they are used) ---
# We use the Sidebar to get inputs, but we calculate the variables out here.
with st.sidebar:
    st.header("👤 Sailor Profile")
    gender = st.radio("Gender", ["Male", "Female"])
    current_weight = st.number_input("Current Weight (lbs)", value=190)
    height = st.number_input("Height (inches)", value=70)
    age = st.number_input("Age", value=25)
    
    # CALCULATE BMR IMMEDIATELY
    w_kg, h_cm = current_weight * 0.453592, height * 2.54
    bmr = (10 * w_kg) + (6.25 * h_cm) - (5 * age) + (5 if gender == "Male" else -161)
    
    st.divider()
    st.header("🎯 BCA Mission")
    target_weight = st.number_input("BCA Target Weight", value=180)
    bca_date = st.date_input("BCA Deadline", datetime.date.today() + datetime.timedelta(days=30))
    
    # CALCULATE DEFICIT
    days_left = (bca_date - datetime.date.today()).days
    if days_left > 0:
        total_to_lose = current_weight - target_weight
        req_deficit = (total_to_lose * 3500) / days_left
        lbs_per_week = (total_to_lose / days_left) * 7
    else:
        req_deficit, lbs_per_week = 0, 0

# Now load today's specific logs
logs = load_data()
today_str = str(datetime.date.today())
today_logs = logs[logs['date'] == today_str]

# --- Initialize Session States for UI Control ---
if 'df_key' not in st.session_state:
    st.session_state['df_key'] = 0

if 'last_workout' not in st.session_state:
    st.session_state['last_workout'] = None

# Calculate final totals for the UI
burned = today_logs[today_logs['type'] == 'Exercise']['calories'].sum()
eaten = today_logs[today_logs['type'] == 'Food']['calories'].sum()

# THESE ARE THE VARIABLES THAT WERE CAUSING ERRORS - Now they are safe!
total_burn_today = bmr + burned
remaining_budget = (total_burn_today - req_deficit) - eaten

# --- 4. MAIN DASHBOARD ---
tab_ex, tab_meal, tab_hist = st.tabs(["🏃 Exercise", "🍽️ Meals", "📊 History"])

with tab_ex:
    st.header("Activity Log")
    
    # Notice: Persistent Success Bar
    if 'last_workout' in st.session_state:
        st.success(f"✅ **Last Logged:** {st.session_state['last_workout']}")
    
    st.metric("Total Active Burn (Today)", f"{int(burned)} kcal")

    # Input Box
    workout_desc = st.text_area("Describe workout:", 
                                placeholder="e.g. Rowed 2k at 2:00 split", 
                                key="workout_text_box")

    # Analysis Button
    if st.button("Analyze and Log Workout", on_click=handle_workout_submission):
        raw_workout = st.session_state.get("temp_workout_val", "")
        if raw_workout:
            success = False
            for attempt in range(3):
                try:
                    with st.spinner(f"Analyzing... (Attempt {attempt + 1})" if attempt > 0 else "Analyzing..."):
                        prompt = f"Weight: {current_weight} lbs. Workout: {raw_workout}. Calc calories (MET). Return ONLY integer."
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        
                        import re
                        match = re.search(r'\d+', response.text.replace(',', ''))
                        if match:
                            burn_val = int(match.group())
                            save_entry("Exercise", raw_workout, burn_val)
                            st.session_state['last_workout'] = f"{raw_workout} — {burn_val} kcal"
                            success = True
                            break 
                except Exception as e:
                    if "503" in str(e) and attempt < 2:
                        import time
                        time.sleep(2)
                        continue
                    else:
                        st.error(f"Analysis Error: {e}")
                        break
            if success:
                st.rerun()

with tab_meal:
    st.header("Daily Calorie Mission")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Burn", f"{int(total_burn_today)}")
    c2.metric("Total Consumed", f"{int(eaten)}")
    c3.metric("Dinner Budget", f"{int(remaining_budget)}")

    if st.button("Prescribe Dinner Portions"):
        with st.spinner("Consulting AI Dietitian..."):
            prescribe_prompt = f"Sailor has {remaining_budget} kcal left. Suggest portions for Chicken, Rice, Broccoli."
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prescribe_prompt)
            st.markdown(response.text)

with tab_hist:
    st.header("Mission Performance History")
    
    if not logs.empty:
        logs_display = logs.sort_values(by='date', ascending=False)
        
        # 1. Enable MULTI-ROW selection
        selection = st.dataframe(
            logs_display,
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row", # Changed from 'single-row'
            hide_index=False,
            key=f"history_table_{st.session_state['df_key']}"
        )

        selected_rows = selection.get("selection", {}).get("rows", [])

        if selected_rows:
            # Get all selected indices and the actual data rows
            selected_indices = [logs_display.index[i] for i in selected_rows]
            selected_data = logs.loc[selected_indices]
            
            st.markdown(f"### ⚡ Actions for {len(selected_rows)} selected entries")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # DELETE: Pass the whole list of indices
                if st.button("🗑️ Delete All", use_container_width=True, type="primary"):
                    confirm_delete_dialog(selected_indices)
            
            with col2:
                # COPY/SHARE: Combine all selected rows into one text block
                combined_text = "\n".join([get_shareable_text(row) for _, row in selected_data.iterrows()])
                st.write("📋 **Copy All:**")
                st.code(combined_text, language=None)
            
            with col3:
                # 1. Determine the label based on how many rows are picked
                num_selected = len(selected_rows)
                export_label = f"📥 Export ({num_selected}) Entries" if num_selected > 1 else "📥 Export Row"
                
                # 2. Create the CSV data for just these rows
                multi_csv = selected_data.to_csv(index=False).encode('utf-8')
                
                # 3. The Download Button with the dynamic label
                st.download_button(
                    label=export_label, 
                    data=multi_csv, 
                    file_name="mission_selection.csv", 
                    mime="text/csv", 
                    use_container_width=True
                )
                            
            with col4:
                # DESELECT: Still works by incrementing the key
                if st.button("✖️ Deselect All", use_container_width=True):
                    st.session_state['df_key'] += 1
                    st.rerun()
                    
        st.divider()
        full_csv = logs.to_csv(index=False).encode('utf-8')
        st.download_button("📂 Download Full Mission History", full_csv, "history.csv", "text/csv")
    else:
        st.info("No logs found.")