"""Tests for Task logs_mount feature."""
import sys
import types as python_types
from unittest.mock import MagicMock


class FakeMount:
    """Minimal stand-in for docker.types.Mount."""
    def __init__(self, target, source, type, read_only):
        self.target = target
        self.source = source
        self.type = type
        self.read_only = read_only


# Inject stub module so `from docker.types import Mount` works in tests
_fake_docker_types = python_types.ModuleType("docker.types")
_fake_docker_types.Mount = FakeMount
sys.modules.setdefault("docker.types", _fake_docker_types)


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
    task._logs_mount_path = None
    task._logs_mount = None
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
        assert task._logs_mount is None

    def test_default_logs_mount_is_false(self):
        from sipssert.task import Task
        assert Task.default_logs_mount is False

    def test_no_mount_when_path_is_none(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir(None)
        assert task._logs_mount is None
        assert task.volumes == {}


class TestSetLogsDirWithMount:
    def test_creates_mount_when_logs_mount_true(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/scenario1")
        assert task._logs_mount is not None
        assert isinstance(task._logs_mount, FakeMount)

    def test_mount_target_is_mount_point(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/scenario1")
        assert task._logs_mount.target == "/sipssert_logs"

    def test_mount_source_is_path(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/scenario1")
        assert task._logs_mount.source == "/run/logs/scenario1"

    def test_mount_is_readwrite(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/scenario1")
        assert task._logs_mount.read_only is False

    def test_custom_mount_point(self):
        task = make_task(logs_mount=True, logs_mount_point="/custom/path")
        task.set_logs_dir("/run/logs/scenario1")
        assert task._logs_mount.target == "/custom/path"

    def test_default_mount_point_value(self):
        from sipssert.task import Task
        assert Task.default_logs_mount_point == "/sipssert_logs"

    def test_second_set_logs_dir_updates_mount(self):
        task = make_task(logs_mount=True)
        task.set_logs_dir("/run/logs/first")
        task.set_logs_dir("/run/logs/second")
        assert task._logs_mount.source == "/run/logs/second"
        assert task.logs_dir == "/run/logs/second"
        assert task._logs_mount_path == "/run/logs/second"

    def test_second_set_logs_dir_does_not_touch_user_volumes(self):
        task = make_task(logs_mount=False)
        # simulate a user-defined volume
        task.volumes["/run/logs/first"] = {"bind": "/external", "mode": "ro"}
        task.set_logs_dir("/run/logs/first")
        task.set_logs_dir("/run/logs/second")
        # user-defined volume must not be deleted
        assert "/run/logs/first" in task.volumes
        assert task.volumes["/run/logs/first"]["bind"] == "/external"
