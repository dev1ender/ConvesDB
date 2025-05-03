Great. I’ll create a detailed, modular, and extensible PRD and architectural plan for an Ollama/LLM-based system that converts natural language to SQL queries using agents, embeddings, and LangChain—designed for future extension to multiple databases (e.g., SQLite, Neo4j) and LLMs (e.g., OpenAI, HuggingFace, Ollama).

I’ll break the design into modular components including: seeding and inspecting the DB, generating schema and embedding it, querying with user prompts, fetching contextual data from vector memory, assembling a system prompt, generating and validating SQL, executing it, and returning raw/computed results. Expect clean abstractions across entities like databases, data contexts, agents, and LLM APIs.

I’ll let you know when the research and design is ready.


# NLP-to-SQL Query System: Requirements and Architecture

This document specifies a modular, LangChain-based system that accepts a natural-language question and returns a SQL query result. Key goals include: seeding a SQLite DB; extracting schema (tables/columns); building a metadata index; using vector search to focus context; prompting an LLM (Ollama/OpenAI/etc.) to generate SQL; validating and executing the SQL; and optionally summarizing results. The design is extensible (supporting different DBs/LLMs), uses robust system prompts, and is intended for a web chat interface.

## High-Level Flow

1. **Database Initialization:** Create and seed a SQLite database (or other DB) with tables and data.
2. **Schema Extraction:** Use a database interface (e.g. LangChain’s `SQLDatabase`) to list tables and fetch their column definitions.
3. **Metadata Generation:** Produce a JSON description of each table’s purpose and column semantics (possibly with human input or LLM assistance).
4. **Indexing (Vector Store):** Embed table/column metadata (using an embeddings model) and store in a vector database (e.g. FAISS).
5. **User Query Input:** Receive a natural-language question.
6. **Context Retrieval:** Embed the query and perform a vector similarity search on the schema metadata to retrieve the most relevant tables/columns. For example, AWS recommends storing embeddings of a central data catalog so an LLM can quickly identify the relevant database tables and columns for a query.
7. **Prompt Construction:** Combine the user’s question with the retrieved schema context into a structured system prompt. The prompt instructs the agent to inspect only relevant tables and to generate a syntactically correct query.
8. **LLM SQL Generation:** Call the chosen LLM (via `LLMClient` interface) with the system prompt. The LLM generates a candidate SQL query. (Using LangChain’s `SQLDatabaseToolkit`, the agent can use tools to list tables, fetch schemas, and run queries.)
9. **SQL Validation:** Check the syntax and safety of the query. This can be done by attempting to execute it with `run_no_throw` (to catch errors) or using a SQL parser. On error, the LLM can be asked to revise the query based on the error message (as a self-correction loop).
10. **Query Execution:** Execute the validated SQL on the database and obtain raw results. The agent may have tools (e.g. `RunSQLTool`) for this.
11. **Result Summarization (Optional):** If requested, invoke a code agent or LLM to compute aggregates or generate a natural-language summary of the results. For example, a Python tool can compute metrics, or an LLM can translate rows into a descriptive answer.
12. **Return to User:** Present the SQL results (and/or summaries) back to the user via the chat UI.

The following figure illustrates a **Retrieval-Augmented (RAG) workflow** for SQL generation. Metadata (table and column descriptions) are embedded and indexed; the user query is embedded and matched to relevant schema; the matched tables/columns guide the LLM in constructing the SQL. The process then executes the query and returns the answer.

&#x20;*Figure: RAG-based SQL query generation pipeline. The user’s question is embedded and matched against stored table/column embeddings. Relevant schema snippets (highlighted by red nodes) are passed to the LLM, which constructs the SQL. The query is validated, executed, and the answer returned.*

## Components and Class Architecture

The system is organized into modular components, each with clear responsibilities. Interfaces and abstractions ensure extensibility (e.g. for multiple DBs or LLMs).

* **Database Interface (`Database`)**: Connects to the target database (SQLite, PostgreSQL, Neo4j, etc). Responsibilities include seeding data, providing table names, and fetching table schemas. For example, LangChain’s `SQLDatabase` can be used for SQL DBs. Key methods: `connect()`, `get_table_names()`, `get_table_info([tables])`, `run(query)`. An abstract base class or interface (`DatabaseConnector`) allows implementing different DBs.

  * *Example:* `SQLiteDatabase` extends `Database` and uses SQLAlchemy or native SQLite APIs. `Neo4jDatabase` would connect via a Bolt driver. LangChain’s `SQLDatabaseToolkit` provides tools for SQL DBs (query building, execution, schema retrieval).

* **Schema/Metadata Manager (`SchemaDocBuilder`)**: Extracts schema details and composes the metadata JSON. It calls the Database interface to get columns and (optionally) example rows, then produces human-readable descriptions of each table’s purpose and column semantics. This might involve manual input or an LLM “prompt” to write descriptions. The result is a JSON (or structured) doc for each table containing `{name, purpose, columns: [{name, description}, …]}`. This metadata is the basis for later retrieval. (LangChain’s `SQLDatabase.get_table_info` can help generate schema text, following best practices.)

* **Embedding Store (`VectorStore`)**: Embeds schema metadata and the user query into vectors and performs similarity search. Implements methods to add documents and to query. For example, it can use FAISS (via LangChain’s FAISS integration) or Chroma, Pinecone, etc. Workflow: split table/column JSON into text chunks; use an embedding model (e.g. OpenAIEmbeddings) to convert each chunk into a dense vector; index them in FAISS. At query time, embed the user question and retrieve the top-k most similar schema chunks. (LangChain shows this pattern: e.g. `vector_store.add_texts(docs)` and `vector_store.as_retriever(...)`.)

* **Context Retriever (`ContextManager`)**: Uses the VectorStore to fetch relevant schema context. Given the embedded query, it finds the most semantically similar table/column descriptions. It may also filter or concatenate multiple snippet results. The retrieved context is formatted (e.g. as text or JSON) and passed to the prompt generator.

* **Prompt Generator (`PromptBuilder`)**: Constructs the system and user prompts for the LLM. It takes the original question and the retrieved schema snippets, and templates them into a coherent prompt. A robust system prompt includes the agent’s role and instructions (e.g. “You are a helpful SQL assistant…”), constraints (e.g. limit results, no destructive queries), and guidelines for querying the schema first. Good prompt design is critical (“a great system prompt delivers coherence…a weak one risks drift and hallucinations”). For instance, LangChain’s example system prompt explicitly instructs the agent to first inspect tables and schemas before querying.

* **LLM Client (`LLMClient`)**: An interface for calling language models. This abstraction allows swapping between providers (Ollama LLaMA models, OpenAI, Google Gemini, etc). Methods include `generate(text_prompt, params)` or `chat(messages)`. Each implementation handles authentication and API calls. The agent invokes `LLMClient` with the system prompt to produce the SQL query string. (For example, LangChain’s `ChatOpenAI` or `Ollama` wrappers can be used.) The LLM is expected to output SQL conforming to instructions.

* **SQL Agent & Tools**: In LangChain terms, an **Agent** orchestrates calls to tools. We define tools for database interactions:

  * `ListTablesTool` (calls `Database.get_table_names()`),
  * `SchemaTool` (calls `Database.get_table_info()` for given tables),
  * `ExecuteSQLTool` (calls `Database.run()` to execute queries),
  * `SyntaxCheckTool` (could parse or test the query without throwing).
    LangChain’s `SQLDatabaseToolkit` already provides such tools (create/execute queries, check syntax, retrieve table descriptions). The agent uses an LLM (via `LLMClient`) plus these tools to convert a question to SQL. Notably, SQL agents can iterate: they can catch SQL errors and regenerate queries. Using agents is advantageous because they are *schema-aware* and support *error recovery*. In practice, we use a React/ReAct agent chain (e.g. `create_react_agent`) with the above tools and the constructed prompt. The agent will typically: (a) list tables, (b) fetch schema for relevant tables, (c) generate SQL, (d) execute, (e) check results, and (f) return the answer. LangChain notes that a SQL agent “will save tokens by only retrieving the schema from relevant tables”, which our vector filtering accomplishes.

* **SQL Validator (`SQLValidator`)**: Ensures the generated SQL is syntactically and semantically valid. It may run the query in a safe mode (e.g. with `fetch='none'`) or use an SQL parser. If an error is detected, it extracts the error message and optionally re-prompts the LLM to fix it. This mirrors the “self-correction” pattern: on failure, feed the error back to the model and ask for a corrected query. LangChain’s SQL agents do this automatically by catching execution tracebacks.

* **Query Executor (`QueryExecutor`)**: Runs the final SQL against the database and returns results. Implements methods like `execute(sql)`. This could be part of the Database interface or a separate agent tool. It must handle parameterization safely. The results (rows or aggregates) are returned for formatting or summarization.

* **Result Interpreter/Summarizer (`ResultSummarizer`)**: Optionally processes raw results for user presentation. This might call an LLM to generate a natural-language answer (e.g. “The top country is X with Y sales”) or compute statistics. Alternatively, a Python tool could compute metrics. This component wraps any post-query analysis, ensuring the final output is user-friendly.

* **Chat Interface (`ChatUI`)**: Integrates the above into a conversation. This is typically a web frontend (Chatbot) with back-end routes that invoke the agent. Responsibilities include handling user messages, managing conversation state/memory, and streaming responses. It invokes the ContextRetriever, PromptBuilder, LLM agent, etc., in sequence for each user query. Frameworks like FastAPI/Streamlit or LangServe can be used. The UI displays raw query results and/or summaries to the user.

* **Extensibility and Configuration**: All components use interfaces so new modules can be plugged in. For instance, a new `PostgresDatabase` implementing `Database` can replace `SQLiteDatabase`. Similarly, an `LLMClient` implementation for Gemini or a locally hosted LLaMA (via Ollama) can be swapped in. LangChain supports many vector stores (FAISS, Chroma, Pinecone) and DB integrations (including a `Neo4jVector` for graphs). The system prompt and chain can be reconfigured per use case, but core logic remains the same. Using dependency injection or factory patterns ensures modularity.

## Architectural Details

* **Database Module:**

  * *Classes:* `DatabaseConnector` (interface), `SQLiteConnector` (implements), `Neo4jConnector`, etc.
  * *Methods:* `seed_database()`, `get_table_names()`, `get_table_schema(table)`, `run(query)`.
  * *Notes:* Uses SQLAlchemy or native drivers. LangChain’s `SQLDatabase.from_uri` can initialize a SQLite connection. Table and column metadata (names, types, comments) are fetched via introspection (e.g. `PRAGMA table_info` in SQLite or INFORMATION\_SCHEMA in SQL).

* **Schema Metadata Module:**

  * *Classes:* `SchemaDocBuilder`, `TableMetadata`, `ColumnMetadata`.
  * *Responsibilities:* Assemble a JSON schema: each `TableMetadata` has `purpose` and a list of `ColumnMetadata` with descriptions. If not provided, an LLM might be used to generate human-readable descriptions of columns (given names and sample data).

* **Embedding and Vector Store:**

  * *Classes:* `EmbeddingModel` (wraps an embedder like OpenAIEmbeddings or Ollama embedder), `SchemaVectorStore` (wraps a LangChain vector store).
  * *Responsibilities:* Convert each table/column description into a vector, store in FAISS (or Chroma, etc). At query time, embed the question and perform `similarity_search`. LangChain example:

    ```python
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Faiss.from_texts(schema_texts, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    ```

    This matches the pattern in LangChain’s tutorial, which shows adding texts to a vector store and retrieving top matches.

* **Context Manager:**

  * *Classes:* `ContextRetriever`.
  * *Responsibilities:* Query the `SchemaVectorStore` for relevant schema entries. It might return full table JSON or select columns. The context is combined (possibly truncated) and fed into the LLM prompt. This may also involve a memory to include conversation history if needed.

* **Prompting and Agent:**

  * *Classes:* `PromptTemplate`, `SQLAgentExecutor`.
  * *Responsibilities:* The `PromptTemplate` holds a system prompt template with placeholders (e.g. for `{schema}`, `{user_question}`). It is populated each round. The `SQLAgentExecutor` uses LangChain’s agent framework (e.g. a ReAct agent with `SQLDatabaseToolkit`) to carry out the prompt. Example prompt content from LangChain:

    > “You are an agent designed to interact with a SQL database. Given an input question, create a syntactically correct SQL query to run… DO NOT make any DML statements… To start you should ALWAYS look at the tables… Then you should query the schema of the most relevant tables.”
    > This enforces consistency. The agent then automatically lists tables (`sql_db_list_tables`), retrieves relevant schemas (`sql_db_schema`), and constructs/executes the query, iterating if errors occur.

* **LLM and API Interfaces:**

  * *Classes:* `LLMClient` (interface), `OpenAIClient`, `OllamaClient`, `GeminiClient`, etc.
  * *Responsibilities:* Convert prompts to model API calls. For chat-based models, handle message formatting. For OpenAI/Gemini, use official APIs; for Ollama, call the local model. All implementations must support function calling if needed (for tool invocation as LangChain’s “agent” does).

* **SQL Validation Tool:**

  * *Function:* `validate_sql(sql)`.
  * *Responsibilities:* Pre-check the query. Options: run `database.run_no_throw(sql)` to catch any SQL errors; or use an SQL parser library (e.g. `sqlparse`). If an error string is returned, form a follow-up LLM prompt: “The following error occurred… please correct the query.” This mirrors the iterative fix pattern.

* **Query Execution & Formatting:**

  * *Function:* `execute_sql(sql)`.
  * *Responsibilities:* Run the SQL on the database and fetch results (up to `LIMIT` if needed). Format results as a table or JSON for the UI. Ensure safe execution with limited privileges.

* **Result Summarizer:**

  * *Classes:* `ResultSummarizer`.
  * *Responsibilities:* Given raw rows, decide if summarization is needed (based on user request). If so, send the data to an LLM (or run a code tool) to generate a concise answer. This uses LLM’s generative ability on structured results.

* **Web Chat Integration:**

  * *Components:* Chat server (e.g. FastAPI/Flask or LangServe), frontend UI (JavaScript/HTML).
  * *Responsibilities:* Maintain conversation state, pass user queries to the agent, and stream back answers. The front-end displays either the raw SQL result table and/or a natural language answer. It can also show the SQL query itself for transparency. (LangChain’s LangSmith or LangGraph can help trace agent steps in development.)

## Component Responsibilities and Interfaces

* **Database (Interface):**

  * *Methods:*

    * `connect()`: Open DB connection.
    * `seed(schema_sql)`: Initialize schema and data.
    * `get_table_names() → List[str]`: Return tables.
    * `get_table_schema(table: str) → str`: Return DDL or descriptive schema for a table.
    * `run(query: str) → ResultSet`: Execute and return results.
  * *Notes:* Use SQLAlchemy for SQL DBs. For graph DB (Neo4j), equivalent methods fetch node labels and relationship types. LangChain’s `SQLDatabase` class provides these for SQL.

* **Metadata (Class):**

  * *Structure:* JSON or Python dict with keys: `table_name`, `purpose`, `columns: [{name, description}, …]`.
  * *Usage:* Stored in vector store. Can be updated if schema changes.

* **Vector Store (Interface):**

  * *Methods:*

    * `index_documents(docs: List[str])`: Embed and add to index.
    * `query_similar(text: str, k: int) → List[str]`: Return top-k similar docs.
  * *Notes:* Can wrap LangChain’s `FAISS` or `Chroma`. In LangChain, `vector_store.as_retriever().get_relevant_documents(query)` fetches top matches.

* **Agent Tools (as LangChain tools):**

  * `list_tables()`: Calls DB to get tables.
  * `get_schema(tables: str)`: Returns CREATE statements or column info for listed tables.
  * `execute_query(sql: str)`: Runs SQL and returns output or error.
  * `search_schema(query: str)`: (Optional) uses the vector store to find relevant schema docs.
  * `summarize_results(data: Any)`: (Optional tool) calls LLM on query results.

* **LLM Model (Interface):**

  * *Method:* `generate(messages: List[Message], **kwargs) → str` (or JSON).
  * *Properties:* model name, temperature, token limit.
  * *Implementation:* Each LLM provider class (e.g. `OllamaLLM`, `OpenAILLM`) implements this.

* **Controller/Orchestrator:**

  * *Class:* `NL2SQLAgent` (orchestrates end-to-end).
  * *Methods:*

    * `answer_question(question: str) → Response`: The main entry point. Internally calls context retrieval, prompt building, LLM execution, validation, execution, summarization, and formats the final answer.
  * *Flow:* Validate input → get context → build prompt → LLM→ validate query → execute → summarize → return.

## Modularity and Extensibility

The design uses well-defined interfaces so components can be replaced or extended:

* **Multiple Databases:** By coding to a `Database` interface, the same agent logic can work on SQL or NoSQL/graph DBs. For example, LangChain also supports Neo4j via `Neo4jVector` which can embed graph properties. A `GraphDatabase` implementation could present node/relationship metadata similarly.
* **Multiple LLMs:** The `LLMClient` abstraction means swapping providers (e.g. using OpenAI’s GPT-4, Google Gemini, or a local LLaMA via Ollama) requires minimal change. Each provider’s API and credentials are isolated.
* **Vector Stores:** Although FAISS (on CPU/GPU) is default, one could use Pinecone, Qdrant, or a managed service. LangChain’s vector store interface allows plugging these in.
* **Agents vs Chains:** The system could be implemented as either a single “superchain” or as an agent with tools. Using an agent (the MRKL/ReAct style) is recommended for flexibility: SQL agents are inherently schema-aware and can loop on their results.

## Prompt and System Behavior

Consistency is enforced by a strong system prompt. The prompt should: set the agent’s role (SQL expert), define objectives (“Answer the user’s question by generating and executing SQL”), and lay out constraints (e.g. “return at most X rows, do not alter data, double-check your query”). As one expert notes, “the system prompt is the meta-instructions that sit above every user query… a great system prompt delivers coherence, context-awareness, and trust”. In practice, we include instructions to “ALWAYS look at the tables” and “then query the schema of the most relevant tables” before answering. This matches LangChain’s example agent prompt, ensuring the agent uses the schema properly.

LangChain’s documentation highlights the benefits of this approach: **schema awareness** (agents can reason over table definitions), **error recovery** (they catch SQL errors and retry) and **multi-query support** (they can issue several SQL statements as needed). For instance, an agent can first invoke a `list_tables` tool, then fetch schemas only for relevant tables, which “saves tokens by only retrieving the schema from relevant tables”. This is combined with our vector filter to further reduce context.

## Summary of Key Points

* **Orchestration:** LangChain is used as the backbone. The SQLAgentExecutor runs tools (DB introspection, query execution) guided by the LLM.
* **Schema Context:** All tables/columns are described and embedded. Vector search (FAISS) picks relevant ones per query.
* **Robust Prompt:** System prompts strictly instruct the agent on steps (inspect tables, double-check SQL, etc.) to avoid mistakes.
* **Validation Loop:** The agent checks query syntax via the SQL engine. On failure, it re-prompts the LLM using the error (self-correction).
* **Modular Design:** Components (Database, LLM, Vector Store, Agent Tools) are decoupled by interfaces, enabling support for new LLMs (e.g. Gemini2.5, Ollama) or new DB types (e.g. adding Neo4j).
* **Web Interface:** The architecture supports a chat UI: user questions invoke the agent chain, and responses (raw rows or summaries) are sent back.

Overall, this design uses LangChain’s agent toolkit and vector retrieval to build a flexible, reliable Natural Language-to-SQL system. By indexing schema information and leveraging a structured prompt/agent workflow, the system can accurately translate user questions into SQL, validate and execute queries, and return insightful results.

**Sources:** LangChain documentation and tutorials on SQL Agents; LangChain vector store and RAG integration guides; AWS and LangChain RAG best practices; LLM prompt engineering advice; and example LLM-driven SQL architectures.
