import pytest
import sys
import os
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import commands
from commands import cli, api

class TestCommandInterfaces:
    """
    Test the command interfaces (CLI, API) to verify they work with the 
    refactored application structure.
    """
    
    @pytest.fixture
    def mock_app(self):
        """Mock app for testing commands"""
        mock_app = MagicMock()
        mock_app.workflow_engine.list_workflows.return_value = ["workflow1", "workflow2"]
        
        # Mock stage data
        stages = [
            {"id": "stage_1", "component_type": "test", "component_id": "test1"},
            {"id": "stage_2", "component_type": "test", "component_id": "test2"},
        ]
        mock_app.workflow_engine.get_workflow.return_value = {
            "workflow": {
                "id": "workflow1",
                "description": "Test workflow",
                "stages": stages
            }
        }
        
        return mock_app
    
    @patch("commands.cli.get_app")
    @patch("commands.cli.process_query")
    @patch("commands.cli.get_available_workflows")
    @patch("commands.cli.get_workflow_stages")
    def test_cli_workflow_listing(self, mock_get_stages, mock_get_workflows, 
                                 mock_process_query, mock_get_app, mock_app, capsys):
        """Test CLI workflow listing functionality"""
        # Set up mocks
        mock_get_app.return_value = mock_app
        mock_get_workflows.return_value = ["workflow1", "workflow2"]
        
        # Call CLI with --list-workflows argument
        with patch("sys.argv", ["cli.py", "--list-workflows"]):
            try:
                cli.main()
            except SystemExit:
                pass  # It's okay if it exits
        
        # Check output
        captured = capsys.readouterr()
        assert "Available Workflows:" in captured.out
        assert "workflow1" in captured.out
        assert "workflow2" in captured.out
    
    @patch("commands.cli.get_app")
    @patch("commands.cli.process_query")
    @patch("commands.cli.get_available_workflows")
    @patch("commands.cli.get_workflow_stages")
    def test_cli_stage_listing(self, mock_get_stages, mock_get_workflows, 
                              mock_process_query, mock_get_app, mock_app, capsys):
        """Test CLI stage listing functionality"""
        # Set up mocks
        mock_get_app.return_value = mock_app
        mock_get_stages.return_value = [
            {"id": "stage_1", "component_type": "test", "component_id": "test1"},
            {"id": "stage_2", "component_type": "test", "component_id": "test2"},
        ]
        
        # Call CLI with --list-stages argument
        with patch("sys.argv", ["cli.py", "--list-stages", "workflow1"]):
            try:
                cli.main()
            except SystemExit:
                pass  # It's okay if it exits
        
        # Check output
        captured = capsys.readouterr()
        assert "Stages for workflow 'workflow1':" in captured.out
        assert "stage_1" in captured.out
        assert "stage_2" in captured.out
    
    @patch("commands.cli.get_app")
    @patch("commands.cli.process_query")
    def test_cli_query_processing(self, mock_process_query, mock_get_app, mock_app, capsys):
        """Test CLI query processing"""
        # Set up mocks
        mock_get_app.return_value = mock_app
        mock_process_query.return_value = {
            "result": {"answer": "Test answer"},
            "execution_history": [
                {"stage_id": "stage_1", "status": "success"},
                {"stage_id": "stage_2", "status": "success"}
            ]
        }
        
        # Call CLI with --query argument
        with patch("sys.argv", ["cli.py", "--query", "test query", "--workflow", "workflow1", 
                               "--stage", "stage_1,stage_2"]):
            try:
                cli.main()
            except SystemExit:
                pass  # It's okay if it exits
        
        # Check process_query was called correctly
        mock_process_query.assert_called_once()
        args, kwargs = mock_process_query.call_args
        assert args[0] == "test query"
        assert kwargs["context"] == {"workflow_id": "workflow1"}
        assert kwargs["stages_to_execute"] == ["stage_1", "stage_2"]
        
        # Check output contains result
        captured = capsys.readouterr()
        assert "Execution History:" in captured.out
        assert "stage_1" in captured.out
        assert "stage_2" in captured.out
        assert "Result:" in captured.out
        assert "answer" in captured.out
    
    @patch("commands.api.get_app")
    @patch("commands.api.process_query")
    @patch("commands.api.get_available_workflows")
    @patch("commands.api.get_workflow_stages")
    def test_api_process_endpoint(self, mock_get_stages, mock_get_workflows, 
                                 mock_process_query, mock_get_app, mock_app):
        """Test API process endpoint"""
        # Set up mocks
        mock_get_app.return_value = mock_app
        mock_process_query.return_value = {
            "result": {"answer": "Test answer"},
            "execution_history": [
                {"stage_id": "stage_1", "status": "success"},
                {"stage_id": "stage_2", "status": "success"}
            ]
        }
        
        # Create a test client for FastAPI
        from fastapi.testclient import TestClient
        client = TestClient(api.app)
        
        # Test process endpoint
        request_data = {
            "query": "test query",
            "workflow_id": "workflow1",
            "stages_to_execute": ["stage_1", "stage_2"]
        }
        response = client.post("/process", json=request_data)
        
        # Check response
        assert response.status_code == 200
        result = response.json()
        assert result["query"] == "test query"
        assert "result" in result
        assert "answer" in result["result"]
        assert result["result"]["answer"] == "Test answer"
        assert "execution_history" in result
        assert len(result["execution_history"]) == 2
        
        # Check process_query was called correctly
        mock_process_query.assert_called_once()
        # In the API implementation, process_query is called with keyword arguments
        call = mock_process_query.call_args
        kwargs = call[1]
        assert kwargs["query"] == "test query"
        assert kwargs["context"] == {"workflow_id": "workflow1"}
        assert kwargs["stages_to_execute"] == ["stage_1", "stage_2"]
    
    @patch("commands.api.get_app")
    @patch("commands.api.get_available_workflows")
    def test_api_workflows_endpoint(self, mock_get_workflows, mock_get_app, mock_app):
        """Test API workflows endpoint"""
        # Set up mocks
        mock_get_app.return_value = mock_app
        mock_get_workflows.return_value = ["workflow1", "workflow2"]
        
        # Create a test client for FastAPI
        from fastapi.testclient import TestClient
        client = TestClient(api.app)
        
        # Test workflows endpoint
        response = client.get("/workflows")
        
        # Check response
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert "workflow1" in result
        assert "workflow2" in result
        
        # Check get_available_workflows was called
        mock_get_workflows.assert_called_once()
    
    @patch("commands.api.app_instance")
    def test_api_workflow_info_endpoint(self, mock_app_instance):
        """Test API workflow info endpoint"""
        # Set up the workflow engine mock to return a workflow
        mock_workflow = {
            "workflow": {
                "id": "workflow1",
                "description": "Test workflow",
                "stages": [
                    {"id": "stage_1", "component_type": "test", "component_id": "test1"},
                    {"id": "stage_2", "component_type": "test", "component_id": "test2"}
                ]
            }
        }
        mock_app_instance.workflow_engine.get_workflow.return_value = mock_workflow
        
        # Create a test client for FastAPI
        from fastapi.testclient import TestClient
        client = TestClient(api.app)
        
        # Test workflow info endpoint
        response = client.get("/workflows/workflow1")
        
        # Check response
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "workflow1"
        assert result["description"] == "Test workflow"
        assert len(result["stages"]) == 2
        assert result["stages"][0]["id"] == "stage_1"
        assert result["stages"][1]["id"] == "stage_2"
        
        # Verify the workflow engine was called correctly
        mock_app_instance.workflow_engine.get_workflow.assert_called_once_with("workflow1") 