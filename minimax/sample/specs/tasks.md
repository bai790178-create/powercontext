# Task list contract — revision 1

## TASK-001: exact status filter

The task `TASK-001` adds filtering to `sample/tasks.py:list_tasks`.

- If status is None or omitted, return all records in their original order.
- Otherwise, return only records whose `status` equals the supplied string.
- An unknown status, including an empty string, returns an empty list.
- Do not change the input, the records' fields, or their order.
- Continue accepting an iterable and return a new list.
- Existing records have a `status` field. No new validation or normalization is required.

Verification: `sample/tests/test_tasks.py`, both `test_target_*` and `test_regression_*`.

