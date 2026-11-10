"""Gunicorn WSGI Configuration for TRASCO Flask Backend (Stage B Deployment).
Provides production WSGI configuration with worker post_fork lifecycle hooks,
ensuring startup security validation and schema compatibility verification without DDL.
"""

import os
import logging

# Server socket binding (strictly loopback by default to mitigate network probing)
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")

# Worker process settings
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "sync"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
keepalive = 2

# Logging configuration
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"


def post_fork(server, worker):
    """Gunicorn post_fork lifecycle hook.

    Executed immediately after a worker process is forked by the master process.
    Guarantees:
    1. Safe execution under both normal and --preload modes.
    2. Runs startup security validation inside each child worker process.
    3. Executes minimum ORM structural compatibility schema probe without DDL.
    4. Sets application readiness state. If schema probe fails, worker remains alive
       in fail-closed unready mode: /health returns 200 (liveness), but /health/ready
       and all business endpoints return HTTP 503 Service Unavailable.
    """
    logger = server.log if (server and hasattr(server, "log")) else logging.getLogger("gunicorn.error")
    worker_pid = worker.pid if (worker and hasattr(worker, "pid")) else os.getpid()

    logger.info("Worker %s: executing bootstrap_flask_worker()...", worker_pid)

    from app.flask_app import bootstrap_flask_worker

    ready = bootstrap_flask_worker()
    if ready:
        logger.info("Worker %s: bootstrap succeeded (status: READY).", worker_pid)
    else:
        logger.warning(
            "Worker %s: schema compatibility probe failed (status: UNREADY). "
            "Traffic will be rejected with HTTP 503 until schema matches ORM metadata.",
            worker_pid
        )
