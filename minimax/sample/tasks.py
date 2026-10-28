"""Small runnable business module for task listing."""


def list_tasks(tasks, status=None):
    """Return tasks in their original order, optionally filtered by exact status."""
    task_list = list(tasks)
    if status is None:
        return task_list
    return [task for task in task_list if task["status"] == status]
