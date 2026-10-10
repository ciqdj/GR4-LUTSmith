"""Long work (checking the firmware, fitting, the photo preview, building) runs off the window's thread."""
import traceback

from PySide6.QtCore import QThread, Signal

import gr4_lutsmith as gl

from .i18n import t
from .logic import Problem


class Task(QThread):
    """Runs fn(report) in the background. report(message) sends progress (text, or any object) to the window."""
    progress = Signal(object)
    succeeded = Signal(object)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            self.succeeded.emit(self.fn(self.progress.emit))
        except gl.Stopped:
            self.stopped.emit()
        except Problem as exc:
            self.failed.emit(str(exc))
        except gl.Refused as exc:
            self.failed.emit(t('Not possible: {reason}', reason=str(exc)))
        except MemoryError:
            self.failed.emit(t('The computer ran out of memory. Close other programs and try again.'))
        except Exception as exc:                               # never lose the window over an unexpected error
            traceback.print_exc()
            self.failed.emit(t('Something went wrong: {error}', error=f'{type(exc).__name__}: {exc}'))
