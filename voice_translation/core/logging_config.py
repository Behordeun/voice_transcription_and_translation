import os
from pathlib import Path

from .error_trace import ErrorTraceLogger


def setup_logging(
    log_dir: str = None, debug_mode: bool = None, preserve_logs: bool = True
) -> ErrorTraceLogger:
    """
    Setup and configure the logging system for the application.

    Args:
        log_dir: Directory for log files (defaults to 'logs' in project root)
        debug_mode: Enable debug logging (defaults to environment variable)
        preserve_logs: Whether to preserve existing logs

    Returns:
        Configured ErrorTraceLogger instance
    """
    # Default log directory
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent
        log_dir = str(project_root / "logs")

    # Debug mode from environment if not specified
    if debug_mode is None:
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    # Create and configure logger
    logger = ErrorTraceLogger(
        log_dir=log_dir, preserve_logs=preserve_logs, debug_mode=debug_mode
    )

    # Log the initialization
    logger.info(
        "Logging system initialized",
        {"log_dir": log_dir, "debug_mode": debug_mode, "preserve_logs": preserve_logs},
    )

    return logger


# Global logger instance
app_logger = setup_logging()
