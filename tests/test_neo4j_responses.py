#!/usr/bin/env python3
"""
Script to test all SAMPLE_NEO4J_QUERIES questions through the Neo4j demo.
This runs each question and compares the actual response with the expected result.
"""

import os
import sys
import subprocess
import json
import re
from typing import Dict, Any, List, Tuple
import argparse
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.seed_neo4j import SAMPLE_NEO4J_QUERIES
from app.utils.logging_setup import setup_logging, get_logger

# Setup logger
setup_logging()
logger = get_logger(__name__)

class Neo4jResponseTester:
    """Class to test Neo4j demo responses against expected results."""
    
    def __init__(self, output_file: str = None, verbose: bool = False):
        """Initialize the tester.
        
        Args:
            output_file: Optional file to write results to
            verbose: Whether to print verbose output
        """
        self.output_file = output_file
        self.verbose = verbose
        self.results = []
    
    def run_demo_with_question(self, question: str) -> str:
        """Run the Neo4j demo with a specific question.
        
        Args:
            question: Question to ask
            
        Returns:
            Output from the demo
        """
        logger.info(f"Running demo with question: {question}")
        
        cmd = ["python", "commands/neo4j_demo.py", "demo", "--question", question]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Demo failed with question: {question}")
            logger.error(f"Error: {result.stderr}")
            return ""
        
        return result.stdout
    
    def extract_query_results(self, output: str) -> List[Dict[str, Any]]:
        """Extract query results from demo output.
        
        Args:
            output: Demo output
            
        Returns:
            List of result dictionaries
        """
        # Find results section
        result_match = re.search(r"Results:(.*?)(?:\.{3}|\n\n)", output, re.DOTALL)
        
        if not result_match:
            return []
        
        # Parse result lines
        result_lines = result_match.group(1).strip().split("\n")
        results = []
        
        for line in result_lines:
            line = line.strip()
            if line and not line.startswith("..."):
                # Remove numbering (e.g., "1. ")
                line = re.sub(r"^\s*\d+\.\s*", "", line)
                
                # Try to parse as dictionary
                try:
                    # Handle both {'key': 'value'} and key: value formats
                    if line.startswith("{") and line.endswith("}"):
                        result_dict = eval(line)  # Safe since we control the input
                    else:
                        # Convert "key: value" to dictionary
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            result_dict = {parts[0].strip(): parts[1].strip()}
                        else:
                            result_dict = {"value": line}
                    
                    results.append(result_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse result line: {line}")
                    results.append({"raw": line})
        
        return results
    
    def verify_results(self, query_data: Dict[str, Any], output: str) -> Tuple[bool, str]:
        """Verify that the output matches the expected results.
        
        Args:
            query_data: Query data from SAMPLE_NEO4J_QUERIES
            output: Demo output
            
        Returns:
            Tuple of (success, reason)
        """
        expected_result = query_data["expected"]
        
        # Check if cypher query was executed
        if "Cypher equivalent: " + query_data["cypher"] not in output:
            return False, "Cypher query not found in output"
        
        # Check if query was successful
        if "Query execution successful" not in output:
            return False, "Query execution failed"
        
        # Extract and check results
        results = self.extract_query_results(output)
        actual_count = len(results)
        
        # Perform checks based on expected format
        if "~" in expected_result:
            # Approximate count expected
            if not results or not any(isinstance(val, (int, float)) for result in results for val in result.values()):
                return False, f"Expected approximate count, but no numeric results found"
            
            # Extract the number from expected result (e.g., "~150" -> 150)
            expected_count = int(re.search(r"~(\d+)", expected_result).group(1))
            
            # Get actual count from results
            actual_counts = [val for result in results for val in result.values() if isinstance(val, (int, float))]
            
            if not actual_counts:
                return False, f"Expected count ~{expected_count}, but no counts found in results"
            
            # Check if any count is within 20% of expected
            for count in actual_counts:
                if abs(count - expected_count) / expected_count <= 0.2:  # Within 20%
                    return True, f"Count {count} is close to expected ~{expected_count}"
            
            return False, f"Expected count ~{expected_count}, got {actual_counts}"
            
        elif "rows" in expected_result:
            # Row count expected
            expected_count = int(re.search(r"(\d+)", expected_result).group(1))
            
            if not results:
                return False, f"Expected {expected_count} rows, but no results found"
            
            # Check if count is as expected (or at least some rows if data is random)
            if expected_count > 100:  # If expecting many rows
                if actual_count > 0:
                    return True, f"Found {actual_count} rows (expected many rows)"
                else:
                    return False, f"Expected {expected_count} rows, got {actual_count}"
            else:
                if actual_count > 0 and (actual_count <= expected_count * 1.2):
                    return True, f"Found {actual_count} rows (expected {expected_count})"
                else:
                    return False, f"Expected {expected_count} rows, got {actual_count}"
                    
        elif "depends on" in expected_result.lower():
            # Results depend on random data
            return actual_count > 0, f"Found {actual_count} results (expected some based on random data)"
            
        else:
            # Just check if we got any results
            if results:
                return True, f"Got {len(results)} results as expected"
            else:
                return False, f"Expected results but got none"
    
    def test_all_queries(self) -> List[Dict[str, Any]]:
        """Test all queries from SAMPLE_NEO4J_QUERIES.
        
        Returns:
            List of result dictionaries
        """
        results = []
        
        for i, query_data in enumerate(SAMPLE_NEO4J_QUERIES):
            nlp_query = query_data["nlp"]
            cypher_query = query_data["cypher"]
            expected = query_data["expected"]
            complexity = query_data["complexity"]
            
            logger.info(f"Testing query {i+1}/{len(SAMPLE_NEO4J_QUERIES)}: {nlp_query}")
            
            # Run demo with query
            output = self.run_demo_with_question(nlp_query)
            
            # Verify results
            success, reason = self.verify_results(query_data, output)
            
            # Store result
            result = {
                "query_idx": i,
                "nlp_query": nlp_query,
                "cypher_query": cypher_query,
                "expected": expected,
                "complexity": complexity,
                "success": success,
                "reason": reason
            }
            
            results.append(result)
            
            # Print result if verbose
            if self.verbose:
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status} Query {i+1}: {nlp_query}")
                print(f"  Reason: {reason}")
                print()
        
        # Store results
        self.results = results
        
        return results
    
    def generate_report(self) -> str:
        """Generate a report from the test results.
        
        Returns:
            Report string
        """
        if not self.results:
            return "No results to report."
        
        # Create summary statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        # Group by complexity
        complexity_stats = {}
        for r in self.results:
            complexity = r["complexity"]
            if complexity not in complexity_stats:
                complexity_stats[complexity] = {"total": 0, "passed": 0, "failed": 0}
            
            complexity_stats[complexity]["total"] += 1
            if r["success"]:
                complexity_stats[complexity]["passed"] += 1
            else:
                complexity_stats[complexity]["failed"] += 1
        
        # Create report
        report = ["# Neo4j Demo Query Test Report", ""]
        
        report.append("## Summary")
        report.append(f"Total queries: {total}")
        report.append(f"Passed: {passed} ({passed/total*100:.1f}%)")
        report.append(f"Failed: {failed} ({failed/total*100:.1f}%)")
        report.append("")
        
        report.append("## Results by Complexity")
        complexity_table = []
        for complexity, stats in complexity_stats.items():
            pass_rate = stats["passed"] / stats["total"] * 100
            complexity_table.append([
                complexity,
                stats["total"],
                stats["passed"],
                stats["failed"],
                f"{pass_rate:.1f}%"
            ])
        
        report.append(tabulate(
            complexity_table,
            headers=["Complexity", "Total", "Passed", "Failed", "Pass Rate"],
            tablefmt="pipe"
        ))
        report.append("")
        
        # Add detailed results
        report.append("## Detailed Results")
        report.append("")
        
        # Prepare data for better-formatted table
        details_data = []
        for r in self.results:
            status = "✅ PASS" if r["success"] else "❌ FAIL"
            # Truncate long queries to prevent markdown table formatting issues
            query = r["nlp_query"]
            if len(query) > 50:
                query = query[:47] + "..."
                
            details_data.append([
                r["query_idx"] + 1,
                status,
                query,
                r["complexity"],
                r["reason"]
            ])
        
        # Generate the table
        details_table = tabulate(
            details_data,
            headers=["#", "Status", "Query", "Complexity", "Reason"],
            tablefmt="pipe"
        )
        report.append(details_table)
        
        # Add full query details separately
        report.append("")
        report.append("## Full Query Details")
        report.append("")
        for i, r in enumerate(self.results):
            report.append(f"### Query {i+1}: {r['nlp_query']}")
            report.append(f"- **Status:** {'Passed' if r['success'] else 'Failed'}")
            report.append(f"- **Complexity:** {r['complexity']}")
            report.append(f"- **Cypher Query:** `{r['cypher_query']}`")
            report.append(f"- **Expected Result:** {r['expected']}")
            report.append(f"- **Reason:** {r['reason']}")
            report.append("")
        
        report_str = "\n".join(report)
        
        # Write to file if specified
        if self.output_file:
            with open(self.output_file, "w") as f:
                f.write(report_str)
            logger.info(f"Report written to {self.output_file}")
        
        return report_str

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Test Neo4j demo responses against expected results")
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")
    
    args = parser.parse_args()
    
    tester = Neo4jResponseTester(args.output, args.verbose)
    tester.test_all_queries()
    report = tester.generate_report()
    
    print(report)

if __name__ == "__main__":
    main() 