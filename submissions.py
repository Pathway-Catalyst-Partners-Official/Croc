import streamlit as st
import pandas as pd
import pymysql
import time

# Database settings
DB_SETTINGS = {
    'host': 'pcp-server-1',
    'user': 'maheedharraogovada',
    'password': 'Password123!',
    'database': 'test_db',
}

def fetch_submissions():
    """
    Fetch the latest submissions from the database.
    Returns a DataFrame containing submissions.
    """
    try:
        connection = pymysql.connect(**DB_SETTINGS)
        query = "SELECT * FROM test_deal ORDER BY dealid DESC LIMIT 25"
        submissions = pd.read_sql(query, connection)
        connection.close()
        return submissions
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def fetch_submission_by_input(business_name=None, deal_id=None):
    """
    Fetch submissions from the database based on business name and/or deal ID.
    Returns a DataFrame containing the matched submission.
    """
    try:
        connection = pymysql.connect(**DB_SETTINGS)
        
        # Dynamically build the query based on inputs
        query = "SELECT * FROM test_deal WHERE 1=1"
        params = []

        if business_name:
            query += " AND business_name = %s"
            params.append(business_name)
        if deal_id:
            query += " AND dealid = %s"
            params.append(deal_id)

        submissions = pd.read_sql(query, connection, params=params)
        connection.close()
        return submissions
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def display_submissions():
    """
    Display submissions in the Streamlit app with real-time updates and a search feature.
    """
    st.title("📊 Submissions Dashboard")
    st.markdown("""
    Welcome to the **Submissions Dashboard**.
    
    """)

    # Create a placeholder for the submissions table
    submissions_placeholder = st.empty()

    # Input fields for business name and deal ID
    st.sidebar.title("🔍 Search Submissions")
    business_name = st.sidebar.text_input("Business Name", value="")
    deal_id = st.sidebar.text_input("Deal ID", value="")

    # Fetch data based on inputs
    if st.sidebar.button("Search"):
        if business_name or deal_id:
            search_results = fetch_submission_by_input(
                business_name=business_name if business_name else None,
                deal_id=deal_id if deal_id else None,
            )
            if not search_results.empty:
                st.sidebar.success("✅ Submission(s) found!")
                st.dataframe(search_results, use_container_width=True)
            else:
                st.sidebar.warning("⚠️ No matching submission found.")
        else:
            st.sidebar.error("❌ Please provide at least one field (Business Name or Deal ID).")

    # Real-time updates for latest submissions
    while True:
        submissions = fetch_submissions()
        
        # Beautify and display the submissions table
        if not submissions.empty:
            with submissions_placeholder.container():
                # Display styled DataFrame
                st.dataframe(
                    submissions.style.format(na_rep="N/A"),  # Handle missing values gracefully
                    use_container_width=True,
                )
        else:
            submissions_placeholder.warning("⚠️ No submissions found or unable to fetch data.")
        
        # Refresh the table every 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    display_submissions()
