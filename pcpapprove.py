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

@st.cache_data(ttl=60)
def fetch_approvals():
    """
    Fetch records from the manual_classifications table that were updated in the last 6 hours.
    Filter for approvals and return relevant fields.
    """
    try:
        six_hours_ago = datetime.now() - timedelta(hours=100)
        six_hours_ago_str = six_hours_ago.strftime('%Y-%m-%d %H:%M:%S')

        connection = pymysql.connect(**DB_SETTINGS)
        query = f"""
            SELECT id, lender_name, business_name, snippet, classification, updated_at
            FROM manual_classifications
            WHERE classification = 'Approval' 
            AND updated_at >= '{six_hours_ago_str}'
        """
        approvals = pd.read_sql(query, connection)
        connection.close()

        return approvals
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def display_approvals():
    st.title("📩 Approvals Dashboard")



    # Input field for business_name search
    business_name_search = st.text_input("🔍 Search by Business Name:", "", help="Type part of the business name to filter results.")

    # Fetch approvals
    approvals = fetch_approvals()

       # Search button
    if st.button("Search"):
        # Save the search term to session state
        st.session_state["business_name"] = business_name_search

    # Retrieve the search term from session state
    business_name_to_search = st.session_state.get("business_name", "")

    if not approvals.empty:
        # Filter approvals by business_name if provided
        if business_name_search:
            approvals = approvals[
                approvals['business_name'].str.contains(business_name_search, case=False, na=False)
            ]

        # Display results
        if not approvals.empty:
            st.markdown(f"### Showing {len(approvals)} Approvals")

            # Highlight table
            st.dataframe(
                approvals.rename(columns={
                    'lender_name': 'Lender Name',
                    'business_name': 'Business Name',
                    'snippet': 'Email Snippet',
                    'updated_at': 'Updated At'
                }),
                use_container_width=True
            )

              # Add collapsible details grouped by Business Name
            grouped_approvals = approvals.groupby('business_name')

            # Add collapsible details
            with st.expander("📋 View Details for Each Approval"):
                for business_name, group in grouped_approvals:
                    st.markdown(f"### Business Name: {business_name}")
                    for _, row in group.iterrows():
                        st.markdown("---")
                        st.markdown(f"**Lender Name:** {row['lender_name']}")
                        st.markdown(f"**Snippet:** {row['snippet']}")
                        #st.markdown(f"**Updated At:** {row['updated_at']}")
                        st.markdown("---")
        else:
            st.info(f"No approvals found for '{business_name_search}'.")
    else:
        st.warning("⚠️ No approvals found in the last 6 hours.")

if __name__ == "__main__":
    display_approvals()
