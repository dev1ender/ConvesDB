"""
Research agent component.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Tuple

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class ResearchAgent(BaseComponent):
    """
    Research agent component.
    
    This component uses LLM-based agents to perform research tasks
    by decomposing questions into sub-questions, exploring data sources,
    and synthesizing findings into comprehensive answers.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the research agent.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.llm_provider = self.get_config_value("llm_provider", "openai")
        self.llm_model = self.get_config_value("llm_model", "gpt-4")
        self.max_research_steps = self.get_config_value("max_research_steps", 5)
        self.max_sub_questions = self.get_config_value("max_sub_questions", 3)
        self.exploration_depth = self.get_config_value("exploration_depth", 2)
        self.include_citations = self.get_config_value("include_citations", True)
        
        # LLM client
        self._llm_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component to perform research.
        
        Args:
            context: Execution context containing research question
            
        Returns:
            Dict[str, Any]: Updated context with research findings
            
        Raises:
            ComponentRegistryError: If research process fails
        """
        self.logger.debug("Executing research agent")
        
        # Get research question from context
        question = context.get("research_question", context.get("query", ""))
        
        if not question:
            error_msg = "No research question found in context"
            self.logger.error(error_msg)
            return {"error": error_msg, "research_findings": {}}
        
        try:
            # Initialize LLM client if needed
            if not self._llm_client:
                self._initialize_llm_client()
            
            # Access database schema if available
            schema = context.get("schema", {})
            
            # Access search results if available
            search_results = context.get("search_results", [])
            
            # Get database connection from context if available
            connection = context.get("connection")
            
            # Get SQL executor if available
            sql_executor = context.get("query_executor")
            
            # Build research plan
            research_plan = self._create_research_plan(question, schema, search_results)
            
            # Execute research steps
            findings, citations = self._execute_research_steps(
                research_plan, 
                question, 
                schema, 
                search_results,
                connection,
                sql_executor,
                context
            )
            
            # Synthesize findings into a comprehensive answer
            answer = self._synthesize_answer(question, findings, citations)
            
            self.logger.debug(f"Research completed with {len(findings)} findings")
            
            # Return research results in context
            research_results = {
                "research_answer": answer,
                "research_findings": findings,
                "research_plan": research_plan,
                "citations": citations if self.include_citations else [],
                "research_agent": self.component_id
            }
            
            return research_results
        
        except Exception as e:
            error_msg = f"Research agent execution failed: {str(e)}"
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
    
    def _create_research_plan(self, question: str, schema: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a research plan by decomposing the question.
        
        Args:
            question: Main research question
            schema: Database schema
            search_results: Existing search results
            
        Returns:
            List[Dict[str, Any]]: Research plan with steps
        """
        # Build prompt for decomposing the question
        schema_str = json.dumps(schema, indent=2) if schema else "No schema provided"
        search_summary = self._summarize_search_results(search_results)
        
        prompt = (
            "You are a research planning assistant tasked with breaking down a complex question "
            "into a series of research steps. Create a plan to answer the following question:\n\n"
            
            f"Research Question: {question}\n\n"
        )
        
        # Add schema if available
        if schema:
            prompt += f"Available Database Schema:\n```json\n{schema_str}\n```\n\n"
        
        # Add search results if available
        if search_results:
            prompt += f"Available Search Results:\n{search_summary}\n\n"
        
        prompt += (
            "Create a research plan with up to 5 steps. Each step should include:\n"
            "1. A specific sub-question to investigate\n"
            "2. A suggested approach to answer it (SQL query, data analysis, etc.)\n"
            "3. Expected insights\n\n"
            
            "Format your response as JSON:\n"
            "```json\n"
            "{\n"
            '  "plan": [\n'
            '    {\n'
            '      "step_id": 1,\n'
            '      "sub_question": "...",\n'
            '      "approach": "...",\n'
            '      "expected_insights": "..."\n'
            '    },\n'
            '    ...\n'
            '  ]\n'
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
                parsed_plan = json.loads(json_str)
                
                # Limit the number of steps
                if "plan" in parsed_plan:
                    steps = parsed_plan["plan"]
                    if len(steps) > self.max_research_steps:
                        steps = steps[:self.max_research_steps]
                    
                    return steps
            
            # Fallback if JSON parsing fails
            self.logger.warning("Failed to parse research plan JSON, using default plan")
            
            # Create a simple default plan
            return [
                {
                    "step_id": 1,
                    "sub_question": question,
                    "approach": "Direct exploration",
                    "expected_insights": "Answer to the main question"
                }
            ]
        
        except Exception as e:
            self.logger.error(f"Error parsing research plan: {str(e)}")
            
            # Return a simple default plan
            return [
                {
                    "step_id": 1,
                    "sub_question": question,
                    "approach": "Direct exploration",
                    "expected_insights": "Answer to the main question"
                }
            ]
    
    def _execute_research_steps(
        self, 
        research_plan: List[Dict[str, Any]], 
        main_question: str,
        schema: Dict[str, Any],
        search_results: List[Dict[str, Any]],
        connection: Any = None,
        sql_executor: Any = None,
        context: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Execute each step in the research plan.
        
        Args:
            research_plan: Research steps to execute
            main_question: Main research question
            schema: Database schema
            search_results: Existing search results
            connection: Database connection if available
            sql_executor: SQL executor component if available
            context: Full execution context
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: Findings and citations
        """
        findings = []
        citations = []
        
        for step in research_plan:
            step_id = step.get("step_id", len(findings) + 1)
            sub_question = step.get("sub_question", "")
            approach = step.get("approach", "")
            
            self.logger.debug(f"Executing research step {step_id}: {sub_question}")
            
            # Skip empty sub-questions
            if not sub_question:
                continue
            
            # Execute the research step
            try:
                # Check if approach suggests SQL query
                if "sql" in approach.lower() or "query" in approach.lower():
                    # Generate SQL query for this step
                    sql_query = self._generate_sql_query(sub_question, schema)
                    
                    # Execute SQL query if executor is available
                    if sql_executor and connection:
                        step_context = {
                            "sql_query": sql_query,
                            "connection": connection
                        }
                        result = sql_executor.execute(step_context)
                        step_findings = {
                            "step_id": step_id,
                            "sub_question": sub_question,
                            "approach": "SQL Query",
                            "sql_query": sql_query,
                            "results": result.get("results", []),
                            "insights": self._extract_insights(sub_question, result.get("results", []))
                        }
                    else:
                        # Just generate insights without execution
                        step_findings = {
                            "step_id": step_id,
                            "sub_question": sub_question,
                            "approach": "SQL Query (not executed)",
                            "sql_query": sql_query,
                            "insights": f"SQL query generated but not executed: {sql_query}"
                        }
                else:
                    # Use LLM reasoning for this step
                    insights = self._reason_about_question(
                        sub_question, 
                        main_question, 
                        schema, 
                        search_results
                    )
                    
                    step_findings = {
                        "step_id": step_id,
                        "sub_question": sub_question,
                        "approach": "LLM Reasoning",
                        "insights": insights
                    }
                
                findings.append(step_findings)
                
                # Add citation if relevant search results were used
                if search_results:
                    relevant_sources = self._find_relevant_sources(sub_question, search_results)
                    if relevant_sources:
                        citations.append({
                            "step_id": step_id,
                            "sub_question": sub_question,
                            "sources": relevant_sources
                        })
            
            except Exception as e:
                self.logger.error(f"Error executing research step {step_id}: {str(e)}")
                findings.append({
                    "step_id": step_id,
                    "sub_question": sub_question,
                    "approach": "Failed",
                    "error": str(e),
                    "insights": "Research step failed"
                })
        
        return findings, citations
    
    def _generate_sql_query(self, question: str, schema: Dict[str, Any]) -> str:
        """
        Generate a SQL query to answer a specific question.
        
        Args:
            question: Question to answer
            schema: Database schema
            
        Returns:
            str: Generated SQL query
        """
        schema_str = json.dumps(schema, indent=2) if schema else "No schema provided"
        
        prompt = (
            "Generate a SQL query to answer the following question based on the provided schema.\n\n"
            
            f"Question: {question}\n\n"
        )
        
        if schema:
            prompt += f"Database Schema:\n```json\n{schema_str}\n```\n\n"
        
        prompt += (
            "Provide only the SQL query with no explanation or additional text.\n"
            "Make sure the query is safe, properly formatted, and addresses the question directly."
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
    
    def _reason_about_question(
        self, 
        question: str, 
        main_question: str, 
        schema: Dict[str, Any],
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Use LLM to reason about a specific question.
        
        Args:
            question: Question to reason about
            main_question: Main research question
            schema: Database schema
            search_results: Relevant search results
            
        Returns:
            str: Reasoning insights
        """
        schema_str = json.dumps(schema, indent=2) if schema else "No schema provided"
        search_summary = self._summarize_search_results(search_results)
        
        prompt = (
            "You are a research assistant tasked with answering a specific question that's part of a "
            "larger research task. Please provide insights to answer this question.\n\n"
            
            f"Main Research Question: {main_question}\n\n"
            
            f"Specific Question to Answer: {question}\n\n"
        )
        
        if schema:
            prompt += f"Available Database Information:\n```json\n{schema_str}\n```\n\n"
        
        if search_results:
            prompt += f"Relevant Information:\n{search_summary}\n\n"
        
        prompt += (
            "Provide a concise answer with clear insights that address the specific question.\n"
            "Focus on providing factual, evidence-based insights rather than speculation."
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        return response.strip()
    
    def _extract_insights(self, question: str, results: Any) -> str:
        """
        Extract insights from query results.
        
        Args:
            question: Question being addressed
            results: Query results
            
        Returns:
            str: Extracted insights
        """
        # Convert results to JSON string for prompt
        results_str = json.dumps(results, indent=2) if results else "No results"
        
        prompt = (
            "You are a data analyst tasked with extracting meaningful insights from query results. "
            "Analyze the following query results to answer a specific question.\n\n"
            
            f"Question: {question}\n\n"
            
            f"Query Results:\n```json\n{results_str}\n```\n\n"
            
            "Provide concise insights derived from these results that directly address the question. "
            "Focus on patterns, significant findings, and direct answers when possible. "
            "If the results do not contain relevant information, state that clearly."
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        return response.strip()
    
    def _synthesize_answer(
        self, 
        main_question: str, 
        findings: List[Dict[str, Any]], 
        citations: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize research findings into a comprehensive answer.
        
        Args:
            main_question: Main research question
            findings: Collected research findings
            citations: Source citations
            
        Returns:
            str: Synthesized answer
        """
        # Format findings for prompt
        findings_str = json.dumps(findings, indent=2) if findings else "No findings"
        
        prompt = (
            "You are a research synthesizer tasked with creating a comprehensive answer to a research question "
            "based on collected findings. Synthesize the following research findings into a clear, "
            "coherent answer.\n\n"
            
            f"Research Question: {main_question}\n\n"
            
            f"Research Findings:\n```json\n{findings_str}\n```\n\n"
            
            "Provide a comprehensive answer that:\n"
            "1. Directly addresses the research question\n"
            "2. Integrates insights from all relevant findings\n"
            "3. Is well-structured and easy to understand\n"
            "4. Acknowledges any limitations or areas of uncertainty\n\n"
            
            "Focus on being informative, accurate, and concise."
        )
        
        # Get response from LLM
        response = self._llm_client.generate(prompt)
        
        return response.strip()
    
    def _summarize_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Summarize search results for prompt context.
        
        Args:
            search_results: Search results to summarize
            
        Returns:
            str: Summarized search results
        """
        if not search_results:
            return "No search results available"
        
        summary = []
        for i, result in enumerate(search_results[:5], 1):  # Limit to first 5 results
            content = result.get("content", "")
            if content:
                # Truncate long content
                if len(content) > 300:
                    content = content[:300] + "..."
                
                summary.append(f"Source {i}: {content}")
        
        if len(search_results) > 5:
            summary.append(f"[{len(search_results) - 5} more sources not shown]")
        
        return "\n\n".join(summary)
    
    def _find_relevant_sources(self, question: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find sources relevant to a specific question.
        
        Args:
            question: Question to find relevant sources for
            search_results: Available search results
            
        Returns:
            List[Dict[str, Any]]: Relevant sources
        """
        relevant_sources = []
        
        for result in search_results:
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            
            # Simple relevance heuristic - could be enhanced with semantic matching
            if score > 0.7 or any(kw in content.lower() for kw in question.lower().split()):
                relevant_sources.append({
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "metadata": metadata,
                    "score": score
                })
        
        # Limit to top 3 sources
        return relevant_sources[:3]
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate max_research_steps
        steps = self.get_config_value("max_research_steps", 5)
        if not isinstance(steps, int) or steps <= 0:
            self.logger.warning("max_research_steps must be a positive integer")
            return False
        
        # Validate max_sub_questions
        sub_qs = self.get_config_value("max_sub_questions", 3)
        if not isinstance(sub_qs, int) or sub_qs <= 0:
            self.logger.warning("max_sub_questions must be a positive integer")
            return False
        
        # Validate exploration_depth
        depth = self.get_config_value("exploration_depth", 2)
        if not isinstance(depth, int) or depth <= 0:
            self.logger.warning("exploration_depth must be a positive integer")
            return False
        
        return True 