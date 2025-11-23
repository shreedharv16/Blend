# LangSmith Integration Guide

This document explains how LangSmith is integrated into the Retail Insights Assistant and how to use it for tracing and monitoring your LangChain/LangGraph agents.

## What is LangSmith?

LangSmith is a platform for debugging, testing, evaluating, and monitoring LLM applications. It provides:
- **Tracing**: Visualize every step of your agent workflows
- **Debugging**: Inspect inputs/outputs of each LLM call
- **Monitoring**: Track performance metrics and costs
- **Testing**: Evaluate your prompts and chains

## Setup

### 1. Get Your API Key

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to Settings → API Keys
3. Create a new API key

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory with:

```env
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=retail-insights-assistant
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Important**: 
- `LANGCHAIN_TRACING_V2` must be the string `"true"` (not a boolean)
- `LANGCHAIN_PROJECT` is the name that will appear in your LangSmith dashboard
- You can customize the project name to organize different environments (e.g., `retail-insights-dev`, `retail-insights-prod`)

### 3. Verify Integration

Start your backend server:

```bash
cd backend
python run.py
```

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{
  "status": "healthy",
  "environment": "development",
  "model": "gemini-2.0-flash-exp",
  "langsmith_enabled": true,
  "langsmith_project": "retail-insights-assistant"
}
```

Look for this log message on startup:

```
✓ LangSmith tracing enabled for project: retail-insights-assistant
```

## What Gets Traced?

LangSmith automatically traces all LangChain/LangGraph operations:

### 1. **Agent Workflow Execution**
   - Entry through `query_understanding` agent
   - Transitions between agents
   - Conditional routing decisions
   - Final output generation

### 2. **LLM Calls**
   - All Gemini API calls via `ChatGoogleGenerativeAI`
   - Prompts sent to the model
   - Model responses
   - Token usage and latency

### 3. **Agent Operations**
   - Query Understanding Agent
   - SQL Generation Agent
   - Data Retrieval Agent
   - Validation Agent
   - Insight Generation Agent

### 4. **Chain Executions**
   - System prompts
   - User messages
   - Intermediate results
   - Error handling and retries

## Using LangSmith Dashboard

### Viewing Traces

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Select your project (e.g., `retail-insights-assistant`)
3. You'll see a list of all trace runs

### Understanding Trace Details

Each trace shows:
- **Run ID**: Unique identifier for the trace
- **Duration**: Total execution time
- **Status**: Success, Error, or Cancelled
- **Input**: User query and initial state
- **Output**: Final response with insights and visualizations
- **Cost**: Estimated API costs (if configured)

### Debugging Failed Runs

Click on any trace to see:
- **Timeline**: Visual representation of agent flow
- **Inputs/Outputs**: For each step
- **Errors**: Stack traces and error messages
- **Metadata**: State changes, retry counts, etc.

## Advanced Features

### Custom Tags and Metadata

You can add custom tags to traces by modifying the graph invocation in `backend/app/agents/graph.py`:

```python
from langsmith import traceable

@traceable(
    run_type="chain",
    name="retail_insights_workflow",
    tags=["production", "user_123"]
)
async def run_agent_workflow(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    # existing code...
```

### Monitoring Specific Agents

Each agent can be individually traced:

```python
from langsmith import traceable

@traceable(name="query_understanding", run_type="llm")
async def query_understanding_agent(state: GraphState):
    # agent code...
```

### Environment-Specific Projects

Use different projects for different environments:

**.env.development**:
```env
LANGCHAIN_PROJECT=retail-insights-dev
```

**.env.production**:
```env
LANGCHAIN_PROJECT=retail-insights-prod
```

## Troubleshooting

### Traces Not Appearing

1. **Check API Key**: Verify `LANGCHAIN_API_KEY` is set correctly
2. **Check Tracing Flag**: Ensure `LANGCHAIN_TRACING_V2=true` (string, not boolean)
3. **Check Logs**: Look for the startup message about LangSmith
4. **Network Issues**: Ensure your server can reach `https://api.smith.langchain.com`

### Partial Traces

If you see incomplete traces:
- Check for unhandled exceptions in agents
- Verify all async operations are properly awaited
- Look for early returns or exits in the workflow

### High Costs

LangSmith itself is free for development, but be aware of:
- Gemini API costs for LLM calls
- Storage costs for large trace volumes
- Consider sampling in production (trace 10% of requests)

## Best Practices

1. **Use Descriptive Project Names**: Helps organize traces by environment or feature
2. **Add Metadata**: Include user IDs, session IDs, or feature flags
3. **Monitor Regularly**: Check traces to identify slow agents or high costs
4. **Test Prompts**: Use LangSmith's playground to iterate on prompts
5. **Set Up Alerts**: Configure alerts for error rates or latency thresholds

## Disabling LangSmith

To disable tracing:

1. Remove `LANGCHAIN_API_KEY` from `.env`, or
2. Set `LANGCHAIN_TRACING_V2=false`

The application will work normally without LangSmith, just without tracing.

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangChain Tracing Guide](https://python.langchain.com/docs/langsmith/)
- [LangGraph with LangSmith](https://langchain-ai.github.io/langgraph/concepts/langsmith/)

