"""
Base workflow implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from app.interfaces.workflow import Workflow
from app.core.component_registry import ComponentRegistry
from app.core.exceptions import WorkflowError


class BaseWorkflow(Workflow):
    """
    Base implementation of the Workflow interface.
    
    This class provides common functionality for all workflows and
    should be extended by concrete workflow implementations.
    """
    
    def __init__(self, workflow_id: str, component_registry: ComponentRegistry, stages: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the base workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            component_registry: Registry for accessing components
            stages: List of stage definitions
        """
        self.workflow_id = workflow_id
        self.component_registry = component_registry
        self.stages = stages or []
        self.logger = logging.getLogger(f"workflows.{self.__class__.__name__.lower()}")
        self.logger.debug(f"Creating workflow {workflow_id} with {len(self.stages)} stages")
    
    def get_id(self) -> str:
        """
        Get the workflow identifier.
        
        Returns:
            str: Workflow identifier
        """
        return self.workflow_id
    
    def get_stages(self) -> List[Dict[str, Any]]:
        """
        Get the workflow stages.
        
        Returns:
            List[Dict[str, Any]]: List of stage definitions
        """
        return self.stages
    
    def add_stage(self, stage_def: Dict[str, Any]) -> None:
        """
        Add a stage to the workflow.
        
        Args:
            stage_def: Stage definition
        """
        self.stages.append(stage_def)
        self.logger.debug(f"Added stage {stage_def.get('id', len(self.stages))} to workflow {self.workflow_id}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            context: Initial context for the workflow
            
        Returns:
            Dict[str, Any]: Final workflow context after execution
            
        Raises:
            WorkflowError: If workflow execution fails
        """
        self.logger.info(f"Executing workflow: {self.workflow_id}")
        
        try:
            # Create a copy of the context to avoid modifying the original
            workflow_context = context.copy()
            
            # Add workflow metadata to context
            workflow_context['workflow'] = {
                'id': self.workflow_id,
                'stages': len(self.stages)
            }
            
            # Execute each stage in sequence
            for stage_idx, stage_def in enumerate(self.stages):
                stage_id = stage_def.get('id', f"stage_{stage_idx}")
                
                # Skip disabled stages
                if stage_def.get('disabled', False):
                    self.logger.debug(f"Skipping disabled stage: {stage_id}")
                    continue
                
                # Execute the stage
                try:
                    workflow_context = self.execute_stage(stage_id, workflow_context)
                    
                    # Check for any stop conditions
                    if workflow_context.get('workflow_stop', False):
                        self.logger.info(f"Workflow {self.workflow_id} stopped early at stage {stage_id} due to stop condition")
                        break
                
                except Exception as e:
                    # Handle stage failure based on error policy
                    error_policy = stage_def.get('error_policy', 'fail')
                    
                    if error_policy == 'continue':
                        self.logger.warning(f"Error in workflow {self.workflow_id} stage {stage_id}, continuing: {str(e)}")
                        workflow_context['stage_error'] = str(e)
                    else:
                        raise WorkflowError(f"Error in workflow {self.workflow_id} stage {stage_id}: {str(e)}")
            
            self.logger.info(f"Workflow {self.workflow_id} execution completed successfully")
            return workflow_context
        
        except Exception as e:
            self.logger.error(f"Workflow {self.workflow_id} execution failed: {str(e)}")
            raise WorkflowError(f"Workflow execution failed: {str(e)}")
    
    def execute_stage(self, stage_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific stage of the workflow.
        
        Args:
            stage_id: Identifier of the stage to execute
            context: Context for the stage execution
            
        Returns:
            Dict[str, Any]: Updated context after stage execution
            
        Raises:
            WorkflowError: If stage execution fails
        """
        # Find the stage definition
        stage_def = None
        stage_idx = -1
        
        for idx, stage in enumerate(self.stages):
            if stage.get('id') == stage_id or (not 'id' in stage and f"stage_{idx}" == stage_id):
                stage_def = stage
                stage_idx = idx
                break
        
        if not stage_def:
            raise WorkflowError(f"Stage not found in workflow {self.workflow_id}: {stage_id}")
        
        self.logger.debug(f"Executing workflow stage: {stage_id}")
        
        # Get stage components
        component_type = stage_def.get('component_type')
        component_id = stage_def.get('component_id')
        
        if not component_type or not component_id:
            raise WorkflowError(f"Invalid stage definition in workflow {self.workflow_id}: missing component_type or component_id")
        
        # Get component from registry
        component = self.component_registry.get_component(component_type, component_id)
        if not component:
            raise WorkflowError(f"Component not found for stage {stage_id}: {component_type}/{component_id}")
        
        # Add stage metadata to context
        stage_context = context.copy()
        stage_context['current_stage'] = {
            'id': stage_id,
            'index': stage_idx,
            'component_type': component_type,
            'component_id': component_id,
            'config': stage_def.get('config', {})
        }
        
        # Execute component
        result = component.execute(stage_context)
        
        # Merge result into context
        if isinstance(result, dict):
            context.update(result)
        else:
            context['stage_result'] = result
        
        return context
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get workflow metadata.
        
        Returns:
            Dict[str, Any]: Workflow metadata
        """
        metadata = super().get_metadata()
        metadata.update({
            "workflow_type": self.__class__.__name__,
            "component_types": self._get_component_types()
        })
        return metadata
    
    def _get_component_types(self) -> List[str]:
        """
        Get list of component types used in this workflow.
        
        Returns:
            List[str]: List of component types
        """
        component_types = set()
        
        for stage in self.stages:
            if 'component_type' in stage:
                component_types.add(stage['component_type'])
        
        return list(component_types) 