from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langserve import add_routes

GrokApi = "Your_API_KEY"

app = FastAPI(title="Langchain Demo With Grok Model")

model = ChatGroq(model="gemma2-9b-it", api_key=GrokApi)

add_routes(app, model)

# Create prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are the best gym trainer in the world and your job is to give accurate gym schedule for any day of the week. based on my question."),
        ("user", "Question:{question}")
    ]
)


# Create output parser
output_parser = StrOutputParser()

# chain
chain = prompt | model | output_parser

# App Defination

add_routes(app, chain, path="/chain")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
