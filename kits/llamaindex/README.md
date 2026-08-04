# SmartPangolin × LlamaIndex
```python
from pangolin_tool import pangolin_tool
from llama_index.core.agent.workflow import FunctionAgent
agent = FunctionAgent(tools=[pangolin_tool], llm=llm)
```
`pip install smartpangolin llama-index-core`
