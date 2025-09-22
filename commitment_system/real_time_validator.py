"""
Real-Time Commitment Validator
Checks every action against the behavioral contract in real-time.
"""

import json
import threading
import time
import queue
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import inspect
import functools

from .memory_store import memory_store
from .behavioral_contract import behavioral_contract
from .compliance_checker import compliance_checker
from .audit_trail import audit_trail, AuditEventType, ComplianceStatus
from .enforcement_engine import enforcement_engine, EnforcementResult

class ValidationMode(Enum):
    """Validation modes for different scenarios"""
    STRICT = "strict"          # Block all violations
    PERMISSIVE = "permissive"  # Warn but allow
    LEARNING = "learning"      # Log only, learn patterns
    DISABLED = "disabled"      # No validation

class ActionCategory(Enum):
    """Categories of actions for validation"""
    TOOL_CALL = "tool_call"
    USER_RESPONSE = "user_response"
    SYSTEM_ACTION = "system_action"
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    DATA_ACCESS = "data_access"

@dataclass
class ValidationRequest:
    """Request for real-time validation"""
    request_id: str
    action_category: ActionCategory
    action_name: str
    action_parameters: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: str
    priority: int = 5  # 1-10, higher = more urgent
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class ValidationResponse:
    """Response from real-time validation"""
    request_id: str
    allowed: bool
    confidence: float  # 0.0-1.0
    violations: List[str]
    warnings: List[str]
    enforcement_result: Optional[EnforcementResult]
    processing_time_ms: float
    validation_mode: ValidationMode
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

class ValidationQueue:
    """High-performance queue for validation requests"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = queue.PriorityQueue(maxsize=max_size)
        self.processing = False
        self.processed_count = 0
        self.dropped_count = 0
    
    def add_request(self, request: ValidationRequest) -> bool:
        """Add a validation request to the queue"""
        try:
            # Use negative priority for correct ordering (higher priority first)
            self.queue.put((-request.priority, time.time(), request), block=False)
            return True
        except queue.Full:
            self.dropped_count += 1
            return False
    
    def get_request(self, timeout: float = 1.0) -> Optional[ValidationRequest]:
        """Get the next validation request"""
        try:
            _, _, request = self.queue.get(timeout=timeout)
            self.processed_count += 1
            return request
        except queue.Empty:
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            "queue_size": self.queue.qsize(),
            "processed_count": self.processed_count,
            "dropped_count": self.dropped_count
        }

class ActionDecorator:
    """Decorator for automatic action validation"""
    
    def __init__(self, validator: 'RealTimeValidator'):
        self.validator = validator
    
    def __call__(self, action_category: ActionCategory = ActionCategory.SYSTEM_ACTION,
                 validate_params: bool = True, validate_result: bool = False):
        """
        Decorator that automatically validates function calls.
        
        Args:
            action_category: Category of the action
            validate_params: Whether to validate input parameters
            validate_result: Whether to validate the result
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.validator.active:
                    return func(*args, **kwargs)
                
                # Prepare validation request
                action_name = func.__name__
                action_parameters = {
                    'args': str(args)[:500],  # Truncate for performance
                    'kwargs': {k: str(v)[:200] for k, v in kwargs.items()}
                }
                
                # Get function context
                context = {
                    'module': func.__module__,
                    'function': action_name,
                    'caller': self._get_caller_info()
                }
                
                # Validate the action
                validation_response = self.validator.validate_action_sync(
                    action_category=action_category,
                    action_name=action_name,
                    action_parameters=action_parameters,
                    context=context
                )
                
                # Handle validation result
                if not validation_response.allowed:
                    raise PermissionError(
                        f"Action '{action_name}' blocked by real-time validator: "
                        f"{', '.join(validation_response.violations)}"
                    )
                
                # Execute the function
                try:
                    result = func(*args, **kwargs)
                    
                    # Validate result if requested
                    if validate_result:
                        self.validator.validate_result(action_name, result, context)
                    
                    return result
                    
                except Exception as e:
                    # Log the exception
                    audit_trail.log_action(
                        f"Function '{action_name}' failed after validation: {str(e)}",
                        action_type="function_error",
                        compliance_status=ComplianceStatus.VIOLATION,
                        severity="high"
                    )
                    raise
            
            return wrapper
        return decorator
    
    def _get_caller_info(self) -> Dict[str, str]:
        """Get information about the calling function"""
        try:
            frame = inspect.currentframe().f_back.f_back.f_back
            return {
                'filename': frame.f_code.co_filename,
                'function': frame.f_code.co_name,
                'line': str(frame.f_lineno)
            }
        except:
            return {'error': 'Could not determine caller'}

class RealTimeValidator:
    """
    Real-time commitment validation system that checks every action
    against the behavioral contract with minimal performance impact.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent
            validator_dir = project_root / "commitment_system" / "data"
            validator_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(validator_dir / "validator.db")
        
        self.db_path = db_path
        self.init_validator_database()
        
        # Core components
        self.validation_queue = ValidationQueue()
        self.validation_mode = ValidationMode.STRICT
        self.active = True
        
        # Performance settings
        self.max_processing_time_ms = 100  # Maximum time per validation
        self.batch_size = 10  # Process multiple requests together
        self.cache_size = 1000
        
        # Validation cache for performance
        self.validation_cache: Dict[str, ValidationResponse] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Statistics
        self.total_validations = 0
        self.blocked_actions = 0
        self.warnings_issued = 0
        self.average_processing_time = 0.0
        
        # Background processing
        self.processing_thread = None
        self.stop_processing = threading.Event()
        
        # Action decorator
        self.validate_action = ActionDecorator(self)
        
        # Start background processing
        self.start_background_processing()
    
    def init_validator_database(self):
        """Initialize the validator database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_requests (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action_category TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    action_parameters TEXT DEFAULT '{}',
                    context TEXT DEFAULT '{}',
                    processing_time_ms REAL DEFAULT 0.0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_responses (
                    request_id TEXT PRIMARY KEY,
                    allowed INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    violations TEXT DEFAULT '[]',
                    warnings TEXT DEFAULT '[]',
                    validation_mode TEXT NOT NULL,
                    recommendations TEXT DEFAULT '[]',
                    FOREIGN KEY (request_id) REFERENCES validation_requests (request_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def validate_action_sync(self, action_category: ActionCategory, action_name: str,
                           action_parameters: Dict[str, Any], 
                           context: Dict[str, Any] = None) -> ValidationResponse:
        """
        Synchronous validation for immediate response.
        Used when blocking validation is required.
        """
        start_time = time.time()
        
        try:
            # Generate request ID
            request_id = f"sync_{int(time.time() * 1000000)}"
            
            # Check cache first
            cache_key = self._generate_cache_key(action_category, action_name, action_parameters)
            if cache_key in self.validation_cache:
                self.cache_hits += 1
                cached_response = self.validation_cache[cache_key]
                cached_response.request_id = request_id  # Update request ID
                return cached_response
            
            self.cache_misses += 1
            
            # Create validation request
            request = ValidationRequest(
                request_id=request_id,
                action_category=action_category,
                action_name=action_name,
                action_parameters=action_parameters,
                context=context or {},
                timestamp=datetime.now().isoformat(),
                priority=10  # Highest priority for sync requests
            )
            
            # Perform validation
            response = self._perform_validation(request)
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            self._update_statistics(processing_time, response)
            
            # Cache the response
            self._cache_response(cache_key, response)
            
            # Log to database
            self._log_validation(request, response)
            
            return response
            
        except Exception as e:
            # Fail-safe response
            processing_time = (time.time() - start_time) * 1000
            
            audit_trail.log_action(
                f"Validation error for {action_name}: {str(e)}",
                action_type="validation_error",
                compliance_status=ComplianceStatus.UNKNOWN,
                severity="high"
            )
            
            return ValidationResponse(
                request_id=request_id,
                allowed=True,  # Fail-safe: allow action
                confidence=0.0,
                violations=[],
                warnings=[f"Validation error: {str(e)}"],
                enforcement_result=None,
                processing_time_ms=processing_time,
                validation_mode=self.validation_mode,
                recommendations=["Review validation system"]
            )
    
    def validate_action_async(self, action_category: ActionCategory, action_name: str,
                            action_parameters: Dict[str, Any], 
                            context: Dict[str, Any] = None,
                            callback: Callable[[ValidationResponse], None] = None) -> str:
        """
        Asynchronous validation for non-blocking scenarios.
        Returns request ID immediately.
        """
        request_id = f"async_{int(time.time() * 1000000)}"
        
        request = ValidationRequest(
            request_id=request_id,
            action_category=action_category,
            action_name=action_name,
            action_parameters=action_parameters,
            context=context or {},
            timestamp=datetime.now().isoformat(),
            priority=5  # Normal priority
        )
        
        # Add callback to context if provided
        if callback:
            request.context['callback'] = callback
        
        # Add to queue
        if not self.validation_queue.add_request(request):
            # Queue is full, handle synchronously
            response = self._perform_validation(request)
            if callback:
                callback(response)
        
        return request_id
    
    def _perform_validation(self, request: ValidationRequest) -> ValidationResponse:
        """Perform the actual validation logic"""
        violations = []
        warnings = []
        confidence = 1.0
        
        try:
            # Check against behavioral contract
            contract_result = behavioral_contract.check_compliance(
                action=request.action_name,
                context=request.context
            )
            
            if not contract_result.compliant:
                violations.extend(contract_result.violations)
                confidence *= 0.8
            
            # Check against enforcement engine
            enforcement_result = enforcement_engine.check_action(
                action_type=request.action_category.value,
                action_details={
                    'action_name': request.action_name,
                    'parameters': request.action_parameters
                },
                context=request.context
            )
            
            if enforcement_result.violation_detected:
                violations.extend([rule.name for rule in enforcement_result.violated_rules])
                confidence *= 0.7
            
            # Check against commitment patterns
            pattern_violations = self._check_commitment_patterns(request)
            violations.extend(pattern_violations)
            
            # Determine if action is allowed
            allowed = True
            if self.validation_mode == ValidationMode.STRICT and violations:
                allowed = False
            elif self.validation_mode == ValidationMode.PERMISSIVE and violations:
                warnings.extend(violations)
                violations = []  # Convert violations to warnings
            elif self.validation_mode == ValidationMode.LEARNING:
                # In learning mode, log everything but allow all actions
                warnings.extend(violations)
                violations = []
                allowed = True
            elif self.validation_mode == ValidationMode.DISABLED:
                allowed = True
                violations = []
                warnings = []
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations, warnings, request)
            
            return ValidationResponse(
                request_id=request.request_id,
                allowed=allowed,
                confidence=confidence,
                violations=violations,
                warnings=warnings,
                enforcement_result=enforcement_result if enforcement_result.violation_detected else None,
                processing_time_ms=0.0,  # Will be set by caller
                validation_mode=self.validation_mode,
                recommendations=recommendations
            )
            
        except Exception as e:
            return ValidationResponse(
                request_id=request.request_id,
                allowed=True,  # Fail-safe
                confidence=0.0,
                violations=[],
                warnings=[f"Validation processing error: {str(e)}"],
                enforcement_result=None,
                processing_time_ms=0.0,
                validation_mode=self.validation_mode,
                recommendations=["Review validation system"]
            )
    
    def _check_commitment_patterns(self, request: ValidationRequest) -> List[str]:
        """Check action against learned commitment patterns"""
        violations = []
        
        try:
            # Get recent commitments from memory store
            recent_commitments = memory_store.get_commitments(limit=50)
            
            # Simple pattern matching against commitment text
            action_text = f"{request.action_name} {str(request.action_parameters)}".lower()
            
            for commitment in recent_commitments:
                commitment_text = commitment.get('content', '').lower()
                
                # Check for contradictory patterns
                if 'not' in commitment_text or 'never' in commitment_text:
                    # Extract the prohibited action
                    prohibited_terms = self._extract_prohibited_terms(commitment_text)
                    for term in prohibited_terms:
                        if term in action_text:
                            violations.append(f"Action conflicts with commitment: {commitment.get('id', 'unknown')}")
                
                # Check for required patterns
                if 'must' in commitment_text or 'always' in commitment_text:
                    required_terms = self._extract_required_terms(commitment_text)
                    for term in required_terms:
                        if term not in action_text and self._is_relevant_action(term, action_text):
                            violations.append(f"Action missing required element from commitment: {commitment.get('id', 'unknown')}")
            
            return violations
            
        except Exception as e:
            print(f"Error checking commitment patterns: {e}")
            return []
    
    def _extract_prohibited_terms(self, commitment_text: str) -> List[str]:
        """Extract terms that are prohibited by a commitment"""
        # Simple extraction - can be enhanced with NLP
        prohibited = []
        
        # Look for patterns like "never do X" or "not allowed to Y"
        words = commitment_text.split()
        for i, word in enumerate(words):
            if word in ['never', 'not', 'cannot', 'must not']:
                # Get the next few words as the prohibited action
                if i + 1 < len(words):
                    prohibited.append(' '.join(words[i+1:i+4]))
        
        return prohibited
    
    def _extract_required_terms(self, commitment_text: str) -> List[str]:
        """Extract terms that are required by a commitment"""
        required = []
        
        # Look for patterns like "must do X" or "always Y"
        words = commitment_text.split()
        for i, word in enumerate(words):
            if word in ['must', 'always', 'required', 'shall']:
                if i + 1 < len(words):
                    required.append(' '.join(words[i+1:i+4]))
        
        return required
    
    def _is_relevant_action(self, term: str, action_text: str) -> bool:
        """Check if a term is relevant to the current action"""
        # Simple relevance check - can be enhanced
        term_words = set(term.lower().split())
        action_words = set(action_text.lower().split())
        
        # If there's any overlap in words, consider it relevant
        return len(term_words.intersection(action_words)) > 0
    
    def _generate_recommendations(self, violations: List[str], warnings: List[str],
                                request: ValidationRequest) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if violations:
            recommendations.append("Review and update relevant commitments before proceeding")
            recommendations.append("Consider alternative approaches that align with stated commitments")
        
        if warnings:
            recommendations.append("Proceed with caution - potential commitment conflicts detected")
        
        if not violations and not warnings:
            recommendations.append("Action appears to be compliant with current commitments")
        
        # Action-specific recommendations
        if request.action_category == ActionCategory.TOOL_CALL:
            recommendations.append("Ensure tool usage aligns with user instructions")
        elif request.action_category == ActionCategory.FILE_OPERATION:
            recommendations.append("Verify file operations are explicitly requested")
        
        return recommendations[:3]  # Limit to top 3
    
    def _generate_cache_key(self, action_category: ActionCategory, action_name: str,
                          action_parameters: Dict[str, Any]) -> str:
        """Generate a cache key for validation results"""
        # Create a hash of the key components
        import hashlib
        
        key_data = f"{action_category.value}_{action_name}_{str(sorted(action_parameters.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_response(self, cache_key: str, response: ValidationResponse):
        """Cache a validation response"""
        if len(self.validation_cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.validation_cache))
            del self.validation_cache[oldest_key]
        
        self.validation_cache[cache_key] = response
    
    def _update_statistics(self, processing_time: float, response: ValidationResponse):
        """Update validation statistics"""
        self.total_validations += 1
        
        if not response.allowed:
            self.blocked_actions += 1
        
        if response.warnings:
            self.warnings_issued += 1
        
        # Update average processing time
        self.average_processing_time = (
            (self.average_processing_time * (self.total_validations - 1) + processing_time) /
            self.total_validations
        )
    
    def _log_validation(self, request: ValidationRequest, response: ValidationResponse):
        """Log validation to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Log request
                conn.execute("""
                    INSERT OR REPLACE INTO validation_requests 
                    (request_id, timestamp, action_category, action_name, 
                     action_parameters, context, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.request_id,
                    request.timestamp,
                    request.action_category.value,
                    request.action_name,
                    json.dumps(request.action_parameters),
                    json.dumps(request.context),
                    response.processing_time_ms
                ))
                
                # Log response
                conn.execute("""
                    INSERT OR REPLACE INTO validation_responses 
                    (request_id, allowed, confidence, violations, warnings, 
                     validation_mode, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    response.request_id,
                    1 if response.allowed else 0,
                    response.confidence,
                    json.dumps(response.violations),
                    json.dumps(response.warnings),
                    response.validation_mode.value,
                    json.dumps(response.recommendations)
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error logging validation: {e}")
    
    def start_background_processing(self):
        """Start background processing thread"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_processing.clear()
            self.processing_thread = threading.Thread(
                target=self._background_processor,
                daemon=True
            )
            self.processing_thread.start()
    
    def stop_background_processing(self):
        """Stop background processing thread"""
        self.stop_processing.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
    
    def _background_processor(self):
        """Background thread for processing async validation requests"""
        while not self.stop_processing.is_set():
            try:
                request = self.validation_queue.get_request(timeout=1.0)
                if request is None:
                    continue
                
                # Process the request
                start_time = time.time()
                response = self._perform_validation(request)
                processing_time = (time.time() - start_time) * 1000
                response.processing_time_ms = processing_time
                
                # Update statistics
                self._update_statistics(processing_time, response)
                
                # Log to database
                self._log_validation(request, response)
                
                # Call callback if provided
                callback = request.context.get('callback')
                if callback and callable(callback):
                    try:
                        callback(response)
                    except Exception as e:
                        print(f"Error calling validation callback: {e}")
                
            except Exception as e:
                print(f"Error in background validation processor: {e}")
                time.sleep(0.1)  # Brief pause on error
    
    def validate_result(self, action_name: str, result: Any, context: Dict[str, Any]):
        """Validate the result of an action"""
        # This can be used to validate outputs/results
        # For now, just log the result
        audit_trail.log_action(
            f"Action '{action_name}' completed successfully",
            action_type="action_completion",
            compliance_status=ComplianceStatus.COMPLIANT,
            context=context
        )
    
    def set_validation_mode(self, mode: ValidationMode):
        """Set the validation mode"""
        old_mode = self.validation_mode
        self.validation_mode = mode
        
        audit_trail.log_action(
            f"Validation mode changed from {old_mode.value} to {mode.value}",
            action_type="system_configuration",
            compliance_status=ComplianceStatus.COMPLIANT
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        queue_stats = self.validation_queue.get_stats()
        
        return {
            "total_validations": self.total_validations,
            "blocked_actions": self.blocked_actions,
            "warnings_issued": self.warnings_issued,
            "average_processing_time_ms": self.average_processing_time,
            "validation_mode": self.validation_mode.value,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "queue_stats": queue_stats,
            "active": self.active
        }
    
    def clear_cache(self):
        """Clear the validation cache"""
        self.validation_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

# Global instance for easy access
real_time_validator = RealTimeValidator()