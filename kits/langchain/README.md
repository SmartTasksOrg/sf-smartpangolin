# SmartPangolin × LangChain
```python
from pangolin_tool import make_pangolin_tools
tools = make_pangolin_tools()
llm_with_tools = llm.bind_tools(tools)   # or add to create_react_agent / AgentExecutor
```
Install SmartPangolin from a clone (see the main README, "Install"; it is not on PyPI yet), then:
`python -m pip install langchain-core pydantic`
