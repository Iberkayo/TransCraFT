import os
from typing import Dict, Any, Optional
import uuid

# Import the Config securely
from src.core.config import Config

class LangfuseTracker:
    _instance = None
    _langfuse = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangfuseTracker, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.enabled = Config.ENABLE_LANGFUSE
        if self.enabled:
            try:
                from langfuse import Langfuse
                self._langfuse = Langfuse(
                    public_key=Config.LANGFUSE_PUBLIC_KEY,
                    secret_key=Config.LANGFUSE_SECRET_KEY,
                    host=Config.LANGFUSE_HOST
                )
            except Exception as e:
                print(f"Warning: Langfuse could not be initialized. Disabling tracking. Error: {e}")
                self.enabled = False

    def get_callback_handler(self, trace_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Returns a Langchain Callback Handler for the given trace."""
        if not self.enabled or not self._langfuse:
            return None
        
        try:
            from langfuse.callback import CallbackHandler
            handler = CallbackHandler(
                public_key=Config.LANGFUSE_PUBLIC_KEY,
                secret_key=Config.LANGFUSE_SECRET_KEY,
                host=Config.LANGFUSE_HOST,
            )
            # Link callback handler to the explicit trace ID
            handler.set_trace_id(trace_id)
            return handler
        except Exception as e:
            print(f"Warning: Failed to create Langfuse callback handler. Error: {e}")
            return None

    def create_trace(self, name: str, trace_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new trace and return its ID."""
        if not trace_id:
            trace_id = str(uuid.uuid4())

        if not self.enabled or not self._langfuse:
            return trace_id

        try:
            self._langfuse.trace(
                id=trace_id,
                name=name,
                metadata=metadata or {}
            )
        except Exception as e:
            pass # Silent failure for observability
            
        return trace_id

    def create_span(self, trace_id: str, name: str, input_data: Any = None, metadata: Optional[Dict[str, Any]] = None):
        """Create a custom span within a trace."""
        if not self.enabled or not self._langfuse:
            return None
            
        try:
            return self._langfuse.span(
                trace_id=trace_id,
                name=name,
                input=input_data,
                metadata=metadata or {}
            )
        except Exception:
            return None

    def end_span(self, span, output_data: Any = None, level: str = "DEFAULT"):
        """End a custom span."""
        if not self.enabled or not span:
            return
            
        try:
            span.end(
                output=output_data,
                level=level
            )
        except Exception:
            pass
            
    def flush(self):
        if self.enabled and self._langfuse:
            try:
                self._langfuse.flush()
            except Exception:
                pass

# Create a singleton instance
tracker = LangfuseTracker()
