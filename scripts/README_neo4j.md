# Neo4j Testing Scripts

This directory contains scripts for testing the Neo4j database integration with the conversDB application.

## Available Scripts

1. `seed_neo4j.py`: Seeds a Neo4j database with cybersecurity graph data
2. `questions_neo4j.py`: Contains sample Neo4j questions with expected Cypher queries
3. `run_neo4j_tests.py`: Script to run and verify Neo4j queries

## Running the Scripts

### Seed the Database

```
python scripts/seed_neo4j.py --uri bolt://localhost:7687 --username neo4j --password password
```

### Run Test Queries

To test a specific question:
```
python scripts/run_neo4j_tests.py --question-index 0
```

To run all test questions:
```
python scripts/run_neo4j_tests.py --test-all
```

## Adding New Questions

To add new questions, edit the `questions_neo4j.py` file:

```python
{
    "question": "Your natural language question",
    "cypher": "MATCH (n) RETURN n LIMIT 10", # Your Cypher query
    "expected_result": "Expected result string"
}
```

## Integration with conversDB

The workflow in `config/workflows/neo4j_workflow.yaml` is configured to:
1. Extract schema information from Neo4j
2. Generate appropriate prompts
3. Convert natural language to Cypher
4. Execute and format the results

## Data Schema

The seeded Neo4j database contains the following node types:

- User (professionals with various roles and risk levels)
- Device (laptops, servers, mobile devices)
- Website (URLs with categories and risk scores)
- EmailAccount (user email accounts)
- Message (communications between email accounts)
- File (documents, executables with attributes like malicious status)
- Application (software installed on devices)
- Network (internal/external network segments)
- Location (physical locations of users and devices)
- Event (security events like logins, malware detections)
- Alert (security alerts triggered by events)
- Organization (companies and departments)
- IPAddress (network addresses, some blacklisted)

And relationships such as:
- User-LOGGED_IN_FROM->Device
- User-ACCESSED->Website
- User-SENT->Message
- Device-CONNECTED_TO->Network
- And many others...

### 3. View Test Results

Test results and verifications are saved in the `logs` directory with timestamped filenames. 