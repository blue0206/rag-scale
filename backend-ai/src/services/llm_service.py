from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Literal
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from ..core.config import env_config
from ..models.chat import State
from ..core.llm_client import llm_client

def classify_query(state: State) -> State:
    """
    Makes an LLM call to classify the query as 'NORMAL' | 'RETRIEVAL'.
    """

    SYSTEM_PROMPT = """
    You are a helpful AI Assistant. You will receive a user query and based on
    the query, return either of the following:

    'NORMAL' - If the query is a normal chat query not involving document look-up.
    'RETRIEVAL' - If the query is related to a document.

    Note that the user query might a be text input by the user, or a transcript of their voice query.

    In case you are unable to make out the type of query, return 'NORMAL'.
    """

    state["messages"] = {"role": "user", "content": state.get("user_query")}
    
    response = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages")
    )

    state["query_type"] = response.output[-1].content[-1].text.strip().upper()
    return state

def route_query(state: State) -> Literal["NORMAL", "RETRIEVAL"]:
    """
    Routes the query to the appropriate node.
    """

    if state.get("query_type") == "RETRIEVAL":
        return "RETRIEVAL"
    
    return "NORMAL"

def normal_query(state: State) -> State:
    """
    Makes an LLM call to answer the user query.
    """

    SYSTEM_PROMPT = """
    You are an expert AI Assistant. 
    You will receive a user query and based on the query, return a helpful response.

    If you are unable to answer the query or need to perform a web search, use the tavily mcp tool to search for the answer.

    Note that the user query might a be text input by the user, or a transcript of their voice query.
    """

    response = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages"),
        tools=[
            {
                "type": "mcp",
                "server_label": "tavily",
                "server_url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={env_config["TAVILY_API_KEY"]}",
                "require_approval": "never",
            },
        ]
    )

    state["messages"] = {"role": "assistant", "content": response.output[-1].content[-1].text}
    return state

def retrieval_query(state: State) -> State:
    """
    Converts user query into vector embeddings and performs a vector similarity
    search to retrieve relevant data from vector database to answer the query.
    The retrieved data is then sent to the LLM to generate a response.
    """

    embeddings = OllamaEmbeddings(
        model=env_config["EMBEDDER_MODEL"],
        base_url="http://localhost:11434",
    )

    vector_db = QdrantVectorStore.from_existing_collection(
        url="http://localhost:6333",
        collection_name=env_config["RAG_COLLECTION_NAME"],
        embedding=embeddings
    )

    search_results = vector_db.similarity_search(
        query=state.get("user_query"), 
        filter=Filter(
            must=[
                FieldCondition(
                    key="user_ID",
                    match=MatchValue(value=state.get("user_id"))
                )
            ]
        )
    )

    context = [f"Page Content: {result.page_content}\nPage Label: {result.metadata.get("page_label")}" for result in search_results]

    SYSTEM_PROMPT = f"""
    You are an expert AI Assistant. You will receive a user query.
    You have to answer the query based on the context provided.

    Note that the user query might a be text input by the user, or a transcript of their voice query.

    If applicable and available, also provide the page number where the answer is found.
    If context not available, try to answer the query based on your general knowledge, else return a helpful message.

    Context:
    {context}
    """

    response = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages"),
    )

    state["messages"] = {"role": "assistant", "content": response.output[-1].content[-1].text}
    return state
