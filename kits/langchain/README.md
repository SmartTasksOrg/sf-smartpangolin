# SmartPangolin × LangChain
```python
from pangolin_tool import make_pangolin_tools
tools = make_pangolin_tools()
llm_with_tools = llm.bind_tools(tools)   # or add to create_react_agent / AgentExecutor
```
Install SmartPangolin (`python -m pip install sf-smartpangolin`, see the main README, "Install"), then:
`python -m pip install langchain-core pydantic`
