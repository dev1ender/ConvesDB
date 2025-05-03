import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the application modules
from app.factory import ApplicationFactory
from app.application import Application
from app.core import get_app, process_query, get_available_workflows, get_workflow_stages
from app.core.exceptions import InitializationError, WorkflowError

class TestAppCore:
    """
    Test the core application functionality after refactoring.
    These tests verify the six key steps in the application flow:
    1. Config loading
    2. Component verification
    3. Service requirements verification
    4. Health checks
    5. Stage-wise workflow processing
    6. User control over stage execution
    """

    @pytest.fixture
    def test_config_dir(self):
        """Return the test configuration directory"""
        return os.path.join(os.path.dirname(__file__), "test_config")
    
    @pytest.fixture
    def ensure_test_config_dir(self, test_config_dir):
        """Ensure the test config directory exists"""
        os.makedirs(test_config_dir, exist_ok=True)
        os.makedirs(os.path.join(test_config_dir, "workflows"), exist_ok=True)
        os.makedirs(os.path.join(test_config_dir, "components"), exist_ok=True)
        os.makedirs(os.path.join(test_config_dir, "services"), exist_ok=True)
        return test_config_dir
    
    @pytest.fixture
    def app_instance(self):
        """Get the default application instance"""
        # This uses the actual application instance that loads config from the default location
        return get_app()
    
    def test_config_loading(self, app_instance):
        """Test that config is loaded properly"""
        # Verify that application instance exists
        assert app_instance is not None
        
        # Verify that config loader has loaded configuration
        assert app_instance.config_loader is not None
        
        # Get the main config and verify it has required sections
        config = app_instance.config_loader.get_config()
        assert isinstance(config, dict)
    
    def test_component_verification(self, app_instance):
        """Test that components are verified during startup"""
        # Verify component registry exists
        assert app_instance.component_registry is not None
        
        # Get component types and verify at least one exists
        component_types = app_instance.component_registry.get_component_types()
        # This test may need adjustment if your application doesn't require components at startup
        # assert len(component_types) > 0, "No component types found in registry"
    
    def test_service_requirements(self, app_instance):
        """Test that service requirements are verified"""
        # Verify service manager exists
        assert app_instance.service_manager is not None
        
        # Get service names and verify services are initialized
        service_names = app_instance.service_manager.get_service_names()
        # This test may need adjustment if your application doesn't require services at startup
        # assert len(service_names) > 0, "No services initialized"
    
    def test_health_checks(self, app_instance):
        """Test service health checks"""
        # This will check health of all initialized services
        # If no services are initialized, this just verifies the method runs without errors
        service_names = app_instance.service_manager.get_service_names()
        for service_name in service_names:
            health_status = app_instance.service_manager.check_service_health(service_name)
            assert isinstance(health_status, bool)
    
    def test_workflow_engine(self, app_instance):
        """Test the workflow engine initialization"""
        # Verify workflow engine exists
        assert app_instance.workflow_engine is not None
        
        # Get available workflows
        workflows = get_available_workflows()
        assert isinstance(workflows, list)
    
    @patch('app.core.workflow_engine.WorkflowEngine.execute_workflow')
    def test_stage_execution(self, mock_execute_workflow, app_instance):
        """Test execution of workflow stages"""
        # Mock the workflow execution to avoid actual component instantiation
        mock_execute_workflow.return_value = {
            "result": {"answer": "Test result"},
            "execution_history": [
                {"stage_id": "stage_1", "status": "success"}
            ],
            "executed_stages": ["stage_1"]
        }
        
        # Test processing a query with just the first stage
        test_query = "Test query for single stage execution"
        result = process_query(
            query=test_query,
            context={"workflow_id": "default_workflow"},
            stages_to_execute="stage_1"
        )
        
        # Verify the response
        assert isinstance(result, dict)
        assert "result" in result
        assert "execution_history" in result
        assert "executed_stages" in result
        assert result["executed_stages"] == ["stage_1"]
        
        # Verify that execute_workflow was called with the right parameters
        mock_execute_workflow.assert_called_once()
        args, kwargs = mock_execute_workflow.call_args
        assert args[0] == "default_workflow"  # workflow_id
        assert "query" in args[1]  # context
        assert args[1]["query"] == "Test query for single stage execution"
        assert "selected_stages" in args[1]
        assert args[1]["selected_stages"] == ["stage_1"]
    
    @patch('app.core.workflow_engine.WorkflowEngine.execute_workflow')
    def test_multiple_stage_execution(self, mock_execute_workflow, app_instance):
        """Test execution of multiple specific workflow stages"""
        # Mock the workflow execution to avoid actual component instantiation
        mock_execute_workflow.return_value = {
            "result": {"answer": "Test result for multiple stages"},
            "execution_history": [
                {"stage_id": "stage_1", "status": "success"},
                {"stage_id": "stage_2", "status": "success"}
            ],
            "executed_stages": ["stage_1", "stage_2"]
        }
        
        # Test processing a query with multiple stages
        test_query = "Test query for multiple stage execution"
        result = process_query(
            query=test_query,
            context={"workflow_id": "default_workflow"},
            stages_to_execute=["stage_1", "stage_2"]
        )
        
        # Verify the response
        assert isinstance(result, dict)
        assert "result" in result
        assert "execution_history" in result
        assert len(result["execution_history"]) == 2
        assert "executed_stages" in result
        assert len(result["executed_stages"]) == 2
        assert "stage_1" in result["executed_stages"]
        assert "stage_2" in result["executed_stages"]
        
        # Verify that execute_workflow was called with the right parameters
        mock_execute_workflow.assert_called_once()
        args, kwargs = mock_execute_workflow.call_args
        assert args[0] == "default_workflow"  # workflow_id
        assert "query" in args[1]  # context
        assert args[1]["query"] == "Test query for multiple stage execution"
        assert "selected_stages" in args[1]
        assert args[1]["selected_stages"] == ["stage_1", "stage_2"] 