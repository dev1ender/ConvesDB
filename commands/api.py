"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

FastAPI entry point for the conversDB application.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

from app.core import get_app, process_query, get_available_workflows, get_workflow_stages
from app.application import Application

# Get application instance
app_instance = get_app()

# Initialize FastAPI app
app = FastAPI(
    title="NLP Processing API",
    description="""
    API for processing natural language queries through configurable workflows.
    
    This API supports:
    - Processing natural language queries 
    - Selecting specific workflows to execute
    - Executing specific stages of a workflow
    - Retrieving available workflows and stages
    """,
    version="0.1.0"
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    workflow_id: Optional[str] = None
    stages_to_execute: Optional[Union[List[str], str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the key features of this product?",
                "workflow_id": "default_workflow",
                "stages_to_execute": ["parse_query", "search_data"]
            }
        }

class QueryResponse(BaseModel):
    query: str
    result: Dict[str, Any]
    execution_history: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the key features of this product?",
                "result": {
                    "answer": "The key features include...",
                    "sources": ["document1.pdf", "document2.pdf"]
                },
                "execution_history": [
                    {"stage_id": "parse_query", "status": "success"},
                    {"stage_id": "search_data", "status": "success"}
                ],
                "error": None
            }
        }

class WorkflowStage(BaseModel):
    id: str
    component_type: str
    component_id: str
    disabled: Optional[bool] = False
    config: Optional[Dict[str, Any]] = None

class WorkflowInfo(BaseModel):
    id: str
    description: Optional[str] = None
    stages: List[WorkflowStage]

@app.post("/process", response_model=QueryResponse)
async def process_nlp_query(request: QueryRequest):
    """Process a natural language query using the specified workflow and stages."""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        # Prepare context with workflow_id if provided
        context = {}
        if request.workflow_id:
            context["workflow_id"] = request.workflow_id
        
        # Process the query with the specified workflow and stages
        result = process_query(
            query=request.query,
            context=context,
            stages_to_execute=request.stages_to_execute
        )
        
        # Build response
        response = {
            "query": request.query,
            "result": result.get("result", {}),
            "execution_history": result.get("execution_history", []),
            "error": result.get("error")
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows", response_model=List[str])
async def list_workflows():
    """Get a list of available workflow IDs."""
    return get_available_workflows()

@app.get("/workflows/{workflow_id}", response_model=WorkflowInfo)
async def get_workflow_info(workflow_id: str):
    """Get detailed information about a specific workflow."""
    # Get workflow definition
    workflow = app_instance.workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    
    # Extract workflow information
    workflow_info = workflow.get("workflow", {})
    
    # Map stages to response model format
    stages = []
    for stage_def in workflow_info.get("stages", []):
        stage = WorkflowStage(
            id=stage_def.get("id", "unknown"),
            component_type=stage_def.get("component_type", "unknown"),
            component_id=stage_def.get("component_id", "unknown"),
            disabled=stage_def.get("disabled", False),
            config=stage_def.get("config", {})
        )
        stages.append(stage)
    
    # Build response
    response = WorkflowInfo(
        id=workflow_id,
        description=workflow_info.get("description"),
        stages=stages
    )
    
    return response

@app.get("/components")
async def list_components():
    """Get a dictionary of available component types and their components."""
    components = {}
    for component_type in app_instance.component_registry.get_component_types():
        components[component_type] = app_instance.component_registry.get_components_by_type(component_type)
    
    return components

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def start():
    """Start the FastAPI server."""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run("commands.api:app", host=host, port=port)

if __name__ == "__main__":
    start() 