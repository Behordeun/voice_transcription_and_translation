import inspect
import sys
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ErrorTraceLogger:
    def __init__(
        self,
        log_dir: str = "logs",
        preserve_logs: bool = True,
        debug_mode: bool = False,
    ) -> None:
        self.log_dir = Path(log_dir)
        self.preserve_logs = preserve_logs
        self.debug_mode = debug_mode
        self.log_files = {
            LogLevel.DEBUG: self.log_dir / "debug.log",
            LogLevel.INFO: self.log_dir / "info.log",
            LogLevel.WARNING: self.log_dir / "warning.log",
            LogLevel.ERROR: self.log_dir / "error.log",
        }
        self._ensure_log_directory()
        self._log_cache = self._load_existing_log_hashes() if preserve_logs else set()

    def _ensure_log_directory(self) -> None:
        """Create the log directory if it doesn't exist."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.log_dir / "test_write.tmp"
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                test_file.unlink()
            except Exception as perm_error:
                print(
                    f"Permission error in log directory: {perm_error}", file=sys.stderr
                )
        except Exception as e:
            print(
                f"Failed to create log directory {self.log_dir}: {e}", file=sys.stderr
            )
            self.log_dir = Path.cwd() / "logs"
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as fallback_error:
                print(
                    f"Fallback directory creation failed: {fallback_error}",
                    file=sys.stderr,
                )

    def _load_existing_log_hashes(self) -> set:
        """Load hashes of existing log entries to prevent duplicates."""
        cache = set()
        for log_file in self.log_files.values():
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        entries = content.split("=" * 80 + "\n")
                        for entry in entries:
                            if entry.strip():
                                cache.add(hash("=" * 80 + "\n" + entry.strip() + "\n"))
                except Exception:
                    pass
        return cache

    @staticmethod
    def _get_caller_info() -> tuple[str, str, str, int]:
        """Get detailed caller information."""
        stack = inspect.stack()
        caller_frame = next(
            (frame for frame in stack if frame.filename != __file__),
            stack[2] if len(stack) > 2 else None,
        )
        if caller_frame:
            return (
                caller_frame.function,
                Path(caller_frame.filename).name,
                caller_frame.filename,
                caller_frame.lineno,
            )
        return "Unknown", "Unknown", "Unknown", 0

    def _format_message(
        self,
        level: LogLevel,
        message: str,
        error: Optional[Union[Exception, str]] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> str:
        """Format the complete log message with all metadata."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        function_name, file_name, _, line_no = self._get_caller_info()

        log_msg = [
            "=" * 80,
            f"TIMESTAMP: {timestamp}",
            f"LEVEL: {level.value}",
            f"FILE: {file_name}",
            f"FUNCTION: {function_name}",
            f"LINE: {line_no}",
            "-" * 80,
            f"MESSAGE: {message}",
        ]

        if isinstance(error, BaseException):
            log_msg.extend(
                [
                    f"ERROR TYPE: {type(error).__name__}",
                    f"ERROR MESSAGE: {str(error)}",
                    "-" * 80,
                ]
            )
            if exc_info:
                try:
                    trace_lines = traceback.format_exception(
                        type(error), error, error.__traceback__
                    )
                    log_msg.extend(["FULL TRACEBACK:", "".join(trace_lines)])
                except Exception as format_err:
                    log_msg.append(f"Failed to format traceback: {str(format_err)}")
        elif isinstance(error, str):
            log_msg.extend([f"ERROR MESSAGE: {error}", "-" * 80])

        # Add context
        context = {"ai_engineer": "Muhammad", "environment": "production"}
        if additional_info:
            context.update(additional_info)

        log_msg.extend(
            [
                "-" * 80,
                "CONTEXT:",
                "\n".join(f"{k}: {v}" for k, v in context.items()),
                "=" * 80 + "\n",
            ]
        )

        return "\n".join(log_msg)

    def _write_log(self, level: LogLevel, message: str) -> None:
        """Write a message to the log file with duplicate prevention."""
        log_hash = hash(message)
        if log_hash in self._log_cache:
            return

        try:
            self._ensure_log_directory()
            log_file = self.log_files[level]
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(message)
                f.flush()
            self._log_cache.add(log_hash)
        except Exception as e:
            print(
                f"Failed to write log to {self.log_files[level]}: {e}", file=sys.stderr
            )

    def debug(
        self, message: str, additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a debug message."""
        log_message = self._format_message(
            LogLevel.DEBUG, message, additional_info=additional_info
        )
        self._write_log(LogLevel.DEBUG, log_message)

    def info(
        self, message: str, additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an informational message."""
        log_message = self._format_message(
            LogLevel.INFO, message, additional_info=additional_info
        )
        self._write_log(LogLevel.INFO, log_message)

    def warning(
        self, message: str, additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a warning message."""
        log_message = self._format_message(
            LogLevel.WARNING, message, additional_info=additional_info
        )
        self._write_log(LogLevel.WARNING, log_message)

    def error(
        self,
        error: Union[Exception, str],
        additional_info: Optional[Dict[str, Any]] = None,
        exc_info: bool = True,
    ) -> None:
        """Log an error with optional traceback."""
        log_message = self._format_message(
            LogLevel.ERROR, "An error occurred", error, additional_info, exc_info
        )
        self._write_log(LogLevel.ERROR, log_message)


# Global logger instance
logger = ErrorTraceLogger(preserve_logs=True, debug_mode=False)
