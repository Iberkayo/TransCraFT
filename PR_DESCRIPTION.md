This PR upgrades TransCraft with production-safe GenAI observability and experiment tracking.

Added:
- Langfuse node-level tracing for LangGraph agents
- MLflow experiment tracking for translation quality metrics
- Streamlit, CLI and evaluation runner tracking support
- Consistency metric logging
- Fail-safe optional integrations
- Updated tests and documentation

Validation:
- 4/4 tests passed
- app.py py_compile passed
