import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Naan Mudhalvan Dashboard", layout="wide")

# Professional CSS Styling
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1A3C6D; font-weight: bold; }
    div.stButton > button { background-color: #1A3C6D; color: white; border-radius: 5px; height: 3em; }
    .header-text { text-align: center; color: #1A3C6D; }
    </style>
    """, unsafe_allow_html=True)

# 2. OFFICIAL HEADER SECTION
# Layout: NM Logo (Left) | Title (Center) | Company Logo (Right)
head_left, head_center, head_right = st.columns([1, 4, 1])

with head_left:
    # Naan Mudhalvan Logo (Left)
    st.image("NM_Logo.png", width=140)

with head_center:
    # Main Title centered
    st.markdown("""
        <div class='header-text'>
            <h1 style='margin-bottom: 0; font-size: 36px;'>Academic Progress Dashboard</h1>
            <h3 style='font-weight: 400; margin-top: 0;'>Naan Mudhalvan Skill Development Initiative</h3>
            <p style='color: #666;'>Government of Tamil Nadu</p>
        </div>
    """, unsafe_allow_html=True)

with head_right:
    # Company Logo (Right) - Using local file
    try:
        st.image("HL_Logo.png", width=300)
    except:
        st.warning("company_logo.png not found")

st.markdown("<hr style='border: 1px solid #1A3C6D; margin-top: 5px;'>", unsafe_allow_html=True)

# 3. DATA ENGINE
@st.cache_data
def load_and_clean_data():
    excel_file = 'Academic_Session_Tracker - Naan Mudhalvan.xlsx'
    
    # Load Sheets
    tracker = pd.read_excel(excel_file, sheet_name='Intervention Tracker', skiprows=4)
    summary = pd.read_excel(excel_file, sheet_name='Summary')
    
    # A. REMOVE GHOST ROWS: Drop rows where Sl. No and Trainer name are missing
    tracker = tracker.dropna(subset=['Sl. No', 'Trainer name'], how='all')
    
    # B. FILL DOWN structural labels
    structural_cols = ['University Code', 'College Name', 'Start Date', 'End Date', 'Timing']
    tracker[structural_cols] = tracker[structural_cols].ffill()
    
    # C. INTEGER CONVERSION: Round and convert academic counts to whole numbers
    cols_to_int = ['Students Count', 'Intervention Completed', 'Pending Intervention ']
    for col in cols_to_int:
        tracker[col] = pd.to_numeric(tracker[col], errors='coerce').fillna(0).round().astype(int)
    
    # D. UNDERLYING DECIMAL DATA: Kept as 0.33 format for accuracy
    tracker['Original_Val'] = pd.to_numeric(tracker['Completeion Percentage'], errors='coerce').fillna(0)
    
    # E. ACADEMIC BUCKETING (Using Decimal logic)
    def get_bucket(val):
        if val < 0.20: return '0%-19%'
        elif 0.20 <= val <= 0.50: return '20%-50%'
        else: return '51%-100%'
        
    tracker['Progress Bucket'] = tracker['Original_Val'].apply(get_bucket)
    
    return tracker, summary

# Execute Data Load
try:
    df, summary_df = load_and_clean_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# 4. PAGE NAVIGATION
if 'page' not in st.session_state:
    st.session_state.page = "Home"

nav1, nav2 = st.columns(2)
with nav1:
    if st.button("🏠 Home (Visual Summary)", use_container_width=True):
        st.session_state.page = "Home"
with nav2:
    if st.button("📊 Assessment Page (Detailed Data)", use_container_width=True):
        st.session_state.page = "Assessment"

# 5. TOP FILTERS (Horizontal Header Bar)
st.markdown("---")
f1, f2, f3, f4 = st.columns(4)
with f1:
    univ_sel = st.multiselect("University", options=df["University Code"].unique())
with f2:
    college_sel = st.multiselect("College Name", options=df["College Name"].unique())
with f3:
    dist_sel = st.selectbox("District", ["All Districts", "Chennai", "Coimbatore", "Madurai"])
with f4:
    trainer_sel = st.multiselect("Trainer Name", options=df["Trainer name"].unique())

# Filtering Logic
filt_df = df.copy()
if univ_sel: filt_df = filt_df[filt_df["University Code"].isin(univ_sel)]
if college_sel: filt_df = filt_df[filt_df["College Name"].isin(college_sel)]
if trainer_sel: filt_df = filt_df[filt_df["Trainer name"].isin(trainer_sel)]

# 6. PAGE CONTENT
if st.session_state.page == "Home":
    # KPI Scorecards
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("Enrolled", int(summary_df.iloc[0]['Enrolled Count']))
    with k2: st.metric("Completed", int(summary_df.iloc[0]['Completed Count']))
    with k3: st.metric("In Progress", int(summary_df.iloc[0]['In Progress']))
    with k4: st.metric("Not Started", int(summary_df.iloc[0]['Not Started']))
    with k5: st.metric("Avg Progress", f"{filt_df['Original_Val'].mean() * 100:.0f}%")

    st.markdown("---")
    
    # Home Page Charts
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Top Colleges by Academic Progress")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        top_data = filt_df.groupby("College Name")["Original_Val"].mean().sort_values(ascending=False).head(10)
        sns.barplot(x=top_data.values * 100, y=top_data.index, palette="Blues_r", ax=ax1)
        ax1.set_xlabel("Completion %")
        st.pyplot(fig1)
        
    with c2:
        st.subheader("Batch Distribution")
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        order = ['0%-19%', '20%-50%', '51%-100%']
        sns.countplot(data=filt_df, x="Progress Bucket", order=order, color="#F39C12", ax=ax2)
        st.pyplot(fig2)

else:
    # ASSESSMENT PAGE (Detailed Table View)
    st.subheader("Detailed Assessment Tracker")
    
    # Selecting columns for display
    display_cols = [
        'University Code', 'College Name', 'Trainer name', 
        'Students Count', 'Intervention Completed', 
        'Pending Intervention ', 'Original_Val'
    ]
    
    # Formatted Dataframe Display
    st.dataframe(
        filt_df[display_cols].rename(columns={'Original_Val': 'Completion %'}).style.format({
            'Completion %': '{:.0%}',
            'Students Count': '{:d}',
            'Intervention Completed': '{:d}',
            'Pending Intervention ': '{:d}'
        }),
        use_container_width=True, hide_index=True
    )
    
    # CSV Download Button
    csv = filt_df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Academic Report", data=csv, file_name="Naan_Mudhalvan_Assessment.csv")