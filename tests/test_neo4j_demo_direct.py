"""
Direct integration tests for Neo4j demo script using subprocess.
This runs the actual script and validates the output.
"""
import os
import sys
import subprocess
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.seed_neo4j import SAMPLE_NEO4J_QUERIES

@pytest.mark.skip(reason="Requires a running Neo4j instance")
class TestNeo4jDemoDirect:
    """Direct integration tests for Neo4j demo script."""
    
    def run_demo_with_question(self, question):
        """Run the Neo4j demo with a specific question."""
        cmd = ["python", "commands/neo4j_demo.py", "demo", "--question", question]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    def test_connection_direct(self):
        """Test that the demo can connect to Neo4j."""
        cmd = ["python", "commands/neo4j_demo.py", "connect"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Connected to Neo4j database" in result.stdout
        
    def test_check_embeddings_direct(self):
        """Test checking embeddings directly."""
        cmd = ["python", "commands/neo4j_demo.py", "check-embeddings", "--node-label", "User"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Embedding statistics for User nodes" in result.stdout
    
    @pytest.mark.parametrize("question_idx", range(3))  # Test first 3 questions
    def test_demo_with_sample_questions(self, question_idx):
        """Test the demo with sample questions."""
        question = SAMPLE_NEO4J_QUERIES[question_idx]["nlp"]
        result = self.run_demo_with_question(question)
        
        assert result.returncode == 0
        assert "COMPREHENSIVE NEO4J DEMO" in result.stdout
        assert "Question: " + question in result.stdout
        
        # Check for key steps in the demo
        assert "Step 1: Performing Neo4j health check" in result.stdout
        assert "Step 2: Checking for seed data" in result.stdout
        assert "Step 3: Checking schema embeddings" in result.stdout
        assert "Step 4: Checking node embeddings" in result.stdout
        assert "Step 5: Asking questions" in result.stdout
        
        # Verify in-memory embedding messages
        assert "Using in-memory" in result.stdout
        
        # Verify cypher query execution
        matching_sample = next((sample for sample in SAMPLE_NEO4J_QUERIES if sample["nlp"] == question), None)
        assert matching_sample is not None
        assert "Cypher equivalent: " + matching_sample["cypher"] in result.stdout
        assert "Expected result: " + matching_sample["expected"] in result.stdout
        assert "Query execution successful" in result.stdout
    
    def test_documents_search_direct(self):
        """Test document search directly."""
        query = "security threat"
        cmd = ["python", "commands/neo4j_demo.py", "documents", "--query", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        # Check for in-memory results (no need for actual documents)
        assert "Found" in result.stdout
        assert "Score:" in result.stdout
    
    def test_schema_search_direct(self):
        """Test schema search directly."""
        query = "What are users"
        cmd = ["python", "commands/neo4j_demo.py", "schema", "--query", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        # Check for in-memory results
        assert "Found" in result.stdout
        assert "Score:" in result.stdout
    
    @pytest.mark.parametrize("custom_question", [
        "What devices have a high risk score?",
        "Show me all compromised devices connected to the internet",
        "Which users accessed unusual websites in the last month?",
        "List all events with critical severity",
        "What is the relationship between users and organizations?"
    ])
    def test_demo_with_custom_questions(self, custom_question):
        """Test the demo with custom questions that aren't in SAMPLE_NEO4J_QUERIES."""
        result = self.run_demo_with_question(custom_question)
        
        assert result.returncode == 0
        assert "COMPREHENSIVE NEO4J DEMO" in result.stdout
        assert "Question: " + custom_question in result.stdout
        
        # Check for key steps in the demo
        assert "Step 1: Performing Neo4j health check" in result.stdout
        assert "Step 2: Checking for seed data" in result.stdout
        assert "Step 3: Checking schema embeddings" in result.stdout
        assert "Step 4: Checking node embeddings" in result.stdout
        assert "Step 5: Asking questions" in result.stdout
        
        # Verify in-memory search is used
        assert "Using in-memory" in result.stdout
        
        # Since this is a custom question not in sample queries,
        # it should NOT have a matching cypher equivalent
        assert "Found matching sample query" not in result.stdout
        
        # Verify schema search was still performed
        assert "Searching schema information" in result.stdout
    
    def test_interactive_custom_question(self):
        """Test the interactive mode with a custom question."""
        # This simulates selecting option 0 (custom question) and then 
        # entering a custom question not in the sample set
        cmd = ["python", "commands/neo4j_demo.py", "demo"]
        
        # Use subprocess.Popen for interactive input
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # First input: '0' to select "Enter your own question"
        # Second input: custom question
        custom_question = "How many devices have critical vulnerabilities reported?"
        input_data = "0\n" + custom_question + "\n"
        
        # Send input and get output
        stdout, stderr = process.communicate(input=input_data)
        
        # Verify the process ran successfully
        assert process.returncode == 0
        assert "COMPREHENSIVE NEO4J DEMO" in stdout
        
        # Verify the custom question was processed
        assert "Enter your question:" in stdout
        assert custom_question in stdout
        
        # Verify in-memory search was used
        assert "Using in-memory" in stdout
        
        # Since this is a custom question, it should NOT match a sample query
        assert "Found matching sample query" not in stdout
        
        # Verify schema search was performed
        assert "Searching schema information" in stdout
    
    def test_malformed_question_handling(self):
        """Test how the system handles malformed or nonsensical questions."""
        malformed_questions = [
            "?????",
            "xyz123",
            "SELECT * FROM users;",  # SQL injection attempt
            "MATCH (n) DETACH DELETE n",  # Dangerous Cypher
            "Tell me everything"  # Too vague
        ]
        
        for question in malformed_questions:
            result = self.run_demo_with_question(question)
            
            # The demo should still run without crashing
            assert result.returncode == 0
            assert "COMPREHENSIVE NEO4J DEMO" in result.stdout
            
            # Verify the system doesn't find a matching sample query
            assert "Found matching sample query" not in result.stdout
            
            # Verify in-memory search was still used
            assert "Using in-memory" in result.stdout 