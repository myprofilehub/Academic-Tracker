import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import io

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Naan Mudhalvan Dashboard", layout="wide")

# Professional UI Styling
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    .card-container {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); text-align: center;
        border-bottom: 4px solid #1A3C6D; margin-bottom: 10px;
        height: 140px; display: flex; flex-direction: column; justify-content: center;
    }
    .border-blue { border-bottom: 5px solid #1A3C6D; }
    .border-green { border-bottom: 5px solid #28A745; }
    .border-red { border-bottom: 5px solid #E74C3C; }
    .card-title { font-size: 13px; color: #666; text-transform: uppercase; margin-bottom: 8px; font-weight: 600; }
    .card-value { font-size: 24px; font-weight: bold; color: #1A3C6D; }
    div.stButton > button { background-color: #1A3C6D; color: white; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

def modern_card(label, value, border_style="border-blue"):
    card_html = f"<div class='card-container {border_style}'><div class='card-title'>{label}</div><div class='card-value'>{value}</div></div>"
    return st.markdown(card_html, unsafe_allow_html=True)

# 2. DATA ENGINE
XLSX_LINK = "https://sheet.zohopublic.in/sheet/published/ddt54238ae124de51497ea894fa1aec84ee18?download=xlsx"

@st.cache_data(ttl=1)
def load_and_clean_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(XLSX_LINK, headers=headers)
    response.raise_for_status() 
    excel_file = io.BytesIO(response.content)
    
    tracker = pd.read_excel(excel_file, sheet_name='Intervention Tracker', skiprows=4)
    summary = pd.read_excel(excel_file, sheet_name='Summary')

    structural_cols = ['University Code', 'College Name', 'Trainer name', 'Batch Size', 'Start Date', 'End Date', 'Timing']
    existing_struct = [c for c in structural_cols if c in tracker.columns]
    tracker[existing_struct] = tracker[existing_struct].ffill()

    tracker = tracker[~tracker['College Name'].astype(str).str.contains('Total|Grand', case=False, na=False)]
    
    cols_to_fix = [
        'Students Count', 'Intervention Completed', 'Pending Intervention ',
        'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Batch Size'
    ]
    
    for col in cols_to_fix:
        if col in tracker.columns:
            tracker[col] = pd.to_numeric(tracker[col], errors='coerce').fillna(0)
            if 'Hours' not in col and 'Percentage' not in col and 'Batch Size' not in col:
                tracker[col] = tracker[col].astype(int)

    for col in ['University Code', 'College Name', 'Trainer name']:
        if col in tracker.columns:
            tracker[col] = tracker[col].astype(str).replace('nan', 'Unknown')

    tracker['Completion Percentage'] = pd.to_numeric(tracker['Completion Percentage'], errors='coerce')  
    tracker['Original_Val'] = tracker['Completion Percentage'] 
    tracker['Completion %'] = (tracker['Original_Val'] * 100).fillna(0).astype(int)
    
    return tracker, summary

try:
    df, summary_df = load_and_clean_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 3. PAGE STATE
if 'page' not in st.session_state: 
    st.session_state.page = "Home"

# 4. MAIN INTERFACE HEADER
head_left, head_center, head_right = st.columns([1, 4, 1])

with head_left:
    st.image("NM_Logo.png", use_container_width=True)

with head_center:
    st.markdown("""
        <div style='text-align: center;'>
            <h1 style='color: #1A3C6D; margin-bottom: 0; font-size: 42px;'>Academic Progress Dashboard</h1>
            <h2 style='color: #1A3C6D; margin-top: 10px; margin-bottom: 0; font-weight: 400;'>Naan Mudhalvan Skill Development Initiative</h2>
            <p style='color: #666; font-size: 16px; margin-top: 5px;'>Government of Tamil Nadu</p>
            <p style='font-size: 20px; margin-top: 20px;'>
                <span style='color: #E74C3C; font-weight: bold;'>Course Name:</span> 
                <span style='color: #000000; font-weight: bold;'>Data Analytics & Visualization</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

with head_right:
    st.image("HL_Logo.png", use_container_width=True)

st.markdown("<hr style='border: 1.5px solid #1A3C6D; margin-top: 0;'>", unsafe_allow_html=True)

# --- NAVIGATION ---
nav_col1, nav_spacer, nav_col2 = st.columns([1, 4, 1])
with nav_col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "Home"
with nav_col2:
    if st.button("📋 Assessment", use_container_width=True):
        st.session_state.page = "Assessment"

st.markdown("<br>", unsafe_allow_html=True)

# --- GLOBAL KPI CARDS (Always Visible at Top) ---
k1, k2, k3, k4, k5 = st.columns(5)
with k1: modern_card("Total Enrolled", int(summary_df.iloc[0]['Enrolled Count']))
with k2: modern_card("Total Completed", int(summary_df.iloc[0]['Completed Count']), "border-green")
with k3: modern_card("In Progress", int(summary_df.iloc[0]['In Progress']))
with k4: modern_card("Not Started", int(summary_df.iloc[0]['Not Started']), "border-red")
with k5: modern_card("Course Duration", "45 Hrs", "border-blue")

# --- CASCADING FILTERS SECTION ---
st.markdown("### 🛠️ Quick Filters")
f1, f2, f3, f4 = st.columns(4)

# 1. University Filter (Base)
with f1:
    u_code = st.multiselect("University Code", options=sorted(df["University Code"].unique()))

# 2. College Filter (Depends on University)
temp_df = df.copy()
if u_code:
    temp_df = temp_df[temp_df["University Code"].isin(u_code)]
with f2:
    c_name = st.multiselect("College Name", options=sorted(temp_df["College Name"].unique()))

# 3. Trainer Filter (Depends on Univ + College)
if c_name:
    temp_df = temp_df[temp_df["College Name"].isin(c_name)]
with f3:
    t_name = st.multiselect("Trainer name", options=sorted(temp_df["Trainer name"].unique()))

# 4. Batch Size Filter (Depends on Univ + College + Trainer)
if t_name:
    temp_df = temp_df[temp_df["Trainer name"].isin(t_name)]
with f4:
    b_size = st.multiselect("Batch Size", options=sorted(temp_df["Batch Size"].unique()))

# Final Filtered DataFrame
filt_df = temp_df.copy()
if b_size:
    filt_df = filt_df[filt_df["Batch Size"].isin(b_size)]

# Reset Logic
st.markdown("<br>", unsafe_allow_html=True)
res_c1, res_c2, res_c3 = st.columns([2, 1, 2])
with res_c2:
    if st.button("🔄 Reset Filters", use_container_width=True): 
        st.rerun()

# Logic for the Dynamic Trainer Card
active_trainers = filt_df['Trainer name'].unique()
if len(t_name) == 1:
    trainer_display = t_name[0]
elif len(t_name) > 1:
    trainer_display = "Multiple Trainers"
elif len(active_trainers) == 1:
    trainer_display = active_trainers[0]
else:
    trainer_display = "All Trainers"

# Centered Trainer Card (Always visible to show context)
card_c1, card_c2, card_c3 = st.columns([1, 2, 1])
with card_c2:
    modern_card("Selected Trainer", trainer_display, "border-blue")

st.markdown("---")

# 5. CONTENT FUNCTIONS
def display_filtered_metrics():
    if filt_df.empty:
        st.warning("No data found for the selected filters.")
        return
    
    m1, m2, m3 = st.columns(3)
    with m1: modern_card("Student Count", f"{filt_df['Students Count'].sum():,}")
    with m2: modern_card("Weekly Hours Done", f"{filt_df['Batch Wise Weekly Hours Completed'].sum():.1f} Hrs")
    with m3: modern_card("Pending Hours", f"{filt_df['Pending Hours Per Batch'].sum():.1f} Hrs", "border-red")

    m4, m5, m6 = st.columns(3)
    with m4: modern_card("Intervention Completed", f"{filt_df['Intervention Completed'].sum():,}", "border-green")
    with m5: modern_card("Pending Intervention", f"{filt_df['Pending Intervention '].sum():,}", "border-red")
    with m6: modern_card("Completion %", f"{round(filt_df['Original_Val'].mean() * 100) if not filt_df['Original_Val'].isna().all() else 0}%")

def display_filtered_table():
    st.markdown("### 📋 Assessment & Detailed Records")
    display_cols = ['University Code', 'College Name', 'Trainer name', 'Batch Size', 'Students Count', 
                    'Intervention Completed', 'Pending Intervention ', 
                    'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Completion %']
    valid_cols = [c for c in display_cols if c in filt_df.columns]
    
    st.dataframe(filt_df[valid_cols].style.format({
        'Completion %': '{:d}%', 
        'Batch Wise Weekly Hours Completed': '{:.1f}', 
        'Pending Hours Per Batch': '{:.1f}',
        'Batch Size': '{:.2f}'
    }), use_container_width=True, hide_index=True)

# 6. PAGE CONDITIONAL CONTENT
if st.session_state.page == "Home":
    # Dedicated Home Content
    display_filtered_metrics()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📈 Performance Visuals")
    c1, c2 = st.columns([2, 1])
    with c1:
        chart_data = filt_df.groupby("College Name")["Batch Wise Weekly Hours Completed"].sum().sort_values().tail(10)
        fig = px.bar(x=chart_data.values, y=chart_data.index, orientation='h', 
                     color_discrete_sequence=['#1A3C6D'], title="Top 10 Colleges by Hours")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        comp = filt_df['Intervention Completed'].sum()
        pend = filt_df['Pending Intervention '].sum()
        fig_pie = px.pie(values=[comp, pend], names=['Done', 'Pending'], title="Overall Status",
                         color=['Done', 'Pending'], color_discrete_map={'Done': '#28A745', 'Pending': '#E74C3C'})
        st.plotly_chart(fig_pie, use_container_width=True)

elif st.session_state.page == "Assessment":
    # Dedicated Assessment Page
    display_filtered_table()
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("📥 Download Filtered Assessment Data", 
                       data=filt_df.to_csv(index=False).encode('utf-8'), 
                       file_name="Assessment_Tracker.csv", 
                       use_container_width=True)