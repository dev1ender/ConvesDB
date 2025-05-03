"""
Copyright (c) 2024 dev1ender

This file is part of conversDB.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

Streamlit entry point for the conversDB application.
To run: streamlit run commands/streamlit_app.py
"""

import streamlit as st
import json
import pandas as pd
from app.core import get_app, process_query, get_available_workflows, get_workflow_stages

# Set page config
st.set_page_config(
    page_title="NLP Processing Application",
    page_icon="🔍",
    layout="wide",
)

# Initialize application on first load
if 'initialized' not in st.session_state:
    # Get application instance
    app = get_app()
    st.session_state.initialized = True
    st.session_state.current_workflow = None
    st.session_state.selected_stages = []

# Add title and description
st.title("Natural Language Processing Application")
st.markdown("""
This application processes natural language queries through configurable workflows.
You can select different workflows and specific stages to execute.
""")

# Create columns layout
col1, col2 = st.columns([2, 1])

# Sidebar with workflow and stage selection
with st.sidebar:
    st.header("Workflow Settings")
    
    # Get available workflows
    workflows = get_available_workflows()
    
    # Workflow selector
    selected_workflow = st.selectbox(
        "Select Workflow",
        options=workflows,
        index=0 if workflows else None,
        key="workflow_selector"
    )
    
    # Update session state when workflow changes
    if selected_workflow != st.session_state.current_workflow:
        st.session_state.current_workflow = selected_workflow
        st.session_state.selected_stages = []
    
    # Get stages for selected workflow
    if selected_workflow:
        stages = get_workflow_stages(selected_workflow)
        stage_options = []
        
        for i, stage in enumerate(stages):
            # Skip disabled stages
            if stage.get('disabled', False):
                continue
                
            stage_id = stage.get('id', f"stage_{i}")
            component = f"{stage.get('component_type', '')}/{stage.get('component_id', '')}"
            stage_options.append({"id": stage_id, "label": f"{stage_id} ({component})"})
        
        # Create stage selector with stage IDs as options
        selected_stage_indices = st.multiselect(
            "Select Stages to Execute (optional)",
            options=[stage["id"] for stage in stage_options],
            format_func=lambda x: next((s["label"] for s in stage_options if s["id"] == x), x),
            key="stage_selector"
        )
        
        # Update session state
        st.session_state.selected_stages = selected_stage_indices
    
    # Show workflow information
    if selected_workflow:
        with st.expander("Workflow Details"):
            workflow = get_app().workflow_engine.get_workflow(selected_workflow)
            if workflow:
                workflow_info = workflow.get("workflow", {})
                st.write(f"**Description:** {workflow_info.get('description', 'No description')}")
                st.write(f"**Total Stages:** {len(workflow_info.get('stages', []))}")

# Main interface
with col1:
    # Input for natural language query
    query = st.text_area("Enter your query", height=100, 
                        placeholder="e.g., What insights can you provide about this data?")
    
    # Process button
    if st.button("Process Query"):
        if query:
            with st.spinner("Processing..."):
                # Process the query with selected workflow and stages
                response = process_query(
                    query=query,
                    context={"workflow_id": st.session_state.current_workflow},
                    stages_to_execute=st.session_state.selected_stages or None
                )
                
                # Display execution history
                if "execution_history" in response:
                    st.subheader("Execution History")
                    history_data = []
                    for step in response["execution_history"]:
                        history_data.append({
                            "Stage": step["stage_id"],
                            "Status": step["status"]
                        })
                    st.dataframe(pd.DataFrame(history_data), hide_index=True)
                
                # Display error if any
                if response.get("error"):
                    st.error(f"Error: {response['error']}")
                
                # Display results
                result = response.get("result", {})
                if result:
                    st.subheader("Results")
                    
                    # For each field in the result
                    for key, value in result.items():
                        if isinstance(value, dict):
                            # Format nested dictionaries
                            st.json(value)
                        elif isinstance(value, list):
                            # Format lists based on content
                            if len(value) > 0 and isinstance(value[0], dict):
                                st.dataframe(pd.DataFrame(value), hide_index=True)
                            else:
                                st.write(f"**{key}:**")
                                for item in value:
                                    st.write(f"- {item}")
                        else:
                            # Format simple values
                            st.write(f"**{key}:** {value}")
                            
                else:
                    st.info("No results returned from processing")
        else:
            st.warning("Please enter a query")

# Example queries panel
with col2:
    st.subheader("Example Queries")
    example_queries = [
        "What are the key features of this product?",
        "Can you summarize the main points in this text?",
        "What data sources support this conclusion?",
        "Find similar documents to this one",
        "Why is this trend happening?",
    ]
    
    for example in example_queries:
        if st.button(example):
            # Set the example as the current query
            st.session_state.query = example
            # Rerun to update the text area
            st.experimental_rerun()

# Footer
st.markdown("---")
st.caption("Built with Streamlit and LangChain")

# Initialize session state for example queries
if 'query' in st.session_state:
    # This will be executed when the app reruns after clicking an example
    query = st.session_state.query 