from ui.presenters.presenter import Presenter


class PopupPresenter(Presenter):
    def __init__(self, view) -> None:
        super().__init__(view)

    def pop(self, text, event):
        self.view.pop(text, event)

