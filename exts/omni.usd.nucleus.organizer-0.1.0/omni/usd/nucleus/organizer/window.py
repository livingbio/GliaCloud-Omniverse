import omni.ui as ui
import carb

class USDNucleusOrganizerWindow(ui.Window):
    # TODO: model delegate
    def __init__(self, title: str):
        super().__init__(title)

        # Set the function that is called to build widgets when the window is visible
        self.frame.set_build_fn(self._build_fn)

    def _build_fn(self):
        """
        The method that is called to build all the UI once the window is
        visible.
        """
        
        self._count = 0

        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("Select Files")