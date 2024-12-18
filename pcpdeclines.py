import streamlit as st
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

def declines():
    try:
        six_hours_ago = datetime.now() - timedelta(hours=100)
        six_hours_ago_str = six_hours_ago.strftime('%Y-%m-%d %H:%M:%S')

        connection = pymysql.connect(**DB_SETTINGS)
        query = f"""
            SELECT id, lender_name, business_name, snippet, classification, updated_at
            FROM manual_classifications
            WHERE classification = 'Decline' 
            AND updated_at >= '{six_hours_ago_str}'
        """
        declines_df = pd.read_sql(query, connection)
        connection.close()

        return declines_df  # Return the fetched DataFrame
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def display_declines():
    """
    Display declined emails from the last 36 hours in the Streamlit app with filtering and additional decision marks.
    """
    st.title("📨 Declines")

    # Input field for business_name search
    business_name_search = st.text_input("Business Name:", "")

    # Search button
    if st.button("Search"):
        # Save the search term to session state
        st.session_state["business_name"] = business_name_search

    # Retrieve the search term from session state
    business_name_to_search = st.session_state.get("business_name", "")

    # Display message based on search input
    if business_name_to_search:
        st.write(f"### Showing Results for '{business_name_to_search}'")
    else:
        st.write("### Decision Ledger")

    # Fetch declined emails from the database
    declined_emails = declines()

    if not declined_emails.empty:
        # Apply filtering by business_name if provided
        if business_name_to_search:
            declined_emails = declined_emails[
                declined_emails['business_name'].str.contains(business_name_to_search, case=False, na=False)
            ]

        # Display results
        if not declined_emails.empty:
            st.dataframe(
                declined_emails.style.format({
                    'updated_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S'),
                }).set_table_styles([
                    {'selector': 'thead th', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold')]},
                    {'selector': 'tbody td', 'props': [('text-align', 'left'), ('font-size', '17px'), ('padding', '10px')]},
                    {'selector': 'thead', 'props': [('border-bottom', '2px solid #D9534F')]},
                ], overwrite=True),
                use_container_width=True
            )
        else:
            st.info(f"No declines found for '{business_name_to_search}'.")
    else:
        st.warning("⚠️ No declined emails found in the last 36 hours.")

if __name__ == "__main__":
    display_declines()
