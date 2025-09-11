#!/usr/bin/env python3
"""
TRAE.AI Centralized Logging System

Production-ready logging configuration with automatic log rotation,
structured formatting, and multiple output handlers. Designed for
high-performance applications with comprehensive audit trails.

Features:
- Automatic log rotation (5 files, 10MB each)
- Structured JSON and text formatting
- Multiple log levels and handlers
- Performance monitoring
- Security-aware logging (no sensitive data)
- Thread-safe operations

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import logging
import logging.handlers
import os
import re
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SecurityFilter(logging.Filter):
    """
    Security filter to prevent logging of sensitive information.

    This filter scans log messages for common patterns that might
    contain sensitive data and either redacts or blocks them.
    """

    SENSITIVE_PATTERNS = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "key",
        "token",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "cred",
        "private",
        "confidential",
        "sensitive",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to prevent sensitive data exposure.

        Args:
            record (LogRecord): The log record to filter

        Returns:
            bool: True if record should be logged, False otherwise
        """
        message = str(record.getMessage()).lower()

        # Check for sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Redact the message instead of blocking it
                record.msg = self._redact_sensitive_data(str(record.msg))
                break

        return True

    def _redact_sensitive_data(self, message: str) -> str:
        """
        Redact sensitive data from log messages.

        Args:
            message (str): Original message

        Returns:
            str: Message with sensitive data redacted
        """
        # Simple redaction - replace potential sensitive values
        import re

        # Redact key-value pairs that might contain sensitive data
        patterns = [
            r"(password|passwd|pwd|secret|key|token|api_key|apikey)\s*[=:]\s*[^\s]+",
            r"(auth|credential|cred)\s*[=:]\s*[^\s]+",
        ]

        redacted_message = message
        for pattern in patterns:
            redacted_message = re.sub(
                pattern, r"\1=***REDACTED***", redacted_message, flags=re.IGNORECASE
            )

        return redacted_message


class RegexNoiseFilter(logging.Filter):
    """
    Regex-based noise filter to reduce chatty log output.

    This filter uses configurable regex patterns to drop or reduce
    repetitive, verbose, or noisy log messages that clutter the logs
    without providing significant value.
    """

    # Default noise patterns - common chatty log messages
    DEFAULT_DROP_PATTERNS = [
        r".*heartbeat.*",  # Heartbeat messages
        r".*ping.*pong.*",  # Ping/pong messages
        r".*health.*check.*ok.*",  # Health check success messages
        r".*connection.*established.*",  # Repeated connection messages
        r".*polling.*",  # Polling messages
        r".*keepalive.*",  # Keepalive messages
        r".*status.*200.*GET.*",  # Successful GET requests
        r".*websocket.*frame.*received.*",  # WebSocket frame messages
        r".*socket\.io.*transport.*",  # Socket.IO transport messages
        r".*received.*ack.*",  # ACK messages
    ]

    # Default reduction patterns - reduce frequency but don't drop entirely
    DEFAULT_REDUCE_PATTERNS = [
        r".*database.*query.*executed.*",  # DB query messages
        r".*cache.*hit.*",  # Cache hit messages
        r".*request.*processed.*",  # Request processing messages
    ]

    def __init__(
        self,
        drop_patterns: List[str] = None,
        reduce_patterns: List[str] = None,
        reduce_frequency: int = 10,
    ):
        """
        Initialize the regex noise filter.

        Args:
            drop_patterns (List[str]): Regex patterns for messages to drop entirely
            reduce_patterns (List[str]): Regex patterns for messages to reduce frequency
            reduce_frequency (int): Show 1 out of every N messages for reduce patterns
        """
        super().__init__()

        self.drop_patterns = drop_patterns or self.DEFAULT_DROP_PATTERNS
        self.reduce_patterns = reduce_patterns or self.DEFAULT_REDUCE_PATTERNS
        self.reduce_frequency = reduce_frequency

        # Compile regex patterns for performance
        self.compiled_drop_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.drop_patterns
        ]
        self.compiled_reduce_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.reduce_patterns
        ]

        # Counter for reduce patterns
        self.reduce_counters = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on regex patterns.

        Args:
            record (LogRecord): The log record to filter

        Returns:
            bool: True if record should be logged, False otherwise
        """
        message = str(record.getMessage()).lower()

        # Check drop patterns - completely block these messages
        for pattern in self.compiled_drop_patterns:
            if pattern.search(message):
                return False

        # Check reduce patterns - reduce frequency of these messages
        for i, pattern in enumerate(self.compiled_reduce_patterns):
            if pattern.search(message):
                pattern_key = f"reduce_{i}"

                # Initialize counter if not exists
                if pattern_key not in self.reduce_counters:
                    self.reduce_counters[pattern_key] = 0

                self.reduce_counters[pattern_key] += 1

                # Only allow every Nth message through
                if self.reduce_counters[pattern_key] % self.reduce_frequency != 0:
                    return False

        return True

    def add_drop_pattern(self, pattern: str) -> None:
        """
        Add a new drop pattern at runtime.

        Args:
            pattern (str): Regex pattern to add
        """
        self.drop_patterns.append(pattern)
        self.compiled_drop_patterns.append(re.compile(pattern, re.IGNORECASE))

    def add_reduce_pattern(self, pattern: str) -> None:
        """
        Add a new reduce pattern at runtime.

        Args:
            pattern (str): Regex pattern to add
        """
        self.reduce_patterns.append(pattern)
        self.compiled_reduce_patterns.append(re.compile(pattern, re.IGNORECASE))

    def clear_patterns(self) -> None:
        """
        Clear all patterns and reset counters.
        """
        self.drop_patterns.clear()
        self.reduce_patterns.clear()
        self.compiled_drop_patterns.clear()
        self.compiled_reduce_patterns.clear()
        self.reduce_counters.clear()


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats log records as JSON objects with consistent structure
    for easy parsing by log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record (LogRecord): The log record to format

        Returns:
            str: JSON-formatted log message
        """
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.

    Adds color coding to different log levels for better readability
    in terminal environments.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record (LogRecord): The log record to format

        Returns:
            str: Colored log message
        """
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format the message
        formatted = super().format(record)

        # Add color if terminal supports it
        if sys.stderr.isatty():
            return f"{color}{formatted}{reset}"
        else:
            return formatted


class TraeLogger:
    """
    Centralized logging system for TRAE.AI.

    Provides a standardized logging interface with automatic rotation,
    multiple output formats, and security-aware filtering.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_dir: str = "data/logs",
        log_level: Union[str, int] = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_json: bool = True,
        enable_security_filter: bool = True,
        enable_noise_filter: bool = False,
        noise_drop_patterns: List[str] = None,
        noise_reduce_patterns: List[str] = None,
        noise_reduce_frequency: int = 10,
    ):
        """
        Initialize the centralized logger.

        Args:
            log_dir (str): Directory for log files
            log_level (str|int): Minimum log level
            max_bytes (int): Maximum size per log file (10MB)
            backup_count (int): Number of backup files to keep (5)
            enable_console (bool): Enable console output
            enable_json (bool): Enable JSON log file
            enable_security_filter (bool): Enable security filtering
            enable_noise_filter (bool): Enable regex-based noise filtering
            noise_drop_patterns (List[str]): Custom patterns to drop entirely
            noise_reduce_patterns (List[str]): Custom patterns to reduce frequency
            noise_reduce_frequency (int): Show 1 out of every N messages for reduce patterns
        """
        # Prevent re-initialization
        if hasattr(self, "_initialized"):
            return

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_level = self._parse_log_level(log_level)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_json = enable_json
        self.enable_security_filter = enable_security_filter
        self.enable_noise_filter = enable_noise_filter
        self.noise_drop_patterns = noise_drop_patterns
        self.noise_reduce_patterns = noise_reduce_patterns
        self.noise_reduce_frequency = noise_reduce_frequency

        # Initialize loggers
        self._setup_root_logger()
        self._setup_application_logger()

        self._initialized = True

    def _parse_log_level(self, level: Union[str, int]) -> int:
        """
        Parse log level from string or int.

        Args:
            level (str|int): Log level

        Returns:
            int: Numeric log level
        """
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level

    def _setup_root_logger(self) -> None:
        """
        Setup the root logger configuration.
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add security filter if enabled
        if self.enable_security_filter:
            security_filter = SecurityFilter()
            root_logger.addFilter(security_filter)

        # Add noise filter if enabled
        if self.enable_noise_filter:
            noise_filter = RegexNoiseFilter(
                drop_patterns=self.noise_drop_patterns,
                reduce_patterns=self.noise_reduce_patterns,
                reduce_frequency=self.noise_reduce_frequency,
            )
            root_logger.addFilter(noise_filter)

    def _setup_application_logger(self) -> None:
        """
        Setup application-specific loggers.
        """
        # Main application logger
        self.app_logger = logging.getLogger("trae_ai")
        self.app_logger.setLevel(self.log_level)

        # Text log file handler with rotation
        text_log_file = self.log_dir / "trae_ai.log"
        text_handler = logging.handlers.RotatingFileHandler(
            text_log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        text_handler.setLevel(self.log_level)

        # Text formatter
        text_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        text_handler.setFormatter(text_formatter)
        self.app_logger.addHandler(text_handler)

        # JSON log file handler (if enabled)
        if self.enable_json:
            json_log_file = self.log_dir / "trae_ai.json.log"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            json_handler.setLevel(self.log_level)
            json_handler.setFormatter(JSONFormatter())
            self.app_logger.addHandler(json_handler)

        # Console handler (if enabled)
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(
                ColoredFormatter(
                    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            self.app_logger.addHandler(console_handler)

        # Error log file (separate file for errors and above)
        error_log_file = self.log_dir / "trae_ai_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(text_formatter)
        self.app_logger.addHandler(error_handler)

    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name (str, optional): Logger name. If None, returns main app logger

        Returns:
            logging.Logger: Configured logger instance
        """
        if name is None:
            return self.app_logger

        # Create child logger
        logger = logging.getLogger(f"trae_ai.{name}")
        logger.setLevel(self.log_level)

        return logger

    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """
        Log performance metrics.

        Args:
            operation (str): Operation name
            duration (float): Duration in seconds
            **kwargs: Additional metrics
        """
        perf_logger = self.get_logger("performance")

        metrics = {
            "operation": operation,
            "duration_seconds": duration,
            "duration_ms": duration * 1000,
            **kwargs,
        }

        # Add extra data for JSON formatter
        extra = {"extra_data": metrics}

        perf_logger.info(
            f"Performance: {operation} completed in {duration:.3f}s", extra=extra
        )

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log security-related events.

        Args:
            event_type (str): Type of security event
            details (Dict): Event details (will be sanitized)
        """
        security_logger = self.get_logger("security")

        # Sanitize details to remove sensitive information
        sanitized_details = self._sanitize_security_details(details)

        extra = {"extra_data": {"event_type": event_type, **sanitized_details}}

        security_logger.warning(f"Security Event: {event_type}", extra=extra)

    def _sanitize_security_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize security event details to remove sensitive data.

        Args:
            details (Dict): Original details

        Returns:
            Dict: Sanitized details
        """
        sanitized = {}

        for key, value in details.items():
            key_lower = key.lower()

            # Check if key might contain sensitive data
            if any(
                pattern in key_lower for pattern in SecurityFilter.SENSITIVE_PATTERNS
            ):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized

    def configure_external_logger(
        self, logger_name: str, level: Union[str, int] = None
    ) -> None:
        """
        Configure external library loggers.

        Args:
            logger_name (str): Name of the external logger
            level (str|int, optional): Log level for the external logger
        """
        external_logger = logging.getLogger(logger_name)

        if level is not None:
            external_logger.setLevel(self._parse_log_level(level))
        else:
            # Set external loggers to WARNING by default to reduce noise
            external_logger.setLevel(logging.WARNING)

    def configure_noise_filter(
        self,
        drop_patterns: List[str] = None,
        reduce_patterns: List[str] = None,
        reduce_frequency: int = None,
    ) -> None:
        """
        Configure the noise filter at runtime.

        Args:
            drop_patterns: List of regex patterns for messages to drop completely
            reduce_patterns: List of regex patterns for messages to reduce frequency
            reduce_frequency: How often to allow reduced messages (1 in N)
        """
        if not self.enable_noise_filter:
            return

        # Find the noise filter in the root logger
        root_logger = logging.getLogger()
        noise_filter = None

        for filter_obj in root_logger.filters:
            if isinstance(filter_obj, RegexNoiseFilter):
                noise_filter = filter_obj
                break

        if noise_filter:
            if drop_patterns is not None:
                noise_filter.clear_patterns()
                for pattern in drop_patterns:
                    noise_filter.add_drop_pattern(pattern)

            if reduce_patterns is not None:
                for pattern in reduce_patterns:
                    noise_filter.add_reduce_pattern(pattern)

            if reduce_frequency is not None:
                noise_filter.reduce_frequency = reduce_frequency

    def shutdown(self) -> None:
        """
        Shutdown the logging system gracefully.
        """
        logging.shutdown()


# Global logger instance
_global_logger = None


def setup_logging(
    log_dir: str = "data/logs", log_level: Union[str, int] = logging.INFO, **kwargs
) -> TraeLogger:
    """
    Setup the global logging system.

    Args:
        log_dir (str): Directory for log files
        log_level (str|int): Minimum log level
        **kwargs: Additional configuration options

    Returns:
        TraeLogger: Configured logger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = TraeLogger(log_dir=log_dir, log_level=log_level, **kwargs)

        # Configure common external loggers
        _global_logger.configure_external_logger("urllib3", logging.WARNING)
        _global_logger.configure_external_logger("requests", logging.WARNING)
        _global_logger.configure_external_logger("cryptography", logging.WARNING)

    return _global_logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance from the global logging system.

    Args:
        name (str, optional): Logger name

    Returns:
        logging.Logger: Configured logger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = setup_logging()

    return _global_logger.get_logger(name)


def setup_logger(
    name: str = None,
    log_dir: str = "data/logs",
    log_level: Union[str, int] = logging.INFO,
    **kwargs,
) -> logging.Logger:
    """
    Setup and return a logger instance (backward compatibility function).

    This function provides backward compatibility for scripts that expect
    a setup_logger function. It initializes the global logging system
    and returns a logger instance.

    Args:
        name (str, optional): Logger name
        log_dir (str): Directory for log files
        log_level (str|int): Minimum log level
        **kwargs: Additional configuration options

    Returns:
        logging.Logger: Configured logger instance
    """
    # Initialize the global logging system
    setup_logging(log_dir=log_dir, log_level=log_level, **kwargs)

    # Return the requested logger
    return get_logger(name)


# Context manager for performance logging
class PerformanceTimer:
    """
    Context manager for automatic performance logging.

    Usage:
        with PerformanceTimer('database_query'):
            # Your code here
            pass
    """

    def __init__(self, operation: str, logger_name: str = None, **kwargs):
        self.operation = operation
        self.logger_name = logger_name
        self.kwargs = kwargs
        self.start_time = None
        self.elapsed_time = 0

    def __enter__(self):
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        self.elapsed_time = time.time() - self.start_time

        global _global_logger
        if _global_logger is None:
            _global_logger = setup_logging()

        _global_logger.log_performance(self.operation, self.elapsed_time, **self.kwargs)


if __name__ == "__main__":
    # Example usage and testing
    import time

    # Setup logging
    logger_system = setup_logging(log_level="DEBUG")

    # Get loggers
    main_logger = get_logger()
    db_logger = get_logger("database")
    api_logger = get_logger("api")

    # Test different log levels
    main_logger.debug("Debug message - system initialization")
    main_logger.info("Info message - application started")
    main_logger.warning("Warning message - deprecated feature used")
    main_logger.error("Error message - failed to connect to service")

    # Test structured logging
    db_logger.info(
        "Database query executed",
        extra={
            "extra_data": {
                "query_type": "SELECT",
                "table": "users",
                "duration_ms": 45.2,
            }
        },
    )

    # Test performance logging
    with PerformanceTimer("test_operation", user_id=123, operation_type="test"):
        time.sleep(0.1)  # Simulate work

    # Test security logging
    logger_system.log_security_event(
        "authentication_failure",
        {
            "username": "test_user",
            "ip_address": "192.168.1.100",
            "password": "secret123",  # This will be redacted
            "timestamp": datetime.now().isoformat(),
        },
    )

    # Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        main_logger.exception("Exception occurred during testing")

    print("\nLogging test completed. Check the logs in data/logs/ directory.")
    print("Files created:")
    print("- trae_ai.log (text format)")
    print("- trae_ai.json.log (JSON format)")
    print("- trae_ai_errors.log (errors only)")
