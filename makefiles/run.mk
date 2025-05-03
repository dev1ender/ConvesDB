# Run application in different modes

# Run the CLI version
run-cli: env-setup
	@echo "Running CLI version..."
	. .venv/bin/activate && . .env && python3 -m app.main

# Run the API version
run-api: env-setup
	@echo "Running API version..."
	. .venv/bin/activate && . .env && python3 -m app.api

# Run the Streamlit UI version
run-ui: env-setup
	@echo "Running Streamlit UI..."
	. .venv/bin/activate && . .env && streamlit run app/streamlit_app.py

# Run the demo script
run-demo: env-setup
	@echo "Running demo script..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 commands/demo.py

# Run the demo with config display
run-demo-config: env-setup
	@echo "Running demo script with configuration display..."
	. .venv/bin/activate && . .env && python3 demo.py --show-config

# Run demo questions with expected answers
run-demo-questions: env-setup
	@echo "Running demo questions with expected answers..."
	. .venv/bin/activate && . .env && python3 tests/demo_questions.py

# Run the Hugging Face local demo script
run-hf-demo: env-setup
	@echo "Running Hugging Face local demo script..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 commands/hf_demo.py $(ARGS)

# Count products using Hugging Face local demo
count-products: env-setup
	@echo "Counting products using Hugging Face local demo..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 commands/hf_demo.py -d 

# Run the Document Store demo script
run-doc-demo: env-setup
	@echo "Running Document Store demo script..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 commands/doc_demo.py $(ARGS)

# Run Document Store demo with document listing
run-doc-list: env-setup
	@echo "Running Document Store demo with document listing..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 commands/doc_demo.py --show-docs 

# Run main.py directly (SQLite)
run-main: env-setup
	@echo "Running app/main.py with SQLite..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 app/main.py --db-type sqlite

# Run main.py with Neo4j
run-neo4j: env-setup
	@echo "Running app/main.py with Neo4j..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 app/main.py --db-type neo4j --workflow neo4j_workflow

# Run main.py with Neo4j and test all Neo4j questions
run-neo4j-all: env-setup
	@echo "Running all Neo4j test questions..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 app/main.py --db-type neo4j --workflow neo4j_workflow --test-all

# Run main.py with Neo4j for a specific question
run-neo4j-question: env-setup
	@echo "Running Neo4j test question $(QUESTION_INDEX)..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python3 app/main.py --db-type neo4j --workflow neo4j_workflow --question-index $(QUESTION_INDEX) 