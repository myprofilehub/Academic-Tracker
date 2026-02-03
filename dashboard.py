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
    .card-value { font-size: 28px; font-weight: bold; color: #1A3C6D; }
    .header-text { text-align: center; color: #1A3C6D; }
    div.stButton > button { background-color: #1A3C6D; color: white; border-radius: 5px; height: 3em; }
    section[data-testid="stSidebar"] { background-color: #F1F3F6; }
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
    
    # Load sheets (skiprows=4 correctly identifies the data starting after headers)
    tracker = pd.read_excel(excel_file, sheet_name='Intervention Tracker', skiprows=4)
    summary = pd.read_excel(excel_file, sheet_name='Summary')

    # STEP 1: FORWARD FILL CATEGORICAL DATA FIRST
    # We must fill labels (Trainer, College, etc.) BEFORE dropping any rows
    # This ensures that merged trainer rows are kept and counted
    structural_cols = ['University Code', 'College Name', 'Trainer name', 'Batch Size', 'Start Date', 'End Date', 'Timing']
    existing_struct = [c for c in structural_cols if c in tracker.columns]
    tracker[existing_struct] = tracker[existing_struct].ffill()

    # STEP 2: EXCLUDE THE SUMMARY ROW (Row 83)
    # We remove the "Total" row to prevent doubling the dashboard numbers
    tracker = tracker[~tracker['College Name'].astype(str).str.contains('Total|Grand', case=False, na=False)]
    
    # Remove truly empty rows (spacer rows)
    #tracker = tracker.dropna(subset=['Sl. No'], how='all')

    # STEP 3: FILL MERGED NUMERICAL DATA WITH 0
    # Note: Using exact names with trailing spaces where they exist in the Excel file
    cols_to_fix = [
        'Students Count', 'Intervention Completed', 'Pending Intervention ',
        'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch'
    ]
    
    for col in cols_to_fix:
        if col in tracker.columns:
            # Force numeric and fill merged blanks with 0 to match Excel's consolidated logic
            tracker[col] = pd.to_numeric(tracker[col], errors='coerce').fillna(0)
            # Formatting as integers where appropriate
            if 'Hours' not in col and 'Percentage' not in col:
                tracker[col] = tracker[col].astype(int)

    # Convert selector columns to string to prevent sort errors (TypeError)
    for col in ['University Code', 'College Name', 'Trainer name']:
        if col in tracker.columns:
            tracker[col] = tracker[col].astype(str).replace('nan', 'Unknown')

    # Percentage Logic (Matches misspelled 'Completeion' in source)
    tracker['Completion Percentage'] = pd.to_numeric(tracker['Completion Percentage'], errors='coerce')  
    tracker['Original_Val'] = tracker['Completion Percentage'] 
    tracker['Completion %'] = (tracker['Original_Val'] * 100).fillna(0).astype(int)
    
    return tracker, summary

try:
    df, summary_df = load_and_clean_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 3. SIDEBAR NAVIGATION & FILTERS
if 'page' not in st.session_state: 
    st.session_state.page = "Home"

with st.sidebar:
    st.title("Control Panel")
    if st.button("🏠 Home Dashboard", use_container_width=True): st.session_state.page = "Home"
    if st.button("📊 Assessment Tracker", use_container_width=True): st.session_state.page = "Assessment"
    
    st.markdown("---")
    u_code = st.multiselect("University Code", options=sorted(df["University Code"].unique()))
    
    temp_df = df.copy()
    if u_code: temp_df = temp_df[temp_df["University Code"].isin(u_code)]
    c_name = st.multiselect("College Name", options=sorted(temp_df["College Name"].unique()))
    t_name = st.multiselect("Trainer name", options=sorted(df["Trainer name"].unique()))
    
    # Apply Filtering logic
    filt_df = df.copy()
    if u_code: filt_df = filt_df[filt_df["University Code"].isin(u_code)]
    if c_name: filt_df = filt_df[filt_df["College Name"].isin(c_name)]
    if t_name: filt_df = filt_df[filt_df["Trainer name"].isin(t_name)]
    
    st.markdown("---")
    min_weekly = st.number_input("Min Weekly Hours Completed", min_value=0.0, value=0.0, step=0.5)
    filt_df = filt_df[filt_df["Batch Wise Weekly Hours Completed"] >= min_weekly]
    
    if st.button("🔄 Reset All Filters"): st.rerun()

# 4. MAIN INTERFACE
head_left, head_center, head_right = st.columns([1, 4, 1])
with head_center:
    st.markdown("<div class='header-text'><h1 style='margin-bottom: 0;'>Academic Progress Dashboard</h1><h3>Naan Mudhalvan Skill Development Initiative</h3></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1: modern_card("Total Enrolled", int(summary_df.iloc[0]['Enrolled Count']))
with k2: modern_card("Total Completed", int(summary_df.iloc[0]['Completed Count']), "border-green")
with k3: modern_card("In Progress", int(summary_df.iloc[0]['In Progress']))
with k4: modern_card("Not Started", int(summary_df.iloc[0]['Not Started']), "border-red")

st.markdown("---")

# 5. METRICS FUNCTIONS
def display_filtered_metrics():
    st.markdown("### 🔍 Filtered Selection Summary")
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
    with m6: modern_card("Completion %", f"{round(filt_df['Original_Val'].mean() * 100)}%")

def display_filtered_table():
    st.markdown("### 📋 Detailed Records")
    # Note: Columns here match the exact Excel header names
    display_cols = ['University Code', 'College Name', 'Trainer name', 'Students Count', 
                    'Intervention Completed', 'Pending Intervention ', 
                    'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Completion %']
    valid_cols = [c for c in display_cols if c in filt_df.columns]
    st.dataframe(filt_df[valid_cols].style.format({
        'Completion %': '{:d}%', 'Batch Wise Weekly Hours Completed': '{:.1f}', 'Pending Hours Per Batch': '{:.1f}'
    }), use_container_width=True, hide_index=True)

# 6. PAGE CONDITIONAL CONTENT
if st.session_state.page == "Home":
    display_filtered_metrics()
    display_filtered_table()
    st.markdown("### 📈 Performance Visuals")
    c1, c2 = st.columns([2, 1])
    with c1:
        chart_data = filt_df.groupby("College Name")["Batch Wise Weekly Hours Completed"].sum().sort_values().tail(10)
        fig = px.bar(x=chart_data.values, y=chart_data.index, orientation='h', color_discrete_sequence=['#1A3C6D'], title="Top 10 Colleges by Hours")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        # Note the space in 'Pending Intervention '
        comp = filt_df['Intervention Completed'].sum()
        pend = filt_df['Pending Intervention '].sum()
        fig_pie = px.pie(values=[comp, pend], names=['Done', 'Pending'], 
                         color_discrete_sequence=['#28A745', '#E74C3C'], title="Overall Status")
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    display_filtered_metrics()
    display_filtered_table()
    st.download_button("📥 Download Filtered Data", data=filt_df.to_csv(index=False).encode('utf-8'), file_name="Filtered_Tracker.csv")