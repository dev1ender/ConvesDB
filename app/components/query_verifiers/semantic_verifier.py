"""
Semantic verifier component.
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class SemanticVerifier(BaseComponent):
    """
    Query semantic verification component.
    
    This component uses language models to verify that queries match the
    user's intent and are semantically valid against the schema.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the semantic verifier.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.llm_provider = self.get_config_value("llm_provider", "openai")
        self.llm_model = self.get_config_value("llm_model", "gpt-4")
        self.confidence_threshold = self.get_config_value("confidence_threshold", 0.7)
        self.verification_points = self.get_config_value("verification_points", [
            "schema_alignment",
            "intent_alignment",
            "security_check",
            "ambiguity_check"
        ])
        
        # LLM client
        self._llm_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to verify query semantics.
        
        Args:
            context: Execution context containing the query and schema
            
        Returns:
            Dict[str, Any]: Updated context with verification result
            
        Raises:
            ComponentRegistryError: If verification fails
        """
        self.logger.debug("Verifying query semantics")
        
        # Get required data from context
        query = context.get("query", "")
        sql_query = context.get("sql_query", "")
        schema = context.get("schema", {})
        original_question = context.get("original_question", query)
        
        # Validate inputs
        if not sql_query:
            error_msg = "No SQL query found in context"
            self.logger.error(error_msg)
            return {"is_valid": False, "error": error_msg}
        
        if not schema:
            self.logger.warning("No schema found in context, semantic verification may be less accurate")
        
        try:
            # Initialize LLM client if needed
            if not self._llm_client:
                self._initialize_llm_client()
            
            # Build verification prompt
            prompt = self._build_verification_prompt(
                sql_query=sql_query,
                schema=schema,
                original_question=original_question
            )
            
            # Send prompt to LLM
            self.logger.debug("Sending verification prompt to LLM")
            verification_result = self._llm_client.generate(prompt)
            
            # Parse verification result
            parsed_result = self._parse_verification_result(verification_result)
            is_valid = parsed_result.get("is_valid", False)
            confidence = parsed_result.get("confidence", 0.0)
            feedback = parsed_result.get("feedback", "")
            
            # Log verification result
            if is_valid:
                self.logger.debug(f"Query semantically verified with confidence {confidence}")
            else:
                self.logger.warning(f"Query semantic verification failed: {feedback}")
            
            # Return verification result in context
            return {
                "is_valid": is_valid and confidence >= self.confidence_threshold,
                "semantic_verified": is_valid,
                "verification_confidence": confidence,
                "verification_feedback": feedback,
                "verification_details": parsed_result.get("details", {}),
                "semantic_verifier": self.component_id
            }
        
        except Exception as e:
            error_msg = f"Error verifying query semantics: {str(e)}"
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
    
    def _build_verification_prompt(self, sql_query: str, schema: Dict[str, Any], original_question: str) -> str:
        """
        Build verification prompt for the LLM.
        
        Args:
            sql_query: SQL query to verify
            schema: Database schema
            original_question: Original user question
            
        Returns:
            str: Verification prompt
        """
        # Format schema for prompt
        schema_str = json.dumps(schema, indent=2) if schema else "No schema provided"
        
        # Base prompt
        prompt = (
            "You are a database expert tasked with verifying if a SQL query correctly and safely "
            "addresses the user's question and follows best practices. Please analyze the following:\n\n"
            
            f"Original Question: {original_question}\n\n"
            
            f"SQL Query to Verify:\n```sql\n{sql_query}\n```\n\n"
        )
        
        # Add schema if available
        if schema:
            prompt += f"Database Schema:\n```json\n{schema_str}\n```\n\n"
        
        # Add verification points
        prompt += "Please evaluate the query on the following points:\n"
        
        if "schema_alignment" in self.verification_points:
            prompt += "1. Schema Alignment: Does the query reference tables and columns that exist in the schema?\n"
        
        if "intent_alignment" in self.verification_points:
            prompt += "2. Intent Alignment: Does the query correctly address the user's question?\n"
        
        if "security_check" in self.verification_points:
            prompt += "3. Security Check: Is the query free from potential SQL injection or other security issues?\n"
        
        if "ambiguity_check" in self.verification_points:
            prompt += "4. Ambiguity Check: Is the query unambiguous and likely to return the expected results?\n"
        
        # Response format instructions
        prompt += (
            "\nProvide your analysis in the following JSON format:\n"
            "```json\n"
            "{\n"
            '  "is_valid": true/false,\n'
            '  "confidence": 0.0-1.0,\n'
            '  "feedback": "brief overall assessment",\n'
            '  "details": {\n'
            '    "schema_alignment": {"valid": true/false, "issues": ["issue1", "issue2"]},\n'
            '    "intent_alignment": {"valid": true/false, "issues": ["issue1", "issue2"]},\n'
            '    "security_check": {"valid": true/false, "issues": ["issue1", "issue2"]},\n'
            '    "ambiguity_check": {"valid": true/false, "issues": ["issue1", "issue2"]}\n'
            "  }\n"
            "}\n"
            "```"
        )
        
        return prompt
    
    def _parse_verification_result(self, result: str) -> Dict[str, Any]:
        """
        Parse verification result from LLM.
        
        Args:
            result: LLM response
            
        Returns:
            Dict[str, Any]: Parsed verification result
        """
        try:
            # Extract JSON from response
            json_start = result.find("{")
            json_end = result.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = result[json_start:json_end + 1]
                parsed = json.loads(json_str)
                return parsed
            
            # Fallback if JSON parsing fails
            self.logger.warning("Failed to parse JSON from LLM response, using fallback parsing")
            
            # Simple fallback parsing
            is_valid = "is_valid: true" in result.lower() or "\"is_valid\": true" in result.lower()
            
            # Extract confidence if available
            confidence = 0.5  # Default confidence
            confidence_match = re.search(r'confidence["\']?\s*:\s*(0\.\d+|1\.0)', result)
            if confidence_match:
                confidence = float(confidence_match.group(1))
            
            # Extract feedback if available
            feedback = "No detailed feedback available"
            feedback_match = re.search(r'feedback["\']?\s*:\s*["\']([^"\']+)["\']', result)
            if feedback_match:
                feedback = feedback_match.group(1)
            
            return {
                "is_valid": is_valid,
                "confidence": confidence,
                "feedback": feedback,
                "details": {}
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing verification result: {str(e)}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "feedback": f"Error parsing verification result: {str(e)}",
                "details": {}
            }
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate confidence_threshold
        threshold = self.get_config_value("confidence_threshold", 0.7)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            self.logger.warning("confidence_threshold must be a number between 0 and 1")
            return False
        
        # Validate verification_points
        points = self.get_config_value("verification_points", [])
        valid_points = ["schema_alignment", "intent_alignment", "security_check", "ambiguity_check"]
        if not isinstance(points, list) or not all(point in valid_points for point in points):
            self.logger.warning(f"verification_points must be a list containing only: {', '.join(valid_points)}")
            return False
        
        return True 