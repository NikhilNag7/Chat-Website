from fastapi import FastAPI, File, Form, UploadFile, HTTPException,Query,Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import database
import logging
from langchain_helpers import get_response
from langchain_helpers import process_text_file
from langchain_helpers import process_website  # Import the get_response function
import langchain_helpers

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize databases
database.init_files_db()
database.init_urls_db()
database.init_chats_db()
database.init_db('your_database.db')

# Endpoint to train the model
@app.post("/train")
async def train_model(
    company_name: str = Form(...),
    url: str = Form(None),
    file: UploadFile = File(None)
):
    # Log received data
    logger.info(f"Received company_name: {company_name}")
    logger.info(f"Received file: {file.filename if file else 'No file provided'}")
    logger.info(f"Received url: {url if url else 'No URL provided'}")

    # Initialize response structure
    response = {
        "company_name": company_name,
        "file_uploaded": None,
        "url_uploaded": None,
        "message": None
    }

    try:
        # Process file upload if provided
        if file:
            try:
                # Try to read file content as text with UTF-8 encoding
                file_content = await file.read()
                file_content_str = file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    # Fallback to ISO-8859-1 if UTF-8 decoding fails
                    file_content_str = file_content.decode("ISO-8859-1")
                except UnicodeDecodeError as e:
                    logger.error(f"UnicodeDecodeError: {str(e)}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Failed to decode file content. Ensure the file is encoded in UTF-8 or ISO-8859-1."}
                    )
                except Exception as e:
                    logger.error(f"Error reading file content: {str(e)}")
                    return JSONResponse(
                        status_code=500,
                        content={"detail": f"Failed to process file: {str(e)}"}
                    )

            # Store file content in the database
            database.store_file(file.filename, file_content_str, company_name)
            db_name_file = database.get_db_name_from_file(file.filename)
            database.init_db(db_name_file)
            response["file_uploaded"] = file.filename

        # Process URL if provided
        if url:
            logger.info(f"URL received: {url}")
            try:
                database.store_url(url, company_name)
                db_name = database.get_db_name_from_url(url)
                database.init_db(db_name)
                response["url_uploaded"] = url
            except Exception as e:
                logger.error(f"Error processing URL: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Failed to process URL: {str(e)}"}
                )
        else:
            logger.warning("URL was not provided or is null.")

        # Set success message
        response["message"] = f"Successfully processed company '{company_name}'."
        if response["file_uploaded"]:
            response["message"] += f" File '{response['file_uploaded']}' has been uploaded."
        if response["url_uploaded"]:
            response["message"] += f" URL '{response['url_uploaded']}' has been processed."

        # Return the response with the processed details
        return response

    except Exception as e:
        logger.error(f"Error in train_model: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to train model: {str(e)}"}
        )


class CompanyChatHistoryResponse(BaseModel):
    company_name: str
    chat_history: list

# Endpoint to retrieve company and chat history
@app.get("/company_chat_history", response_model=CompanyChatHistoryResponse)
async def get_company_chat_history(company_name: str):
    try:
        # Check if the company exists
        url = database.get_url_by_company_name(company_name)
        if not url:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get the database name associated with the company
        db_name = database.get_db_name_from_url(url)
        
        # Retrieve chat history from the specific database
        chat_history = database.read_from_db(db_name)
        if not chat_history:
            chat_history = []
        
        # Create response object
        response = CompanyChatHistoryResponse(
            company_name=company_name,
            chat_history=[{"question": q, "answer": a} for q, a in chat_history]
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in get_company_chat_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

# Model for the ask_question endpoint
@app.get("/ask_question")
async def ask_question(
    company_name: str = Query(..., description="Name of the company"),
    question: str = Query(..., description="Question to ask about the company")
):
    try:
        # Get the URL associated with the company
        url = database.get_url_by_company_name(company_name)
        if not url:
            raise HTTPException(status_code=404, detail="Company not found")
        
        logger.info(f"URL for company '{company_name}': {url}")

        # Get the vector store for the company
        vector_store = langchain_helpers.get_vectorstore_from_url(url)
        
        if not vector_store:
            raise HTTPException(status_code=500, detail="Vector store not found or not initialized.")

        # Get the response from the vector store
        chat_history = []  # Initialize an empty chat history
        response = langchain_helpers.get_response(question, vector_store, chat_history)
        
        logger.info(f"Response for question '{question}': {response}")

        # Return the response
        return {
            "question": question,
            "answer": response
        }

    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)























