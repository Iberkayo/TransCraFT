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

# Create singleton
mlflow_tracker = MLflowTracker()
