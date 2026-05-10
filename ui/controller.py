import logging
import traceback
from typing import Callable, Any, Literal

from PySide6.QtCore import QObject, Slot, QThread, QThreadPool, QRunnable, Signal

from ui import ProcessingOverlay
from ui.area_overlay import AreaSelectionOverlay
from util.decorator import singleton

logger = logging.getLogger("ui.controller")

class WorkerSignals(QObject):
    """
    Signaux émis par une tâche exécutée dans le thread pool.

    - finished : toujours émis à la fin
    - error : émis si une exception se produit
    """
    finished = Signal()
    error = Signal(str)


class FunctionWorker(QRunnable):
    """
    Worker générique qui exécute une fonction Python avec ses arguments
    dans un thread du QThreadPool.
    """

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """
        Méthode appelée par Qt dans un thread du pool.
        """
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(repr(e))
        finally:
            self.signals.finished.emit()


@singleton
class GuiController(QObject):
    selection_overlay: AreaSelectionOverlay | None
    processing_overlay: ProcessingOverlay | None
    processing_thread: QThread
    pool: QThreadPool

    wait = Signal()
    load = Signal()
    play = Signal()
    close = Signal()

    def __init__(self):
        super().__init__()
        self.selection_overlay = None
        self.processing_overlay = None
        self.processing_thread = QThread()
        self.pool = QThreadPool.globalInstance()
        self.processing_width = 200
        self.processing_height = 20
        self.bar_color = (0, 140, 255)
        self.wait.connect(lambda: self.__show_processing_indicator("wait"))
        self.load.connect(lambda: self.__show_processing_indicator("load"))
        self.play.connect(lambda: self.__show_processing_indicator("play"))
        self.close.connect(self.__close_processing_indicator)


    def configure_processing_overlay(self,
                                    width: int = 200,
                                    height: int = 20,
                                    bar_color: tuple[int, int, int, int] = (0, 140, 255)):
        logger.info("Configuring processing overlay")
        self.processing_width = width
        self.processing_height = height
        self.bar_color = bar_color

    @Slot()
    def pool_start(self, fct: Callable, *args: Any, **kwargs: Any):
        logger.info(f"Starting background task {fct}")
        self.pool.start(FunctionWorker(fct, *args, **kwargs))

    @Slot()
    def open_area_selection(self, on_area_selected: Callable[[tuple[int, int], tuple[int, int]], None]) -> None:
        logger.info("Opening area selection")
        if self.selection_overlay is None:
            self.selection_overlay = AreaSelectionOverlay()

        def callback(start, end):
            logger.info("Closing area selection")

            # Closes the overlay GUI
            if self.selection_overlay is not None:
                self.selection_overlay.close()
                self.selection_overlay.deleteLater()
                self.selection_overlay = None
            self.pool_start(on_area_selected, start, end)

        self.selection_overlay.area_selected.connect(callback)
        self.selection_overlay.show()

    @Slot()
    def __show_processing_indicator(self, animation: Literal["load", "wait", "play"] = "wait"):
        logger.info(f"Opening processing indicator in '{animation}' mode")
        if self.processing_overlay is None:
            self.processing_overlay = ProcessingOverlay(width=self.processing_width,
                                                        height=self.processing_height,
                                                        bar_color=self.bar_color)

        if animation == "load":
            self.processing_overlay.set_loading()
        elif animation == "wait":
            self.processing_overlay.set_waiting()
        else:
            self.processing_overlay.set_playing()

        self.processing_overlay.show()

    @Slot()
    def __close_processing_indicator(self):
        logger.info("Closing processing indicator")
        if self.processing_overlay:
            self.processing_overlay.hide()