"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

CLI entry point for the conversDB application.
"""

import os
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from app.core import get_app, process_query, get_available_workflows, get_workflow_stages
from app.utils.logging_setup import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup application logger
logger = get_logger(__name__)

def main():
    """Main function for CLI application."""
    # Set up logging
    setup_logging("INFO")
    logger.info("Starting CLI application")
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="NLP processing command line interface")
    parser.add_argument("--interactive", action="store_true", help="Enter interactive mode")
    parser.add_argument("--workflow", type=str, help="Specify workflow to use")
    parser.add_argument("--stage", type=str, help="Specify specific stage(s) to execute (comma-separated)")
    parser.add_argument("--list-workflows", action="store_true", help="List available workflows")
    parser.add_argument("--list-stages", type=str, help="List stages for a specified workflow")
    parser.add_argument("--query", type=str, help="Process a single query")
    
    args = parser.parse_args()
    
    # Get application instance
    app = get_app()
    logger.info("Application initialized")
    
    # List workflows if requested
    if args.list_workflows:
        workflows = get_available_workflows()
        print("\nAvailable Workflows:")
        for workflow in workflows:
            print(f"  - {workflow}")
        return
    
    # List stages for a workflow if requested
    if args.list_stages:
        workflow_id = args.list_stages
        stages = get_workflow_stages(workflow_id)
        if not stages:
            print(f"No stages found for workflow: {workflow_id}")
            return
            
        print(f"\nStages for workflow '{workflow_id}':")
        for i, stage in enumerate(stages):
            stage_id = stage.get('id', f"stage_{i}")
            status = "✓ Enabled" if not stage.get('disabled', False) else "✗ Disabled"
            component = f"{stage.get('component_type', 'unknown')}/{stage.get('component_id', 'unknown')}"
            print(f"  - {stage_id} [{status}]: {component}")
        return
    
    # Process a single query if provided
    if args.query:
        query = args.query
        logger.info(f"Processing query: '{query}'")
        print(f"\nQuery: {query}")
        
        # Prepare stages if specified
        stages_to_execute = None
        if args.stage:
            stages_to_execute = args.stage.split(',')
        
        # Execute query with specified workflow and stages
        workflow = args.workflow
        response = process_query(query, 
                                context={"workflow_id": workflow} if workflow else None,
                                stages_to_execute=stages_to_execute)
        
        # Display results
        print_query_results(response)
        return
    
    # Enter interactive mode if requested or no specific action was provided
    if args.interactive or not (args.list_workflows or args.list_stages or args.query):
        enter_interactive_mode(args.workflow, args.stage)
    
    logger.info("Application shutdown")

def print_query_results(response):
    """Print the results of a query in a formatted way."""
    # Get result fields
    result = response.get('result', {})
    execution_history = response.get('execution_history', [])
    error = response.get('error')
    
    # Print execution history if available
    if execution_history:
        print("\nExecution History:")
        for step in execution_history:
            print(f"  - Stage {step['stage_id']}: {step['status']}")
    
    # Print error if any
    if error:
        print(f"\nError: {error}")
    
    # Print result information
    if result:
        print("\nResult:")
        for key, value in result.items():
            if isinstance(value, dict) or isinstance(value, list):
                print(f"  {key}: {json.dumps(value, indent=2)}")
            else:
                print(f"  {key}: {value}")
    
    # Print additional context information if available
    if 'partial_execution' in response:
        print("\nNote: This was a partial workflow execution")
        
    if 'executed_stages' in response:
        print(f"Executed stages: {', '.join(response['executed_stages'])}")

def enter_interactive_mode(workflow=None, stages=None):
    """Enter interactive mode for processing queries."""
    print("\nEntering interactive mode. Type 'exit' to quit.")
    print("Type 'workflows' to list available workflows.")
    print("Type 'stages <workflow_id>' to list stages for a workflow.")
    print("Type 'use workflow <workflow_id>' to set current workflow.")
    print("Type 'use stage <stage_id>' to set stages to execute.")
    
    # Current workflow and stages
    current_workflow = workflow
    current_stages = stages.split(',') if stages else None
    
    while True:
        try:
            # Print current context
            if current_workflow or current_stages:
                context_info = []
                if current_workflow:
                    context_info.append(f"workflow: {current_workflow}")
                if current_stages:
                    context_info.append(f"stages: {', '.join(current_stages)}")
                print(f"\n[Context: {' | '.join(context_info)}]")
            
            # Get user input
            user_input = input("\nEnter query (or command): ")
            
            # Handle exit command
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Handle workflows command
            if user_input.lower() == "workflows":
                workflows = get_available_workflows()
                print("\nAvailable Workflows:")
                for workflow in workflows:
                    print(f"  - {workflow}")
                continue
            
            # Handle stages command
            if user_input.lower().startswith("stages "):
                workflow_id = user_input[7:].strip()
                stages = get_workflow_stages(workflow_id)
                if not stages:
                    print(f"No stages found for workflow: {workflow_id}")
                    continue
                    
                print(f"\nStages for workflow '{workflow_id}':")
                for i, stage in enumerate(stages):
                    stage_id = stage.get('id', f"stage_{i}")
                    status = "✓ Enabled" if not stage.get('disabled', False) else "✗ Disabled"
                    component = f"{stage.get('component_type', 'unknown')}/{stage.get('component_id', 'unknown')}"
                    print(f"  - {stage_id} [{status}]: {component}")
                continue
            
            # Handle use workflow command
            if user_input.lower().startswith("use workflow "):
                workflow_id = user_input[13:].strip()
                current_workflow = workflow_id
                print(f"Set current workflow to: {current_workflow}")
                continue
            
            # Handle use stage command
            if user_input.lower().startswith("use stage "):
                stage_ids = user_input[10:].strip()
                current_stages = stage_ids.split(',')
                print(f"Set stages to execute: {', '.join(current_stages)}")
                continue
            
            # Process query
            response = process_query(
                user_input, 
                context={"workflow_id": current_workflow} if current_workflow else None,
                stages_to_execute=current_stages
            )
            
            # Display results
            print_query_results(response)
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 