"""
Stage processor for workflow execution.

This module provides functionality for executing individual workflow stages.
"""

import logging
from typing import Any, Dict, Optional

from app.core.component_registry import ComponentRegistry
from app.core.exceptions import WorkflowError


class StageProcessor:
    """
    Processor for workflow stages.
    
    This class is responsible for:
    1. Processing individual workflow stages
    2. Managing stage context and execution flow
    3. Handling stage errors and reporting results
    """
    
    def __init__(self, component_registry: ComponentRegistry):
        """
        Initialize the stage processor.
        
        Args:
            component_registry: Registry for accessing components
        """
        self.logger = logging.getLogger("core.stage_processor")
        self.component_registry = component_registry
    
    def process_stage(self, stage_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a workflow stage.
        
        Args:
            stage_def: Stage definition
            context: Execution context
            
        Returns:
            Dict[str, Any]: Updated context after stage execution
            
        Raises:
            WorkflowError: If stage execution fails
        """
        # Extract stage information
        stage_id = stage_def.get('id', 'unknown')
        component_type = stage_def.get('component_type')
        component_id = stage_def.get('component_id')
        config = stage_def.get('config', {})
        
        self.logger.debug(f"Processing stage: {stage_id} with {component_type}/{component_id}")
        
        # Validate stage definition
        if not component_type or not component_id:
            raise WorkflowError(f"Invalid stage definition: missing component_type or component_id in stage {stage_id}")
        
        # Skip disabled stages
        if stage_def.get('disabled', False):
            self.logger.debug(f"Skipping disabled stage: {stage_id}")
            return context
        
        # Get component
        component = self.component_registry.get_component(component_type, component_id)
        if not component:
            raise WorkflowError(f"Component not found for stage {stage_id}: {component_type}/{component_id}")
        
        # Create stage context (copy of input context plus stage metadata)
        stage_context = context.copy()
        stage_context['current_stage'] = {
            'id': stage_id,
            'component_type': component_type,
            'component_id': component_id,
            'config': config
        }
        
        # Special handling for task_agent component to pass task_type and task_description
        if component_type == "agents" and component_id == "task_agent":
            if 'task_type' in config and 'task_type' not in stage_context:
                stage_context['task_type'] = config['task_type']
                self.logger.debug(f"Adding task_type to context: {config['task_type']}")
            
            if 'task_description' in config and 'task_description' not in stage_context:
                stage_context['task_description'] = config['task_description']
                self.logger.debug(f"Adding task_description to context: {config['task_description']}")
        
        # Override component config if specified in stage
        original_config = None
        if config:
            # Save original config
            if hasattr(component, 'config'):
                original_config = component.config.copy()
                
                # Merge configs (stage config takes precedence)
                merged_config = original_config.copy()
                merged_config.update(config)
                component.config = merged_config
        
        try:
            # Execute component
            self.logger.debug(f"Executing component: {component_id}")
            result = component.execute(stage_context)
            
            # Restore original config if needed
            if original_config is not None:
                component.config = original_config
            
            # Handle result
            if result is None:
                self.logger.warning(f"Component {component_id} returned None, using original context")
                return context
            
            if isinstance(result, dict):
                # Merge result into input context
                updated_context = context.copy()
                updated_context.update(result)
                
                # Add stage result metadata
                updated_context['last_stage'] = {
                    'id': stage_id,
                    'status': 'success'
                }
                
                return updated_context
            else:
                # Non-dict result, add to context as stage_result
                context['stage_result'] = result
                context['last_stage'] = {
                    'id': stage_id,
                    'status': 'success'
                }
                
                return context
        
        except Exception as e:
            # Restore original config if needed
            if original_config is not None:
                component.config = original_config
            
            # Handle error based on error policy
            error_policy = stage_def.get('error_policy', 'fail')
            error_msg = f"Error in stage {stage_id}: {str(e)}"
            
            if error_policy == 'continue':
                self.logger.warning(f"{error_msg}, continuing")
                
                # Add error to context
                context['last_stage'] = {
                    'id': stage_id,
                    'status': 'error',
                    'error': str(e)
                }
                
                return context
            else:
                # Rethrow error
                self.logger.error(error_msg)
                raise WorkflowError(error_msg) from e
    
    def process_conditional_stage(self, stage_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a conditional workflow stage.
        
        Args:
            stage_def: Stage definition
            context: Execution context
            
        Returns:
            Dict[str, Any]: Updated context after stage execution
            
        Raises:
            WorkflowError: If stage execution fails
        """
        stage_id = stage_def.get('id', 'unknown')
        condition = stage_def.get('condition', {})
        
        self.logger.debug(f"Processing conditional stage: {stage_id}")
        
        # Evaluate condition
        condition_type = condition.get('type', 'value_check')
        
        if condition_type == 'value_check':
            # Simple value check: check if a context key equals a value
            key = condition.get('key')
            value = condition.get('value')
            
            if key is None:
                raise WorkflowError(f"Invalid condition in stage {stage_id}: missing key")
            
            # Get actual value from context (supports dot notation)
            parts = key.split('.')
            actual_value = context
            for part in parts:
                if isinstance(actual_value, dict) and part in actual_value:
                    actual_value = actual_value[part]
                else:
                    actual_value = None
                    break
            
            # Check condition
            if condition.get('operator', 'eq') == 'eq':
                condition_met = (actual_value == value)
            elif condition.get('operator') == 'neq':
                condition_met = (actual_value != value)
            elif condition.get('operator') == 'contains':
                condition_met = isinstance(actual_value, str) and value in actual_value
            elif condition.get('operator') == 'in':
                condition_met = actual_value in value if isinstance(value, (list, tuple)) else False
            elif condition.get('operator') == 'exists':
                condition_met = actual_value is not None
            else:
                raise WorkflowError(f"Invalid operator in condition for stage {stage_id}")
        
        elif condition_type == 'python':
            # Python expression (use with caution)
            expression = condition.get('expression')
            if not expression:
                raise WorkflowError(f"Invalid python condition in stage {stage_id}: missing expression")
            
            try:
                # Evaluate expression with context
                condition_met = eval(expression, {"__builtins__": {}}, {"context": context})
            except Exception as e:
                raise WorkflowError(f"Error evaluating condition in stage {stage_id}: {str(e)}")
        
        else:
            raise WorkflowError(f"Unknown condition type in stage {stage_id}: {condition_type}")
        
        # Execute appropriate branch
        if condition_met:
            if 'then' in stage_def:
                return self.process_stage(stage_def['then'], context)
        else:
            if 'else' in stage_def:
                return self.process_stage(stage_def['else'], context)
        
        # No branch taken
        return context 