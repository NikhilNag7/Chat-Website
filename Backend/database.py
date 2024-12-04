import sqlite3
from urllib.parse import urlparse

def init_chats_db():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    
    # Check if table exists and has the correct schema
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'company_name' not in columns:
        # If 'company_name' column is missing, recreate the table
        cursor.execute('''
            CREATE TABLE chat_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                question TEXT,
                answer TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO chat_history_new (id, question, answer)
            SELECT id, question, answer FROM chat_history
        ''')
        cursor.execute('DROP TABLE chat_history')
        cursor.execute('ALTER TABLE chat_history_new RENAME TO chat_history')
    
    conn.commit()
    conn.close()

def delete_company(company_name):
    # Delete company from URLs database
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM urls WHERE company_name = ?', (company_name,))
    conn.commit()
    conn.close()

    # Delete company from files database
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE company_name = ?', (company_name,))
    conn.commit()
    conn.close()

    # Delete company chat history from chat history database
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE company_name = ?', (company_name,))
    conn.commit()
    conn.close()    

def save_chat(company_name: str, question: str, answer: str) -> int:
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (company_name, question, answer)
        VALUES (?, ?, ?)
    """, (company_name, question, answer))
    conn.commit()
    chat_id = cursor.lastrowid
    conn.close()
    return chat_id

def get_chats(company_name: str):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question, answer FROM chat_history
        WHERE company_name = ?
    """, (company_name,))
    chats = cursor.fetchall()
    conn.close()
    return chats

def init_db(db_name):
    """ Initialize the chat_history table with the correct schema. """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if the company_name column exists
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = cursor.fetchall()
    
    if not any(column[1] == 'company_name' for column in columns):
        # If the company_name column doesn't exist, add it
        cursor.execute("ALTER TABLE chat_history ADD COLUMN company_name TEXT")

    # If the table doesn't exist, create it with the company_name column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        question TEXT,
        answer TEXT,
        company_name TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def store_file(file_name, file_content, company_name):
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()

    # Check if the file already exists
    cursor.execute('SELECT COUNT(*) FROM files WHERE file_name = ?', (file_name,))
    exists = cursor.fetchone()[0]

    if exists:
        # If file exists, update its content
        cursor.execute('UPDATE files SET file_content = ?, company_name = ? WHERE file_name = ?', 
                       (file_content, company_name, file_name))
        conn.commit()
        print(f"File '{file_name}' updated successfully.")
    else:
        cursor.execute('INSERT INTO files (file_name, file_content, company_name) VALUES (?, ?, ?)', 
                       (file_name, file_content, company_name))
        conn.commit()
        print(f"File '{file_name}' inserted successfully.")

    conn.close()


def get_db_name_from_file(file_name):
    company_name = file_name.split('.')[0]
    return f"{company_name}.db"

def extract_company_name(url):
    hostname = urlparse(url).hostname
    if hostname:
        hostname = hostname.lstrip('www.')
        company_name = hostname.split('.')[0]
        return company_name.capitalize()
    else:
        raise ValueError("Invalid URL provided")

def update_files_db_schema():
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(files)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'file_content' not in columns:
        cursor.execute('ALTER TABLE files ADD COLUMN file_content TEXT')
        conn.commit()
        print("Added 'file_content' column to 'files' table.")
    else:
        print("'file_content' column already exists.")
    conn.close()

update_files_db_schema()

def init_urls_db():
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            company_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_files_db():
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_content TEXT,
            company_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def store_url(url, company_name):
    if url:  # Check if the URL is not None or empty
        conn = sqlite3.connect('urls.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO urls (url, company_name) VALUES (?, ?)', (url, company_name))
        conn.commit()
        conn.close()
        print(f"Successfully stored URL: {url} for company: {company_name}")
    else:
        print(f"No URL provided for company: {company_name}. Skipping URL storage.")

def get_company_names():
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT company_name FROM urls')
    url_company_names = [row[0] for row in cursor.fetchall()]
    conn.close()

    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT company_name FROM files')
    file_company_names = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Combine company names from both URLs and files, removing duplicates
    company_names = list(set(url_company_names + file_company_names))
    return company_names

def get_url_by_company_name(company_name):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM urls WHERE company_name = ?', (company_name,))
    url = cursor.fetchone()
    conn.close()
    return url[0] if url else None

def get_files_by_company_name(company_name):
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file_content FROM files WHERE company_name = ?', (company_name,))
    files = [row[0] for row in cursor.fetchall()]
    conn.close()
    return files

def store_in_db(db_name, question, answer, company_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            company_name TEXT NOT NULL
        )
    ''')
    cursor.execute('INSERT INTO chat_history (question, answer, company_name) VALUES (?, ?, ?)', (question, answer, company_name))
    conn.commit()
    conn.close()

def read_from_db(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT question, answer FROM chat_history')
    chat_history = cursor.fetchall()
    conn.close()
    return chat_history

def get_db_name_from_url(url):
    company_name = extract_company_name(url)
    return f"{company_name}.db"










