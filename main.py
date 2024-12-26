import streamlit as st
from submissions import display_submissions
from pcpapprove import display_approvals
from pcpdeclines import display_declines
import pandas as pd
import pymysql
from datetime import datetime, timedelta

# Database settings
DB_SETTINGS = {
    'host': 'pcp-server-1',
    'user': 'maheedharraogovada',
    'password': 'Password123!',
    'database': 'test_db',
}

@st.cache_data(ttl=60)
def fetch_all_decisions():
    """
    Fetch all records from the manual_classifications table inserted in the last 6 hours,
    and classify them as Approved, Declined, or Other based on the classification column.
    """
    try:
        # Calculate the timestamp for 6 hours ago
        six_hours_ago = datetime.now() - timedelta(hours=100)
        six_hours_ago_str = six_hours_ago.strftime('%Y-%m-%d %H:%M:%S')

        # Connect to the database
        connection = pymysql.connect(**DB_SETTINGS)

        # Query the manual_classifications table (using updated_at instead of created_at)
        query = f"""
            SELECT id, lender_name, business_name, snippet, classification, updated_at
            FROM manual_classifications
            WHERE updated_at >= '{six_hours_ago_str}'
        """
        data = pd.read_sql(query, connection)
        connection.close()

        # Map classifications to decisions
        classification_map = {
            'approval': "✅ Approved",
            'decline': "❌ Declined"
        }

        # Apply the mapping, and fallback to "Other" for unrecognized classifications
        data['Decision'] = data['classification'].apply(
            lambda x: classification_map.get(x.lower(), "🔍 Other")
        )
       
        # Add snippet column based on decision
        data['Snippet'] = data.apply(
            lambda row: row['snippet'] if row['Decision'] in ['✅ Approved', '❌ Declined'] else None,
            axis=1
        )


        return data

    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def display_home():
    """
    Display a decision tree on the home page based on the recent emails, grouped by business name.
    """
    st.title("📊 Home - Decision Overview")

    # Add a calendar filter with a maximum date set to today
    selected_date = st.date_input(
        "📅 Submitted On ",
        value=datetime.now().date(),
        max_value=datetime.now().date(),  # Disable dates greater than today
    )

    # Fetch decision data
    decisions = fetch_all_decisions()

    if not decisions.empty:
        # Filter decisions based on the selected date
        decisions['created_at_date'] = pd.to_datetime(decisions['updated_at']).dt.date
        filtered_decisions = decisions[decisions['created_at_date'] == selected_date]

        if not filtered_decisions.empty:
            st.write(f"#### Decision Tree Overview ")

            # Normalize business names to handle duplicates due to minor differences
            filtered_decisions['normalized_business_name'] = filtered_decisions['business_name'].str.strip().str.replace(r'[^\w\s]', '').str.lower()

            # Group decisions by normalized business name
            grouped_by_business = filtered_decisions.groupby('normalized_business_name')

            for normalized_name, group in grouped_by_business:
                # Use the original business name of the first entry in the group for display
                display_name = group['business_name'].iloc[0]
                with st.expander(f"📂 {display_name}"):
                    for _, row in group.iterrows():
                        st.write(f"📌 **Lender Name**: {row['lender_name']}")
                        st.write(f"📝 **Decision**: {row['Decision']}")
        else:
            st.warning(f"⚠️ No decisions found for the selected date: {selected_date}.")
    else:
        st.warning("⚠️ No recent decisions found in the last 6 hours.")



def main():
    st.sidebar.image("croc.png", width=80)
    st.sidebar.title("CROC Dashboard")

    if "page" not in st.session_state:
        st.session_state.page = "home"  # Default page

    # Sidebar buttons
    home_button = st.sidebar.button("Home")
    submissions_button = st.sidebar.button("Submissions")
    Requestedinfo_button = st.sidebar.button("Requested Information")
    approvals_button = st.sidebar.button("Approvals")
    declines_button = st.sidebar.button("Declines")

    # Custom CSS for uniform button sizes
    st.markdown("""
    <style>
        /* Center the sidebar title */
        .css-1n76vyd {
            text-align: center;
        }

        /* Center the sidebar image */
        .css-1lcbqj6 {
            display: flex;
            justify-content: center;
            padding-top: 15px;
        }
        /* Ensure the sidebar image is properly displayed */
        .css-1lcbqj6 {
            padding-top: 15px;
        }

        /* Targeting button styles for uniform size */
        .css-1aumxhk, .stButton, .stButton>button {
            width: 80%;
            padding: 15px;
            font-size: 16px;
            text-align: center;
        }

        /* Style buttons specifically in the sidebar */
        .css-1n76vyd {
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Button actions
    if home_button:
        st.session_state.page = "home"
    elif submissions_button:
        st.session_state.page = "submissions"
    elif submissions_button:
        st.session_state.page = "Requested Information"
    elif approvals_button:
        st.session_state.page = "approvals"
    elif declines_button:
        st.session_state.page = "declines"

    # Display the content based on the selected page
    if st.session_state.page == "home":
        st.title("Welcome to  CROC! ")
        #st.write("Let's Go!!")
        display_home()
    elif st.session_state.page == "submissions":
        display_submissions()
    elif st.session_state.page == "approvals":
        display_approvals()
    elif st.session_state.page == "declines":
        display_declines()

if __name__ == "__main__":
    main()
