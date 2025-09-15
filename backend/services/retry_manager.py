#!/usr/bin/env python3
"""""""""
Advanced Retry Manager with Circuit Breaker Patterns
""""""
This module provides sophisticated retry mechanisms with exponential backoff,
circuit breaker patterns, and intelligent failure handling to ensure 100%
model generation reliability.
"""

Advanced Retry Manager with Circuit Breaker Patterns



""""""


Features:



- Exponential backoff with jitter
- Circuit breaker pattern implementation
- Bulkhead isolation
- Adaptive retry strategies
- Failure classification and handling
- Performance monitoring and metrics
- Automatic recovery mechanisms

"""

import asyncio
import json
import logging
import os
import random
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI = "fibonacci"
    ADAPTIVE = "adaptive"


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class FailureType(Enum):
    """Types of failures"""

    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNKNOWN = "unknown"


class RetryDecision(Enum):
    """Retry decision outcomes"""

    RETRY = "retry"
    FAIL_FAST = "fail_fast"
    CIRCUIT_OPEN = "circuit_open"
    MAX_ATTEMPTS_REACHED = "max_attempts_reached"


@dataclass
class RetryConfig:
    """
Configuration for retry behavior


    max_attempts: int = 5
    base_delay_ms: int = 1000
    max_delay_ms: int = 60000
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    timeout_ms: int = 30000
    retryable_exceptions: List[type] = field(default_factory=list)
    non_retryable_exceptions: List[type] = field(default_factory=list)
    retryable_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    circuit_breaker_enabled: bool = True
    bulkhead_enabled: bool = True
   
""""""

    adaptive_enabled: bool = True
   

    
   
"""
@dataclass
class CircuitBreakerConfig:
    """
Configuration for circuit breaker


    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_ms: int = 60000
    half_open_max_calls: int = 3
    minimum_throughput: int = 10
    error_percentage_threshold: float = 50.0
   
""""""

    sliding_window_size: int = 100
   

    
   
"""
@dataclass
class RetryAttempt:
    """
Information about a retry attempt


    attempt_number: int
    delay_ms: int
    timestamp: datetime
    error: Optional[Exception] = None
    failure_type: Optional[FailureType] = None
    response_time_ms: Optional[int] = None
   
""""""

    metadata: Dict[str, Any] = field(default_factory=dict)
   

    
   
"""
@dataclass
class RetryResult:
    """
Result of retry operation


    success: bool
    result: Any = None
    error: Optional[Exception] = None
    total_attempts: int = 0
    total_time_ms: int = 0
    attempts: List[RetryAttempt] = field(default_factory=list)
    decision: Optional[RetryDecision] = None
    circuit_breaker_triggered: bool = False
   
""""""

    metadata: Dict[str, Any] = field(default_factory=dict)
   

    
   
"""
class FailureClassifier:
    """
Classifies failures for appropriate retry handling


    @staticmethod
    def classify_exception(exception: Exception) -> FailureType:
        
"""Classify exception into failure type"""

        exception_name = type(exception).__name__.lower()
       

        
       
"""
        exception_message = str(exception).lower()
       """"""

        

       """

        exception_message = str(exception).lower()
       

        
       
"""
        if "timeout" in exception_name or "timeout" in exception_message:
            return FailureType.TIMEOUT
        elif "connection" in exception_name or "connection" in exception_message:
            return FailureType.CONNECTION_ERROR
        elif "rate" in exception_message or "429" in exception_message:
            return FailureType.RATE_LIMIT
        elif (
            "500" in exception_message
            or "502" in exception_message
            or "503" in exception_message
            or "504" in exception_message
#         ):
            return FailureType.SERVER_ERROR
        elif (
            "400" in exception_message
            or "401" in exception_message
            or "403" in exception_message
            or "404" in exception_message
#         ):
            return FailureType.CLIENT_ERROR
        elif "validation" in exception_message or "invalid" in exception_message:
            return FailureType.VALIDATION_ERROR
        elif "resource" in exception_message or "exhausted" in exception_message:
            return FailureType.RESOURCE_EXHAUSTED
        else:
            return FailureType.UNKNOWN

    @staticmethod
    def is_retryable(failure_type: FailureType, config: RetryConfig) -> bool:
        """
Determine if failure type is retryable

       
""""""

        # Non - retryable failure types
       

        
       
""""""

        
       

        non_retryable = {FailureType.CLIENT_ERROR, FailureType.VALIDATION_ERROR}
       
""""""

       

        
       
"""
        # Non - retryable failure types
       """

        
       

        if failure_type in non_retryable:
            return False

        # All other types are generally retryable
        return True

    @staticmethod
    def get_retry_delay_multiplier(failure_type: FailureType) -> float:
        
"""Get delay multiplier based on failure type"""

        multipliers = {
            FailureType.RATE_LIMIT: 2.0,  # Longer delays for rate limits
            FailureType.SERVER_ERROR: 1.5,
            FailureType.TIMEOUT: 1.2,
            FailureType.CONNECTION_ERROR: 1.0,
            FailureType.RESOURCE_EXHAUSTED: 2.5,
            FailureType.UNKNOWN: 1.0,
         }
        

        return multipliers.get(failure_type, 1.0)
        
""""""

        
       

        
"""

        return multipliers.get(failure_type, 1.0)

        """"""
class CircuitBreaker:
    """Advanced circuit breaker implementation"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.call_history = []  # Sliding window of recent calls
        self.lock = threading.RLock()

        logger.info(f"Circuit breaker '{name}' initialized")

    def can_execute(self) -> bool:
        """
Check if execution is allowed

        
"""
        with self.lock:
        """"""
            if self.state == CircuitState.CLOSED:
        """

        with self.lock:
        

       
""""""
                return True
            elif self.state == CircuitState.OPEN:
                # Check if timeout period has passed
                if (
                    self.last_failure_time
                    and (datetime.now() - self.last_failure_time).total_seconds() * 1000
                    > self.config.timeout_ms
#                 ):
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return self.half_open_calls < self.config.half_open_max_calls

            return False

    def record_success(self):
        """
Record successful execution

        with self.lock:
           
""""""

            self._add_to_history(True)
           

            
           
"""
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed after recovery")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset failure count on success

    def record_failure(self):
        """
Record failed execution

        with self.lock:
            self._add_to_history(False)
            self.failure_count += 1
           
""""""

            self.last_failure_time = datetime.now()
           

            
           
"""
            if self.state == CircuitState.HALF_OPEN:
                # Failure during half - open, go back to open
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit breaker '{self.name}' opened after half - open failure")
            elif self.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self._should_open_circuit():
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker '{self.name}' opened due to failures")

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1

    def _add_to_history(self, success: bool):
        """Add call result to sliding window history"""
        self.call_history.append({"success": success, "timestamp": datetime.now()})

        # Maintain sliding window size
        if len(self.call_history) > self.config.sliding_window_size:
            self.call_history.pop(0)

    def _should_open_circuit(self) -> bool:
        """
Determine if circuit should be opened

       
""""""

        # Simple threshold - based decision
       

        
       
"""
        if self.failure_count >= self.config.failure_threshold:
       """

        
       

        # Simple threshold - based decision
       
""""""

            

            return True
            
""""""

            
           

        # Percentage - based decision with minimum throughput
            
"""
            return True
            """"""
        if len(self.call_history) >= self.config.minimum_throughput:
            failures = sum(1 for call in self.call_history if not call["success"])
            failure_percentage = (failures / len(self.call_history)) * 100

            if failure_percentage >= self.config.error_percentage_threshold:
                return True

        return False

    def get_state_info(self) -> Dict[str, Any]:
        """
Get current state information

        
"""
        with self.lock:
        """

            recent_calls = len(self.call_history)
        

        with self.lock:
        
"""
            recent_failures = sum(1 for call in self.call_history if not call["success"])
            failure_rate = (recent_failures / recent_calls * 100) if recent_calls > 0 else 0

            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "half_open_calls": self.half_open_calls,
                "recent_calls": recent_calls,
                "recent_failures": recent_failures,
                "failure_rate_percent": failure_rate,
                "last_failure_time": (
                    self.last_failure_time.isoformat() if self.last_failure_time else None
                 ),
             }


class AdaptiveRetryCalculator:
    """
Calculates adaptive retry delays based on historical performance


    def __init__(self):
        self.success_rates = {}  # service_name -> success_rate
        self.avg_response_times = {}  # service_name -> avg_response_time
        self.lock = threading.Lock()

    def update_metrics(self, service_name: str, success: bool, response_time_ms: int):
        
"""Update metrics for adaptive calculation"""

        

        with self.lock:
        
""""""

        
       

            if service_name not in self.success_rates:
                self.success_rates[service_name] = []
               
""""""

                self.avg_response_times[service_name] = []
               

                
               
""""""

        with self.lock:
        

       
""""""

            # Keep last 100 results for moving average
            self.success_rates[service_name].append(1 if success else 0)
            self.avg_response_times[service_name].append(response_time_ms)

            if len(self.success_rates[service_name]) > 100:
                self.success_rates[service_name].pop(0)
                self.avg_response_times[service_name].pop(0)

    def calculate_adaptive_delay(
        self, service_name: str, base_delay_ms: int, attempt_number: int
#     ) -> int:
        
Calculate adaptive delay based on service performance
""""""

        with self.lock:
        

       
""""""

            if service_name not in self.success_rates:
        

        with self.lock:
        
""""""

        
       

                
"""
                return base_delay_ms
                """"""
                """


                return base_delay_ms

                

            success_rate = sum(self.success_rates[service_name]) / len(
                self.success_rates[service_name]
             )
            avg_response_time = sum(self.avg_response_times[service_name]) / len(
                self.avg_response_times[service_name]
             )

            # Adjust delay based on success rate and response time
            success_multiplier = 2.0 - success_rate  # Lower success rate = higher multiplier
            response_time_multiplier = min(avg_response_time / 1000, 3.0)  # Cap at 3x

            adaptive_multiplier = success_multiplier * response_time_multiplier
            adaptive_delay = int(base_delay_ms * adaptive_multiplier)

            return min(adaptive_delay, 300000)  # Cap at 5 minutes


class BulkheadIsolation:
    """
    Implements bulkhead pattern for resource isolation
    """
    
    def __init__(self, max_concurrent_calls: int = 10):
        self.max_concurrent_calls = max_concurrent_calls
        self.current_calls = 0
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.lock = threading.Lock()

    async def acquire(self) -> bool:
        """
        Acquire a slot in the bulkhead
        """
        try:
            await asyncio.wait_for(self.semaphore.acquire(), timeout=1.0)
            with self.lock:
               """

                
               

                self.current_calls += 1
               
""""""

            return True
        except asyncio.TimeoutError:
               

                
               
"""
                self.current_calls += 1
               """"""
            return False
            """"""
            """


            return False

            

           
""""""

    def release(self):
        """
        Release a slot in the bulkhead
        """"""

        with self.lock:
        

       
""""""

            if self.current_calls > 0:
                self.current_calls -= 1
       

        
       
"""
        self.semaphore.release()
       """"""
        with self.lock:
        """"""
    def get_utilization(self) -> float:
        """
Get current utilization percentage

        
"""
        with self.lock:
        """"""
            """

            return (self.current_calls / self.max_concurrent_calls) * 100
            

        
"""
        with self.lock:
        """"""
class AdvancedRetryManager:
    """Advanced retry manager with circuit breakers and adaptive strategies"""

    def __init__(self, db_path: str = "data/retry_manager.db"):
        self.db_path = db_path
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, BulkheadIsolation] = {}
        self.adaptive_calculator = AdaptiveRetryCalculator()
        self.failure_classifier = FailureClassifier()
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.lock = threading.RLock()

        # Initialize database
        self._init_database()

        logger.info("AdvancedRetryManager initialized")

    def _init_database(self):
        """
Initialize retry tracking database

       
""""""

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
       

        
       
""""""


        with sqlite3.connect(self.db_path) as conn:

        

       
""""""

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
       

        
       
""""""

            
           

            cursor = conn.cursor()
           
""""""

            # Retry attempts table
            cursor.execute(
               

                
               
"""
                CREATE TABLE IF NOT EXISTS retry_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        operation_id TEXT NOT NULL,
                        attempt_number INTEGER NOT NULL,
                        success BOOLEAN NOT NULL,
                        failure_type TEXT,
                        delay_ms INTEGER,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                 )
            """"""

            

             
            
"""
             )
            """"""
            
           """

            cursor = conn.cursor()
           

            
           
"""
            # Circuit breaker events
            cursor.execute(
               """

                
               

                CREATE TABLE IF NOT EXISTS circuit_breaker_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        circuit_name TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        previous_state TEXT,
                        new_state TEXT,
                        failure_count INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )
            
""""""

            

             
            
"""
             )
            """

             
            

            # Performance metrics
            cursor.execute(
               
""""""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        success_rate REAL,
                        avg_response_time_ms REAL,
                        total_calls INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )
            """"""

            

             
            
"""
             )
            """"""
             
            """

             )
            

             
            
""""""


            

           

            conn.commit()
           
""""""

    def get_or_create_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig = None
#     ) -> CircuitBreaker:
        
Get or create circuit breaker for service
""""""

        with self.lock:
        

       
""""""

            if name not in self.circuit_breakers:
        

        with self.lock:
        
""""""

        
       

                if config is None:
                    config = CircuitBreakerConfig()
                self.circuit_breakers[name] = CircuitBreaker(name, config)
            
"""
            return self.circuit_breakers[name]
            """"""
            """


            return self.circuit_breakers[name]

            

           
""""""

    def get_or_create_bulkhead(self, name: str, max_concurrent: int = 10) -> BulkheadIsolation:
        
Get or create bulkhead for service
""""""

        with self.lock:
        

       
""""""

            if name not in self.bulkheads:
                self.bulkheads[name] = BulkheadIsolation(max_concurrent)
        

        with self.lock:
        
""""""

        
       

            
"""
            return self.bulkheads[name]
            """"""
    async def execute_with_retry(
        self,
        func: Callable,
        service_name: str,
        operation_id: str = None,
        config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
        *args,
        **kwargs,
#     ) -> RetryResult:
       """"""
        
       """

        Execute function with advanced retry logic
       

        
       
""""""

            return self.bulkheads[name]
            

           
""""""

        Args:
            func: Function to execute
            service_name: Name of the service (for circuit breaker isolation)
            operation_id: Unique operation identifier
            config: Retry configuration
            circuit_config: Circuit breaker configuration
            *args, **kwargs: Arguments to pass to function

        Returns:
            RetryResult with execution details
       

        
       
"""
        if config is None:
           """

            
           

            config = RetryConfig()
           
""""""

           


            

           
"""
            config = RetryConfig()
           """"""
        if operation_id is None:
            operation_id = f"{service_name}_{int(time.time() * 1000)}"

        # Get circuit breaker and bulkhead
        circuit_breaker = self.get_or_create_circuit_breaker(service_name, circuit_config)
        bulkhead = self.get_or_create_bulkhead(service_name, config.max_attempts * 2)

        start_time = time.time()
        attempts = []
        last_error = None

        for attempt in range(1, config.max_attempts + 1):
            # Check circuit breaker
            if config.circuit_breaker_enabled and not circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker open for {service_name}, failing fast")
                return RetryResult(
                    success=False,
                    error=Exception(f"Circuit breaker open for {service_name}"),
                    total_attempts=attempt - 1,
                    total_time_ms=int((time.time() - start_time) * 1000),
                    attempts=attempts,
                    decision=RetryDecision.CIRCUIT_OPEN,
                    circuit_breaker_triggered=True,
                 )

            # Acquire bulkhead slot
            if config.bulkhead_enabled:
                if not await bulkhead.acquire():
                    logger.warning(f"Bulkhead full for {service_name}, failing fast")
                    return RetryResult(
                        success=False,
                        error=Exception(f"Bulkhead capacity exceeded for {service_name}"),
                        total_attempts=attempt - 1,
                        total_time_ms=int((time.time() - start_time) * 1000),
                        attempts=attempts,
                        decision=RetryDecision.FAIL_FAST,
                     )

            attempt_start = time.time()

            try:
                # Execute function with timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=config.timeout_ms / 1000
                     )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.executor, lambda: func(*args, **kwargs)
                     )

                response_time_ms = int((time.time() - attempt_start) * 1000)

                # Success!
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay_ms=0,
                    timestamp=datetime.now(),
                    response_time_ms=response_time_ms,
                 )
                attempts.append(attempt_info)

                # Update circuit breaker and metrics
                if config.circuit_breaker_enabled:
                    circuit_breaker.record_success()

                if config.adaptive_enabled:
                    self.adaptive_calculator.update_metrics(service_name, True, response_time_ms)

                # Log successful attempt
                self._log_attempt(service_name, operation_id, attempt_info, True)

                # Release bulkhead
                if config.bulkhead_enabled:
                    bulkhead.release()

                return RetryResult(
                    success=True,
                    result=result,
                    total_attempts=attempt,
                    total_time_ms=int((time.time() - start_time) * 1000),
                    attempts=attempts,
                 )

            except Exception as e:
                response_time_ms = int((time.time() - attempt_start) * 1000)
                last_error = e

                # Classify failure
                failure_type = self.failure_classifier.classify_exception(e)

                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay_ms=0,
                    timestamp=datetime.now(),
                    error=e,
                    failure_type=failure_type,
                    response_time_ms=response_time_ms,
                 )
                attempts.append(attempt_info)

                # Update circuit breaker and metrics
                if config.circuit_breaker_enabled:
                    circuit_breaker.record_failure()

                if config.adaptive_enabled:
                    self.adaptive_calculator.update_metrics(service_name, False, response_time_ms)

                # Log failed attempt
                self._log_attempt(service_name, operation_id, attempt_info, False)

                # Release bulkhead
                if config.bulkhead_enabled:
                    bulkhead.release()

                # Check if we should retry
                if attempt >= config.max_attempts:
                    break

                if not self.failure_classifier.is_retryable(failure_type, config):
                    logger.info(f"Non - retryable failure for {service_name}: {failure_type.value}")
                    return RetryResult(
                        success=False,
                        error=e,
                        total_attempts=attempt,
                        total_time_ms=int((time.time() - start_time) * 1000),
                        attempts=attempts,
                        decision=RetryDecision.FAIL_FAST,
                     )

                # Calculate delay for next attempt
                delay_ms = self._calculate_delay(config, attempt, failure_type, service_name)
                attempt_info.delay_ms = delay_ms

                logger.warning(
                    f"Attempt {attempt} failed for {service_name}: {e}. Retrying in {delay_ms}ms"
                 )

                # Wait before next attempt
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000)

        # All attempts failed
        return RetryResult(
            success=False,
            error=last_error,
            total_attempts=config.max_attempts,
            total_time_ms=int((time.time() - start_time) * 1000),
            attempts=attempts,
            decision=RetryDecision.MAX_ATTEMPTS_REACHED,
         )

    def _calculate_delay(
        self,
        config: RetryConfig,
        attempt: int,
        failure_type: FailureType,
        service_name: str,
#     ) -> int:
        """
Calculate delay for next retry attempt

       
""""""

        base_delay = config.base_delay_ms
       

        
       
""""""


        

       

        base_delay = config.base_delay_ms
       
""""""

        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif config.strategy == RetryStrategy.FIBONACCI:
            fib_sequence = [1, 1]
            for i in range(2, attempt + 1):
                fib_sequence.append(fib_sequence[i - 1] + fib_sequence[i - 2])
            delay = base_delay * fib_sequence[min(attempt, len(fib_sequence) - 1)]
        elif config.strategy == RetryStrategy.ADAPTIVE:
            delay = self.adaptive_calculator.calculate_adaptive_delay(
                service_name, base_delay, attempt
             )
        else:
            delay = base_delay

        # Apply failure type multiplier
        failure_multiplier = self.failure_classifier.get_retry_delay_multiplier(failure_type)
        delay = int(delay * failure_multiplier)

        # Add jitter to prevent thundering herd
        if config.jitter_factor > 0:
            jitter = delay * config.jitter_factor * (random.random() - 0.5)
            delay = int(delay + jitter)

        # Ensure delay is within bounds
        delay = max(0, min(delay, config.max_delay_ms))

        return delay

    def _log_attempt(
        self, service_name: str, operation_id: str, attempt: RetryAttempt, success: bool
#     ):
        
Log retry attempt to database
"""
        try:
            """

            with sqlite3.connect(self.db_path) as conn:
            

                cursor = conn.cursor()
                cursor.execute(
                   
""""""

                    INSERT INTO retry_attempts
                    (service_name, operation_id, attempt_number, success,
#                         failure_type, delay_ms, response_time_ms, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                
,
"""
                    (
                        service_name,
                        operation_id,
                        attempt.attempt_number,
                        success,
                        attempt.failure_type.value if attempt.failure_type else None,
                        attempt.delay_ms,
                        attempt.response_time_ms,
                        str(attempt.error) if attempt.error else None,
                        json.dumps(attempt.metadata),
                     ),
                 )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log retry attempt: {e}")
            """

            with sqlite3.connect(self.db_path) as conn:
            

           
""""""

    def get_service_metrics(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        
Get metrics for a service over specified time period
"""
        try:
            """

            with sqlite3.connect(self.db_path) as conn:
            

               
""""""

                cursor = conn.cursor()
               

                
               
""""""

            with sqlite3.connect(self.db_path) as conn:
            

           
""""""

                # Get attempt statistics
                cursor.execute(
                   

                    
                   
"""
                    SELECT
                        COUNT(*) as total_attempts,
                            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                            AVG(response_time_ms) as avg_response_time,
                            AVG(delay_ms) as avg_delay,
                            MAX(attempt_number) as max_attempts_per_operation
                    FROM retry_attempts
                    WHERE service_name = ?
                    AND timestamp > datetime('now', '-{} hours')
                """
.format(

                        hours
                     ),
                    (service_name,),
                
""""""

                 )
                

                 
                
"""
                stats = cursor.fetchone()

                if stats and stats[0] > 0:
                    (
                        total_attempts,
                        successful_attempts,
                        avg_response_time,
                        avg_delay,
                        max_attempts,
#                     ) = stats
                    success_rate = (successful_attempts / total_attempts) * 100
                else:
                    total_attempts = successful_attempts = 0
                    success_rate = avg_response_time = avg_delay = max_attempts = 0

                # Get circuit breaker info
                circuit_info = {}
                if service_name in self.circuit_breakers:
                    circuit_info = self.circuit_breakers[service_name].get_state_info()

                # Get bulkhead info
                bulkhead_info = {}
                if service_name in self.bulkheads:
                    bulkhead_info = {
                        "current_utilization_percent": self.bulkheads[
                            service_name
                        ].get_utilization(),
                        "max_concurrent_calls": self.bulkheads[service_name].max_concurrent_calls,
                     }

                return {
                    "service_name": service_name,
                    "time_period_hours": hours,
                    "total_attempts": total_attempts,
                    "successful_attempts": successful_attempts,
                    "success_rate_percent": success_rate,
                    "avg_response_time_ms": avg_response_time or 0,
                    "avg_retry_delay_ms": avg_delay or 0,
                    "max_attempts_per_operation": max_attempts or 0,
                    "circuit_breaker": circuit_info,
                    "bulkhead": bulkhead_info,
                 }

        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {}

    def get_system_status(self) -> Dict[str, Any]:
        """
Get overall system status

        
"""
        with self.lock:
        """

            circuit_breaker_status = {}
            for name, cb in self.circuit_breakers.items():
               

                
               
"""
                circuit_breaker_status[name] = cb.get_state_info()
               """"""
        with self.lock:
        """"""
            bulkhead_status = {}
            for name, bh in self.bulkheads.items():
                bulkhead_status[name] = {
                    "utilization_percent": bh.get_utilization(),
                    "max_concurrent": bh.max_concurrent_calls,
                 }

            return {
                "circuit_breakers": circuit_breaker_status,
                "bulkheads": bulkhead_status,
                "total_circuit_breakers": len(self.circuit_breakers),
                "open_circuit_breakers": sum(
                    1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN
                 ),
                "total_bulkheads": len(self.bulkheads),
                "high_utilization_bulkheads": sum(
                    1 for bh in self.bulkheads.values() if bh.get_utilization() > 80
                 ),
             }

    def reset_circuit_breaker(self, service_name: str):
        """
Manually reset a circuit breaker

        
"""
        with self.lock:
        """"""
            if service_name in self.circuit_breakers:
        """
        with self.lock:
        """
                cb = self.circuit_breakers[service_name]
                cb.state = CircuitState.CLOSED
                cb.failure_count = 0
                cb.success_count = 0
                logger.info(f"Circuit breaker '{service_name}' manually reset")

    def shutdown(self):
        """Shutdown retry manager"""
        logger.info("Shutting down AdvancedRetryManager...")
        self.executor.shutdown(wait=True)
        logger.info("AdvancedRetryManager shutdown complete")


# Global instance
_global_retry_manager = None


def get_retry_manager() -> AdvancedRetryManager:
    """
Get global retry manager instance

   
""""""

    global _global_retry_manager
   

    
   
"""
    if _global_retry_manager is None:
   """

    
   

    global _global_retry_manager
   
""""""

        _global_retry_manager = AdvancedRetryManager()
    

    return _global_retry_manager
    
""""""

    
   

    
"""

    return _global_retry_manager

    """"""
# Decorator for easy retry functionality


def with_retry(
    service_name: str,
    config: RetryConfig = None,
    circuit_config: CircuitBreakerConfig = None,
# ):
    """Decorator to add retry functionality to functions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_manager = get_retry_manager()
            result = await retry_manager.execute_with_retry(
                func,
                service_name,
                config=config,
                circuit_config=circuit_config,
                *args,
                **kwargs,
             )

            if result.success:
                return result.result
            else:
                raise result.error

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage

    async def main():
        retry_manager = AdvancedRetryManager()

        # Example function that might fail

        async def unreliable_function(fail_probability: float = 0.7):
            if random.random() < fail_probability:
                raise Exception("Random failure occurred")
            return "Success!"

        # Test retry with different configurations
        config = RetryConfig(
            max_attempts=5,
            base_delay_ms=1000,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            circuit_breaker_enabled=True,
         )

        # Execute with retry
        result = await retry_manager.execute_with_retry(
            unreliable_function, "test_service", config=config, fail_probability=0.3
         )

        print(f"Result: {result.success}")
        print(f"Total attempts: {result.total_attempts}")
        print(f"Total time: {result.total_time_ms}ms")

        # Get service metrics
        metrics = retry_manager.get_service_metrics("test_service")
        print(f"Service metrics: {json.dumps(metrics, indent = 2)}")

        # Get system status
        status = retry_manager.get_system_status()
        print(f"System status: {json.dumps(status, indent = 2)}")

        retry_manager.shutdown()

    asyncio.run(main())