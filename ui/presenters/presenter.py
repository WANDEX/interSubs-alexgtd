class Presenter:
    def __init__(self, view) -> None:
        self.view = view
        self._attach_self_in_view()

    def _attach_self_in_view(self) -> None:
        self.view.attach_presenter(self)
