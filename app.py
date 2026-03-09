import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title = 'School of Dandori',
    page_icon = "🌱",
    layout = 'wide'
)

# ---------- Load data ----------
@st.cache_data
def load_data():
    df = pd.read_csv("classes.csv")
    df['Cost_Numeric'] = df['Cost'].str.replace('£', '').astype(float)
    return df

df = load_data()

# ---------- Header ----------
st.title("**School of Dandori**")
if 'first_visit' not in st.session_state:
    st.balloons()
    st.session_state['first_visit'] = True

col_logo, col_title = st.columns([2, 4])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=200)
with col_title:
    st.subheader("Where grown-ups come to play!")
    st.markdown(""" #### *Dandori: The art of arranging your time, energy, and wellbeing.* """)

with st.expander("🌱 Our Story & Philosophy"):
    st.markdown("""
    **Founded in 2017**, the School of Dandori helps adults reclaim their attention from the digital world.
    We believe in **self-reclamation**, not self-improvement.

    Our evening and weekend classes are:
    * **Whimsical & Thoughtful:** Designed to help you unplug.
    * **Community-Led:** Run by vibrant freelance instructors across the UK.
    * **Radically Joyful:** A small act of rebellion against burnout.

    *Come manage your time beautifully. Come play again.*
    """)

st.divider()

# ---------- Sidebar Filters ----------
st.sidebar.header("🌿 Find Your Class")

search_query = st.sidebar.text_input("Search", placeholder="e.g. weaving, foraging...")

locations = ["All"] + sorted(df['Location'].dropna().unique().tolist())
selected_location = st.sidebar.selectbox("Location", locations)

min_price = float(df['Cost_Numeric'].min())
max_price = float(df['Cost_Numeric'].max())
price_range = st.sidebar.slider("Price Range (£)", min_value=min_price, max_value=max_price, value=(min_price, max_price))

all_skills = set()
for skills_str in df['Skills Developed'].dropna():
    for skill in skills_str.split(" | "):
        if skill.strip():
            all_skills.add(skill.strip())
selected_skills = st.sidebar.multiselect("Skills", options=sorted(all_skills), placeholder="Any skill")

instructors = ["All"] + sorted(df['Instructor'].dropna().unique().tolist())
selected_instructor = st.sidebar.selectbox("Instructor", instructors)

# ---------- Apply Filters ----------
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df['Class Name'].str.contains(search_query, case=False, na=False) |
        filtered_df['Description'].str.contains(search_query, case=False, na=False) |
        filtered_df['Skills Developed'].str.contains(search_query, case=False, na=False)
    ]

if selected_location != "All":
    filtered_df = filtered_df[filtered_df['Location'] == selected_location]

filtered_df = filtered_df[
    (filtered_df['Cost_Numeric'] >= price_range[0]) &
    (filtered_df['Cost_Numeric'] <= price_range[1])
]

if selected_skills:
    def has_skill(skills_str):
        if pd.isna(skills_str):
            return False
        course_skills = [s.strip() for s in skills_str.split(" | ")]
        return any(skill in course_skills for skill in selected_skills)
    filtered_df = filtered_df[filtered_df['Skills Developed'].apply(has_skill)]

if selected_instructor != "All":
    filtered_df = filtered_df[filtered_df['Instructor'] == selected_instructor]

# ---------- Results ----------
st.write(f"**Showing {len(filtered_df)} of {len(df)} courses**")

for index, row in filtered_df.iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(row['Class Name'])
            st.caption(f"📍 {row['Location']}  |  💰 {row['Cost']}  |  👤 {row['Instructor']}")
            if pd.notna(row['Skills Developed']):
                skills = " · ".join([s.strip() for s in row['Skills Developed'].split(" | ")])
                st.caption(f"🎯 {skills}")

        with col2:
            if st.button("More Info", key=f"btn_{index}"):
                st.session_state[f"show_{index}"] = not st.session_state.get(f"show_{index}", False)

        if st.session_state.get(f"show_{index}", False):
            st.divider()
            st.write(f"**Class ID:** {row['Class ID']}")
            st.write("**Description:**")
            st.write(row['Description'])

            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Objectives:**")
                for obj in row['Objectives'].split(" | "):
                    st.write(f"• {obj}")
            with col_b:
                st.write("**Provided Materials:**")
                for mat in row['Provided Materials'].split(" | "):
                    st.write(f"• {mat}")

