from operator import add
from openai.types.responses import ResponseInputParam
from typing_extensions import TypedDict, Literal, Optional, Annotated

class State(TypedDict):
    user_id: str
    user_query: str
    messages: Annotated[ResponseInputParam, add]
    query_type: Optional[Literal["NORMAL", "RETRIEVAL"]]
