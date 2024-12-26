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

# Database connection function
def get_db_connection():
    return pymysql.connect(**DB_SETTINGS)

# Fetch classified records from the database
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def fetch_classified_records():
    try:
        with get_db_connection() as connection:
            query = """
            SELECT id, lender_name, business_name, snippet, classification, created_at
            FROM processed_emails
            ORDER BY created_at DESC
            LIMIT 60
            """
            records = pd.read_sql(query, connection)
        return records
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Update the manual classifications table
def update_manual_classification(record_id, new_classification):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch business_name, lender_name, and snippet (if not already in scope)
        query_fetch = "SELECT business_name, lender_name, snippet FROM processed_emails WHERE id = %s"
        cursor.execute(query_fetch, (record_id,))
        result = cursor.fetchone()
        if not result:
            st.error(f"Record ID {record_id} not found.")
            return

        business_name, lender_name, snippet = result

        # Insert or update the manual classification
        query = """
        INSERT INTO manual_classifications (id, business_name, lender_name, snippet, classification, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE classification = VALUES(classification), updated_at = NOW(), snippet = VALUES(snippet)
        """
        cursor.execute(query, (record_id, business_name, lender_name, snippet, new_classification))
        connection.commit()
    except pymysql.MySQLError as e:
        st.error(f"Failed to update classification: {e}")
    finally:
        connection.close()

# Display records with manual adjustment options
def display_records_with_manual_adjustments():
    st.title("Manual Email Classification Adjustments")

    # Fetch classified records
    records = fetch_classified_records()
    if records.empty:
        st.warning("No records found.")
        return

    # Search by Business Name
    search_term = st.text_input("Search by Business Name", value="")
    if search_term:
        records = records[records["business_name"].str.contains(search_term, case=False, na=False)]

    # Show records with buttons for manual adjustments
    if records.empty:
        st.warning("No matching records found.")
    else:
        for _, row in records.iterrows():
            record_id = row["id"]
            lender_name = row["lender_name"]
            business_name = row["business_name"]
            snippet = row["snippet"]
            created_at = row["created_at"]

            st.write(f"**Lender Name:** {lender_name}")
            st.write(f"**Business Name:** {business_name}")
            st.write(f"**Snippet:** {snippet}")
            st.write(f"**Created at:** {created_at}")

            if st.button(f"Move {record_id} to Decline", key=f"decline_{record_id}"):
                update_manual_classification(record_id, "Decline")
                st.success(f"Record {record_id} moved to Decline.")

            if st.button(f"Move {record_id} to Approval", key=f"approval_{record_id}"):
                update_manual_classification(record_id, "Approval")
                st.success(f"Record {record_id} moved to Approval.")

            if st.button(f"Move {record_id} to Review", key=f"review_{record_id}"):
                update_manual_classification(record_id, "Other")
                st.success(f"Record {record_id} moved to Review.")

            st.markdown("---")  # Add a horizontal line between records

    # Auto-refresh every 5 minutes
    st.write("\nRefreshing data every 5 minutes...")
    time.sleep(300)
 

# Main function
if __name__ == "__main__":
    display_records_with_manual_adjustments()
