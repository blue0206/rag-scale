from operator import add
from typing_extensions import TypedDict, Literal, Optional

class State(TypedDict):
    user_id: str
    user_query: str
    messages: list
    query_type: Optional[Literal["NORMAL", "RETRIEVAL"]]
