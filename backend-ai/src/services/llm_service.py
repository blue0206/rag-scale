import asyncio
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Literal
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from ..core.config import env_config
from ..models.chat import State
from ..core.llm_client import llm_client
from ..db.mem0 import mem0_client


async def stream_llm_response(user_id: str, user_query: str):
    """
    Invokes the langgraph workflow and streams the response as SSE.
    """

    config: RunnableConfig = {"configurable": {"thread_id": user_id}}
    initial_state = State(
        {
            "user_id": user_id,
            "user_query": user_query,
            "messages": [],
            "query_type": None,
        }
    )

    full_response = ""

    async for chunk in graph.astream(
        initial_state, config=config, stream_mode="custom"
    ):
        delta = chunk.get("delta")
        if delta:
            full_response += delta
            yield delta
            await asyncio.sleep(0.01)


def classify_query(state: State) -> State:
    """
    Makes an LLM call to classify the query as 'NORMAL' | 'RETRIEVAL'.
    """

    # Search mem0 for user context.
    mem_search = mem0_client.search(
        query=state.get("user_query"), user_id=state.get("user_id")
    )

    mem_list = [entry.get("memory") for entry in mem_search.get("results", [])]
    user_context = "\n".join(f"- {mem}" for mem in mem_list)

    SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant. You will receive a user query and based on
    the query, return either of the following:

    'NORMAL' - If the query is a normal chat query not involving document look-up.
    'RETRIEVAL' - If the query is related to a document.

    You are also provided with a context about the user:
    {user_context}

    Note that the user query might a be text input by the user, or a transcript of their voice query.

    In case you are unable to make out the type of query, return 'NORMAL'.
    """

    # Add user query to messages.
    state["messages"] = [{"role": "user", "content": state.get("user_query")}]

    # Make LLM call.
    response = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages"),
    )

    # Update state with query type.
    output_text = response.output_text.strip().upper()
    if output_text not in ["NORMAL", "RETRIEVAL"]:
        output_text = "NORMAL"

    assert output_text == "NORMAL" or output_text == "RETRIEVAL"

    state["query_type"] = output_text
    return state


def route_query(state: State) -> Literal["normal_query", "retrieval_query"]:
    """
    Routes the query to the appropriate node.
    """

    if state.get("query_type") == "RETRIEVAL":
        return "retrieval_query"

    return "normal_query"


def normal_query(state: State):
    """
    Makes a streaming LLM call to answer the user query and yeilds response
    as chunks.
    """

    # Search mem0 for user context.
    mem_search = mem0_client.search(
        query=state.get("user_query"), user_id=state.get("user_id")
    )

    mem_list = [entry.get("memory") for entry in mem_search.get("results", [])]
    user_context = "\n".join(f"- {mem}" for mem in mem_list)

    SYSTEM_PROMPT = f"""
    You are an expert AI Assistant. 
    You will receive a user query and based on the query, return a helpful response.

    If you are unable to answer the query or need to perform a web search, use the tavily mcp tool to search for the answer.

    Note that the user query might a be text input by the user, or a transcript of their voice query.

    You are also provided with a context about the user:
    {user_context}
    """

    writer = get_stream_writer()

    # Make LLM call with web search mcp.
    stream = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages"),
        tools=[
            {
                "type": "mcp",
                "server_label": "tavily",
                "server_url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={env_config['TAVILY_API_KEY']}",
                "require_approval": "never",
            },
        ],
        stream=True,
    )

    response_text = ""
    for chunk in stream:
        if chunk.type == "response.output_text.delta":
            response_text += chunk.delta
            writer({"delta": chunk.delta})

    # Update state messages with final response.
    state["messages"] = [{"role": "assistant", "content": response_text}]

    # mem0 handles updating factual, episodic, and semantic memory
    # about user based on provided messages.
    mem0_client.add(
        user_id=state.get("user_id"),
        messages=[
            {"role": "user", "content": state.get("user_query")},
            {"role": "assistant", "content": response_text},
        ],
    )

    return state


def retrieval_query(state: State):
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
        embedding=embeddings,
    )

    # Perform vector similarity search with user query and filter by user ID.
    # This ensures that the search is only performed on the user's documents.
    search_results = vector_db.similarity_search(
        query=state.get("user_query"),
        filter=Filter(
            must=[
                FieldCondition(
                    key="user_ID", match=MatchValue(value=state.get("user_id"))
                )
            ]
        ),
    )

    # Format search results into context.
    context = [
        f"Page Content: {result.page_content}\nPage Label: {result.metadata.get('page_label')}"
        for result in search_results
    ]

    # Search mem0 for user context.
    mem_search = mem0_client.search(
        query=state.get("user_query"), user_id=state.get("user_id")
    )

    mem_list = [entry.get("memory") for entry in mem_search.get("results", [])]
    user_context = "\n".join(f"- {mem}" for mem in mem_list)

    SYSTEM_PROMPT = f"""
    You are an expert AI Assistant. You will receive a user query.
    You have to answer the query based on the document context provided.

    Note that the user query might a be text input by the user, or a transcript of their voice query.

    If applicable and available, also provide the page number where the answer is found.
    If context not available, try to answer the query based on your general knowledge, else return a helpful message.

    You are also provided with a context about the user:
    {user_context}

    Document Context:
    {context}
    """

    writer = get_stream_writer()

    stream = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=state.get("messages"),
        stream=True,
    )

    response_text = ""
    for chunk in stream:
        if chunk.type == "response.output_text.delta":
            response_text += chunk.delta
            writer({"delta": chunk.delta})

    # Update state messages with final response.
    state["messages"] = [{"role": "assistant", "content": response_text}]

    # mem0 handles updating factual, episodic, and semantic memory
    # about user based on provided messages.
    mem0_client.add(
        user_id=state.get("user_id"),
        messages=[
            {"role": "user", "content": state.get("user_query")},
            {"role": "assistant", "content": response_text},
        ],
    )

    return state


workflow = StateGraph(State)
# Add nodes.
workflow.add_node("classify_query", classify_query)
workflow.add_node("normal_query", normal_query)
workflow.add_node("retrieval_query", retrieval_query)

# Setup edges.
workflow.add_edge(START, "classify_query")
workflow.add_conditional_edges("classify_query", route_query)
workflow.add_edge("normal_query", END)
workflow.add_edge("retrieval_query", END)

# Setup in-memory checkpoint
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
