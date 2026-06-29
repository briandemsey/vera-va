"""
VERA-VA: Verification Engine for Results & Accountability - Virginia
Type 4 Detection using ACCESS for ELLs Speaking vs Writing + SOL Achievement Data

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

VA_BLUE = "#002B5C"
VA_GOLD = "#C8A951"
VA_DARK = "#001a3d"
VA_RED = "#B22234"

# ============================================================================
# DATA: Virginia School Divisions with EL Populations
# ============================================================================

def load_divisions():
    """
    Load VA school divisions with significant EL populations.
    Virginia uses 3-digit FIPS codes as division IDs and calls districts 'school divisions'.
    ~145,000 ELs statewide (~10% of enrollment). Data modeled from VDOE sources.
    """
    data = [
        ("059", "Fairfax County Public Schools", 180000, 37000, 20.6, 90.2, 73.8, 71.5, 82.5, 56.2, 48.3),
        ("153", "Prince William County Public Schools", 90000, 18000, 20.0, 87.5, 70.2, 68.1, 79.8, 52.4, 45.1),
        ("107", "Loudoun County Public Schools", 83000, 10800, 13.0, 93.5, 82.1, 79.4, 88.6, 62.8, 55.7),
        ("013", "Arlington County Public Schools", 28000, 7000, 25.0, 91.8, 78.5, 75.2, 86.3, 58.9, 50.4),
        ("510", "Alexandria City Public Schools", 16000, 5600, 35.0, 83.2, 62.4, 59.8, 75.1, 44.6, 38.2),
        ("683", "Manassas City Public Schools", 7500, 2400, 32.0, 81.5, 58.7, 55.1, 72.3, 41.2, 35.8),
        ("685", "Manassas Park City Public Schools", 3400, 1156, 34.0, 79.8, 55.2, 51.8, 70.5, 38.7, 33.1),
        ("660", "Harrisonburg City Public Schools", 6200, 2046, 33.0, 82.1, 60.5, 57.2, 73.8, 43.1, 37.5),
        ("087", "Henrico County Public Schools", 51000, 5610, 11.0, 88.4, 72.5, 69.8, 80.1, 54.8, 47.2),
        ("760", "Richmond City Public Schools", 22000, 2420, 11.0, 78.5, 52.8, 48.5, 68.2, 38.4, 32.6),
        ("550", "Chesapeake City Public Schools", 40000, 2800, 7.0, 89.1, 74.2, 71.8, 82.8, 56.8, 49.5),
        ("810", "Virginia Beach City Public Schools", 63000, 3780, 6.0, 91.5, 78.8, 76.2, 85.4, 60.1, 53.2),
        ("740", "Portsmouth City Public Schools", 13000, 650, 5.0, 76.2, 48.5, 44.2, 65.8, 34.2, 28.5),
        ("680", "Lynchburg City Public Schools", 8500, 1020, 12.0, 82.8, 61.2, 58.5, 74.5, 44.8, 38.1),
        ("069", "Frederick County Public Schools", 14000, 980, 7.0, 88.2, 75.5, 73.1, 84.2, 58.2, 51.4),
    ]

    return pd.DataFrame(data, columns=[
        'fips_code', 'division_name', 'total_students',
        'el_count', 'el_percent', 'graduation_rate',
        'sol_reading_all', 'sol_math_all', 'sol_reading_white',
        'sol_reading_el', 'sol_math_el'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (modeled from VDOE EL reports)
# ============================================================================

def load_access_data(divisions_df):
    """Generate division ACCESS domain data modeled from VDOE ACCESS reporting patterns."""
    access_data = []

    for _, d in divisions_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                base_speaking = 342 + (grade * 8)
                base_writing = 292 + (grade * 6)

                # Division adjustments based on EL proficiency and density
                el_factor = d['sol_reading_el'] / 56.0  # normalize to approx state avg for ELs
                speaking_adj = int(16 * el_factor + d['el_percent'] * 0.45)
                writing_adj = int(-6 + (el_factor - 1) * 13)

                access_data.append({
                    'fips_code': d['fips_code'],
                    'division_name': d['division_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(20, int(d['el_count'] / 6)),
                    'listening_avg': base_speaking + speaking_adj - 4,
                    'speaking_avg': base_speaking + speaking_adj,
                    'reading_avg': base_writing + writing_adj + 14,
                    'writing_avg': base_writing + writing_adj,
                    'composite_avg': int((base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 19),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: SOL Achievement Data (modeled from VDOE School Quality Profiles)
# ============================================================================

def load_sol_data(divisions_df):
    """
    Generate SOL achievement data based on Virginia SOL patterns.
    SOL scores: 0-600, Pass = 400+, Advanced = 500+.
    Using pass rates modeled from VDOE School Quality Profiles.
    """
    sol_data = []

    for _, d in divisions_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['Reading', 'Math']:
                    # Base from division-level real data
                    base = d['sol_reading_all'] if subject == 'Reading' else d['sol_math_all']
                    # Grade adjustment
                    pass_rate = max(10, min(95, base + (grade - 5) * -1.3))

                    advanced = max(3, pass_rate * 0.28)
                    pass_only = pass_rate - advanced
                    fail_near = max(8, (100 - pass_rate) * 0.50)
                    fail_low = max(3, 100 - pass_rate - fail_near)

                    sol_data.append({
                        'fips_code': d['fips_code'],
                        'division_name': d['division_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'pass_rate': round(pass_rate, 1),
                        'advanced_pct': round(advanced, 1),
                        'pass_pct': round(pass_only, 1),
                        'fail_near_pass_pct': round(fail_near, 1),
                        'fail_low_pct': round(fail_low, 1),
                    })

    return pd.DataFrame(sol_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (modeled from VDOE ACCESS reports)
# ============================================================================

def load_statewide_domain_data():
    """
    Statewide ACCESS domain proficiency percentages by grade cluster.
    Virginia exit criterion: composite proficiency level 4.4.
    WIDA member since 2007. ~145,000 ELs statewide.
    """
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 44, 'speaking': 40, 'reading': 30, 'writing': 23},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 50, 'speaking': 46, 'reading': 34, 'writing': 25},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 54, 'speaking': 48, 'reading': 37, 'writing': 27},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 57, 'speaking': 50, 'reading': 40, 'writing': 29},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 42, 'speaking': 38, 'reading': 28, 'writing': 21},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 48, 'speaking': 44, 'reading': 32, 'writing': 23},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 52, 'speaking': 46, 'reading': 35, 'writing': 25},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 55, 'speaking': 48, 'reading': 38, 'writing': 27},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, fips_code, grade, year):
    filtered = access_df[
        (access_df['fips_code'] == fips_code) & (access_df['grade'] == grade) & (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'fips_code': fips_code, 'division_name': row['division_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'delta': delta, 'delta_normalized': delta_normalized, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(divisions_df):
    st.header("Virginia Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pilot Divisions", len(divisions_df))
    with col2: st.metric("Total Students", f"{divisions_df['total_students'].sum():,}")
    with col3: st.metric("English Learners", f"{divisions_df['el_count'].sum():,}")
    with col4: st.metric("Statewide Reading SOL", "74%", help="2024-25 pass rate")

    st.divider()

    st.subheader("Virginia Equity Context")
    col1, col2, col3 = st.columns(3)
    with col1: st.error("**25-30+ pt gap**\nWhite-Black SOL Achievement")
    with col2: st.error("**6th Worst**\nEL Graduation Rate Nationally")
    with col3: st.warning("**HB 1186 / SB 394**\nAI Guidance for Schools (2026)")

    st.divider()

    st.subheader("Key Virginia Facts")
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        - **131 school divisions** (called "divisions" not districts)
        - **Division ID:** 3-digit FIPS code
        - **Data system:** Virginia Longitudinal Data System (VLDS)
        - **Dashboard:** School Quality Profiles (schoolquality.virginia.gov)
        - **WIDA member since 2007** — EXIT criterion: composite 4.4
        """)
    with col2:
        st.info("""
        - **SOL:** Standards of Learning (0-600 scale, Pass=400+, Advanced=500+)
        - **~145,000 ELs** (~10% of total enrollment)
        - **Statewide:** Reading 74%, Math 72%
        - **Highest EL %:** Manassas Park (34%), Harrisonburg (33%)
        - **Largest EL division:** Fairfax County (~37,000 ELs)
        """)

    st.divider()

    st.subheader("Pilot Divisions -- Highest EL Populations")
    display = divisions_df[['fips_code', 'division_name', 'total_students', 'el_count', 'el_percent',
                            'graduation_rate', 'sol_reading_all', 'sol_math_all']].copy()
    display['el_percent'] = display['el_percent'].apply(lambda x: f"{x:.1f}%")
    display['graduation_rate'] = display['graduation_rate'].apply(lambda x: f"{x:.1f}%")
    display['sol_reading_all'] = display['sol_reading_all'].apply(lambda x: f"{x:.1f}%")
    display['sol_math_all'] = display['sol_math_all'].apply(lambda x: f"{x:.1f}%")
    display.columns = ['FIPS', 'Division', 'Students', 'EL Count', 'EL %',
                       'Grad Rate', 'Reading SOL %', 'Math SOL %']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Learner Population by Division")
    fig = px.bar(
        divisions_df.sort_values('el_count', ascending=True),
        x='el_count', y='division_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, VA_BLUE]],
        labels={'el_count': 'English Learners', 'division_name': 'Division', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** VDOE ACCESS for ELLs reporting. Virginia is a WIDA Consortium member (since 2007).
    Domain proficiency percentages show the systemic oral-written delta: Speaking consistently
    outperforms Writing across all grade clusters. Virginia uses a **composite 4.4 exit criterion**.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', VA_BLUE), ('speaking', VA_GOLD), ('reading', '#888'), ('writing', VA_RED)]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 70])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[VA_RED if d > 18 else VA_GOLD for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")


def render_access_analysis(access_df, divisions_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains: Listening, Speaking, Reading, Writing.
    Virginia has been a WIDA member since **2007**. Exit criterion: **composite proficiency level 4.4**.
    ~145,000 ELs statewide (~10% of enrollment).
    """)

    col1, col2, col3 = st.columns(3)
    with col1: division = st.selectbox("Division", divisions_df['division_name'].tolist(), key="acc_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="acc_y")

    fips = divisions_df[divisions_df['division_name'] == division]['fips_code'].values[0]
    filtered = access_df[(access_df['fips_code'] == fips) & (access_df['grade'] == grade) & (access_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(x=domains, y=scores, marker_color=[VA_BLUE, VA_GOLD, '#888', VA_RED],
                               text=[f"{s:.0f}" for s in scores], textposition='outside'))
        fig.update_layout(title=f"ACCESS Domains -- {division} -- Grade {grade} ({year})",
                         yaxis_title="Scale Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        st.subheader("Oral vs Written Gap")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average", f"{oral:.0f}")
        with col2: st.metric("Written Average", f"{written:.0f}")
        with col3: st.metric("Gap", f"{gap:+.0f}", delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")


def render_type4(access_df, divisions_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score. Flag threshold: normalized delta > 8 points.

    In Virginia, the ACCESS composite weighting (Reading 35%, Writing 35%, Speaking 15%, Listening 15%)
    means writing deficiency heavily drags down composite scores, potentially keeping students
    classified as EL long past oral fluency.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: division = st.selectbox("Division", divisions_df['division_name'].tolist(), key="t4_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    fips = divisions_df[divisions_df['division_name'] == division]['fips_code'].values[0]
    result = compute_type4_analysis(access_df, fips, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2: st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3: st.metric("Delta", f"{result['delta']:+.0f}")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']], marker_color=VA_GOLD))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']], marker_color=VA_BLUE))
        fig.update_layout(title=f"Speaking vs Writing -- {division} -- Grade {grade}", barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        st.subheader(f"All Grades -- {division} ({year})")
        all_data = [compute_type4_analysis(access_df, fips, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                                     mode='lines+markers', line=dict(color=VA_GOLD, width=3)))
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                                     mode='lines+markers', line=dict(color=VA_BLUE, width=3)))
            fig.update_layout(title="Speaking vs Writing Across Grades", xaxis_title="Grade",
                             yaxis_title="Scale Score", height=400)
            st.plotly_chart(fig, use_container_width=True)


def render_achievement_gaps(divisions_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **SOL proficiency by subgroup** across pilot divisions. Virginia's White-Black achievement gap
    ranges **25-30+ points** on SOL assessments. EL graduation rate ranks **6th worst nationally**.
    """)

    st.divider()

    fig = go.Figure()
    sorted_df = divisions_df.sort_values('sol_reading_all', ascending=True)
    for col, name, color in [
        ('sol_reading_white', 'White', '#666'),
        ('sol_reading_all', 'All Students', VA_BLUE),
        ('sol_reading_el', 'English Learners', VA_GOLD),
        ('sol_math_el', 'EL Math', VA_RED),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['division_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="SOL Pass Rates by Subgroup -- Reading & Math",
        barmode='group', xaxis_title="% Pass", height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("White-EL Reading Gap by Division")
    divisions_df_copy = divisions_df.copy()
    divisions_df_copy['gap'] = divisions_df_copy['sol_reading_white'] - divisions_df_copy['sol_reading_el']
    sorted_gap = divisions_df_copy.sort_values('gap', ascending=True)
    colors = [VA_RED if g > 30 else VA_GOLD if g > 20 else VA_BLUE for g in sorted_gap['gap']]
    fig2 = go.Figure(go.Bar(
        x=sorted_gap['gap'], y=sorted_gap['division_name'],
        orientation='h', marker_color=colors,
        text=[f"{g:.0f} pts" for g in sorted_gap['gap']], textposition='outside'
    ))
    fig2.update_layout(title="White-EL Reading SOL Gap", xaxis_title="Gap (percentage points)", height=550)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("EL Reading SOL vs Division Overall")
    fig3 = px.scatter(
        divisions_df, x='sol_reading_all', y='sol_reading_el', size='el_count',
        color='el_percent', color_continuous_scale=[[0, '#ccc'], [1, VA_BLUE]],
        hover_name='division_name',
        labels={'sol_reading_all': 'All Students Reading %', 'sol_reading_el': 'EL Reading %',
                'el_count': 'EL Count', 'el_percent': 'EL %'}
    )
    fig3.add_shape(type="line", x0=30, y0=30, x1=95, y1=95, line=dict(dash="dash", color="gray"))
    fig3.update_layout(title="EL vs Overall Reading SOL -- Gap Visualization", height=450)
    st.plotly_chart(fig3, use_container_width=True)


def render_sol(sol_df, divisions_df):
    st.header("SOL Assessment Analysis")
    st.markdown("""
    **Standards of Learning (SOL)** -- Virginia's academic assessment system.
    Score range: **0-600**. Pass: **400+**. Advanced: **500+**.
    Reading pass rate statewide: **74%**. Math: **72%**.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1: division = st.selectbox("Division", divisions_df['division_name'].tolist(), key="sol_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="sol_g")
    with col3: subject = st.selectbox("Subject", ['Reading', 'Math'], key="sol_s")
    with col4: year = st.selectbox("Year", [2025, 2024], key="sol_y")

    fips = divisions_df[divisions_df['division_name'] == division]['fips_code'].values[0]
    filtered = sol_df[(sol_df['fips_code'] == fips) & (sol_df['grade'] == grade) &
                      (sol_df['subject'] == subject) & (sol_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Fail/Low", f"{row['fail_low_pct']:.1f}%")
        with col2: st.metric("Fail/Near Pass", f"{row['fail_near_pass_pct']:.1f}%")
        with col3: st.metric("Pass", f"{row['pass_pct']:.1f}%")
        with col4: st.metric("Advanced", f"{row['advanced_pct']:.1f}%")

        levels = ['Fail/Low', 'Fail/Near Pass', 'Pass', 'Advanced']
        values = [row['fail_low_pct'], row['fail_near_pass_pct'], row['pass_pct'], row['advanced_pct']]
        colors = [VA_RED, '#f57c00', VA_GOLD, VA_BLUE]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"SOL {subject} -- {division} -- Grade {grade} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Pass Rate", f"{row['pass_rate']:.1f}%",
                  help="Pass + Advanced combined (SOL score 400+)")

        # Cross-grade comparison
        st.subheader(f"SOL {subject} Pass Rate Across Grades -- {division} ({year})")
        all_grades = sol_df[(sol_df['fips_code'] == fips) & (sol_df['subject'] == subject) & (sol_df['year'] == year)]
        if not all_grades.empty:
            fig2 = go.Figure(go.Bar(
                x=all_grades['grade'], y=all_grades['pass_rate'],
                marker_color=VA_BLUE,
                text=[f"{v:.0f}%" for v in all_grades['pass_rate']], textposition='outside'
            ))
            fig2.update_layout(
                xaxis_title="Grade", yaxis_title="Pass Rate %",
                height=350, yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig2, use_container_width=True)


def render_export(access_df, sol_df, divisions_df, domain_df):
    st.header("Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button("Download ACCESS CSV", access_df.to_csv(index=False),
                          "vera_va_access.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("SOL Data")
        st.dataframe(sol_df, use_container_width=True, hide_index=True)
        st.download_button("Download SOL CSV", sol_df.to_csv(index=False),
                          "vera_va_sol.csv", "text/csv", use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Division Summary")
        st.dataframe(divisions_df, use_container_width=True, hide_index=True)
        st.download_button("Download Divisions CSV", divisions_df.to_csv(index=False),
                          "vera_va_divisions.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button("Download Domain CSV", domain_df.to_csv(index=False),
                          "vera_va_domains.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-VA | Virginia Type 4 Detection", page_icon="🏛️", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {VA_BLUE}; }}
        .stButton > button {{ background-color: {VA_BLUE}; color: white; }}
        .stButton > button:hover {{ background-color: {VA_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    divisions_df = load_divisions()
    access_df = load_access_data(divisions_df)
    sol_df = load_sol_data(divisions_df)
    domain_df = load_statewide_domain_data()

    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {VA_BLUE}; margin: 0;">VERA-VA</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Virginia Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "SOL Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - VDOE School Quality Profiles
    - Virginia Longitudinal Data System
    - Standards of Learning (SOL)

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points
    - EXIT criterion: composite 4.4

    **Key Context:**
    - ~145,000 ELs (~10%)
    - 131 school divisions
    - HB 1186/SB 394 AI guidance (2026)
    - White-Black gap: 25-30+ pts
    - EL grad rate: 6th worst nationally

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(divisions_df)
    elif page == "Domain Analysis": render_domain_analysis(domain_df)
    elif page == "ACCESS Analysis": render_access_analysis(access_df, divisions_df)
    elif page == "Type 4 Detection": render_type4(access_df, divisions_df)
    elif page == "Achievement Gaps": render_achievement_gaps(divisions_df)
    elif page == "SOL Analysis": render_sol(sol_df, divisions_df)
    elif page == "Export Data": render_export(access_df, sol_df, divisions_df, domain_df)


if __name__ == "__main__":
    main()
