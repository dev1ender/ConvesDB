"""
Fact checking agent component.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Tuple

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class FactCheckingAgent(BaseComponent):
    """
    Fact checking agent component.
    
    This component uses LLM-based agents to verify the factual accuracy
    of statements by checking against reference data, search results,
    and database queries.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the fact checking agent.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.llm_provider = self.get_config_value("llm_provider", "openai")
        self.llm_model = self.get_config_value("llm_model", "gpt-4")
        self.verification_threshold = self.get_config_value("verification_threshold", 0.8)
        self.include_evidence = self.get_config_value("include_evidence", True)
        self.max_evidence_items = self.get_config_value("max_evidence_items", 3)
        self.confidence_levels = self.get_config_value("confidence_levels", [
            "Verified", 
            "Likely True", 
            "Uncertain", 
            "Likely False", 
            "Refuted"
        ])
        
        # LLM client
        self._llm_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to verify facts.
        
        Args:
            context: Execution context containing statements to verify
            
        Returns:
            Dict[str, Any]: Updated context with verification results
            
        Raises:
            ComponentRegistryError: If verification process fails
        """
        self.logger.debug("Executing fact checking agent")
        
        # Get statements to verify from context
        statements = context.get("statements_to_verify", [])
        
        if not statements:
            error_msg = "No statements to verify found in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "verification_results": []}
        
        try:
            # Initialize LLM client if needed
            if not self._llm_client:
                self._initialize_llm_client()
            
            # Access reference data if available
            reference_data = context.get("reference_data", [])
            
            # Access search results if available
            search_results = context.get("search_results", [])
            
            # Access database schema if available
            schema = context.get("schema", {})
            
            # Get database connection from context if available
            connection = context.get("connection")
            
            # Get SQL executor if available
            sql_executor = context.get("query_executor")
            
            # Verify each statement
            verification_results = []
            for statement in statements:
                # Verify the statement
                result = self._verify_statement(
                    statement,
                    reference_data,
                    search_results,
                    schema,
                    connection,
                    sql_executor
                )
                
                verification_results.append(result)
            
            self.logger.debug(f"Fact checking completed for {len(statements)} statements")
            
            # Return verification results in context
            return {
                "verification_results": verification_results,
                "fact_checking_agent": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Fact checking agent execution failed: {str(e)}"
            self.logger.error(error_msg)
            raise ComponentRegistryError(error_msg)
    
    def _initialize_llm_client(self) -> None:
        """
        Initialize the LLM client.
        
        Raises:
            ComponentRegistryError: If client initialization fails
        """
        try:
            factory = LLMFactory()
            self._llm_client = factory.get_llm_client(
                provider=self.llm_provider,
                model_name=self.llm_model
            )
            
            self.logger.debug(f"Initialized LLM client: {self.llm_provider}/{self.llm_model}")
        
        except Exception as e:
            raise ComponentRegistryError(f"Failed to initialize LLM client: {str(e)}")
    
    def _verify_statement(
        self,
        statement: str,
        reference_data: List[Dict[str, Any]],
        search_results: List[Dict[str, Any]],
        schema: Dict[str, Any],
        connection: Any = None,
        sql_executor: Any = None
    ) -> Dict[str, Any]:
        """
        Verify a single statement against available data sources.
        
        Args:
            statement: Statement to verify
            reference_data: Reference data for verification
            search_results: Search results for verification
            schema: Database schema
            connection: Database connection if available
            sql_executor: SQL executor component if available
            
        Returns:
            Dict[str, Any]: Verification result
        """
        self.logger.debug(f"Verifying statement: {statement[:50]}...")
        
        # Collect evidence from different sources
        evidence = []
        
        # Check reference data
        reference_evidence = self._check_reference_data(statement, reference_data)
        if reference_evidence:
            evidence.extend(reference_evidence)
        
        # Check search results
        search_evidence = self._check_search_results(statement, search_results)
        if search_evidence:
            evidence.extend(search_evidence)
        
        # Query database if available
        if schema and sql_executor and connection:
            sql_evidence = self._check_database(statement, schema, connection, sql_executor)
            if sql_evidence:
                evidence.extend(sql_evidence)
        
        # Determine verification status based on evidence
        if evidence:
            verification = self._assess_verification(statement, evidence)
        else:
            # No evidence found
            verification = {
                "status": "Uncertain",
                "confidence": 0.5,
                "reason": "No relevant evidence found to verify or refute the statement."
            }
        
        # Prepare verification result
        result = {
            "statement": statement,
            "verification": verification,
            "evidence": evidence[:self.max_evidence_items] if self.include_evidence else []
        }
        
        return result
    
    def _check_reference_data(self, statement: str, reference_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check statement against reference data.
        
        Args:
            statement: Statement to verify
            reference_data: Reference data for verification
            
        Returns:
            List[Dict[str, Any]]: Evidence from reference data
        """
        if not reference_data:
            return []
        
        evidence = []
        
        # Determine relevant reference items
        reference_items = self._find_relevant_references(statement, reference_data)
        
        for item in reference_items:
            content = item.get("content", "")
            metadata = item.get("metadata", {})
            
            # Create evidence item
            evidence_item = {
                "source": "reference_data",
                "content": content,
                "metadata": metadata,
                "relevance": item.get("relevance", 0.0)
            }
            
            evidence.append(evidence_item)
        
        return evidence
    
    def _check_search_results(self, statement: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check statement against search results.
        
        Args:
            statement: Statement to verify
            search_results: Search results for verification
            
        Returns:
            List[Dict[str, Any]]: Evidence from search results
        """
        if not search_results:
            return []
        
        evidence = []
        
        # Find relevant search results
        relevant_results = self._find_relevant_sources(statement, search_results)
        
        for result in relevant_results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            
            # Create evidence item
            evidence_item = {
                "source": "search_results",
                "content": content,
                "metadata": metadata,
                "relevance": result.get("score", 0.0)
            }
            
            evidence.append(evidence_item)
        
        return evidence
    
    def _check_database(
        self, 
        statement: str, 
        schema: Dict[str, Any],
        connection: Any,
        sql_executor: Any
    ) -> List[Dict[str, Any]]:
        """
        Check statement against database by generating and executing queries.
        
        Args:
            statement: Statement to verify
            schema: Database schema
            connection: Database connection
            sql_executor: SQL executor component
            
        Returns:
            List[Dict[str, Any]]: Evidence from database
        """
        evidence = []
        
        try:
            # Generate verification query
            sql_query = self._generate_verification_query(statement, schema)
            
            # Execute query
            query_context = {
                "sql_query": sql_query,
                "connection": connection
            }
            
            result = sql_executor.execute(query_context)
            query_results = result.get("results", [])
            
            if query_results:
                # Analyze query results
                analysis = self._analyze_query_results(statement, query_results)
                
                # Create evidence item
                evidence_item = {
                    "source": "database",
                    "sql_query": sql_query,
                    "results": query_results,
                    "analysis": analysis,
                    "relevance": 0.9  # Database evidence is considered highly relevant
                }
                
                evidence.append(evidence_item)
        
        except Exception as e:
            self.logger.error(f"Error checking database for statement verification: {str(e)}")
        
        return evidence
    
    def _generate_verification_query(self, statement: str, schema: Dict[str, Any]) -> str:
        """
        Generate SQL query to verify a statement.
        
        Args:
            statement: Statement to verify
            schema: Database schema
            
        Returns:
            str: Generated SQL query
        """
        schema_str = json.dumps(schema, indent=2) if schema else "No schema provided"
        
        prompt = (
            "Generate a SQL query to verify the following statement based on the provided database schema. "
            "The query should return data that can help confirm or refute the statement.\n\n"
            
            f"Statement to verify: {statement}\n\n"
            
            f"Database Schema:\n```json\n{schema_str}\n```\n\n"
            
            "Generate a SQL query that:\n"
            "1. Is targeted specifically to verify the statement\n"
            "2. Is safe and properly formatted\n"
            "3. Returns only relevant data needed for verification\n"
            "4. Uses appropriate filters to find exact matches or relevant records\n\n"
            
            "Provide only the SQL query with no explanation or additional text."
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        # Extract SQL query from response
        sql_query = response.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "", 1)
        if sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "", 1)
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    
    def _analyze_query_results(self, statement: str, results: Any) -> str:
        """
        Analyze query results to determine if they verify the statement.
        
        Args:
            statement: Statement being verified
            results: Query results to analyze
            
        Returns:
            str: Analysis of how results relate to statement
        """
        # Convert results to JSON string for prompt
        results_str = json.dumps(results, indent=2) if results else "No results"
        
        prompt = (
            "Analyze these database query results to determine if they verify, refute, or are inconclusive "
            "regarding the following statement. Provide a brief, objective analysis.\n\n"
            
            f"Statement: {statement}\n\n"
            
            f"Query Results:\n```json\n{results_str}\n```\n\n"
            
            "Provide a concise analysis focusing on how the data relates to the statement's accuracy. "
            "Be objective and focus only on what the data explicitly shows."
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        return response.strip()
    
    def _find_relevant_references(self, statement: str, reference_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find reference data relevant to the statement.
        
        Args:
            statement: Statement to verify
            reference_data: Available reference data
            
        Returns:
            List[Dict[str, Any]]: Relevant reference items with relevance scores
        """
        relevant_items = []
        
        for item in reference_data:
            content = item.get("content", "")
            
            # Simple relevance calculation - could be enhanced with semantic matching
            keywords = statement.lower().split()
            content_lower = content.lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            
            if matches > 0:
                relevance = min(1.0, matches / len(keywords))
                
                if relevance > 0.3:  # Only include items with reasonable relevance
                    relevant_item = item.copy()
                    relevant_item["relevance"] = relevance
                    relevant_items.append(relevant_item)
        
        # Sort by relevance (highest first)
        relevant_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Return top 5 most relevant items
        return relevant_items[:5]
    
    def _find_relevant_sources(self, statement: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find sources relevant to a statement.
        
        Args:
            statement: Statement to find relevant sources for
            search_results: Available search results
            
        Returns:
            List[Dict[str, Any]]: Relevant sources
        """
        relevant_sources = []
        
        for result in search_results:
            content = result.get("content", "")
            score = result.get("score", 0)
            
            # Simple relevance check - could be enhanced with semantic matching
            if score > 0.7 or any(kw in content.lower() for kw in statement.lower().split()):
                relevant_sources.append(result)
        
        # Limit to top 5 sources
        return relevant_sources[:5]
    
    def _assess_verification(self, statement: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess verification status based on collected evidence.
        
        Args:
            statement: Statement being verified
            evidence: Collected evidence
            
        Returns:
            Dict[str, Any]: Verification assessment
        """
        # Format evidence for prompt
        evidence_str = json.dumps(evidence, indent=2)
        
        prompt = (
            "You are a fact verification expert. Based on the provided evidence, assess the factual "
            "accuracy of the following statement. Provide an objective assessment with a confidence level.\n\n"
            
            f"Statement: {statement}\n\n"
            
            f"Evidence:\n```json\n{evidence_str}\n```\n\n"
            
            "Determine if the statement is:\n"
            "- Verified (statement is fully supported by evidence)\n"
            "- Likely True (evidence mostly supports the statement)\n"
            "- Uncertain (evidence is inconclusive or contradictory)\n"
            "- Likely False (evidence mostly contradicts the statement)\n"
            "- Refuted (statement is directly contradicted by evidence)\n\n"
            
            "Also provide a confidence score from 0.0 to 1.0, where 1.0 is highest confidence.\n\n"
            
            "Format your response as JSON:\n"
            "```json\n"
            "{\n"
            '  "status": "one of the verification statuses above",\n'
            '  "confidence": 0.X,\n'
            '  "reason": "A brief explanation of your assessment based on the evidence"\n'
            "}\n"
            "```"
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end + 1]
                assessment = json.loads(json_str)
                
                # Validate assessment
                if "status" in assessment and "confidence" in assessment and "reason" in assessment:
                    # Ensure status is one of the allowed values
                    if assessment["status"] not in self.confidence_levels:
                        assessment["status"] = "Uncertain"
                    
                    # Ensure confidence is within range
                    confidence = float(assessment.get("confidence", 0.5))
                    assessment["confidence"] = max(0.0, min(1.0, confidence))
                    
                    return assessment
            
            # Fallback if JSON parsing fails
            self.logger.warning("Failed to parse verification assessment JSON, using default assessment")
        
        except Exception as e:
            self.logger.error(f"Error parsing verification assessment: {str(e)}")
        
        # Default assessment if parsing fails
        return {
            "status": "Uncertain",
            "confidence": 0.5,
            "reason": "Unable to determine verification status due to processing error."
        }
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate verification_threshold
        threshold = self.get_config_value("verification_threshold", 0.8)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            self.logger.warning("verification_threshold must be a number between 0 and 1")
            return False
        
        # Validate max_evidence_items
        max_items = self.get_config_value("max_evidence_items", 3)
        if not isinstance(max_items, int) or max_items <= 0:
            self.logger.warning("max_evidence_items must be a positive integer")
            return False
        
        # Validate confidence_levels
        levels = self.get_config_value("confidence_levels", [])
        if not isinstance(levels, list) or len(levels) < 2:
            self.logger.warning("confidence_levels must be a list with at least 2 elements")
            return False
        
        return True 