Lets create a ollama llm project prd to sql query based on npl questions  and return response using agents 

things it should do 
1. Seed sqlite data base 
2. Create a agent to fetch database all table. defination and strcuture column infomration 
3.  create a table defination json with table info what is table use for what is each column used from 
4. Create embeddings of sqlite database  schema and defination json
5.  Store all these embedding inmemory 
6.  get user prompt 
7. fetch related inforamtion from embedding 
7.  generate a very well writtien system prompt contains user prompt information related embedding information
8. send it ollama llama model ask to generate a sql query
9. Check the query syntax
10. call agnet to executre the query 
11. compute some results if need usign agent or llm 
12 return output 



Things to keep in mind 
1. Use langchain
2. create diff modular components or classes being used  for all entities  as data base can be multiple in fucture expected one neo4j , can use diff llm openai , gemeia2.5pro or ollmam
3. Entiteis: Database , data/columns , indexs, context, Agents , llm models or apis 
4. things for expandable code design for all modules copnnonets