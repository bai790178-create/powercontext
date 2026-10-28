"""The same target and regression tests are used before and after modification."""

import copy

import pytest

from sample.tasks import list_tasks


@pytest.fixture
def tasks():
    return [
        {"id": 1, "title": "write spec", "status": "done"},
        {"id": 2, "title": "implement", "status": "pending"},
        {"id": 3, "title": "review", "status": "done"},
    ]


@pytest.mark.parametrize("status,ids", [("pending", [2]), ("done", [1, 3])])
def test_target_filter_by_status(tasks, status, ids):
    assert [task["id"] for task in list_tasks(tasks, status)] == ids


def test_target_unknown_status_is_empty(tasks):
    assert list_tasks(tasks, "archived") == []


def test_target_empty_string_is_an_exact_filter(tasks):
    assert list_tasks(tasks, "") == []


def test_regression_no_filter_preserves_all_tasks_and_order(tasks):
    assert list_tasks(tasks) == tasks
    assert list_tasks(tasks, None) == tasks


def test_regression_empty_input():
    assert list_tasks([]) == []
    assert list_tasks([], "pending") == []


def test_regression_input_is_not_modified(tasks):
    original = copy.deepcopy(tasks)
    result = list_tasks(tasks, "done")
    assert tasks == original
    assert result is not tasks


def test_regression_iterable_input(tasks):
    assert list_tasks(iter(tasks)) == tasks
