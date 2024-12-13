import logging
import psutil
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SystemStatus:
    """System status constants"""
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"

class MonitoringService:
    """Monitors system health and resource usage."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_health(self) -> Tuple[str, List[str]]:
        """
        Check system health status.
        
        Returns:
            Tuple[str, List[str]]: Status and list of warnings
        """
        warnings = []
        status = SystemStatus.OK

        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            warnings.append(f"High CPU usage: {cpu_percent}%")
            status = SystemStatus.WARNING

        return status, warnings