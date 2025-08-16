import streamlit as st
from goose3 import Goose
from urllib.parse import urlparse
from langchain_groq import ChatGroq
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from ddgs import DDGS
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from bs4 import BeautifulSoup
import requests

# -------------------------
# 🔑 Config
# -------------------------
st.set_page_config(page_title="AI Research Assistant",
                   layout="wide", page_icon="🧠")
st.title("🧠 AI-Powered Research Assistant")
st.write("Ask me anything — I’ll search, extract, and summarize content from multiple sources.")

# ✅ Groq API key
GROQ_API_KEY = ""
llm = ChatGroq(model="gemma2-9b-it", api_key=GROQ_API_KEY)

# -------------------------
# ⚒️ Tools
# -------------------------
wiki_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=wiki_wrapper)

arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=500)
arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

tools = [wiki, arxiv]

# -------------------------
# 🐦 Robust article extractor
# -------------------------
goose = Goose()


def extract_article_text(url: str, max_chars: int = 3000) -> str:
    """Extract main content from URL using Goose, fallback to requests+BS."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url

        # Try Goose first
        article = goose.extract(url=url)
        text = article.cleaned_text.strip()
        if text:
            return text[:max_chars]

        # Fallback: requests + BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return f"⚠️ Failed to fetch article: {resp.status_code}"

        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text().strip()
                         for p in paragraphs if p.get_text().strip())
        return text[:max_chars] if text else "⚠️ No content found"

    except Exception as e:
        return f"⚠️ Article extraction error: {e}"

# -------------------------
# 🔍 DuckDuckGo URL fetcher (limit 3)
# -------------------------


def fetch_valid_urls(query: str, max_results: int = 3):
    urls = []
    seen = set()
    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query, safesearch="Off", timelimit="", region="wt-wt", max_results=max_results*2
            )  # fetch extra in case of duplicates/bad links
            for r in results:
                link = r.get("href")
                if link and link.startswith("http") and link not in seen:
                    urls.append(link)
                    seen.add(link)
                if len(urls) >= max_results:
                    break
    except Exception as e:
        st.warning(f"⚠️ DuckDuckGo search error: {e}")
    return urls

# -------------------------
# 🔍 Research function
# -------------------------


def research_question(question: str) -> str:
    reasoning_trace = []

    # Step 1: Collect snippets from Wikipedia/Arxiv
    snippets = []
    for tool in tools:
        try:
            r = tool.run(question)
            if r:
                snippets.append(f"{tool.name}: {r}")
                reasoning_trace.append(f"✅ Tool result: {tool.name}")
        except Exception as e:
            reasoning_trace.append(f"⚠️ Tool error: {tool.name} - {e}")

    # Step 2: Fetch URLs via DuckDuckGo
    ddg_urls = fetch_valid_urls(question, max_results=3)
    reasoning_trace.append(f"🔹 DuckDuckGo found {len(ddg_urls)} URLs")

    # Step 3: Extract content via Goose + fallback
    article_texts = []
    valid_urls = []  # keep track of extracted URLs
    for url in ddg_urls:
        extracted = extract_article_text(url)
        if extracted and not extracted.startswith("⚠️"):
            article_texts.append(f"[Source]({url}):\n{extracted}")
            valid_urls.append(url)
            reasoning_trace.append(f"✅ Extracted article from {url}")
        else:
            reasoning_trace.append(f"⚠️ Failed to extract article from {url}")

    # Step 4: Compose prompt for Groq
    if article_texts:
        combined = "\n\n".join(article_texts)
        prompt = f"""
The user asked: {question}

Please summarize the following content into a readable, concise answer that:
- Retains all important facts, numbers, dates, and context
- Highlights source URLs in Markdown
- Uses clear paragraphs
- Avoids repetitive phrases

Content:
{combined}
{print(combined)}
"""
        reasoning_trace.append("🤖 Groq summarizing extracted content...")
        answer = llm.invoke(prompt).content

    elif snippets:
        combined = "\n\n".join(snippets)
        prompt = f"""
The user asked: {question}

Please summarize the following research snippets into a readable, concise answer:
{combined}
"""
        reasoning_trace.append("🤖 Groq summarizing research snippets...")
        answer = llm.invoke(prompt).content

    else:
        prompt = f"""
The user asked: {question}

No external sources returned results. Provide a concise, factual answer from internal knowledge.
"""
        reasoning_trace.append("🤖 Groq answering from internal knowledge...")
        answer = llm.invoke(prompt).content

    # Display reasoning trace
    st.write("📝 Reasoning trace")
    for line in reasoning_trace:
        st.write(line)

    # Display answer in styled box
    st.markdown(
        f"<div style='font-size:16px; font-family:Arial; color:#0b3d91'>{answer}</div>", unsafe_allow_html=True
    )

    # Display only valid sources
    if valid_urls:
        st.markdown("**Sources:**")
        for url in valid_urls:
            st.markdown(f"- [🔗 {url}]({url})", unsafe_allow_html=True)

    return answer


# -------------------------
# 💬 Chat UI
# -------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.chat_input("🔎 Ask me a research question...")

if user_query:
    st.session_state.chat_history.append(
        {"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        with st.spinner("🔍 Researching and summarizing..."):
            answer = research_question(user_query)

            # Styled answer box
            st.markdown(
                f"<div style='font-size:18px; font-weight:bold; color:#0b3d91; background-color:#e1f0ff; "
                f"padding:15px; border-radius:10px'>{answer}</div>",
                unsafe_allow_html=True
            )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer})
