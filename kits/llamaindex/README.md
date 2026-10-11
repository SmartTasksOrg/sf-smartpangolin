# SmartPangolin × LlamaIndex
```python
from pangolin_tool import pangolin_tool
from llama_index.core.agent.workflow import FunctionAgent
agent = FunctionAgent(tools=[pangolin_tool], llm=llm)
```
Install SmartPangolin (`python -m pip install sf-smartpangolin`, see the main README, "Install"), then:
`python -m pip install llama-index-core`
