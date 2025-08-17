import streamlit as st
import pathlib as path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
import pandas as pd
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
from streamlit_extras.stylable_container import stylable_container


# -----------------------
# 🎨 Streamlit UI Setup
# -----------------------
st.set_page_config(page_title="SQL Chat with Groq",
                   page_icon="💬", layout="centered")
st.title("💬 Chat with Your SQL Database")
st.write("Ask questions about your data in natural language. Powered by **LangChain + Groq** ⚡")

# -----------------------
# 📂 Database Setup (SQLite)
# -----------------------
db_file = "emp.db"

# If db doesn’t exist, create a demo Employees table
if not path.Path(db_file).exists():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE Employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        salary REAL,
        hire_date TEXT
    )
    """)
    conn.commit()
    conn.close()

# SQLAlchemy engine
engine = create_engine(f"sqlite:///{db_file}")
db = SQLDatabase(engine)

# -----------------------
# 🔑 Groq API Setup
# -----------------------
groq_api_key = "YOUR_GROQ_API_KEY"


system_prompt = """You are a SQL assistant. 
You ONLY have these tools:
- sql_db_list_tables
- sql_db_schema
- sql_db_query
Never invent tool names. Always respond in the required format.
"""


system_message_prompt = SystemMessagePromptTemplate.from_template(
    system_prompt)


if groq_api_key:
    llm = ChatGroq(model="gemma2-9b-it", api_key=groq_api_key)

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        system_message=system_message_prompt   # 👈 here
    )


# -----------------------
# 💬 Chat Interface
# -----------------------
st.markdown(
    """
    <style>
    .user-bubble {
        background-color: #DCF8C6;
        color: #000;
        padding: 10px 15px;
        border-radius: 15px 15px 0px 15px;
        margin: 5px 0;
        display: inline-block;
        max-width: 80%;
    }
    .assistant-bubble {
        background-color: #F1F0F0;
        color: #000;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0px;
        margin: 5px 0;
        display: inline-block;
        max-width: 80%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render previous chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='assistant-bubble'>{msg['content']}</div>", unsafe_allow_html=True)

# Input box at the bottom
if prompt := st.chat_input("💬 Ask something about your database..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.markdown(
        f"<div class='user-bubble'>{prompt}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.run(prompt, callbacks=[st_callback])

        # If response looks tabular
        if isinstance(response, list):
            try:
                df = pd.DataFrame(response)
                st.dataframe(df, use_container_width=True)

                summary = f"✅ Found **{len(df)} rows** for your query."
                st.markdown(
                    f"<div class='assistant-bubble'>{summary}</div>", unsafe_allow_html=True)
                response_text = summary
            except Exception:
                st.markdown(
                    f"<div class='assistant-bubble'>{response}</div>", unsafe_allow_html=True)
                response_text = str(response)
        else:
            st.markdown(
                f"<div class='assistant-bubble'>{response}</div>", unsafe_allow_html=True)
            response_text = str(response)

    st.session_state["messages"].append(
        {"role": "assistant", "content": response_text})
