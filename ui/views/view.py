class View:
    def __init__(self) -> None:
        self.presenter = None

    def attach_presenter(self, presenter) -> None:
        self.presenter = presenter
