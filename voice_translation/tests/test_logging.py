#!/usr/bin/env python3
"""
Test script for the logging system
"""

from voice_translation.core.error_trace import logger
from voice_translation.core.logging_config import app_logger


def test_logging_system():
    """Test all logging levels and functionality"""
    print("Testing logging system...")

    # Test debug logging
    logger.debug("This is a debug message", {"test_type": "debug"})

    # Test info logging
    logger.info(
        "Application started successfully", {"version": "1.0.0", "component": "test"}
    )

    # Test warning logging
    logger.warning("This is a warning message", {"warning_type": "test"})

    # Test error logging with string
    logger.error("This is a test error message", {"error_type": "test"})

    # Test error logging with exception
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error(e, {"component": "test_exception"}, exc_info=True)

    # Test the configured app logger
    app_logger.info("Testing app logger configuration", {"test": "app_logger"})

    print("Logging test completed. Check the logs directory for output files.")


if __name__ == "__main__":
    test_logging_system()
