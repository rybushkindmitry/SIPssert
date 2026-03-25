"""Tests for SIPPTask log file arguments."""
from unittest.mock import MagicMock


def make_sipp_task(logs_mount=None, name="my_sipp"):
    """Build a minimal SIPPTask without Docker or filesystem."""
    from sipssert.tasks.sipp import SIPPTask

    config = {
        "name": name,
        "image": "ctaloi/sipp",
        "calls": "1",
        "duration": "5000",
    }
    if logs_mount is not None:
        config["logs_mount"] = logs_mount

    task = SIPPTask.__new__(SIPPTask)
    task.config = MagicMock()
    task.config.get = lambda key, default=None: config.get(key, default)
    task.volumes = {}
    task.logs_dir = None
    task._logs_mount_path = None
    task.container = None
    task.name = name
    task.username = None
    task.password = None
    task.port = None
    task.keys = {}
    task.calls = "1"
    task.duration = "5000"
    task.proxy = None
    task.service = None
    task.ip = None
    task.config_file = None
    task.mount_point = "/home"
    task.logs_mount = config.get("logs_mount", SIPPTask.default_logs_mount)
    task.logs_mount_point = SIPPTask.default_logs_mount_point
    return task


class TestSIPPTaskDefaults:
    def test_default_logs_mount_is_true(self):
        from sipssert.tasks.sipp import SIPPTask
        assert SIPPTask.default_logs_mount is True

    def test_inherits_default_logs_mount_point(self):
        from sipssert.tasks.sipp import SIPPTask
        from sipssert.task import Task
        assert SIPPTask.default_logs_mount_point == Task.default_logs_mount_point


class TestSIPPTaskArgsWithLogs:
    def test_log_file_args_present_when_logs_dir_set(self):
        task = make_sipp_task()
        task.logs_dir = "/run/logs/scenario1"
        args = task.get_task_args()
        assert "-log_file" in args
        assert "-message_file" in args
        assert "-shortmessage_file" in args

    def test_log_file_path_uses_name(self):
        task = make_sipp_task(name="caller")
        task.logs_dir = "/run/logs/scenario1"
        args = task.get_task_args()
        idx = args.index("-log_file")
        assert args[idx + 1] == "/sipssert_logs/caller_errors.log"

    def test_message_file_path_uses_name(self):
        task = make_sipp_task(name="caller")
        task.logs_dir = "/run/logs/scenario1"
        args = task.get_task_args()
        idx = args.index("-message_file")
        assert args[idx + 1] == "/sipssert_logs/caller_messages.log"

    def test_shortmessage_file_path_uses_name(self):
        task = make_sipp_task(name="caller")
        task.logs_dir = "/run/logs/scenario1"
        args = task.get_task_args()
        idx = args.index("-shortmessage_file")
        assert args[idx + 1] == "/sipssert_logs/caller_shortmessages.log"

    def test_custom_mount_point_used_in_args(self):
        task = make_sipp_task(name="caller")
        task.logs_dir = "/run/logs/scenario1"
        task.logs_mount_point = "/custom/output"
        args = task.get_task_args()
        idx = args.index("-log_file")
        assert args[idx + 1] == "/custom/output/caller_errors.log"


class TestSIPPTaskArgsWithoutLogs:
    def test_no_log_args_when_logs_dir_not_set(self):
        task = make_sipp_task()
        task.logs_dir = None
        args = task.get_task_args()
        assert "-log_file" not in args
        assert "-message_file" not in args
        assert "-shortmessage_file" not in args

    def test_no_log_args_when_logs_mount_disabled(self):
        task = make_sipp_task(logs_mount=False)
        task.logs_dir = "/run/logs/scenario1"
        args = task.get_task_args()
        assert "-log_file" not in args
