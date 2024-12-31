import streamlit as st
import mysql.connector
import pandas as pd

# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="pcp-server-1",
        user="maheedharraogovada",
        password="Password123!",
        database="test_db"
    )

# Fetch Data from MySQL Database
def fetch_data():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM deal_tracker"
    cursor.execute(query)
    data = cursor.fetchall()
    connection.close()
    return pd.DataFrame(data)

# Streamlit App
st.title("MySQL Data Viewer")

# Button to Fetch Data
if st.button("Fetch Data"):
    try:
        df = fetch_data()
        if not df.empty:
            st.success("Data fetched successfully!")
            st.dataframe(df)
        else:
            st.warning("No data found in the table.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# Instructions for Hosting on GitHub
"""
### Hosting Instructions:
1. Install the required libraries: `pip install streamlit mysql-connector-python pandas`
2. Save this file as `app.py`.
3. Run the app locally using: `streamlit run app.py`.
4. Push the code to GitHub following these steps:
   - Initialize a Git repository (`git init`).
   - Add the files to the repository (`git add .`).
   - Commit the changes (`git commit -m "Initial commit"`).
   - Push the repository to GitHub (`git remote add origin <your-repo-url>` and `git push -u origin main`).
5. Use Streamlit sharing or deploy the app to platforms like Streamlit Community Cloud, Heroku, or AWS.
"""
