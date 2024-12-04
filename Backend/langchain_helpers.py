import requests
import database
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

#Extracts the company name from a given URL.
def extract_company_name(url):
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) > 2:
        company_name = domain_parts[-2].capitalize()
    else:
        company_name = domain_parts[0].capitalize()
    return company_name

#Processes a website URL to extract and store its content in a vector store.
def process_website(url):
    company_name = extract_company_name(url)
    print(f"Processing website: {url} for company: {company_name}")  # Debugging line
    database.store_url(url, company_name)
    vector_store = get_vectorstore_from_url(url)
    print(f"Vector store initialized for URL: {url}")  # Debugging line
    return vector_store

#Collects all links from a given URL, ensuring they are within the same domain.
def get_all_links_from_url(url):
    visited = set()
    to_visit = [url]
    domain = urlparse(url).netloc
    
    while to_visit:
        current_url = to_visit.pop()
        if current_url in visited:
            continue
        visited.add(current_url)
        
        response = requests.get(current_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if urlparse(full_url).netloc == domain and full_url not in visited:
                to_visit.append(full_url)
    
    return list(visited)

#Creates a vector store containing the content from all pages linked to the provided URL.
def get_vectorstore_from_url(url):
    urls = get_all_links_from_url(url)
    all_documents = []
    for link in urls:
        loader = WebBaseLoader(link)
        document = loader.load()
        all_documents.extend(document)
    
    text_splitter = RecursiveCharacterTextSplitter()
    document_chunks = text_splitter.split_documents(all_documents)
    vector_store = Chroma.from_documents(document_chunks, OpenAIEmbeddings())
    
    print(f"Vector store initialized for URL: {url}")
    print(f"Number of documents loaded: {len(document_chunks)}")
    
    return vector_store
#Creates a retriever chain that can retrieve relevant context from the vector store based on user input and chat history.

def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI()
    retriever = vector_store.as_retriever()
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    return retriever_chain

#Creates a retrieval-augmented generation (RAG) chain that answers user questions based on the retrieved context.
    
def get_conversational_rag_chain(retriever_chain):
    llm = ChatOpenAI()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the user's questions based on the below context:\n\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
    ])
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)

#Generates a response to a user’s query using the stored vector data and chat history.

def get_response(user_input, vector_store, chat_history):
    retriever_chain = get_context_retriever_chain(vector_store)
    conversation_rag_chain = get_conversational_rag_chain(retriever_chain)
    response = conversation_rag_chain.invoke({
        "chat_history": chat_history,
        "input": user_input
    })
    print(f"Generated response: {response['answer']}")  # Debugging line
    return response['answer']

#Processes a text file's content and stores it in a vector store for later retrieval.#

def process_text_file(file_content):
    text_splitter = RecursiveCharacterTextSplitter()
    document_chunks = text_splitter.split_text(file_content)
    
    documents = [Document(page_content=chunk) for chunk in document_chunks]
    
    vector_store = Chroma.from_documents(documents, OpenAIEmbeddings())
    
    print(f"Vector store initialized from text file content.")
    print(f"Number of document chunks: {len(documents)}")
    
    return vector_store







