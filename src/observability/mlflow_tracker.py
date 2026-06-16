import os
import time
from typing import Dict, Any, Optional
from src.core.config import Config

class MLflowTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLflowTracker, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.enabled = Config.ENABLE_MLFLOW
        if self.enabled:
            try:
                import mlflow
                mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
                mlflow.set_experiment(Config.MLFLOW_EXPERIMENT_NAME)
                self._mlflow = mlflow
            except Exception as e:
                print(f"Warning: MLflow could not be initialized. Disabling tracking. Error: {e}")
                self.enabled = False

    def log_translation_experiment(self, 
                                   run_name: str, 
                                   params: Dict[str, Any], 
                                   metrics: Dict[str, float], 
                                   artifacts: Optional[Dict[str, str]] = None):
        """Logs a complete translation experiment run."""
        if not self.enabled:
            return

        try:
            with self._mlflow.start_run(run_name=run_name):
                # Log parameters
                self._mlflow.log_params(params)
                
                # Log metrics
                self._mlflow.log_metrics(metrics)
                
                # Log artifacts (files)
                if artifacts:
                    for name, path in artifacts.items():
                        if os.path.exists(path):
                            self._mlflow.log_artifact(path)
        except Exception as e:
            print(f"Warning: Failed to log experiment to MLflow. Error: {e}")

    def log_memory_effectiveness_metrics(self, metrics: Dict[str, Any]):
        """Log memory effectiveness metrics without failing translation."""
        if not self.enabled:
            return

        try:
            numeric_metrics = {
                key: float(value)
                for key, value in metrics.items()
                if isinstance(value, (int, float))
            }
            with self._mlflow.start_run(run_name="memory_effectiveness", nested=True):
                self._mlflow.log_metrics(numeric_metrics)
        except Exception as e:
            print(f"Warning: Failed to log memory effectiveness to MLflow. Error: {e}")

    def log_memory_router_metrics(self, metrics: Dict[str, Any]):
        """Log memory-aware router metrics without failing translation."""
        if not self.enabled or not metrics:
            return

        try:
            numeric_metrics = {
                key: float(value)
                for key, value in metrics.items()
                if isinstance(value, (int, float))
            }
            with self._mlflow.start_run(run_name="memory_aware_router", nested=True):
                self._mlflow.log_metrics(numeric_metrics)
        except Exception as e:
            print(f"Warning: Failed to log memory-aware router metrics to MLflow. Error: {e}")

    def log_strategy_planner_metrics(self, strategy: Dict[str, Any]):
        """Log strategy planner metrics without failing translation."""
        if not self.enabled or not strategy:
            return

        try:
            metrics = {
                "strategy_planner_enabled": 1.0,
                "strategy_meaning_unit_count": float(len(strategy.get("meaning_units", []) or [])),
                "strategy_structural_risk_count": float(len(strategy.get("structural_risks", []) or [])),
                "strategy_fallback_used": 1.0 if strategy.get("fallback_used") else 0.0,
            }
            params = {
                "strategy_text_type": str(strategy.get("text_type", "")),
                "strategy_literalness_level": str(strategy.get("literalness_level", "")),
            }
            with self._mlflow.start_run(run_name="translation_strategy_planner", nested=True):
                self._mlflow.log_metrics(metrics)
                self._mlflow.log_params(params)
        except Exception as e:
            print(f"Warning: Failed to log strategy planner metrics to MLflow. Error: {e}")

# Create singleton
mlflow_tracker = MLflowTracker()
