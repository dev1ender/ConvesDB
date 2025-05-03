from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uvicorn

from app.main import NLToSQLApp
from app.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager()
app_config = config_manager.get("app", {})

# Initialize FastAPI app
app = FastAPI(
    title=app_config.get("name", "NL to SQL API"),
    description="API for converting natural language to SQL queries",
    version="0.1.0"
)

# Initialize the NL to SQL app
nl_to_sql_app = NLToSQLApp()

# Make sure database is seeded
@app.on_event("startup")
async def startup_event():
    if config_manager.get("database.seed_on_startup", True):
        nl_to_sql_app.seed_database()
        print("Database seeded successfully")


# Request/Response models
class QuestionRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql_query: str
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QuestionRequest):
    """Process a natural language question and return SQL query and results."""
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    response = nl_to_sql_app.process_question(request.question)
    return response


@app.get("/schema")
async def get_schema():
    """Get the database schema."""
    schema = nl_to_sql_app.get_schema_info()
    return {"schema": schema}


@app.get("/config")
async def get_config():
    """Get the current configuration (excluding secrets)."""
    # Create a safe copy of the configuration without sensitive data
    safe_config = {}
    
    # Copy app settings
    safe_config["app"] = config_manager.get("app", {})
    
    # Copy database settings without any credentials
    db_config = config_manager.get("database", {})
    safe_config["database"] = {
        "type": db_config.get("type"),
        "path": db_config.get("path"),
        "seed_on_startup": db_config.get("seed_on_startup")
    }
    
    # Copy LLM settings without API keys
    llm_config = {
        "provider": config_manager.get_llm_provider()
    }
    
    if config_manager.is_using_openai():
        llm_config["openai"] = {
            "model": config_manager.get("llm.openai.model"),
            "temperature": config_manager.get("llm.openai.temperature")
        }
    else:
        llm_config["ollama"] = {
            "model": config_manager.get("llm.ollama.model"),
            "temperature": config_manager.get("llm.ollama.temperature"),
            "host": config_manager.get("llm.ollama.host")
        }
    
    safe_config["llm"] = llm_config
    
    return safe_config


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def start():
    """Start the FastAPI server."""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = config_manager.get("app.debug", False)
    
    uvicorn.run("app.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    start() 