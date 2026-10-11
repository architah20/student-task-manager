from datetime import date

from flask import Blueprint, jsonify, render_template, request

from .metrics import TASKS_CREATED
from .models import Task, db

bp = Blueprint("tasks", __name__)

VALID_STATUS = {"pending", "done"}


def _validate(data, require_title):
    """Return (clean_values, errors) for a task payload."""
    if not isinstance(data, dict):
        return {}, {"body": "A JSON object is required"}

    clean, errors = {}, {}

    if require_title or "title" in data:
        title = str(data.get("title") or "").strip()
        if not title:
            errors["title"] = "title is required"
        elif len(title) > 200:
            errors["title"] = "title must be 200 characters or fewer"
        else:
            clean["title"] = title

    if "description" in data:
        clean["description"] = str(data["description"] or "")

    if "status" in data:
        if data["status"] not in VALID_STATUS:
            errors["status"] = "status must be 'pending' or 'done'"
        else:
            clean["status"] = data["status"]

    if "due_date" in data:
        if data["due_date"] in (None, ""):
            clean["due_date"] = None
        else:
            try:
                clean["due_date"] = date.fromisoformat(str(data["due_date"]))
            except ValueError:
                errors["due_date"] = "due_date must use the format YYYY-MM-DD"

    return clean, errors


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/health")
def health():
    return jsonify(status="ok")


@bp.route("/api/tasks", methods=["GET"])
def list_tasks():
    query = Task.query
    status = request.args.get("status")
    if status in VALID_STATUS:
        query = query.filter_by(status=status)
    tasks = query.order_by(Task.id.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@bp.route("/api/tasks", methods=["POST"])
def create_task():
    clean, errors = _validate(request.get_json(silent=True), require_title=True)
    if errors:
        return jsonify(errors=errors), 400
    task = Task(**clean)
    db.session.add(task)
    db.session.commit()
    TASKS_CREATED.inc()
    return jsonify(task.to_dict()), 201


@bp.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = db.get_or_404(Task, task_id)
    return jsonify(task.to_dict())


@bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = db.get_or_404(Task, task_id)
    clean, errors = _validate(request.get_json(silent=True), require_title=False)
    if errors:
        return jsonify(errors=errors), 400
    for key, value in clean.items():
        setattr(task, key, value)
    db.session.commit()
    return jsonify(task.to_dict())


@bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    return "", 204


@bp.app_errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify(error="Not found"), 404
    return "Page not found", 404
