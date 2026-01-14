from typing_extensions import TypedDict, Literal, Optional, List

class State(TypedDict):
    user_id: str
    user_query: str
    messages: List
    query_type: Optional[Literal["NORMAL", "RETRIEVAL"]]
