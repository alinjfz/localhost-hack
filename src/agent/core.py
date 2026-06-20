"""Main agent loop — LLM + memory + tools."""
import json
import ollama
from . import memory, tools, tracer
from .config import get_settings

settings = get_settings()

SYSTEM_PROMPT = f"""\
You are {settings.agent_name}, a fully offline AI assistant running on this device.
You have persistent memory (knowledge graph), can use tools, and operate without any internet connection.
Always think step-by-step. When you need information from memory or the filesystem, use a tool.
Keep responses concise and helpful.
"""


def _make_ollama_client():
    return ollama.AsyncClient(host=settings.ollama_base_url)


async def chat(
    messages: list[dict],
    use_memory: bool = True,
) -> tuple[str, list[dict]]:
    """
    Run one turn of the agent loop.
    Returns (assistant_text, updated_messages).
    """
    client = _make_ollama_client()
    await memory.init_memory()

    user_text = messages[-1]["content"] if messages else ""

    # Inject relevant memory as system context
    memory_ctx = ""
    if use_memory and user_text:
        recalled = await memory.recall(user_text)
        if recalled:
            memory_ctx = "\n\n[Memory context]\n" + "\n".join(recalled[:5])

    sys_message = {"role": "system", "content": SYSTEM_PROMPT + memory_ctx}
    full_messages = [sys_message] + messages

    tracer.record("user", user_text)

    # Agentic loop: keep calling until no more tool calls
    while True:
        response = await client.chat(
            model=settings.ollama_model,
            messages=full_messages,
            tools=tools.TOOL_DEFINITIONS,
        )
        msg = response["message"]
        tool_calls = msg.get("tool_calls") or []
        tracer.record("assistant", msg.get("content", ""), tool_calls)

        if not tool_calls:
            # Final answer
            answer = msg.get("content", "")
            # Store this exchange in memory
            if use_memory:
                exchange = f"User: {user_text}\nAssistant: {answer}"
                await memory.remember(exchange)
            await tracer.flush()
            updated = messages + [{"role": "assistant", "content": answer}]
            return answer, updated

        # Execute tool calls and feed results back
        full_messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc["function"]
            result = await tools.dispatch(fn["name"], fn.get("arguments", {}))
            tracer.record("tool", result)
            full_messages.append(
                {
                    "role": "tool",
                    "content": result,
                }
            )
