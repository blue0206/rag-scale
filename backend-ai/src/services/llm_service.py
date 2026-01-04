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

    Note that the user_query might a be text input by the user, or a transcript of their voice query.

    In case you are unable to make out the type of query, return 'NORMAL'.
    """
    
    response = llm_client.responses.create(
        model=env_config["GROQ_MODEL"],
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": state["user_query"]}],
    )

    state["query_type"] = response.output[-1].content[-1].text.strip().upper()
    return state

