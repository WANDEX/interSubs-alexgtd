import logging

from ui.presenters.presenter import Presenter

log = logging.getLogger(__name__)


class SubtitlesPresenter(Presenter):
    def __init__(self, subtitles_view, subtitles_data_source) -> None:
        super().__init__(subtitles_view)
        self._subs_data_source = subtitles_data_source

        self._start_fetching_subtitles()

    def _start_fetching_subtitles(self) -> None:
        self._subs_data_source.on_subtitles_change.connect(self.view.submit_subs)
        self._subs_data_source.on_error.connect(
            lambda e: log.error("Exception occurred while watching the subtitles file.", exc_info=e)
        )
        self._subs_data_source.start()
