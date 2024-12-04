import streamlit as st
import database
import langchain_helpers
import docx
from urllib.parse import urlparse

def read_file_content(file):
    if file.name.endswith('.txt'):
        return file.read().decode("utf-8")
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    return ""

def extract_sub_urls(url):
    # Function to extract sub-URLs (implement the logic to find sub-URLs)
    return [url]  # Placeholder: Implement actual extraction logic

# Initialize databases
database.init_urls_db()
database.init_files_db()

st.title("Train The Websites")

company_name = st.text_input("Enter the Name of the Company")

# Website URL Training
new_website_url = st.text_input("Enter website URL for training", key="website_url")
url_message_placeholder = st.empty()  # Placeholder for the URL message

# File Upload Training
uploaded_file = st.file_uploader("Upload a text or docx file for training", type=["txt", "docx"])
file_message_placeholder = st.empty()  # Placeholder for the file upload message

# Frequently Asked Questions File Upload
faq_file = st.file_uploader("Upload a text or docx file for Frequently Asked Questions", type=["txt", "docx"])
faq_message_placeholder = st.empty()  # Placeholder for the FAQ file upload message

# Training Button
if st.button("Process"):
    all_processed = True

    if company_name:
        if new_website_url:
            # Process the website and store its information
            sub_urls = extract_sub_urls(new_website_url)
            for url in sub_urls:
                database.store_url(url, company_name)

                # Initialize the database for the new URL
                db_name = database.get_db_name_from_url(url)
                database.init_db(db_name)

                # Train the vector store with the new website content
                try:
                    langchain_helpers.process_website(url)
                    url_message_placeholder.success(f"Website {company_name} trained successfully for URL {url}.")
                    print(f"Website {url} for {company_name} stored in Chroma DB successfully.")
                except Exception as e:
                    url_message_placeholder.error(f"Failed to train website: {e}")
                    print(f"Failed to train website {url} for {company_name}: {e}")
                    all_processed = False

        if uploaded_file:
            # Process the uploaded file
            file_content = read_file_content(uploaded_file)
            database.store_file(uploaded_file.name, file_content, company_name)

            # Initialize the database for the new file
            db_name_file = database.get_db_name_from_file(uploaded_file.name)
            database.init_db(db_name_file)

            # Train the vector store with the file content
            try:
                langchain_helpers.process_text_file(file_content)
                file_message_placeholder.success(f"File {uploaded_file.name} trained successfully.")
                print(f"File {uploaded_file.name} for {company_name} stored in Chroma DB successfully.")
            except Exception as e:
                file_message_placeholder.error(f"Failed to train file: {e}")
                print(f"Failed to train file {uploaded_file.name} for {company_name}: {e}")
                all_processed = False

        if faq_file:
            # Process the uploaded FAQ file
            faq_content = read_file_content(faq_file)
            database.store_file(faq_file.name, faq_content, company_name)

            # Initialize the database for the new FAQ file
            db_name_faq = database.get_db_name_from_file(faq_file.name)
            database.init_db(db_name_faq)

            # Train the vector store with the FAQ file content
            try:
                langchain_helpers.process_text_file(faq_content)
                faq_message_placeholder.success(f"File {faq_file.name} for FAQs trained successfully.")
                print(f"FAQ file {faq_file.name} for {company_name} stored in Chroma DB successfully.")
            except Exception as e:
                faq_message_placeholder.error(f"Failed to train FAQ file: {e}")
                print(f"Failed to train FAQ file {faq_file.name} for {company_name}: {e}")
                all_processed = False

        if not new_website_url and not uploaded_file and not faq_file:
            st.write("Please enter a valid website URL or upload a text or docx file.")
    else:
        st.write("Please enter the name of the company.")

    if all_processed:
        st.success("All selected data has been processed and stored successfully.")
    else:
        st.warning("Some items were not processed successfully. Please check the error messages.")



























