from operator import add
from typing_extensions import TypedDict, Annotated, Literal, Optional

class State(TypedDict):
    user_id: str
    user_query: str
    messages: Annotated[list, add]
    query_type: Optional[Literal["NORMAL", "RETRIEVAL"]]
