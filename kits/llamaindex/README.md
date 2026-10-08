# SmartPangolin × LlamaIndex
```python
from pangolin_tool import pangolin_tool
from llama_index.core.agent.workflow import FunctionAgent
agent = FunctionAgent(tools=[pangolin_tool], llm=llm)
```
Install SmartPangolin from a clone (see the main README, "Install"; it is not on PyPI yet), then:
`python -m pip install llama-index-core`
