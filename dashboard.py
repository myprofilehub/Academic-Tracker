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
    
    /* KPI Card Styling */
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

    /* Active Trainer Banner */
    .active-trainer-box {
        font-size: 20px; font-weight: bold; 
        text-align: center; padding: 15px; border-radius: 8px;
        background-color: #FFFFFF; border: 1px solid #DDDDDD;
        margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        line-height: 1.6;
    }

    /* --- GLOBAL BUTTON STYLING --- */
    div.stButton > button {
        background-color: #1A3C6D;
        color: white;
        border-radius: 8px;
        height: 3.5em;
        width: 100%;
        font-weight: 500;
        border: none;
        transition: background-color 0.3s ease, color 0.3s ease, font-weight 0.1s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    div.stButton > button:hover {
        background-color: #F39C12 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        border: 1.5px solid #000000;
    }
    /* --- DOWNLOAD BUTTON STYLING (GREEN) --- */
    div.stDownloadButton > button {
        background-color: #28A745;  /* Green */
        color: white;
        border-radius: 8px;
        height: 3.5em;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    div.stDownloadButton > button:hover {
        background-color: #28A745;  /* Dark green */
        color: white !important;    /* Black text */
        font-weight: 800 !important; /* Bold text */
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

def modern_card(label, value, border_style="border-blue"):
    card_html = f"<div class='card-container {border_style}'><div class='card-title'>{label}</div><div class='card-value'>{value}</div></div>"
    return st.markdown(card_html, unsafe_allow_html=True)

# 2. DATA ENGINE
XLSX_LINK = "https://sheet.zohopublic.in/sheet/published/ydgt683ffbc94742d42859985572cd73c80c7?download=xlsx"

@st.cache_data(ttl=1)
def load_and_clean_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(XLSX_LINK, headers=headers)
    response.raise_for_status() 
    excel_file = io.BytesIO(response.content)
    
    tracker = pd.read_excel(excel_file, sheet_name='Intervention Tracker', skiprows=4)
    summary = pd.read_excel(excel_file, sheet_name='Summary')

    structural_cols = ['University Code', 'College Name', 'Trainer name', 'Batch No', 'Start Date', 'End Date', 'Timing']
    existing_struct = [c for c in structural_cols if c in tracker.columns]
    tracker[existing_struct] = tracker[existing_struct].ffill()

    tracker = tracker[~tracker['College Name'].astype(str).str.contains('Total|Grand', case=False, na=False)]
    
    cols_to_fix = [
        'Students Count', 'Intervention Completed', 'Pending Intervention ',
        'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Batch No'
    ]
    
    for col in cols_to_fix:
        if col in tracker.columns:
            tracker[col] = pd.to_numeric(tracker[col], errors='coerce').fillna(0)
            if 'Hours' not in col and 'Percentage' not in col and 'Batch No' not in col:
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

# 3. PAGE STATE & RESET LOGIC
if 'page' not in st.session_state: 
    st.session_state.page = "Home"

if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

def reset_filters():
    st.session_state.reset_counter += 1
    # st.rerun() is optional here as the state change triggers a refresh

# 4. MAIN INTERFACE HEADER
head_left, head_center, head_right = st.columns([1, 4, 1])
with head_left: st.image("NM_Logo.png", use_container_width=True)
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
with head_right: st.image("HL_Logo.png", use_container_width=True)

st.markdown("<hr style='border: 1.5px solid #1A3C6D; margin-top: 0;'>", unsafe_allow_html=True)

# --- NAVIGATION ---
nav_col1, nav_spacer, nav_col2 = st.columns([1, 4, 1])
with nav_col1:
    if st.button("🏠 Home", use_container_width=True): st.session_state.page = "Home"
with nav_col2:
    if st.button("📑 Academic Report", width='stretch'): st.session_state.page = "Academic Report"

st.markdown("<br>", unsafe_allow_html=True)

# --- GLOBAL KPI CARDS ---
k1, k2, k3, k4, k5 = st.columns(5)
with k1: modern_card("Total Enrolled", int(summary_df.iloc[0]['Enrolled Count']))
with k2: modern_card("Total Completed", int(summary_df.iloc[0]['Completed Count']), "border-green")
with k3: modern_card("In Progress", int(summary_df.iloc[0]['In Progress']))
with k4: modern_card("Not Started", int(summary_df.iloc[0]['Not Started']), "border-red")
with k5: modern_card("Course Duration", "45 Hrs", "border-blue")

# --- CASCADING FILTERS SECTION ---
st.markdown("### 🛠️ Quick Filters")
f1, f2, f3, f4 = st.columns(4)

# Use Dynamic Keys based on reset_counter
with f1: 
    u_code = st.multiselect("University Code", 
                            options=sorted(df["University Code"].unique()),
                            key=f"univ_{st.session_state.reset_counter}")

temp_df = df.copy()
if u_code: temp_df = temp_df[temp_df["University Code"].isin(u_code)]

with f2: 
    c_name = st.multiselect("College Name", 
                            options=sorted(temp_df["College Name"].unique()),
                            key=f"coll_{st.session_state.reset_counter}")

if c_name: temp_df = temp_df[temp_df["College Name"].isin(c_name)]

with f3: 
    t_name = st.multiselect("Trainer name", 
                            options=sorted(temp_df["Trainer name"].unique()),
                            key=f"train_{st.session_state.reset_counter}")

if t_name: temp_df = temp_df[temp_df["Trainer name"].isin(t_name)]

with f4: 
    b_size = st.multiselect("Batch No", 
                            options=sorted(temp_df["Batch No"].unique()),
                            key=f"batch_{st.session_state.reset_counter}")

filt_df = temp_df.copy()
if b_size: filt_df = filt_df[filt_df["Batch No"].isin(b_size)]

# Global Reset Button calling the reset function
st.markdown("<br>", unsafe_allow_html=True)
res_c1, res_c2, res_c3 = st.columns([2, 1, 2])
with res_c2:
    if st.button("🔄 Reset Filters", use_container_width=True, on_click=reset_filters):
        pass # The logic is handled in the callback

st.markdown("---")

# 5. PAGE CONDITIONAL CONTENT
if st.session_state.page == "Home":
    # --- DYNAMIC MULTI-COLOR TRAINER TEXT LOGIC ---
    trainer_uni_map = filt_df.groupby('Trainer name')['University Code'].unique()
    active_trainer_list = sorted(trainer_uni_map.index.tolist())
    total_trainers_count = len(df['Trainer name'].unique())
    
    label_html = "<span style='color: #E74C3C;'>Active Trainer: </span>"
    
    if len(active_trainer_list) == total_trainers_count:
        content_html = "<span style='color: #000000;'>All Trainers</span>"
    elif len(active_trainer_list) == 0:
        content_html = "<span style='color: #000000;'>No Data Selected</span>"
    else:
        formatted_list = []
        for trainer in active_trainer_list:
            codes = ", ".join(trainer_uni_map[trainer])
            trainer_part = f"<span style='color: #000000;'>{trainer}</span>"
            uni_part = f" <span style='color: #F39C12;'>({codes})</span>"
            formatted_list.append(trainer_part + uni_part)
        content_html = ", ".join(formatted_list)

    st.markdown(f"<div class='active-trainer-box'>{label_html} {content_html}</div>", unsafe_allow_html=True)

    if filt_df.empty:
        st.warning("No data found for the selected filters.")
    else:
        m1, m2, m3 = st.columns(3)
        with m1: modern_card("Student Count", f"{filt_df['Students Count'].sum():,}")
        with m2: modern_card("Weekly Hours Done", f"{filt_df['Batch Wise Weekly Hours Completed'].sum():.1f} Hrs")
        with m3: modern_card("Pending Hours", f"{filt_df['Pending Hours Per Batch'].sum():.1f} Hrs", "border-red")

        m4, m5, m6 = st.columns(3)
        with m4: modern_card("Intervention Completed", f"{filt_df['Intervention Completed'].sum():,}", "border-green")
        with m5: modern_card("Pending Intervention", f"{filt_df['Pending Intervention '].sum():,}", "border-red")
        with m6: modern_card("Completion %", f"{round(filt_df['Original_Val'].mean() * 100) if not filt_df['Original_Val'].isna().all() else 0}%")

    # ===============================
    # 📈 WEEK-WISE INTERVENTION COUNT TREND (FILTER AWARE)
    # ===============================

    st.markdown("### 📊 College-wise Weekly Intervention Trend")

    # Identify weekday columns (week-wise structure)
    week_cols = [col for col in filt_df.columns 
                if any(day in col for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])]

    if len(week_cols) == 0:
        st.warning("No weekday columns found for weekly trend calculation.")
    else:
        # Convert wide → long
        long_df = filt_df.melt(
            id_vars=['College Name', 'Batch No'],   # ✅ added Batch No
            value_vars=week_cols,
            var_name='Day',
            value_name='Value'
        )

        # Convert to numeric
        long_df['Value'] = pd.to_numeric(long_df['Value'], errors='coerce').fillna(0)

        # Extract week number (Monday.1 → Week 2 etc.)
        long_df['Week'] = long_df['Day'].str.extract(r'\.(\d+)')
        long_df['Week'] = long_df['Week'].fillna('0')
        long_df['Week'] = long_df['Week'].astype(int) + 1

        # Create display label: Week 1, Week 2, ...
        long_df['Week_Label'] = "Week " + long_df['Week'].astype(str)

        # COUNT interventions (value > 0 = one intervention)
        weekly_interventions = (
            long_df[long_df['Value'] > 0]
            .groupby(['College Name', 'Batch No', 'Week', 'Week_Label'])  # ✅ added Batch No
            .size()
            .reset_index(name='Intervention Count')
        )

        if weekly_interventions.empty:
            st.warning("No intervention data available for selected filters.")
        else:
            # 🔽 Horizontal filters (College | Batch)
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                college_list = sorted(weekly_interventions['College Name'].unique())
                selected_college = st.selectbox(
                "Select College",
                college_list,
                key="weekly_trend_college"
                )

            with col_f2:
                batch_list = sorted(
                weekly_interventions[
                weekly_interventions['College Name'] == selected_college
                ]['Batch No'].unique()
                )

                selected_batch = st.selectbox(
                "Select Batch No",
                batch_list,
                key="weekly_trend_batch"
                )
            trend_df = weekly_interventions[
                (weekly_interventions['College Name'] == selected_college) &
                (weekly_interventions['Batch No'] == selected_batch)
            ].sort_values("Week")

            # Plot trend with Week labels
            fig = px.line(
                trend_df,
                x='Week_Label',
                y='Intervention Count',
                markers=True,
                title=f"📈 {selected_college} (Batch {int(selected_batch)})",
            )

            fig.update_traces(
                line=dict(width=1.5, color="black"),
                marker=dict(size=9, color="#FF8C00"),
                hovertemplate="<b>%{x}</b><br>Interventions: %{y}<extra></extra>"
            )

            fig.update_layout(
                title_x=0.3,
                font=dict(size=14),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Week",
                yaxis_title="Intervention Count",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False, rangemode="tozero"),
                margin=dict(l=40, r=40, t=60, b=40),
            )

            # Force Y-axis to show only integers
            fig.update_yaxes(dtick=1)

            st.plotly_chart(fig, use_container_width=True)


        #st.markdown("<br>### 📈 Performance Visuals")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 📈 Overall Intervention Status")

            # Aggregate completed and pending per college
            college_status = (
                filt_df.groupby("College Name")[["Intervention Completed", "Pending Intervention "]]
                .sum()
                .reset_index()
            )

            # Take top 10 colleges by total interventions
            college_status["Total"] = (
                college_status["Intervention Completed"] + college_status["Pending Intervention "]
            )
            college_status = college_status.sort_values("Total", ascending=False).head(10)

            fig = px.bar(
                college_status,
                y="College Name",
                x=["Intervention Completed", "Pending Intervention "],
                orientation="h",
                title="College-wise Intervention Status",
                labels={"value": "Intervention Count", "variable": "Status"},
                color_discrete_map={
                    "Intervention Completed": "#28A745",
                    "Pending Intervention ": "#E74C3C"
                }
            )

            fig.update_layout(
                barmode="stack",
                xaxis_title="Intervention Count",
                yaxis_title="College Name",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                title_x=0.0
            )

            st.plotly_chart(fig, use_container_width=True)

        with c2:
            #comp = int(round(filt_df['Intervention Completed'].sum()))
            #pend = int(round(filt_df['Pending Intervention '].sum()))
            comp, pend = filt_df['Intervention Completed'].sum(), filt_df['Pending Intervention '].sum()
            fig_pie = px.pie(values=[comp, pend], names=['Done', 'Pending'], title="Completion Percentage (%)",
                             color=['Done', 'Pending'], color_discrete_map={'Done': '#28A745', 'Pending': '#E74C3C'})
            fig_pie.update_traces(
                texttemplate='%{percent:.0%}',   # rounds 33.5% → 34%
                hovertemplate='%{label}: %{value} (%{percent:.0%})'
            )
            fig_pie.update_layout(title_x=0.0)
            st.plotly_chart(fig_pie, use_container_width=True)

elif st.session_state.page == "Academic Report":
    #st.markdown("### 📋 College-Wise Academic Progress Report")
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### 📋 College-Wise Academic Progress Report")
    with h2:
        st.download_button(
            "Download",
            data=filt_df[['University Code', 'College Name', 'Trainer name', 'Batch No', 'Students Count',
                      'Intervention Completed', 'Pending Intervention ',
                      'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Completion %']]
                .to_csv(index=False).encode('utf-8'),
            file_name="College_Wise_Academic_Report.csv",
            mime="text/csv"
        )

    if filt_df.empty:
        st.warning("No data found for the selected filters.")
    else:
        display_cols = ['University Code', 'College Name', 'Trainer name', 'Batch No', 'Students Count', 
                        'Intervention Completed', 'Pending Intervention ', 
                        'Batch Wise Weekly Hours Completed', 'Pending Hours Per Batch', 'Completion %']
        st.dataframe(filt_df[display_cols].style.format({
            'Completion %': '{:d}%', 'Batch Wise Weekly Hours Completed': '{:.1f}', 
            'Pending Hours Per Batch': '{:.1f}', 'Batch No': '{:.2f}'
        }), use_container_width=True, hide_index=True)
        
    # ===============================
    # 📊 WEEK-WISE INTERVENTION COUNT TABLE (WITH COLLEGE FILTER)
    # ===============================
    #st.markdown("### 📈 Weekly Intervention Completed")
    h3, h4 = st.columns([4, 1])
    with h3:
        st.markdown("### 📈 Weekly Intervention Completed")
    
    week_cols = [col for col in filt_df.columns 
                 if any(day in col for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])]

    if len(week_cols) == 0:
        st.warning("No weekday columns found for weekly calculation.")
    else:
        long_df = filt_df.melt(
            id_vars=['College Name', 'Batch No'],
            value_vars=week_cols,
            var_name='Day',
            value_name='Value'
        )

        long_df['Value'] = pd.to_numeric(long_df['Value'], errors='coerce').fillna(0)

        long_df['Week'] = long_df['Day'].str.extract(r'\.(\d+)')
        long_df['Week'] = long_df['Week'].fillna('0')
        long_df['Week'] = long_df['Week'].astype(int) + 1

        long_df['Week_Label'] = "Week " + long_df['Week'].astype(str)

        weekly_interventions = (
            long_df[long_df['Value'] > 0]
            .groupby(['College Name', 'Batch No', 'Week_Label'])
            .size()
            .reset_index(name='Intervention Count')
        )

        if weekly_interventions.empty:
            st.warning("No weekly intervention data available.")
        else:
            # 🔽 College + Batch filter for Weekly Intervention Completed Table
            college_list = sorted(weekly_interventions['College Name'].unique())
            col1, col2 = st.columns(2)

            with col1:
                selected_college_table = st.selectbox(
                    "Select College for Weekly Table",
                    ["All Colleges"] + college_list,
                    key="weekly_table_college"
                )

            # Filter batch list based on college selection
            if selected_college_table != "All Colleges":
                batch_list = sorted(
                    weekly_interventions[
                        weekly_interventions['College Name'] == selected_college_table
                    ]['Batch No'].dropna().unique()
                )
            else:
                batch_list = sorted(weekly_interventions['Batch No'].dropna().unique())

            with col2:
                selected_batch_table = st.selectbox(
                    "Select Batch for Weekly Table",
                    ["All Batches"] + [str(b) for b in batch_list],
                    key="weekly_table_batch"
                )

            # Apply filters
            table_df = weekly_interventions.copy()
            if selected_college_table != "All Colleges":
                table_df = table_df[table_df['College Name'] == selected_college_table]

            if selected_batch_table != "All Batches":
                table_df = table_df[table_df['Batch No'].astype(str) == selected_batch_table]
            # -------------------
            # Move the download button to the heading row's right column
            with h4:
                st.download_button(
                    "Download",
                    data=table_df.to_csv(index=False).encode('utf-8') if 'table_df' in locals() else b"",
                    file_name="Weekly_Intervention_Report.csv",
                    mime="text/csv"
                )
            # Display table
            st.dataframe(
                table_df.sort_values(['College Name', 'Week_Label']),
                use_container_width=True,
                hide_index=True
            )
