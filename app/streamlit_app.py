import streamlit as st
import json
import pandas as pd
from app.main import NLToSQLApp
from app.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager()
ui_config = config_manager.get_ui_config()

# Set page config
st.set_page_config(
    page_title=ui_config.get("page_title", "NL to SQL Converter"),
    page_icon=ui_config.get("page_icon", "🔍"),
    layout=ui_config.get("layout", "wide"),
)

# Initialize the application
@st.cache_resource
def get_app():
    app = NLToSQLApp()
    app.seed_database()
    return app

app = get_app()

# Add title and description
st.title("Natural Language to SQL Converter")
st.markdown("""
This application converts natural language questions into SQL queries and executes them.
Simply type your question about the database and get SQL and results!
""")

# Create two columns
col1, col2 = st.columns([2, 1])

# Database schema in the sidebar
with st.sidebar:
    st.header("Database Schema")
    
    schema_info = json.loads(app.get_schema_info())
    
    for table_name, table_info in schema_info["tables"].items():
        with st.expander(f"Table: {table_name}"):
            # Create a DataFrame for the columns
            columns_data = []
            for column in table_info["columns"]:
                col_data = {
                    "Name": column["name"],
                    "Type": column["type"],
                    "PK": "✓" if column.get("primary_key") else "",
                    "Nullable": "No" if not column.get("nullable", True) else "Yes"
                }
                columns_data.append(col_data)
                
            st.dataframe(pd.DataFrame(columns_data), hide_index=True)
    
    # Relationships
    if schema_info.get("relationships"):
        with st.expander("Relationships"):
            for rel in schema_info["relationships"]:
                st.write(f"• {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
    
    # Display configuration info
    with st.expander("Configuration"):
        st.write("**LLM Provider:**", config_manager.get_llm_provider())
        st.write("**Database:**", config_manager.get("database.type"))
        
        # LLM configuration
        st.write("**LLM Model:**", 
                 config_manager.get("llm.openai.model") 
                 if config_manager.is_using_openai() 
                 else config_manager.get("llm.ollama.model"))

# Main interface
with col1:
    # Input for natural language question
    question = st.text_area("Enter your question", height=100, 
                           placeholder="e.g., How many orders did John Doe make?")
    
    # Button to process the question
    if st.button("Convert to SQL and Run"):
        if question:
            with st.spinner("Processing..."):
                # Process the question
                response = app.process_question(question)
                
                # Display the SQL query
                st.subheader("Generated SQL")
                st.code(response["sql_query"], language="sql")
                
                # Display error if any
                if response["error"]:
                    st.error(f"Error: {response['error']}")
                
                # Display results if available
                elif response["results"]:
                    st.subheader("Query Results")
                    st.dataframe(pd.DataFrame(response["results"]), hide_index=True)
                    
                    # Show number of results
                    st.info(f"Query returned {len(response['results'])} results")
                else:
                    st.info("Query executed successfully but returned no results")
        else:
            st.warning("Please enter a question")

# Example questions
with col2:
    st.subheader("Example Questions")
    example_questions = [
        "How many orders did each customer make?",
        "What is the most expensive product?",
        "List all customers who ordered headphones",
        "What is the total value of all orders?",
        "How many products cost more than $500?",
    ]
    
    for example in example_questions:
        if st.button(example):
            # Set the example as the current question
            st.session_state.question = example
            # Rerun to update the text area
            st.experimental_rerun()

# Footer
st.markdown("---")
st.caption("Built with Streamlit, LangChain, and SQLite")

# Initialize session state for example questions
if 'question' in st.session_state:
    # This will be executed when the app reruns after clicking an example
    question = st.session_state.question 