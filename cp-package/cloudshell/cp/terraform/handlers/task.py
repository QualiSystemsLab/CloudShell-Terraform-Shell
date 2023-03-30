from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from logging import Logger
from typing import Any

from attrs import define, field, setters

from cloudshell.cp.terraform.exceptions import BaseTFException

ON_TASK_PROGRESS_TYPE = Callable[["Task", Any], None]


class TaskFailed(BaseTFException):
    def __init__(self, task: Task):
        self.task = task
        self.error_msg = task.error_msg
        super().__init__(f"{task} failed. {task.error_msg}")


class TaskState(Enum):
    success = "success"
    running = "running"
    queued = "queued"
    error = "error"


@define(repr=False)
class Task:
    _vc_obj: vim.Task = field(on_setattr=setters.frozen)
    logger: Logger

    def __repr__(self):
        return f"Task {self.key}"

    @property
    def key(self) -> str:
        return self._vc_obj.info.key

    @property
    def result(self) -> Any:
        return self._vc_obj.info.result

    @property
    def cancelable(self) -> bool:
        return self._vc_obj.info.cancelable

    @property
    def cancelled(self) -> bool:
        return self._vc_obj.info.cancelled

    @property
    def state(self) -> TaskState:
        return TaskState(self._vc_obj.info.state)

    @property
    def complete_time(self) -> datetime:
        return self._vc_obj.info.completeTime

    @property
    def error_msg(self) -> str | None:
        if self.state is not TaskState.error:
            return None

        error = self._vc_obj.info.error
        if error and error.faultMessage:
            emsg = "; ".join([err.message for err in error.faultMessage])
        elif error and error.msg:
            emsg = error.msg
        else:
            emsg = "Task failed with some error"
        return emsg

    def wait(
        self,
        raise_on_error: bool = True,
        on_progress: ON_TASK_PROGRESS_TYPE | None = None,
    ) -> Any:
        if on_progress is not None:
            on_progress = wrapper_on_progress(on_progress, self.logger)
        try:
            WaitForTask(
                self._vc_obj, raiseOnError=raise_on_error, onProgressUpdate=on_progress
            )
        except Exception as e:
            raise TaskFailed(self) from e
        return self.result

    def cancel(self) -> None:
        if self.cancelable and not self.cancelled:
            self._vc_obj.CancelTask()


def wrapper_on_progress(
    fn: ON_TASK_PROGRESS_TYPE, logger: Logger
) -> Callable[[vim.Task, Any], None]:
    def on_progress(task: vim.Task, progress: Any) -> None:
        fn(Task(task, logger), progress)

    return on_progress
