import streamlit as st
import pandas as pd
import plotly.express as px
from models import Employee, ShiftRequest, Day, TimeBlock, RoleConstraint
from solver import solve_schedule
import uuid
import json

# --- CONFIG ---
st.set_page_config(page_title="ShiftHero V1.6", layout="wide")

# --- STATE MANAGEMENT ---
if 'staff_data' not in st.session_state:
    st.session_state.staff_data = pd.DataFrame([
        {"name": "Alice", "role": "Manager", "max_hours": 40},
        {"name": "Bob", "role": "Chef", "max_hours": 45},
        {"name": "Charlie", "role": "Server", "max_hours": 30},
        {"name": "David", "role": "Server", "max_hours": 20},
    ])

if 'unavailable_constraints' not in st.session_state:
    st.session_state.unavailable_constraints = []

if 'role_rules' not in st.session_state:
    st.session_state.role_rules = pd.DataFrame([
        {"role": "Manager", "min_count": 1},
        {"role": "Chef", "min_count": 1}
    ])

if 'demand_data' not in st.session_state:
    rows = []
    for d in Day:
        rows.append({"Day": d.value, "Morning": 2, "Lunch": 3, "Dinner": 3})
    st.session_state.demand_data = pd.DataFrame(rows)

# --- SIDEBAR: PERSISTENCE & CONFIG ---
with st.sidebar:
    # NEW: Help / Onboarding
    with st.expander("❓ How to use"):
        st.markdown("""
        1. **Edit Staff:** Update names and roles in *Step 1*.
        2. **Set Rules:** Add "Availability Exceptions" if someone is off.
        3. **Input Demand:** Set how many staff you need in *Step 2*.
        4. **Generate:** Click the rocket button!
        5. **Refine:** Edit the result table directly, then download or copy to WhatsApp.
        """)
    
    st.title("ShiftHero 🦸")
    st.markdown("---")
    
    # NEW: Save/Load Section
    st.markdown("### 💾 Save/Load Team")
    
    # 1. Download Config
    # We bundle Staff, Rules, and Unavailability into one JSON
    current_state = {
        "staff": st.session_state.staff_data.to_dict(orient="records"),
        "role_rules": st.session_state.role_rules.to_dict(orient="records"),
        "unavailable": st.session_state.unavailable_constraints
    }
    json_str = json.dumps(current_state, indent=2)
    
    st.download_button(
        label="📥 Download Team Config",
        data=json_str,
        file_name="shifthero_team_config.json",
        mime="application/json",
        help="Save your staff list and rules for next week."
    )
    
    # 2. Upload Config
    uploaded_file = st.file_uploader("Upload Config", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.staff_data = pd.DataFrame(data["staff"])
            st.session_state.role_rules = pd.DataFrame(data["role_rules"])
            st.session_state.unavailable_constraints = data["unavailable"]
            st.success("✅ Team loaded successfully!")
            # Force rerun to update UI
            st.rerun() 
        except Exception as e:
            st.error(f"Error loading file: {e}")

    st.markdown("---")
    
    # ROLE RULES (Existing)
    st.markdown("### 🛡️ Role Rules")
    st.session_state.role_rules = st.data_editor(
        st.session_state.role_rules, 
        num_rows="dynamic", 
        hide_index=True,
        key="role_rules_editor"
    )

# --- MAIN UI ---
st.header("Draft Your Schedule")

# STEP 1: STAFF & AVAILABILITY
with st.expander("1. Staff & Constraints", expanded=True):
    tab1, tab2, tab3 = st.tabs(["Staff List", "Availability Exceptions", "Paste CSV"])
    
    with tab1:
        st.session_state.staff_data = st.data_editor(
            st.session_state.staff_data, 
            num_rows="dynamic",
            use_container_width=True
        )
        
    with tab2:
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            # Safe unique check
            staff_names = st.session_state.staff_data['name'].unique() if not st.session_state.staff_data.empty else []
            sel_name = st.selectbox("Staff", staff_names) if len(staff_names) > 0 else st.text_input("Staff Name")
        with c2:
            sel_day = st.selectbox("Day", [d.value for d in Day])
        with c3:
            sel_block = st.selectbox("Block", [b.value for b in TimeBlock])
        with c4:
            st.write("") 
            if st.button("🚫 Block"):
                st.session_state.unavailable_constraints.append({
                    "name": sel_name, "day": sel_day, "block": sel_block
                })
        
        if st.session_state.unavailable_constraints:
            st.caption("Active Blocks:")
            st.dataframe(pd.DataFrame(st.session_state.unavailable_constraints), use_container_width=True)
            if st.button("Clear All Blocks"):
                st.session_state.unavailable_constraints = []
                st.rerun()
        else:
            st.caption("No specific unavailability set.")

    with tab3:
        txt = st.text_area("Paste: Name, Role, MaxHours")
        if st.button("Parse CSV"):
            try:
                lines = [l.split(',') for l in txt.split('\n') if l.strip()]
                parsed = [{"name": l[0].strip(), "role": l[1].strip(), "max_hours": int(l[2].strip())} for l in lines if len(l) > 2]
                if parsed:
                    st.session_state.staff_data = pd.DataFrame(parsed)
                    st.rerun()
            except Exception as e:
                st.error(f"Parse error: {e}")

# STEP 2: DEMAND
with st.expander("2. Demand (Staff Count)", expanded=True):
    st.session_state.demand_data = st.data_editor(
        st.session_state.demand_data, 
        hide_index=True,
        use_container_width=True
    )

# STEP 3: GENERATE
if st.button("🚀 Generate Schedule", type="primary"):
    with st.spinner("Optimizing schedule..."):
        
        employees = []
        for _, row in st.session_state.staff_data.iterrows():
            my_blocks = [
                f"{x['day']}-{x['block']}" 
                for x in st.session_state.unavailable_constraints 
                if x['name'] == row['name']
            ]
            
            employees.append(Employee(
                id=str(uuid.uuid4()), 
                name=row['name'],
                role=row['role'],
                max_hours=int(row['max_hours']),
                unavailable_slots=my_blocks
            ))
            
        requests = []
        for _, row in st.session_state.demand_data.iterrows():
            d = Day(row['Day'])
            requests.append(ShiftRequest(day=d, block=TimeBlock.MORNING, required_staff=int(row['Morning'])))
            requests.append(ShiftRequest(day=d, block=TimeBlock.LUNCH, required_staff=int(row['Lunch'])))
            requests.append(ShiftRequest(day=d, block=TimeBlock.DINNER, required_staff=int(row['Dinner'])))

        role_constraints = []
        if 'role_rules' in st.session_state and not st.session_state.role_rules.empty:
            for _, row in st.session_state.role_rules.iterrows():
                r_role = row.get('role')
                r_count = row.get('min_count')
                if r_role and pd.notna(r_count) and r_count > 0:
                    role_constraints.append(RoleConstraint(
                        role=str(r_role), 
                        min_count=int(r_count)
                    ))
        
        st.session_state.result = solve_schedule(employees, requests, role_constraints)

# STEP 4: RESULTS
if 'result' in st.session_state:
    res = st.session_state.result
    st.divider()
    
    # --- METRICS ---
    st.markdown("### 📊 Scorecard")
    m1, m2, m3 = st.columns(3)
    
    score = res.metrics.get('total_penalty', 0)
    score_color = "normal"
    if score > 500: score_color = "off"
    if score > 2000: score_color = "inverse"

    m1.metric("Penalty Score", f"{score:.0f}", delta_color=score_color)
    m2.metric("Fairness (StdDev)", f"{res.metrics.get('fairness_std_dev', 0):.2f}")
    
    with m3:
        if score > 0:
            st.warning(f"⚠️ **Issues Detected** (Score: {score:.0f})")
            has_role_rules = False
            if 'role_rules' in st.session_state and not st.session_state.role_rules.empty:
                active_rules = st.session_state.role_rules[
                    pd.to_numeric(st.session_state.role_rules['min_count'], errors='coerce') > 0
                ]
                if not active_rules.empty: has_role_rules = True

            if has_role_rules and score >= 2000:
                st.write("• **Missing Roles:** Key staff missing.")
                st.write("• **Understaffing:** Cannot fill shifts.")
            else:
                approx_empty_slots = int(score / 1000)
                st.write(f"• **Understaffing:** Short ~{approx_empty_slots} shifts.")
        else:
            st.success("✅ Perfect Schedule")
    
    # --- VIEW ---
    st.subheader("Schedule View")
    
    df_res = pd.DataFrame(res.assignments)
    
    if not df_res.empty:
        # Sort Chronologically
        day_map = {d.value: i for i, d in enumerate(Day)}
        block_map = {"Morning": 0, "Lunch": 1, "Dinner": 2}
        df_res['day_rank'] = df_res['day'].map(day_map)
        df_res['block_rank'] = df_res['block'].map(block_map)
        df_res = df_res.sort_values(['day_rank', 'block_rank']).drop(columns=['day_rank', 'block_rank'])

        # Editable Grid
        edited_df = st.data_editor(
            df_res[['day', 'block', 'staff_str']], 
            column_config={
                "day": st.column_config.TextColumn("Day", disabled=True),
                "block": st.column_config.TextColumn("Shift", disabled=True),
                "staff_str": st.column_config.TextColumn("Assigned Staff (Edit to Override)")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # --- NEW: CSV DOWNLOAD ---
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Schedule (CSV)",
            data=csv,
            file_name="weekly_schedule.csv",
            mime="text/csv",
        )
        
        # Workload Chart
        st.caption("Hours Distribution Check")
        all_assigned = []
        for _, r in df_res.iterrows():
            all_assigned.extend(r['staff'])
        
        if all_assigned:
            counts = pd.Series(all_assigned).value_counts().reset_index()
            counts.columns = ['Name', 'Shifts']
            counts['Est_Hours'] = counts['Shifts'] * 4 
            fig = px.bar(counts, x='Name', y='Est_Hours', title="Estimated Workload (Hours)")
            st.plotly_chart(fig, use_container_width=True)

        # WhatsApp Export
        st.subheader("📲 WhatsApp Export")
        updated_assignments = []
        for _, row in edited_df.iterrows():
            updated_assignments.append({
                "day": row['day'],
                "block": row['block'],
                "staff_str": row['staff_str']
            })
            
        from solver import generate_whatsapp_export
        final_text = generate_whatsapp_export(updated_assignments)
        st.text_area("Copy this text:", value=final_text, height=300)
    else:
        st.warning("No shifts assigned.")