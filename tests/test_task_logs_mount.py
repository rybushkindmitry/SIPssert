"""Tests for Task logs_mount feature."""
import pytest
from unittest.mock import MagicMock, patch


def make_task(logs_mount=None, logs_mount_point=None):
    """Build a minimal Task instance without Docker."""
    from sipssert.task import Task

    config = {
        "name": "test_task",
        "image": "dummy:latest",
    }
    if logs_mount is not None:
        config["logs_mount"] = logs_mount
    if logs_mount_point is not None:
        config["logs_mount_point"] = logs_mount_point

    task = Task.__new__(Task)
    task.config = MagicMock()
    task.config.get = lambda key, default=None: config.get(key, default)
    task.volumes = {}
    task.logs_dir = None
    task.container = None
    task.logs_mount = config.get("logs_mount", Task.default_logs_mount)
    task.logs_mount_point = config.get(
        "logs_mount_point", Task.default_logs_mount_point
    )
    return task


class TestSetLogsDirBase:
    def test_sets_logs_dir(self):
        task = make_task()
        task.set_logs_dir("/some/logs")
        assert task.logs_dir == "/some/logs"

    def test_no_mount_when_logs_mount_false(self):
        task = make_task(logs_mount=False)
        task.set_logs_dir("/some/logs")
        assert "/some/logs" not in task.volumes

    def test_default_logs_mount_is_false(self):
        from sipssert.task import Task
        assert Task.default_logs_mount is False

    def test_no_mount_when_path_is_none(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir(None)
        assert task.volumes == {}


class TestSetLogsDirWithMount:
    def test_adds_volume_when_logs_mount_true(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/scenario1")
        assert "/run/logs/scenario1" in task.volumes
        assert task.volumes["/run/logs/scenario1"]["bind"] == "/sipssert_logs"
        assert task.volumes["/run/logs/scenario1"]["mode"] == "rw"

    def test_custom_mount_point(self):
        task = make_task(logs_mount=True, logs_mount_point="/custom/path")
        task.set_logs_dir("/run/logs/scenario1")
        assert task.volumes["/run/logs/scenario1"]["bind"] == "/custom/path"

    def test_default_mount_point_value(self):
        from sipssert.task import Task
        assert Task.default_logs_mount_point == "/sipssert_logs"

    def test_second_set_logs_dir_updates_volume(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/first")
        task.set_logs_dir("/run/logs/second")
        assert "/run/logs/second" in task.volumes
        assert task.logs_dir == "/run/logs/second"
        assert "/run/logs/first" not in task.volumes
