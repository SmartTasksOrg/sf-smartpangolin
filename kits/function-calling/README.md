# SmartPangolin × any tool-calling API (OpenAI / Anthropic / Gemini / Mistral / Bedrock)
```python
from pangolin_tool import TOOLS_OPENAI, TOOLS_ANTHROPIC, dispatch
# advertise TOOLS_OPENAI (or TOOLS_ANTHROPIC) to the model; when it calls a tool:
result = dispatch(tool_call.name, tool_call.arguments)   # -> JSON string for the model
```
`example_openai.py` shows a guarded call that refuses to share when secrets are present.
