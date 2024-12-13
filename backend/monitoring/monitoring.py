import logging
import logging.config
import json
from pathlib import Path
import psutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import threading

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


@dataclass
class SystemMetrics:
    """Container for system metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_tasks: int
    failed_tasks: int
    processing_time: float
    timestamp: str = datetime.utcnow().isoformat()


class SystemStatus:
    """System status constants"""
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class MetricsCollector:
    """Collects and stores system metrics"""

    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        self._lock = threading.Lock()

    def add_metrics(self, metrics: SystemMetrics):
        with self._lock:
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

    def get_recent_metrics(self, n: int = 10) -> List[SystemMetrics]:
        with self._lock:
            return self.metrics_history[-n:]

    def export_metrics(self, export_path: Path):
        """Export metrics to JSON file"""
        with self._lock:
            metrics_data = [vars(m) for m in self.metrics_history]
            export_path.write_text(json.dumps(metrics_data, indent=2))


class MonitoringService:
    """Enhanced monitoring service with metrics collection and health checks"""

    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.metrics_collector = MetricsCollector()

        # Create metrics export directory
        self.metrics_dir = PROJECT_ROOT / "logs" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure logging using config file"""
        config_path = PROJECT_ROOT / "config" / "logging_config.json"

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

            # Update log file paths to use project structure
            for handler in config.get("handlers", {}).values():
                if "filename" in handler:
                    # Convert relative paths to absolute using project structure
                    log_path = PROJECT_ROOT / "logs" / handler["filename"]
                    handler["filename"] = str(log_path)

            logging.config.dictConfig(config)
        else:
            # Fallback logging config
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(PROJECT_ROOT / "logs" / "app.log"),
                    logging.StreamHandler()
                ]
            )

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        metrics = SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            active_tasks=self._count_active_tasks(),
            failed_tasks=self._count_failed_tasks(),
            processing_time=self._get_average_processing_time()
        )

        # Store metrics
        self.metrics_collector.add_metrics(metrics)

        # Export metrics periodically
        if len(self.metrics_collector.metrics_history) % 100 == 0:
            export_path = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.metrics_collector.export_metrics(export_path)

        return metrics

    def _count_active_tasks(self) -> int:
        """Count currently processing tasks"""
        return len([p for p in psutil.process_iter(['name'])
                   if p.info['name'] == 'python' and 'process_single_file' in p.cmdline()])

    def _count_failed_tasks(self) -> int:
        """Count failed tasks from status tracker"""
        return 0  # Implement based on your status tracking

    def _get_average_processing_time(self) -> float:
        """Calculate average processing time of recent tasks"""
        return 0.0

    def check_health(self) -> Tuple[str, List[str]]:
        """Comprehensive health check"""
        warnings = []
        status = SystemStatus.OK

        metrics = self.collect_metrics()

        # CPU check
        if metrics.cpu_percent > 90:
            warnings.append(f"Critical CPU usage: {metrics.cpu_percent}%")
            status = SystemStatus.CRITICAL
        elif metrics.cpu_percent > 75:
            warnings.append(f"High CPU usage: {metrics.cpu_percent}%")
            status = SystemStatus.WARNING

        # Memory check
        if metrics.memory_percent > 90:
            warnings.append(f"Critical memory usage: {metrics.memory_percent}%")
            status = SystemStatus.CRITICAL
        elif metrics.memory_percent > 75:
            warnings.append(f"High memory usage: {metrics.memory_percent}%")
            status = SystemStatus.WARNING

        # Disk check
        if metrics.disk_usage_percent > 90:
            warnings.append(f"Critical disk usage: {metrics.disk_usage_percent}%")
            status = SystemStatus.CRITICAL

        # Log health check results
        self.logger.info({
            "event": "health_check",
            "status": status,
            "warnings": warnings,
            "metrics": vars(metrics)
        })

        return status, warnings

    def log_task_completion(self, task_id: str, success: bool, duration: float):
        """Log task completion metrics"""
        self.logger.info({
            "event": "task_completion",
            "task_id": task_id,
            "success": success,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_extraction_metrics(self, task_id: str, pdf_path: str, courses_found: int):
        """Log extraction-specific metrics"""
        self.logger.info({
            "event": "extraction_metrics",
            "task_id": task_id,
            "pdf_path": str(pdf_path),
            "courses_found": courses_found,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_llm_metrics(self, task_id: str, model_name: str, tokens_processed: int, processing_time: float):
        """Log LLM-specific processing metrics"""
        self.logger.info({
            "event": "llm_metrics",
            "task_id": task_id,
            "model": model_name,
            "tokens_processed": tokens_processed,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        })
