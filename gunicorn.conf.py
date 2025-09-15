# Gunicorn Configuration - MacBook Air M1 Optimized
# TRAE AI Production System

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - Optimized for M1 8-core CPU with 16GB RAM
workers = int(os.environ.get("WORKERS", 4))  # 4 workers for M1 efficiency
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = int(os.environ.get("MAX_REQUESTS", 1000))
max_requests_jitter = 100
preload_app = True

# Memory management for 16GB RAM
# Each worker should use max 2GB (4 workers = 8GB total)
# Leaving 8GB for system, database, and other processes
max_worker_memory = 2048 * 1024 * 1024  # 2GB in bytes

# Timeouts
timeout = int(os.environ.get("TIMEOUT", 30))
keepalive = int(os.environ.get("KEEPALIVE", 2))
graceful_timeout = 30

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "traeai-production"

# Server mechanics
daemon = False
pidfile = "/app/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = "/app/tmp"

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Performance tuning for M1
# Enable SO_REUSEPORT for better load distribution
reuse_port = True


# Worker lifecycle hooks
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("TRAE AI Production server is ready. Optimized for M1 MacBook Air.")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker {worker.pid} is being forked")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} spawned")

    # Set worker-specific optimizations
    import resource

    # Set memory limit per worker (2GB)
    resource.setrlimit(resource.RLIMIT_AS, (max_worker_memory, max_worker_memory))

    # Optimize for M1 architecture
    os.environ["OMP_NUM_THREADS"] = "2"  # Limit OpenMP threads per worker
    os.environ["MKL_NUM_THREADS"] = "2"  # Limit MKL threads per worker
    os.environ["OPENBLAS_NUM_THREADS"] = "2"  # Limit OpenBLAS threads per worker


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT signal")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Log memory usage for monitoring
    import psutil

    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024

    if memory_mb > 1800:  # Warn if approaching 2GB limit
        worker.log.warning(f"Worker {worker.pid} memory usage: {memory_mb:.1f}MB")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exited")


def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker {worker.pid} exit")


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting."""
    server.log.info("TRAE AI Production server is shutting down.")


# M1 Specific Environment Variables
raw_env = [
    "PLATFORM=linux/arm64",
    "ARCH=arm64",
    "OPTIMIZED_FOR=M1_MACBOOK_AIR",
    "MEMORY_LIMIT=16GB",
    "CPU_CORES=8",
    "WORKER_MEMORY_LIMIT=2GB",
# BRACKET_SURGEON: disabled
# ]

# Security
user = "traeai"
group = "traeai"

# Monitoring
statsd_host = None
statsd_prefix = "traeai.production"

# Development vs Production
if os.environ.get("ENVIRONMENT") == "development":
    reload = True
    reload_extra_files = ["templates/", "static/"]
    loglevel = "debug"
else:
    reload = False
    loglevel = "info"


# Custom configuration validation
def validate_config():
    """Validate M1 specific configuration."""
    import psutil

    # Check available memory
    available_memory_gb = psutil.virtual_memory().total / (1024**3)
    if available_memory_gb < 15:  # Less than 15GB available
        print(
            f"WARNING: Only {available_memory_gb:.1f}GB RAM available. M1 optimization requires 16GB."
# BRACKET_SURGEON: disabled
#         )

    # Check CPU cores
    cpu_count = multiprocessing.cpu_count()
    if cpu_count < 8:
        print(f"WARNING: Only {cpu_count} CPU cores detected. M1 optimization expects 8 cores.")

    # Validate worker configuration
    total_worker_memory = workers * (max_worker_memory / (1024**3))
    if total_worker_memory > available_memory_gb * 0.6:  # More than 60% of RAM
        print(f"WARNING: Worker memory allocation ({total_worker_memory:.1f}GB) may be too high.")


# Run validation on import
validate_config()