import streamlit as st
import database
import langchain_helpers
from langchain_core.messages import AIMessage, HumanMessage

# Initialize databases
database.init_urls_db()
database.init_files_db()

# App config
st.set_page_config(page_title="Chat with Content", page_icon="🤖")
st.title("Chat with Content")

# Initialize session state
if 'selected_company' not in st.session_state:
    st.session_state['selected_company'] = None
if 'vector_store' not in st.session_state:
    st.session_state['vector_store'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'cached_vector_stores' not in st.session_state:
    st.session_state['cached_vector_stores'] = {}

def refresh_company_names():
    """ Refresh the company names for the dropdown list. """
    st.session_state['company_names'] = database.get_company_names()

def handle_training_error(company_name):
    """ Handle errors during training or processing. """
    st.error(f"Error processing {company_name}. Please check the training status.")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Refresh company names
    if 'company_names' not in st.session_state:
        refresh_company_names()
    
    # Dropdown for Company selection
    company_names = st.session_state['company_names']
    if company_names:
        company_name = st.selectbox("Select Company", company_names, key='company_select')

        if company_name and st.session_state['selected_company'] != company_name:
            st.session_state['selected_company'] = company_name
            
            # Check if vector store is cached
            if company_name in st.session_state['cached_vector_stores']:
                st.session_state['vector_store'] = st.session_state['cached_vector_stores'][company_name]
            else:
                try:
                    website_url = database.get_url_by_company_name(company_name)
                    vector_store = langchain_helpers.get_vectorstore_from_url(website_url)
                    st.session_state['cached_vector_stores'][company_name] = vector_store
                    st.session_state['vector_store'] = vector_store
                    
                    # Retrieve and process file contents
                    file_contents = database.get_files_by_company_name(company_name)
                    combined_file_contents = "\n".join(file_contents)
                    if combined_file_contents:
                        st.session_state['vector_store'] = langchain_helpers.process_text_file(combined_file_contents)
                    
                    st.session_state['chat_history'] = [
                        AIMessage(content=f"Hello, I am a bot for {company_name}. How can I help you?")
                    ]
                except Exception as e:
                    handle_training_error(company_name)
                    st.session_state['vector_store'] = None
                    st.session_state['chat_history'] = []

        # Option to delete selected company
        if st.button("Delete Selected Company"):
            if company_name:
                try:
                    database.delete_company(company_name)
                    refresh_company_names()
                    st.session_state['selected_company'] = None
                    st.session_state['vector_store'] = None
                    st.session_state['chat_history'] = []
                    st.write(f"Company '{company_name}' has been deleted.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error deleting company: {e}")
            else:
                st.warning("No company selected for deletion.")
    else:
        st.write("No company names available.")
        company_name = None

    if st.button("Show Chat History"):
        if st.session_state['selected_company']:
            db_name = database.get_db_name_from_url(database.get_url_by_company_name(st.session_state['selected_company']))
            chat_history = database.read_from_db(db_name)
        else:
            chat_history = []
        
        if chat_history:
            st.write("Chat History:")
            for question, answer in chat_history:
                st.write(f"*Q:* {question}")
                st.write(f"*A:* {answer}")
        else:
            st.write("No chat history found.")

# Main chat functionality
if not st.session_state['selected_company']:
    st.info("Please select a company")
else:
    company_name = st.session_state['selected_company']
    db_name = database.get_db_name_from_url(database.get_url_by_company_name(company_name))
    database.init_db(db_name)

    if not st.session_state['chat_history']:
        st.session_state['chat_history'] = [
            AIMessage(content=f"Hello, I am a bot for {company_name}. How can I assist you?")
        ]
    
    if not st.session_state['vector_store']:
        st.session_state['vector_store'] = langchain_helpers.get_vectorstore_from_url(database.get_url_by_company_name(company_name))
        st.write("Vector store initialized.")

    user_query = st.chat_input("Type your message here...")
    if user_query:
        try:
            response = langchain_helpers.get_response(user_query, st.session_state['vector_store'], st.session_state['chat_history'])
            st.session_state['chat_history'].append(HumanMessage(content=user_query))
            st.session_state['chat_history'].append(AIMessage(content=response))

            database.store_in_db(db_name, user_query, response, company_name)
        except Exception as e:
            st.error(f"Error processing query: {e}")

    for message in st.session_state['chat_history']:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)
























