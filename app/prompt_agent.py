from typing import Dict, List, Any, Optional
from app.schema_agent import SchemaAgent
from app.logging_setup import get_logger
import logging

# Setup module logger
logger = get_logger(__name__)

class PromptAgent:
    """Agent responsible for constructing effective prompts for SQL generation."""
    
    def __init__(self, schema_agent: SchemaAgent):
        self.schema_agent = schema_agent
        logger.debug("PromptAgent initialized")
    
    def build_prompt(self, user_question: str, relevant_tables: Optional[List[str]] = None) -> str:
        """Build a comprehensive prompt for the LLM to generate SQL."""
        logger.info(f"Building prompt for question: '{user_question}'")
        
        # If relevant tables not provided, try to determine them
        if relevant_tables is None:
            logger.debug("No relevant tables provided, determining automatically")
            relevant_tables = self.schema_agent.get_relevant_tables(user_question)
        
        logger.debug(f"Using relevant tables: {', '.join(relevant_tables) if relevant_tables else 'None'}")
        
        # Find related tables through relationships
        schema = self.schema_agent.schema_cache
        related_tables = set()
        
        # Add all tables that are related to our relevant tables through relationships
        for rel in schema.get("relationships", []):
            if rel["from_table"] in relevant_tables and rel["to_table"] not in relevant_tables:
                related_tables.add(rel["to_table"])
                logger.debug(f"Adding related table {rel['to_table']} (referenced by {rel['from_table']})")
            elif rel["to_table"] in relevant_tables and rel["from_table"] not in relevant_tables:
                related_tables.add(rel["from_table"])
                logger.debug(f"Adding related table {rel['from_table']} (references {rel['to_table']})")
        
        # Also find tables that are related to our related tables (secondary relationships)
        secondary_tables = set()
        for rel in schema.get("relationships", []):
            if rel["from_table"] in related_tables and rel["to_table"] not in relevant_tables and rel["to_table"] not in related_tables:
                secondary_tables.add(rel["to_table"])
                logger.debug(f"Adding secondary related table {rel['to_table']} (referenced by {rel['from_table']})")
            elif rel["to_table"] in related_tables and rel["from_table"] not in relevant_tables and rel["from_table"] not in related_tables:
                secondary_tables.add(rel["from_table"])
                logger.debug(f"Adding secondary related table {rel['from_table']} (references {rel['to_table']})")
        
        # For complex queries about people (customers), ensure customers table is included
        if any(term in user_question.lower() for term in ["customer", "person", "people", "who", "john", "jane", "bob"]):
            if "customers" not in relevant_tables and "customers" not in related_tables and "customers" not in secondary_tables:
                secondary_tables.add("customers")
                logger.debug("Adding customers table due to person-related question")
        
        # Combine all tables for schema context
        all_tables = list(relevant_tables) + list(related_tables) + list(secondary_tables)
        logger.debug(f"Tables for schema context: {', '.join(all_tables)}")
        
        # Extract schema information for all tables
        schema_context = ""
        
        if all_tables:
            schema_context += "# Database Schema Information\n\n"
            
            # First describe any views that are relevant
            views = [table_name for table_name in all_tables if table_name.startswith('vw_')]
            tables = [table_name for table_name in all_tables if not table_name.startswith('vw_')]
            
            if views:
                schema_context += "## Pre-computed Aggregated Views\n\n"
                schema_context += "The following views contain pre-computed aggregated data that can be more efficient to query directly:\n\n"
                
                for view_name in views:
                    view_schema = self.schema_agent.get_table_schema(view_name)
                    if not view_schema:
                        logger.warning(f"View schema not found for view: {view_name}")
                        continue
                    
                    # Get view description
                    view_description = ""
                    if view_name in schema.get("views", {}):
                        view_description = schema["views"][view_name].get("description", "")
                    
                    schema_context += f"View: {view_name}\n"
                    if view_description:
                        schema_context += f"Description: {view_description}\n"
                    schema_context += "Columns:\n"
                    
                    for column in view_schema.get("columns", []):
                        column_desc = f"- {column['name']} ({column['type']})"
                        schema_context += column_desc + "\n"
                    
                    schema_context += "\n"
                
                # Add usage examples for views
                schema_context += self._generate_view_usage_examples(views) + "\n\n"
            
            # Then describe regular tables
            if tables:
                schema_context += "## Database Tables\n\n"
                
                for table_name in tables:
                    table_schema = self.schema_agent.get_table_schema(table_name)
                    if not table_schema:
                        logger.warning(f"Table schema not found for table: {table_name}")
                        continue
                    
                    schema_context += f"Table: {table_name}\n"
                    schema_context += "Columns:\n"
                    
                    for column in table_schema.get("columns", []):
                        column_desc = f"- {column['name']} ({column['type']})"
                        
                        if column.get("primary_key"):
                            column_desc += " PRIMARY KEY"
                        
                        if not column.get("nullable", True):
                            column_desc += " NOT NULL"
                            
                        schema_context += column_desc + "\n"
                    
                    schema_context += "\n"
            
            # Add relationships if any
            relationships = [r for r in schema.get("relationships", []) 
                           if r["from_table"] in all_tables or r["to_table"] in all_tables]
            
            if relationships:
                logger.debug(f"Adding {len(relationships)} relationships to prompt")
                schema_context += "## Relationships\n\n"
                for rel in relationships:
                    schema_context += f"- {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}\n"
                schema_context += "\n"
        
        # Construct the full prompt
        system_prompt = f"""You are a SQL expert that converts natural language questions into SQL queries. 
Follow these guidelines:

1. Generate ONLY SQLite-compatible SQL queries
2. Return ONLY the SQL query without any explanations or markdown formatting
3. Use proper JOIN syntax when querying across tables
4. Use appropriate WHERE clauses to filter results
5. If aggregations like COUNT, SUM, AVG are needed, use them correctly with GROUP BY as needed
6. Ensure your query directly answers the user's question
7. When pre-computed aggregated views are available, use them instead of calculating the same metrics from raw tables
8. Consider query performance, especially when dealing with large tables or complex joins

{schema_context}

User Question: {user_question}

SQL Query:
"""
        
        logger.debug(f"Prompt schema context length: {len(schema_context)} characters")
        logger.debug(f"Full prompt length: {len(system_prompt)} characters")
        
        if logger.isEnabledFor(logging.DEBUG):
            # Only log the full prompt if debug logging is enabled (to avoid excessive logs)
            logger.debug(f"Full prompt: \n{system_prompt}")
        
        logger.info("Prompt generation complete")
        return system_prompt
    
    def _generate_view_usage_examples(self, views: List[str]) -> str:
        """Generate example SQL queries for using views."""
        example_queries = "### View Usage Examples\n\n"
        
        # Add specific examples for known views
        view_examples = {
            "vw_product_sales_summary": [
                "-- Example: Get products with highest sales revenue",
                "SELECT product_name, category, total_revenue",
                "FROM vw_product_sales_summary",
                "ORDER BY total_revenue DESC",
                "LIMIT 10;",
                "",
                "-- Instead of the more complex equivalent:",
                "-- SELECT p.name AS product_name, p.category, SUM(oi.line_total) AS total_revenue",
                "-- FROM products p",
                "-- JOIN order_items oi ON p.product_id = oi.product_id",
                "-- JOIN orders o ON oi.order_id = o.order_id",
                "-- WHERE oi.status != 'cancelled'",
                "-- GROUP BY p.product_id, p.name, p.category",
                "-- ORDER BY total_revenue DESC",
                "-- LIMIT 10;"
            ],
            "vw_customer_purchase_summary": [
                "-- Example: Find top customers by total spend",
                "SELECT customer_name, email, total_spent, order_count",
                "FROM vw_customer_purchase_summary",
                "ORDER BY total_spent DESC",
                "LIMIT 5;"
            ],
            "vw_monthly_sales_trends": [
                "-- Example: Get monthly sales for the past year",
                "SELECT month, order_count, total_revenue, average_order_value",
                "FROM vw_monthly_sales_trends",
                "ORDER BY month DESC",
                "LIMIT 12;"
            ],
            "vw_inventory_status_summary": [
                "-- Example: Find products that need restocking",
                "SELECT product_name, total_quantity, locations_needing_restock",
                "FROM vw_inventory_status_summary",
                "WHERE locations_needing_restock > 0",
                "ORDER BY total_quantity ASC;"
            ],
            "vw_product_review_stats": [
                "-- Example: Find highest rated products",
                "SELECT product_name, average_rating, review_count",
                "FROM vw_product_review_stats",
                "WHERE review_count >= 5",
                "ORDER BY average_rating DESC, review_count DESC",
                "LIMIT 10;"
            ]
        }
        
        for view in views:
            if view in view_examples:
                example_queries += f"Examples for {view}:\n```sql\n"
                example_queries += "\n".join(view_examples[view])
                example_queries += "\n```\n\n"
        
        return example_queries
    
    def build_error_correction_prompt(self, original_query: str, error_message: str, 
                                      schema_context: str) -> str:
        """Build a prompt to correct a SQL query that failed."""
        logger.info("Building error correction prompt")
        logger.debug(f"Original query with error: {original_query}")
        logger.debug(f"Error message: {error_message}")
        
        error_correction_prompt = f"""You are a SQL expert who corrects errors in SQL queries.

Original Query:
{original_query}

Error Message:
{error_message}

Database Schema:
{schema_context}

Please correct the SQL query to fix the error. Return ONLY the corrected SQL query without explanations or markdown.

Corrected SQL Query:
"""
        
        logger.debug(f"Error correction prompt length: {len(error_correction_prompt)} characters")
        logger.info("Error correction prompt generated")
        return error_correction_prompt 