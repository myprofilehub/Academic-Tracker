import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Naan Mudhalvan Dashboard", layout="wide")

# Professional UI Styling (Standard metrics/headers)
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1A3C6D; font-weight: bold; }
    div.stButton > button { background-color: #1A3C6D; color: white; border-radius: 5px; height: 3em; }
    .header-text { text-align: center; color: #1A3C6D; }
    </style>
    """, unsafe_allow_html=True)

# 2. OFFICIAL HEADER SECTION
head_left, head_center, head_right = st.columns([1, 4, 1])
with head_left:
    st.image("NM_Logo.png", width=140)
with head_center:
    st.markdown("""
        <div class='header-text'>
            <h1 style='margin-bottom: 0; font-size: 36px;'>Academic Progress Dashboard</h1>
            <h3 style='font-weight: 400; margin-top: 0;'>Naan Mudhalvan Skill Development Initiative</h3>
            <p style='color: #666;'>Government of Tamil Nadu</p>
        </div>
    """, unsafe_allow_html=True)
with head_right:
    try:
        st.image("HL_Logo.png", width=350)
    except:
        st.warning("HL_Logo.png not found")
st.markdown("<hr style='border: 1px solid #1A3C6D; margin-top: 5px;'>", unsafe_allow_html=True)

# 3. DATA ENGINE
@st.cache_data
def load_and_clean_data():
    excel_file = 'Academic_Session_Tracker - Naan Mudhalvan.xlsx'
    tracker = pd.read_excel(excel_file, sheet_name='Intervention Tracker', skiprows=4)
    summary = pd.read_excel(excel_file, sheet_name='Summary')
    
    tracker = tracker.dropna(subset=['Sl. No', 'Trainer name'], how='all')
    structural_cols = ['University Code', 'College Name', 'Start Date', 'End Date', 'Timing']
    tracker[structural_cols] = tracker[structural_cols].ffill()
    
    cols_to_int = ['Students Count', 'Intervention Completed', 'Pending Intervention ']
    for col in cols_to_int:
        tracker[col] = pd.to_numeric(tracker[col], errors='coerce').fillna(0).round().astype(int)
    
    tracker['Original_Val'] = pd.to_numeric(tracker['Completeion Percentage'], errors='coerce').fillna(0)
    
    def get_bucket(val):
        if val < 0.20: return '0%-19%'
        elif 0.20 <= val <= 0.50: return '20%-50%'
        else: return '51%-100%'
    tracker['Progress Bucket'] = tracker['Original_Val'].apply(get_bucket)
    
    return tracker, summary

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
    if st.button("🏠 Home", use_container_width=True): st.session_state.page = "Home"
with nav2:
    if st.button("📊 Assessment Page", use_container_width=True): st.session_state.page = "Assessment"

# 5. TOP FILTERS
st.markdown("---")
f1, f2, f3, f4 = st.columns(4)
with f1: univ_sel = st.multiselect("University", options=df["University Code"].unique())
with f2: college_sel = st.multiselect("College Name", options=df["College Name"].unique())
with f3: dist_sel = st.selectbox("District", ["All Districts", "Chennai", "Coimbatore", "Madurai"])
with f4: trainer_sel = st.multiselect("Trainer Name", options=df["Trainer name"].unique())

filt_df = df.copy()
if univ_sel: filt_df = filt_df[filt_df["University Code"].isin(univ_sel)]
if college_sel: filt_df = filt_df[filt_df["College Name"].isin(college_sel)]
if trainer_sel: filt_df = filt_df[filt_df["Trainer name"].isin(trainer_sel)]

# 6. PAGE CONTENT
if st.session_state.page == "Home":
    # Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("Enrolled", int(summary_df.iloc[0]['Enrolled Count']))
    with k2: st.metric("Completed", int(summary_df.iloc[0]['Completed Count']))
    with k3: st.metric("In Progress", int(summary_df.iloc[0]['In Progress']))
    with k4: st.metric("Not Started", int(summary_df.iloc[0]['Not Started']))
    with k5: st.metric("Avg Progress", f"{filt_df['Original_Val'].mean() * 100:.0f}%")

    st.markdown("---")
    
    # ROW 1: LOLLIPOP CHART (Red with Regular Black Text)
    st.markdown("### College-wise Academic Progress")
    search_query = st.text_input("🔍 Search for a specific College:", "")
    
    chart_data = filt_df.groupby("College Name")["Original_Val"].mean().sort_values(ascending=True)
    display_data = chart_data[chart_data.index.str.contains(search_query, case=False)].tail(10) if search_query else chart_data.tail(10)

    fig_lollipop = go.Figure()
    for i, college in enumerate(display_data.index):
        fig_lollipop.add_shape(type='line', x0=0, y0=i, x1=display_data.values[i] * 100, y1=i,
                              line=dict(color='black', width=1.5))

    fig_lollipop.add_trace(go.Scatter(
        x=display_data.values * 100, y=display_data.index, mode='markers+text',
        marker=dict(color='#E74C3C', size=14),
        text=(display_data.values * 100).round(0).astype(int).astype(str) + "%",
        textposition='middle right',
        textfont=dict(color='black', size=12),
        hoverinfo='text',
        hovertext=[f"{col}: {val*100:.0f}%" for col, val in zip(display_data.index, display_data.values)]
    ))

    fig_lollipop.update_layout(
        height=500, showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title=dict(text="Completion %", font=dict(color="black", size=14)), 
                   showgrid=False, tickfont=dict(color="black")),
        yaxis=dict(showgrid=False, tickfont=dict(color="black")),
        margin=dict(l=250, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_lollipop, use_container_width=True)

    st.markdown("---")

    # ROW 2: PIE & BATCH DISTRIBUTION
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Enrollment Status Distribution")
        labels = ['Completed', 'In Progress', 'Not Started']
        values = [summary_df.iloc[0]['Completed Count'], summary_df.iloc[0]['In Progress'], summary_df.iloc[0]['Not Started']]
        colors = ['#28A745', '#3498DB', '#E74C3C']
        
        
        fig_pie = go.Figure()
        
        # 1. Pie Trace (Text inside removed)
        fig_pie.add_trace(go.Pie(
            labels=labels, values=values, marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textinfo='none', # Numbers removed from inside
            hoverinfo='label+percent+value', 
            showlegend=False
        ))

        # 2. Proxy Scatter Traces for Circular Legend (Size increased to 24)
        for label, color in zip(labels, colors):
            fig_pie.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                marker=dict(size=24, color=color, symbol='circle'), # Legend circle size 24
                legendgroup=label, showlegend=True, name=label))
        
        fig_pie.update_layout(
            height=550, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5,
                        itemsizing='constant', font=dict(size=16, color="black"), itemwidth=60),
            margin=dict(t=130, b=30, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.markdown("### Batch Distribution")
        val_counts = filt_df['Progress Bucket'].value_counts().reindex(['0%-19%', '20%-50%', '51%-100%']).fillna(0)

        fig_dist = px.bar(x=val_counts.index, y=val_counts.values, color_discrete_sequence=['#F39C12'], text_auto=True)
        fig_dist.update_layout(
            height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title=dict(text="Progress Bucket", font=dict(color="black", size=14)), 
                       showgrid=False, tickfont=dict(color="black")),
            yaxis=dict(title=dict(text="Number of Batches", font=dict(color="black", size=14)), 
                       showgrid=False, tickfont=dict(color="black")),
        )
        fig_dist.update_traces(textfont=dict(color="black", size=14))
        st.plotly_chart(fig_dist, use_container_width=True)

else:
    # ASSESSMENT PAGE
    st.subheader("Detailed Assessment Tracker")
    display_cols = ['University Code', 'College Name', 'Trainer name', 'Students Count', 
                    'Intervention Completed', 'Pending Intervention ', 'Original_Val']
    st.dataframe(
        filt_df[display_cols].rename(columns={'Original_Val': 'Completion %'}).style.format({
            'Completion %': '{:.0%}', 'Students Count': '{:d}', 
            'Intervention Completed': '{:d}', 'Pending Intervention ': '{:d}'
        }), use_container_width=True, hide_index=True
    )
    csv = filt_df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Academic Report", data=csv, file_name="Naan_Mudhalvan_Assessment.csv")