import re
import pandas as pd
import pymysql
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import streamlit as st
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import time

# Database connection settings
DB_SETTINGS = {
    'host': 'pcp-server-1',
    'user': 'maheedharraogovada',
    'password': 'Password123!',
    'database': 'test_db',
}

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Database connection function
def get_db_connection():
    """Establish and return a database connection."""
    return pymysql.connect(**DB_SETTINGS)

# Authenticate Gmail API
def authenticate_gmail():
    """Authenticate and return the Gmail API service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8081)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

# Extract lender name
def extract_lender_name(from_field):
    """Extract lender name from the 'From' field of the email."""
    if not from_field:
        return None
    
     # If 'via' is present, remove it and keep only the email address part
    if "via" in from_field:
        from_field = from_field.split(" via")[0].strip()
    match = re.search(r'<([^>]+)>', from_field)
    email = match.group(1) if match else from_field.split('<')[0].strip()
    if '@' in email:
        domain_name = email.split('@')[1]
        domain_name_base = domain_name.split('.')[0]
        return domain_name_base.lower()
    return None

# Parse subject for business name
def parse_subject_for_business_name(subject):
    """Parse the subject line to extract the business name."""
    try:
        if not subject:
            return "Unable to parse"
        # Specific condition: Approval with business name and amount
        if "Approval for $" in subject and "DBA" in subject:
            parts = subject.split(" ")
            dba_index = parts.index("DBA")
            if dba_index > 0 and dba_index + 1 < len(parts):
                return " ".join(parts[dba_index + 1:]).strip()
        if " - " in subject:
            parts = subject.split(" - ")
            if len(parts) >= 3:
                return parts[-1].strip()
        if "Congratulations! Your deal for" in subject and "has been approved" in subject:
            start = subject.find("Congratulations! Your deal for") + len("Congratulations! Your deal for")
            end = subject.find("has been approved")
            return subject[start:end].strip().strip('"')
        
        # Condition: Decline notice with "business name"
        if "Decline Notice. Unfortunately, we are not able to approve your file at this time for" in subject:
            start = subject.find("Decline Notice. Unfortunately, we are not able to approve your file at this time for") + len("Decline Notice. Unfortunately, we are not able to approve your file at this time for")
            return subject[start:].strip().strip('"')
         # Condition: "Missing Docs for 'business name'"
        if "Missing Docs for" in subject:
            start = subject.find("Missing Docs for") + len("Missing Docs for")
            return subject[start:].strip().strip('"')

        # Condition: "Decline for 'business name'"
        if "Decline for" in subject:
            start = subject.find("Decline for") + len("Decline for")
            return subject[start:].strip().strip('"')
             # Condition: "'Business name' Decline Notification: Your Application Has Been Declined"
        if "Decline Notification: Your Application Has Been Declined" in subject:
            end = subject.find(" Decline Notification: Your Application Has Been Declined")
            return subject[:end].strip().strip('"')
        if "for business name:" in subject:
            start = subject.find("for business name:") + len("for business name:")
            return subject[start:].split()[0].strip()
        if "Application for" in subject and "has been Declined" in subject:
            start = subject.find("Application for") + len("Application for")
            end = subject.find("has been Declined")
            return subject[start:end].strip()
        if "Unfortunately, we are not able to approve your file at this time for" in subject:
            start = subject.find("Unfortunately, we are not able to approve your file at this time for") + len("Unfortunately, we are not able to approve your file at this time for")
            return subject[start:].strip().strip('"')
        # Condition: "Application submission for 'business name' with ID 11111 declined"
        if "Application submission for" in subject and "with ID" in subject and "declined" in subject:
            start = subject.find("Application submission for") + len("Application submission for")
            end = subject.find("with ID")
            return subject[start:end].strip().strip('"')
          # Condition: "FNX - Application # 372080 for 'business name:' Declined"
        if "FNX - Application" in subject and "for" in subject and "Declined" in subject:
            start = subject.find("for") + len("for")
            end = subject.find("Declined")
            return subject[start:end].strip().strip('"')
          # Condition: Congratulations! SFC is considering an offer for 'business name'
        if "SFC is considering an offer for" in subject:
            start = subject.find("SFC is considering an offer for") + len("SFC is considering an offer for")
            return subject[start:].strip().strip('"')
        if "Your deal for" in subject and "has Missing Information" in subject:
            start = subject.find("Your deal for") + len("Your deal for")
            end = subject.find("has Missing Information")
            return subject[start:end].strip()
        if "Your deal for" in subject and "has been Approved" in subject:
            start = subject.find("Your deal for") + len("Your deal for")
            end = subject.find("has been Approved")
            return subject[start:end].strip()
     
        

        if "Submission Declined for" in subject:
            start = subject.find("Submission Declined for") + len("Submission Declined for")
            end = subject.find(" - ", start)
            return subject[start:end].strip() if end != -1 else subject[start:].strip()
        if "New sub -(Pathway Catalyst)" in subject:
            start = subject.find("New sub -(Pathway Catalyst)") + len("New sub -(Pathway Catalyst)")
            return subject[start:].strip()
        return "Unable to parse"
    except Exception:
        return "Unable to parse"

# Check matches in the database using fuzzy matching
def check_matches_in_db(lender_name, business_name):
    """Check for fuzzy matches with lender names and business names in the test_deal table."""
    try:
        connection = get_db_connection()
        query = "SELECT lender_names, business_name FROM test_deal"
        df = pd.read_sql(query, connection)

        # Initialize match flags
        lender_match = False
        business_match = False

        if lender_name:
            df['lender_score'] = df['lender_names'].apply(
                lambda x: fuzz.partial_ratio(lender_name.lower(), x.lower()) if isinstance(x, str) else 0
            )
            lender_match = df['lender_score'].max() > 80

        if business_name and business_name != "Unable to parse":
            df['business_score'] = df['business_name'].apply(
                lambda x: fuzz.partial_ratio(business_name.lower(), x.lower()) if isinstance(x, str) else 0
            )
            business_match = df['business_score'].max() > 80

        return lender_match, business_match
    except pymysql.MySQLError as e:
        st.error(f"Database query failed: {e}")
        return False, False
    finally:
        connection.close()

# Insert processed emails into the database
def insert_into_processed_emails(email_df):
    """Insert processed emails into the `processed_emails` table."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS processed_emails (
            id VARCHAR(255) PRIMARY KEY,
            lender_name VARCHAR(255),
            subject VARCHAR(255),
            business_name VARCHAR(255),
            snippet TEXT,
            classification VARCHAR(50) DEFAULT 'Uncategorized',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)

        for _, row in email_df.iterrows():
            insert_query = """
                INSERT INTO processed_emails (id, lender_name, subject, business_name, snippet, classification)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    lender_name = VALUES(lender_name),
                    subject = VALUES(subject),
                    business_name = VALUES(business_name),
                    snippet = VALUES(snippet),
                    classification = VALUES(classification)
            """
            cursor.execute(insert_query, (
                row['id'], row['lender_name_extracted'], row['subject'],
                row['business_name_extracted'], row['snippet'], row['classification']
            ))
        connection.commit()
    except pymysql.MySQLError as e:
        st.error(f"Database operation failed: {e}")
    finally:
        connection.close()

# Main application
def main():
    st.title("Submissions and Email Replies Parser")

    # Authenticate Gmail API outside the loop
    gmail_service = authenticate_gmail()

    while True:
        st.info("Fetching emails...")

        try:
            # Fetch emails and process them
            results = gmail_service.users().messages().list(userId='me', labelIds=['INBOX'], q="").execute()
            messages = results.get('messages', [])
            email_data = []

            for msg in messages:
                msg_data = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
                subject = next((header['value'] for header in msg_data['payload']['headers'] if header['name'] == 'Subject'), None)
                from_header = next((header['value'] for header in msg_data['payload']['headers'] if header['name'] == 'From'), None)

                lender_name = extract_lender_name(from_header)
                business_name = parse_subject_for_business_name(subject)
                lender_match, business_match = check_matches_in_db(lender_name, business_name)

                email_data.append({
                    'id': msg_data['id'],
                    'subject': subject,
                    'from': from_header,
                    'lender_name_extracted': lender_name,
                    'business_name_extracted': business_name,
                    'lender_match': lender_match,
                    'business_match': business_match,
                    'snippet': msg_data['snippet'],
                    'classification': 'Matched' if lender_match and business_match else 'Unmatched'
                })

            email_df = pd.DataFrame(email_data)
            insert_into_processed_emails(email_df)

            st.write("### Processed Emails")
            st.dataframe(email_df)

        except Exception as e:
            st.error(f"Error processing emails: {e}")

        # Wait for 5 minutes
        time.sleep(300)
        st.rerun()

if __name__ == "__main__":
    main()
