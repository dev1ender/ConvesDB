"""
Workflow engine for processing pipelines.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml

from app.core.exceptions import WorkflowError
from app.core.component_registry import ComponentRegistry
from app.core.stage_processor import StageProcessor
from app.utils.logging_setup import TICK_ICON, CROSS_ICON


class WorkflowEngine:
    """
    Engine for executing workflow pipelines.
    
    This class is responsible for:
    1. Loading workflow definitions
    2. Executing workflow stages in sequence
    3. Managing workflow context and data flow
    4. Handling errors and retries
    """
    
    def __init__(self, component_registry: ComponentRegistry, workflows_dir: Optional[str] = None):
        """
        Initialize the workflow engine.
        
        Args:
            component_registry: Component registry for accessing components
            workflows_dir: Directory containing workflow definitions
        """
        self.logger = logging.getLogger("core.workflow_engine")
        self.logger.debug(f"{TICK_ICON} WorkflowEngine initialized with workflows_dir={workflows_dir}")
        self.component_registry = component_registry
        self.workflows_dir = workflows_dir
        
        # Create stage processor
        self.stage_processor = StageProcessor(component_registry)
        
        # Dictionary of workflow definitions, keyed by workflow ID
        self._workflows: Dict[str, Dict[str, Any]] = {}
        
        # Load workflow definitions if directory is provided
        if workflows_dir:
            self.logger.debug("Loading workflows from directory.")
            self._load_workflows()
    
    def _load_workflows(self) -> None:
        """
        Load workflow definitions from the workflows directory.
        
        Raises:
            WorkflowError: If loading fails
        """
        self.logger.debug("Loading workflow definitions from workflows directory.")
        try:
            workflows_path = Path(self.workflows_dir)
            if not workflows_path.exists():
                raise WorkflowError(f"Workflows directory not found: {self.workflows_dir}")
            
            for workflow_file in workflows_path.glob("*.yaml"):
                try:
                    with open(workflow_file, 'r') as file:
                        workflow_def = yaml.safe_load(file)
                        
                        if 'workflow' in workflow_def and 'id' in workflow_def['workflow']:
                            workflow_id = workflow_def['workflow']['id']
                            self._workflows[workflow_id] = workflow_def
                            self.logger.debug(f"Loaded workflow: {workflow_id} from {workflow_file}")
                        else:
                            self.logger.warning(f"Skipping invalid workflow file: {workflow_file} (missing workflow.id)")
                except Exception as e:
                    self.logger.error(f"Error loading workflow file {workflow_file}: {str(e)}")
            
            self.logger.info(f"{TICK_ICON} Loaded {len(self._workflows)} workflow definitions")
        
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Failed to load workflows: {str(e)}")
            raise WorkflowError(f"Failed to load workflows: {str(e)}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow definition by ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dict[str, Any]: Workflow definition or None if not found
        """
        return self._workflows.get(workflow_id)
    
    def register_workflow(self, workflow_id: str, workflow_def: Dict[str, Any]) -> None:
        """
        Register a workflow definition.
        
        Args:
            workflow_id: Workflow identifier
            workflow_def: Workflow definition
        """
        self.logger.debug(f"Registering workflow: {workflow_id}")
        self._workflows[workflow_id] = workflow_def
        self.logger.info(f"{TICK_ICON} Registered workflow: {workflow_id}")
    
    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow by ID.
        
        Args:
            workflow_id: Workflow identifier
            context: Initial context for the workflow
                     If context contains 'selected_stages', only those stages will be executed
            
        Returns:
            Dict[str, Any]: Final workflow context
            
        Raises:
            WorkflowError: If workflow execution fails
        """
        self.logger.debug(f"Executing workflow: {workflow_id}")
        workflow_def = self.get_workflow(workflow_id)
        if not workflow_def:
            self.logger.error(f"{CROSS_ICON} Workflow not found: {workflow_id}")
            raise WorkflowError(f"Workflow not found: {workflow_id}")
        
        self.logger.info(f"{TICK_ICON} Executing workflow: {workflow_id}")
        
        try:
            # Create a copy of the context to avoid modifying the original
            workflow_context = context.copy()
            
            # Apply initial_context from workflow definition if present
            initial_context = workflow_def.get('workflow', {}).get('initial_context', {})
            if initial_context:
                self.logger.debug(f"Applying initial context from workflow definition: {initial_context}")
                workflow_context.update(initial_context)
            
            # Add workflow metadata to context
            workflow_context['workflow'] = {
                'id': workflow_id,
                'definition': workflow_def
            }
            
            # Get stages from workflow definition
            stages = workflow_def.get('workflow', {}).get('stages', [])
            if not stages:
                self.logger.warning(f"Workflow {workflow_id} has no stages defined")
                return workflow_context
            
            # Check if specific stages are requested
            selected_stages = workflow_context.get('selected_stages', None)
            if selected_stages:
                self.logger.info(f"Executing selected stages: {', '.join(selected_stages)}")
            
            # Execute each stage in sequence
            for stage_idx, stage_def in enumerate(stages):
                stage_id = stage_def.get('id', f"stage_{stage_idx}")
                
                # Skip disabled stages
                if stage_def.get('disabled', False):
                    self.logger.debug(f"Skipping disabled stage: {stage_id}")
                    continue
                
                # Skip stages not in selected_stages if specified
                if selected_stages and stage_id not in selected_stages:
                    self.logger.debug(f"Skipping non-selected stage: {stage_id}")
                    continue
                
                # Process stage based on type
                if 'condition' in stage_def:
                    # Conditional stage
                    workflow_context = self.stage_processor.process_conditional_stage(stage_def, workflow_context)
                else:
                    # Regular component stage
                    workflow_context = self.stage_processor.process_stage(stage_def, workflow_context)
                
                # Add stage result to execution history
                if 'execution_history' not in workflow_context:
                    workflow_context['execution_history'] = []
                workflow_context['execution_history'].append({
                    'stage_id': stage_id,
                    'status': workflow_context.get('last_stage', {}).get('status', 'unknown')
                })
                
                # Check for workflow stop condition
                if workflow_context.get('workflow_stop', False):
                    self.logger.info(f"Workflow {workflow_id} stopped early at stage {stage_id} due to stop condition")
                    break
                
                # Check if user wants response after this stage
                if workflow_context.get('return_after_stage', False):
                    self.logger.info(f"Returning early after stage {stage_id} as requested")
                    workflow_context['partial_execution'] = True
                    break
            
            # Clean up workflow context
            workflow_context.pop('current_stage', None)
            workflow_context.pop('return_after_stage', False)
            
            # Mark if this was a complete or partial execution
            if selected_stages:
                workflow_context['executed_stages'] = selected_stages
            
            self.logger.info(f"{TICK_ICON} Workflow {workflow_id} execution completed successfully")
            return workflow_context
        
        except Exception as e:
            self.logger.error(f"{CROSS_ICON} Workflow {workflow_id} execution failed: {str(e)}")
            raise WorkflowError(f"Workflow execution failed: {str(e)}")
    
    def list_workflows(self) -> List[str]:
        """
        Get a list of all available workflow IDs.
        
        Returns:
            List[str]: List of workflow IDs
        """
        return list(self._workflows.keys()) 