"""
Task agent component.
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.components.base_component import BaseComponent
from app.core.exceptions import ComponentRegistryError
from app.llm.factory import LLMFactory


class TaskAgent(BaseComponent):
    """
    Task agent component.
    
    This component uses LLM-based agents to execute specific tasks
    by planning, executing, and validating a sequence of actions.
    """
    
    def __init__(self, component_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the task agent.
        
        Args:
            component_id: Unique identifier for the component
            config: Configuration parameters for the component
        """
        super().__init__(component_id, config)
        
        # Configuration options with defaults
        self.llm_provider = self.get_config_value("llm_provider", "openai")
        self.llm_model = self.get_config_value("llm_model", "gpt-4")
        self.max_iterations = self.get_config_value("max_iterations", 5)
        self.reflection_enabled = self.get_config_value("reflection_enabled", True)
        self.allowed_tasks = self.get_config_value("allowed_tasks", [
            "data_analysis", 
            "query_generation", 
            "text_summarization",
            "information_extraction"
        ])
        self.tools = self.get_config_value("tools", {})
        
        # Get default task type and description if provided in config
        self.default_task_type = self.get_config_value("task_type", "")
        self.default_task_description = self.get_config_value("task_description", "")
        
        # LLM client
        self._llm_client = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task agent.
        
        Args:
            context: Context for the task
            
        Returns:
            Dict[str, Any]: Updated context with task results
        """
        task_type = context.get('task_type', self.config.get('task_type'))
        if not task_type:
            self.logger.warning("No task type provided in context or config")
            return context
        
        task_description = context.get('task_description', self.config.get('task_description'))
        if not task_description:
            self.logger.warning("No task description provided in context or config")
            return context
        
        self.logger.debug(f"Executing task agent")
        
        # Initialize LLM client if not already initialized
        if not hasattr(self, 'llm_client') or self.llm_client is None:
            self._init_llm_client()
        
        # Generate or load task plan
        if not hasattr(self, 'task_plan') or not self.task_plan:
            self._generate_task_plan(task_type, task_description)
        
        # Store plan in context
        context['task_plan'] = self.task_plan
        
        # Execute task steps
        results = {'steps': [], 'success': True}
        
        for step in self.task_plan:
            step_id = step.get('step_id')
            action = step.get('action')
            inputs = step.get('inputs', [])
            
            self.logger.debug(f"Executing task step {step_id}: {action}")
            
            # Check if required inputs are in context
            for input_key in inputs:
                if input_key not in context:
                    self.logger.warning(f"Required input '{input_key}' not found in context")
            
            # Execute the step based on the action
            step_result = self._execute_step(step, context)
            
            # Record step results
            results['steps'].append({
                'step_id': step_id,
                'action': action,
                'success': True if step_result else False,
                'output': step_result
            })
            
            # Break if step failed and is critical
            if not step_result and step.get('critical', True):
                results['success'] = False
                break
        
        # Handle SQL query generation task specifically
        if task_type == 'query_generation' and not self._has_sql_query(results):
            # If the model didn't generate a SQL query, use a template approach
            query_text = context.get('query', '')
            schema = context.get('schema', {})
            
            # Generate SQL query using a template
            sql_query = self._generate_sql_from_template(query_text, schema)
            
            # Add the SQL query to the results
            if sql_query:
                results['final_output'] = sql_query
                context['sql_query'] = sql_query
        
        # Store final output
        if 'final_output' not in results:
            best_step_output = self._get_best_step_output(results['steps'])
            results['final_output'] = best_step_output
            
            # For query generation, store in the context
            if task_type == 'query_generation' and best_step_output:
                # Try to extract SQL query from text
                sql_query = self._extract_sql_query(best_step_output)
                if sql_query:
                    context['sql_query'] = sql_query
        
        # Add validation info
        results['validation'] = self._validate_results(results, task_type, task_description)
        
        # Store results in context
        context['task_results'] = results
        
        self.logger.debug(f"Task execution completed: {task_type}")
        return context
    
    def _has_sql_query(self, results: Dict[str, Any]) -> bool:
        """
        Check if the results contain a SQL query.
        
        Args:
            results: Task results
            
        Returns:
            bool: True if a SQL query is found
        """
        if not results or 'final_output' not in results:
            return False
            
        output = results.get('final_output', '')
        
        # Check if the output contains a SQL statement
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
        output_upper = output.upper()
        
        return any(keyword in output_upper for keyword in sql_keywords)
    
    def _extract_sql_query(self, text: str) -> Optional[str]:
        """
        Extract SQL query from text.
        
        Args:
            text: Text that may contain a SQL query
            
        Returns:
            Optional[str]: Extracted SQL query or None
        """
        # Look for SQL query in text (simple heuristics)
        if not text:
            return None
            
        # Try to find a SQL query between code blocks
        import re
        sql_blocks = re.findall(r'```sql\s*(.*?)\s*```', text, re.DOTALL)
        if sql_blocks:
            return sql_blocks[0].strip()
            
        # Try to find statements that look like SQL
        lines = text.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            
            # Check if line contains SQL keywords
            if re.search(r'\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE)\b', line, re.IGNORECASE):
                in_sql = True
                sql_lines.append(line)
            elif in_sql and line and not line.startswith('#') and not line.startswith('--'):
                sql_lines.append(line)
            elif in_sql and not line:
                # Empty line might end SQL block
                in_sql = False
        
        if sql_lines:
            return '\n'.join(sql_lines)
            
        return None
    
    def _generate_sql_from_template(self, query_text: str, schema: Dict[str, Any]) -> Optional[str]:
        """
        Generate a simple SQL query from a template based on the question.
        
        Args:
            query_text: The question to answer
            schema: Database schema information
            
        Returns:
            Optional[str]: Generated SQL query or None
        """
        # Simplistic approach for common query patterns
        if not query_text or not schema:
            return None
            
        query_lower = query_text.lower()
        
        # Handle "How many" questions
        if "how many" in query_lower:
            # Check what entity is being counted
            if "customers" in query_lower and "active" in query_lower:
                return "SELECT COUNT(*) FROM customers WHERE status = 'active'"
            
            if "customers" in query_lower:
                return "SELECT COUNT(*) FROM customers"
                
            if "orders" in query_lower:
                return "SELECT COUNT(*) FROM orders"
                
            if "products" in query_lower:
                return "SELECT COUNT(*) FROM products"
                
            # Generic count for other entities
            for table_name in schema.get('tables', {}).keys():
                if table_name.lower() in query_lower:
                    return f"SELECT COUNT(*) FROM {table_name}"
        
        # Handle "List/Show all" questions
        if any(x in query_lower for x in ["list", "show", "get", "display"]):
            # Check what entity is being listed
            for table_name in schema.get('tables', {}).keys():
                if table_name.lower() in query_lower:
                    columns = [col['name'] for col in schema['tables'][table_name].get('columns', [])[:5]]
                    if columns:
                        return f"SELECT {', '.join(columns)} FROM {table_name} LIMIT 10"
                    else:
                        return f"SELECT * FROM {table_name} LIMIT 10"
        
        # If we couldn't generate a template, return None
        return None
    
    def _init_llm_client(self) -> None:
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
    
    def _generate_task_plan(
        self, 
        task_type: str, 
        task_description: str,
        available_tools: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Generate a task execution plan.
        
        Args:
            task_type: Type of task to perform
            task_description: Description of the task
            available_tools: Optional dictionary of available tools
        """
        self.logger.debug(f"Generating task plan for {task_type}: {task_description}")
        
        # Use default task templates based on task type
        if task_type == "query_generation":
            self.task_plan = [
                {
                    "step_id": 1,
                    "action": "Generate SQL query",
                    "inputs": ["query", "schema"],
                    "tools": ["sql_generation"],
                    "description": "Generate SQL query based on user question and database schema"
                }
            ]
        elif task_type == "data_analysis":
            self.task_plan = [
                {
                    "step_id": 1,
                    "action": "Analyze data and extract insights",
                    "inputs": ["data", "analysis_type"],
                    "tools": ["data_analysis"],
                    "description": "Analyze data to extract relevant insights based on analysis type"
                }
            ]
        elif task_type == "text_summarization":
            self.task_plan = [
                {
                    "step_id": 1,
                    "action": "Summarize text content",
                    "inputs": ["text", "max_length"],
                    "tools": ["text_processing"],
                    "description": "Generate a concise summary of the text content"
                }
            ]
        elif task_type == "information_extraction":
            self.task_plan = [
                {
                    "step_id": 1,
                    "action": "Extract structured information",
                    "inputs": ["text", "extraction_type"],
                    "tools": ["information_extraction"],
                    "description": "Extract structured information from text based on extraction type"
                }
            ]
        else:
            self.task_plan = [
                {
                    "step_id": 1,
                    "action": f"Execute {task_type}",
                    "inputs": ["context"],
                    "tools": [],
                    "description": task_description
                }
            ]
    
    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a single step in the task plan.
        
        Args:
            step: Task step to execute
            context: Execution context
            
        Returns:
            Any: Step execution result
        """
        step_id = step.get("step_id")
        action = step.get("action")
        inputs = step.get("inputs", [])
        tools = step.get("tools", [])
        
        self.logger.debug(f"Executing task step {step_id}: {action}")
        
        # Skip empty actions
        if not action:
            return None
        
        # Execute the step based on the action
        try:
            # Get required inputs from context if available
            step_inputs = {}
            for input_name in inputs:
                if input_name in context:
                    step_inputs[input_name] = context[input_name]
                else:
                    self.logger.warning(f"Required input '{input_name}' not found in context")
            
            # Execute action based on type
            if "analyze" in action.lower() or "data_analysis" in action.lower():
                step_output = self._execute_analysis_action(action, step_inputs, tools, context)
            
            elif "generate" in action.lower() or "query" in action.lower():
                step_output = self._execute_generation_action(action, step_inputs, tools, context)
            
            elif "summarize" in action.lower() or "summarization" in action.lower():
                step_output = self._execute_summarization_action(action, step_inputs, tools, context)
            
            elif "extract" in action.lower() or "extraction" in action.lower():
                step_output = self._execute_extraction_action(action, step_inputs, tools, context)
            
            else:
                # Generic LLM-based action for unknown types
                step_output = self._execute_generic_action(action, step_inputs, tools, context)
            
            # Record step result
            step_result = {
                "step_id": step_id,
                "action": action,
                "success": True,
                "output": step_output
            }
            
            # Update context with step output
            for key, value in step_result.items():
                if key != "step_id" and key != "action":
                    context[f"step_{step_id}_{key}"] = value
            
            return step_output
        
        except Exception as e:
            self.logger.error(f"Error executing task step {step_id}: {str(e)}")
            
            step_result = {
                "step_id": step_id,
                "action": action,
                "success": False,
                "error": str(e)
            }
            
            # Mark overall task as failed
            return None
    
    def _execute_analysis_action(
        self, 
        action: str, 
        inputs: Dict[str, Any], 
        tools: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute a data analysis action.
        
        Args:
            action: Action description
            inputs: Action inputs
            tools: Required tools
            context: Execution context
            
        Returns:
            Any: Analysis results
        """
        # Get data to analyze
        data = inputs.get("data", inputs.get("results", []))
        
        if not data:
            self.logger.warning("No data found for analysis action")
            return {"error": "No data found for analysis"}
        
        # Format data for prompt
        data_str = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
        
        # Build analysis prompt
        prompt = (
            "You are a data analysis expert tasked with analyzing data to extract meaningful insights. "
            "Please analyze the following data and provide insights.\n\n"
            
            f"Analysis Task: {action}\n\n"
            
            f"Data to Analyze:\n```\n{data_str}\n```\n\n"
        )
        
        if "question" in inputs:
            prompt += f"Specific Question: {inputs['question']}\n\n"
        
        prompt += (
            "Provide a thorough analysis with specific insights. Include:\n"
            "1. Key observations and patterns\n"
            "2. Significant findings\n"
            "3. Answers to specific questions if provided\n"
            "4. Recommendations based on the data\n\n"
            
            "Format your analysis in a clear, structured manner suitable for a business audience."
        )
        
        # Get response from LLM
        analysis = self._llm_client.generate(prompt)
        
        return analysis.strip()
    
    def _execute_generation_action(
        self, 
        action: str, 
        inputs: Dict[str, Any], 
        tools: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute a generation action (e.g., SQL query).
        
        Args:
            action: Action description
            inputs: Action inputs
            tools: Required tools
            context: Execution context
            
        Returns:
            Any: Generated content
        """
        # Determine what type of content to generate
        generate_type = "query"  # Default
        if "generate_sql" in action.lower():
            generate_type = "sql"
        elif "generate_prompt" in action.lower():
            generate_type = "prompt"
        elif "generate_summary" in action.lower():
            generate_type = "summary"
        
        # Get relevant inputs
        prompt_base = (
            "You are a content generation expert tasked with creating high-quality content "
            f"based on specific requirements. Please generate a {generate_type}.\n\n"
            
            f"Generation Task: {action}\n\n"
        )
        
        # Add specific inputs based on generation type
        if generate_type == "sql":
            # For SQL generation
            schema = inputs.get("schema", context.get("schema", {}))
            question = inputs.get("question", "")
            
            if schema:
                schema_str = json.dumps(schema, indent=2)
                prompt_base += f"Database Schema:\n```json\n{schema_str}\n```\n\n"
            
            if question:
                prompt_base += f"Question to Answer: {question}\n\n"
            
            prompt_base += (
                "Generate a SQL query that:\n"
                "1. Is correctly formatted and syntactically valid\n"
                "2. Directly addresses the question or task\n"
                "3. Is optimized for performance\n"
                "4. Uses only tables and columns from the provided schema\n\n"
                
                "Provide only the SQL query with no explanation."
            )
        
        elif generate_type == "prompt":
            # For prompt generation
            context_info = inputs.get("context", "")
            goal = inputs.get("goal", "")
            
            if context_info:
                prompt_base += f"Context Information:\n{context_info}\n\n"
            
            if goal:
                prompt_base += f"Goal: {goal}\n\n"
            
            prompt_base += (
                "Generate a well-crafted prompt that:\n"
                "1. Is clear and specific in its instructions\n"
                "2. Provides all necessary context\n"
                "3. Specifies the desired format and style\n"
                "4. Will elicit high-quality responses from an AI system\n\n"
                
                "Provide the complete prompt text."
            )
        
        else:
            # Generic generation
            if "requirements" in inputs:
                prompt_base += f"Requirements: {inputs['requirements']}\n\n"
            
            if "context" in inputs:
                prompt_base += f"Context: {inputs['context']}\n\n"
            
            prompt_base += (
                f"Generate a high-quality {generate_type} that meets all requirements and is "
                "clear, concise, and effective for its intended purpose."
            )
        
        # Get response from LLM
        generated_content = self._llm_client.generate(prompt_base)
        
        # Post-process based on type
        if generate_type == "sql":
            # Clean up SQL query
            sql_query = generated_content.strip()
            
            # Remove markdown code blocks if present
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "", 1)
            if sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "", 1)
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
        
        return generated_content.strip()
    
    def _execute_summarization_action(
        self, 
        action: str, 
        inputs: Dict[str, Any], 
        tools: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute a summarization action.
        
        Args:
            action: Action description
            inputs: Action inputs
            tools: Required tools
            context: Execution context
            
        Returns:
            Any: Summary results
        """
        # Get text to summarize
        text = inputs.get("text", "")
        documents = inputs.get("documents", [])
        
        if not text and not documents:
            self.logger.warning("No text or documents found for summarization action")
            return {"error": "No text or documents found for summarization"}
        
        # Combine documents if provided
        if not text and documents:
            if isinstance(documents, list):
                # Extract text from documents
                if all(isinstance(doc, str) for doc in documents):
                    text = "\n\n".join(documents)
                elif all(isinstance(doc, dict) for doc in documents):
                    text = "\n\n".join(doc.get("content", "") for doc in documents if "content" in doc)
            else:
                text = str(documents)
        
        # Get summarization parameters
        max_length = inputs.get("max_length", 500)
        focus_areas = inputs.get("focus_areas", [])
        
        # Build summarization prompt
        prompt = (
            "You are a text summarization expert tasked with creating concise, informative summaries. "
            "Please summarize the following text.\n\n"
            
            f"Summarization Task: {action}\n\n"
            
            f"Text to Summarize:\n{text[:3000]}...\n\n"  # Truncate very long texts
        )
        
        if focus_areas:
            focus_str = ", ".join(focus_areas)
            prompt += f"Focus on these aspects: {focus_str}\n\n"
        
        prompt += (
            f"Create a summary that:\n"
            "1. Captures the most important information and key points\n"
            "2. Is concise and well-structured\n"
            "3. Maintains factual accuracy\n"
            f"4. Is approximately {max_length} words in length\n\n"
            
            "Provide only the summary with no additional explanation."
        )
        
        # Get response from LLM
        summary = self._llm_client.generate(prompt)
        
        return summary.strip()
    
    def _execute_extraction_action(
        self, 
        action: str, 
        inputs: Dict[str, Any], 
        tools: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute an information extraction action.
        
        Args:
            action: Action description
            inputs: Action inputs
            tools: Required tools
            context: Execution context
            
        Returns:
            Any: Extracted information
        """
        # Get text to extract from
        text = inputs.get("text", "")
        documents = inputs.get("documents", [])
        
        if not text and not documents:
            self.logger.warning("No text or documents found for extraction action")
            return {"error": "No text or documents found for extraction"}
        
        # Combine documents if provided
        if not text and documents:
            if isinstance(documents, list):
                # Extract text from documents
                if all(isinstance(doc, str) for doc in documents):
                    text = "\n\n".join(documents)
                elif all(isinstance(doc, dict) for doc in documents):
                    text = "\n\n".join(doc.get("content", "") for doc in documents if "content" in doc)
            else:
                text = str(documents)
        
        # Get extraction parameters
        fields = inputs.get("fields", [])
        extraction_format = inputs.get("format", "json")
        
        # Build extraction prompt
        prompt = (
            "You are an information extraction expert tasked with extracting structured information from text. "
            "Please extract the specified information from the following text.\n\n"
            
            f"Extraction Task: {action}\n\n"
            
            f"Text to Process:\n{text[:3000]}...\n\n"  # Truncate very long texts
        )
        
        if fields:
            fields_str = ", ".join(fields)
            prompt += f"Extract the following fields: {fields_str}\n\n"
        
        if extraction_format.lower() == "json":
            prompt += (
                "Extract the information and format it as a JSON object with the specified fields as keys. "
                "If a field is not found in the text, use null as the value.\n\n"
                
                "Format your response as valid JSON with no additional text."
            )
        else:
            prompt += (
                f"Extract the information and format it as {extraction_format}.\n\n"
                
                "Ensure your extraction is accurate and comprehensive."
            )
        
        # Get response from LLM
        extraction_result = self._llm_client.generate(prompt)
        
        # Post-process if JSON format requested
        if extraction_format.lower() == "json":
            try:
                # Try to parse JSON
                json_start = extraction_result.find("{")
                json_end = extraction_result.rfind("}")
                
                if json_start != -1 and json_end != -1:
                    json_str = extraction_result[json_start:json_end + 1]
                    return json.loads(json_str)
            except:
                # Return raw text if JSON parsing fails
                self.logger.warning("Failed to parse extracted JSON, returning raw text")
        
        return extraction_result.strip()
    
    def _execute_generic_action(
        self, 
        action: str, 
        inputs: Dict[str, Any], 
        tools: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute a generic action using LLM.
        
        Args:
            action: Action description
            inputs: Action inputs
            tools: Required tools
            context: Execution context
            
        Returns:
            Any: Action results
        """
        # Build generic prompt
        prompt = (
            "You are an AI assistant tasked with completing a specific action. "
            "Please perform the following task:\n\n"
            
            f"Task: {action}\n\n"
        )
        
        # Add all inputs to prompt
        for key, value in inputs.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
                prompt += f"{key}:\n```json\n{value_str}\n```\n\n"
            else:
                prompt += f"{key}: {value}\n\n"
        
        prompt += (
            "Complete this task to the best of your ability, providing a comprehensive response "
            "that fully addresses all requirements.\n\n"
            
            "Focus on being accurate, thorough, and helpful in your response."
        )
        
        # Get response from LLM
        result = self._llm_client.generate(prompt)
        
        return result.strip()
    
    def _validate_results(self, results: Dict[str, Any], task_type: str, task_description: str) -> Dict[str, Any]:
        """
        Validate task results and add reflections.
        
        Args:
            results: Task execution results
            task_type: Original task type
            task_description: Original task description
            
        Returns:
            Dict[str, Any]: Validation results
        """
        # Skip validation if task failed
        if not results.get("success", False):
            return {"error": "Task execution failed"}
        
        # Get final output
        final_output = results.get("final_output", "")
        
        # Build validation prompt
        prompt = (
            "You are a task validation expert tasked with evaluating the quality and completeness "
            "of task outputs. Please evaluate the following task results:\n\n"
            
            f"Original Task: {task_description}\n\n"
            
            f"Task Output:\n{final_output}\n\n"
            
            "Evaluate this output on the following criteria:\n"
            "1. Completeness: Does it fully address the original task?\n"
            "2. Accuracy: Is the information accurate and reliable?\n"
            "3. Clarity: Is it clear and well-structured?\n"
            "4. Usefulness: How useful is this for the intended purpose?\n\n"
            
            "Provide your evaluation as a JSON object with the following format:\n"
            "```json\n"
            "{\n"
            '  "quality_score": 0-10,\n'
            '  "strengths": ["strength1", "strength2"],\n'
            '  "weaknesses": ["weakness1", "weakness2"],\n'
            '  "suggestions": ["suggestion1", "suggestion2"]\n'
            "}\n"
            "```"
        )
        
        try:
            # Get response from LLM
            validation_result = self._llm_client.generate(prompt)
            
            # Parse JSON response
            json_start = validation_result.find("{")
            json_end = validation_result.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = validation_result[json_start:json_end + 1]
                validation = json.loads(json_str)
                
                # Add validation to results
                results["validation"] = validation
            else:
                # Add raw text if JSON parsing fails
                results["validation"] = {"raw_feedback": validation_result.strip()}
        
        except Exception as e:
            self.logger.error(f"Error validating task results: {str(e)}")
            results["validation"] = {"error": str(e)}
        
        return results["validation"]
    
    def validate_config(self) -> bool:
        """
        Validate the component configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Validate max_iterations
        max_iter = self.get_config_value("max_iterations", 5)
        if not isinstance(max_iter, int) or max_iter <= 0:
            self.logger.warning("max_iterations must be a positive integer")
            return False
        
        # Validate reflection_enabled
        reflection = self.get_config_value("reflection_enabled", True)
        if not isinstance(reflection, bool):
            self.logger.warning("reflection_enabled must be a boolean")
            return False
        
        # Validate allowed_tasks
        tasks = self.get_config_value("allowed_tasks", [])
        if not isinstance(tasks, list):
            self.logger.warning("allowed_tasks must be a list")
            return False
        
        return True
    
    def _get_best_step_output(self, steps: List[Dict[str, Any]]) -> Optional[str]:
        """
        Get the best output from the steps results.
        
        Args:
            steps: List of step results
            
        Returns:
            Optional[str]: Best step output or None
        """
        if not steps:
            return None
            
        # First try to find the last successful step with output
        for step in reversed(steps):
            if step.get('success', False) and step.get('output'):
                return step['output']
        
        # If no successful step, return the last step with any output
        for step in reversed(steps):
            if step.get('output'):
                return step['output']
                
        return None 