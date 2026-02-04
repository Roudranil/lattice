import datetime
import sys
import time
import uuid
from typing import Annotated, List, TypedDict

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from src.prompts.system import PRIMER_SYSTEM_PROMPT
from src.config.settings import get_settings
from src.utils.logger import create_logger
from src.utils.printer import ChatPrinter

# grab the settings
settings = get_settings()

# create two loggers
# one for normal stuff
# one for chat specific logs
logger = create_logger(path=settings.paths.logs_dir)
logger.debug(f"settings loaded as \n{settings.model_dump_json(indent=2)}")
printer = ChatPrinter()

# load the system prompt
SYSTEM_PROMPT = PRIMER_SYSTEM_PROMPT.format(
    date=datetime.datetime.now().strftime("%B %Y"), version="0.0.1-alpha"
)

# initialise the model
model = ChatOpenAI(
    model=settings.models.hf.chat,
    base_url=settings.env.HF_API_ENDPOINT,
    api_key=settings.env.HF_API_KEY,
    temperature=0,
)


# now build the graph in langgraph
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


# define the chat node
def chat_node(state: State) -> State:
    full_context = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model.invoke(full_context)
    return {"messages": [response]}


graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.add_edge(START, "chat")
graph.add_edge("chat", END)

# checkpointer = MemorySaver()
agent = graph.compile()
logger.info("Graph compiled and agent created.")

## create the chat loop
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
printer.system(f"Chat started (thread id: {config['configurable']['thread_id']})")
printer.debug("Type 'exit' to quit.\n")


while True:
    try:
        user_input = printer.prompt_user(">> ")
        if user_input.lower() == "exit":
            printer.system("Chat ended by user.")
            break

        if not user_input.strip():
            continue

        # pass a mutable dict to track token usage
        stream_stats = {"input": 0, "output": 0}

        def response_generator():
            for msg_chunk, metadata in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages",
            ):
                if isinstance(msg_chunk, AIMessageChunk):
                    # B. Capture Usage Metadata (usually in the last chunk)
                    if msg_chunk.usage_metadata:
                        stream_stats["input"] = msg_chunk.usage_metadata.get(
                            "input_tokens", 0
                        )
                        stream_stats["output"] = msg_chunk.usage_metadata.get(
                            "output_tokens", 0
                        )
                    # A. Yield the content for the UI
                    if msg_chunk.content:
                        yield msg_chunk.content

        start_time = time.time()
        final_response = printer.stream_ai(response_generator())
        duration = time.time() - start_time
        printer.token_usage(
            prompt_tokens=stream_stats["input"],
            completion_tokens=stream_stats["output"],
            latency=duration,
        )
    except KeyboardInterrupt:
        printer.warning("Interrupted by user.")
        logger.warning("Chat interrupted by user via KeyboardInterrupt.")
        break
    except Exception as e:
        printer.error(f"Runtime Error: {e}")
        logger.exception(f"Runtime Error: {e}")
        break
