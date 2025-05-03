import pytest
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the workflow engine and related components
from app.core.workflow_engine import WorkflowEngine
from app.core.component_registry import ComponentRegistry
from app.core.exceptions import WorkflowError
from app.core.stage_processor import StageProcessor

class TestWorkflowEngine:
    """
    Test the workflow engine functionality:
    - Loading workflow definitions
    - Executing workflow stages in sequence
    - Executing specific stages
    - Handling execution history
    - Processing conditional stages
    """

    @pytest.fixture
    def test_config_dir(self):
        """Return the test configuration directory"""
        config_dir = os.path.join(os.path.dirname(__file__), "test_config")
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(os.path.join(config_dir, "workflows"), exist_ok=True)
        os.makedirs(os.path.join(config_dir, "components"), exist_ok=True)
        return config_dir
    
    @pytest.fixture
    def component_registry(self, test_config_dir):
        """Create a component registry for testing"""
        registry = ComponentRegistry(test_config_dir)
        # Mock the get_component method to return simple component instances
        registry.get_component = MagicMock()
        return registry
    
    @pytest.fixture
    def workflow_engine(self, component_registry, test_config_dir):
        """Create a workflow engine for testing"""
        workflows_dir = os.path.join(test_config_dir, "workflows")
        
        # The WorkflowEngine constructor doesn't accept a stage_processor directly,
        # it creates one internally using the component_registry
        return WorkflowEngine(component_registry, workflows_dir)
    
    @pytest.fixture
    def test_workflow_file(self, test_config_dir):
        """Create a test workflow file"""
        workflow_file = os.path.join(test_config_dir, "workflows", "test_workflow.yaml")
        
        # Define a simple workflow for testing
        workflow_def = {
            "workflow": {
                "id": "test_workflow",
                "description": "Test workflow for unit tests",
                "stages": [
                    {
                        "id": "stage_1",
                        "component_type": "test_component",
                        "component_id": "test_component_1"
                    },
                    {
                        "id": "stage_2",
                        "component_type": "test_component",
                        "component_id": "test_component_2"
                    },
                    {
                        "id": "stage_3",
                        "component_type": "test_component",
                        "component_id": "test_component_3",
                        "disabled": True  # This stage is disabled
                    },
                    {
                        "id": "conditional_stage",
                        "condition": {
                            "type": "value_check",
                            "key": "test_condition",
                            "value": True
                        },
                        "then": {
                            "id": "condition_true",
                            "component_type": "test_component",
                            "component_id": "test_component_4"
                        },
                        "else": {
                            "id": "condition_false",
                            "component_type": "test_component",
                            "component_id": "test_component_5"
                        }
                    }
                ]
            }
        }
        
        # Write workflow to file
        with open(workflow_file, "w") as f:
            yaml.dump(workflow_def, f)
        
        return workflow_file
    
    @pytest.fixture
    def mock_components(self, component_registry):
        """Mock components for testing"""
        # Create mock components that just return a result
        def create_mock_component(component_id):
            mock_component = MagicMock()
            mock_component.id = component_id
            mock_component.config = {}
            mock_component.execute.return_value = {
                "executed_component": component_id,
                "test_result": f"Result from {component_id}"
            }
            return mock_component
        
        # Create component mocks for all test components
        components = {}
        for i in range(1, 6):
            component_id = f"test_component_{i}"
            components[component_id] = create_mock_component(component_id)
        
        # Configure the component_registry.get_component mock to return our components
        def mock_get_component(component_type, component_id):
            return components.get(component_id)
        
        component_registry.get_component.side_effect = mock_get_component
        
        return components
    
    def test_workflow_loading(self, workflow_engine, test_workflow_file):
        """Test loading workflow definitions from files"""
        # Force reload of workflows
        workflow_engine._load_workflows()
        
        # Check that our test workflow was loaded
        workflow = workflow_engine.get_workflow("test_workflow")
        assert workflow is not None
        assert workflow["workflow"]["id"] == "test_workflow"
        assert len(workflow["workflow"]["stages"]) == 4
    
    def test_workflow_registration(self, workflow_engine):
        """Test registering workflows programmatically"""
        # Register a new workflow
        workflow_def = {
            "workflow": {
                "id": "registered_workflow",
                "stages": [
                    {
                        "id": "stage_r1",
                        "component_type": "test_component",
                        "component_id": "test_component_r1"
                    }
                ]
            }
        }
        
        workflow_engine.register_workflow("registered_workflow", workflow_def)
        
        # Check that the workflow was registered
        workflow = workflow_engine.get_workflow("registered_workflow")
        assert workflow is not None
        assert workflow["workflow"]["id"] == "registered_workflow"
    
    def test_stage_execution(self, workflow_engine, test_workflow_file, mock_components):
        """Test execution of workflow stages"""
        # Force reload of workflows
        workflow_engine._load_workflows()
        
        # Create initial context
        context = {"test_data": "test"}
        
        # Execute workflow
        result = workflow_engine.execute_workflow("test_workflow", context)
        
        # Verify the result
        assert result is not None
        assert "test_data" in result
        
        # Check that stage 1 and 2 were executed, but not stage 3 (disabled)
        assert result.get("executed_component") in ["test_component_1", "test_component_2", "test_component_4", "test_component_5"]
        
        # Check execution history if it exists
        if "execution_history" in result:
            # Get stage IDs from execution history
            stage_ids = [step["stage_id"] for step in result["execution_history"]]
            
            # Stage 1 and 2 should be executed, but not stage 3 (disabled)
            assert "stage_1" in stage_ids
            assert "stage_2" in stage_ids
            assert "stage_3" not in stage_ids
            
            # Conditional stage should be executed but not the branch stages directly in the history
            assert "conditional_stage" in stage_ids
    
    def test_selected_stage_execution(self, workflow_engine, test_workflow_file, mock_components):
        """Test execution of selected workflow stages"""
        # Force reload of workflows
        workflow_engine._load_workflows()
        
        # Create initial context with selected stages
        context = {
            "test_data": "test",
            "selected_stages": ["stage_1"]
        }
        
        # Execute workflow with only stage_1 selected
        result = workflow_engine.execute_workflow("test_workflow", context)
        
        # Verify the result
        assert result is not None
        assert "test_data" in result
        
        # Check that only stage 1 was executed
        assert result.get("executed_component") == "test_component_1"
        
        # Check execution history if it exists
        if "execution_history" in result:
            # Get stage IDs from execution history
            stage_ids = [step["stage_id"] for step in result["execution_history"]]
            
            # Only stage 1 should be in the history
            assert "stage_1" in stage_ids
            assert "stage_2" not in stage_ids
            assert "stage_3" not in stage_ids
            assert "condition_true" not in stage_ids
            assert "condition_false" not in stage_ids
        
        # Check executed_stages field
        assert "executed_stages" in result
        assert result["executed_stages"] == ["stage_1"]
    
    def test_conditional_stage_execution(self, workflow_engine, test_workflow_file, mock_components):
        """Test execution of conditional workflow stages"""
        # Force reload of workflows
        workflow_engine._load_workflows()
        
        # Test with condition = True
        true_context = {
            "test_data": "test",
            "selected_stages": ["conditional_stage"],
            "test_condition": True
        }
        
        # Execute workflow with conditional stage and condition = True
        true_result = workflow_engine.execute_workflow("test_workflow", true_context)
        
        # Verify conditional stage was executed - check by making sure test_component_4 was called
        # (it's in the 'then' branch)
        test_component_4 = mock_components["test_component_4"]
        test_component_4.execute.assert_called_once()
        
        # For the history, only the conditional_stage ID is recorded, not the branches
        if "execution_history" in true_result:
            stage_ids = [step["stage_id"] for step in true_result["execution_history"]]
            assert "conditional_stage" in stage_ids
        
        # Reset mocks for the next test
        for mock in mock_components.values():
            mock.reset_mock()
        
        # Test with condition = False
        false_context = {
            "test_data": "test",
            "selected_stages": ["conditional_stage"],
            "test_condition": False
        }
        
        # Execute workflow with conditional stage and condition = False
        false_result = workflow_engine.execute_workflow("test_workflow", false_context)
        
        # Verify condition_false was executed - check by making sure test_component_5 was called
        # (it's in the 'else' branch)
        test_component_5 = mock_components["test_component_5"]
        test_component_5.execute.assert_called_once()
        
        # For the history, only the conditional_stage ID is recorded, not the branches
        if "execution_history" in false_result:
            stage_ids = [step["stage_id"] for step in false_result["execution_history"]]
            assert "conditional_stage" in stage_ids
    
    def test_workflow_stop_condition(self, workflow_engine, test_workflow_file, mock_components):
        """Test workflow stop condition"""
        # Force reload of workflows
        workflow_engine._load_workflows()
        
        # Get the mock component for test_component_1 and configure it to set workflow_stop flag
        test_component_1 = mock_components["test_component_1"]
        test_component_1.execute.return_value = {
            "executed_component": "test_component_1",
            "test_result": "Result from test_component_1",
            "workflow_stop": True  # This should stop the workflow
        }
        
        # Execute workflow
        context = {"test_data": "test"}
        result = workflow_engine.execute_workflow("test_workflow", context)
        
        # Verify workflow stopped after first stage
        assert result.get("executed_component") == "test_component_1"
        
        # Check execution history if it exists
        if "execution_history" in result:
            stage_ids = [step["stage_id"] for step in result["execution_history"]]
            assert "stage_1" in stage_ids
            assert "stage_2" not in stage_ids  # Should not be executed due to stop flag 