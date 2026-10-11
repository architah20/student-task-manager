import time

from flask import Response, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from .models import Task

REQUEST_COUNT = Counter(
    "http_requests", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency in seconds", ["endpoint"]
)
TASKS_CREATED = Counter("tasks_created", "Total number of tasks created")
TASKS_PENDING = Gauge("tasks_pending", "Tasks currently pending")
TASKS_DONE = Gauge("tasks_done", "Tasks currently done")


def register_metrics(app):
    @app.before_request
    def start_timer():
        g.start_time = time.perf_counter()

    @app.after_request
    def record_metrics(response):
        if request.path == "/metrics":
            return response
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        elapsed = time.perf_counter() - g.get("start_time", time.perf_counter())
        REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(endpoint).observe(elapsed)
        return response

    @app.route("/metrics")
    def metrics():
        TASKS_PENDING.set(Task.query.filter_by(status="pending").count())
        TASKS_DONE.set(Task.query.filter_by(status="done").count())
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
