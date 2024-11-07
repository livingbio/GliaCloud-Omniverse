import omni.ui as ui

class USDNucleusOrganizerWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        # Set the function that is called to build widgets when the window is
        # visible
        self.frame.set_build_fn(self._build_fn)

    def _build_fn(self):
        """
        The method that is called to build all the UI once the window is
        visible.
        """
        self._count = 0

        with ui.ScrollingFrame():
            with ui.VStack():
                label = ui.Label("")

                # input_path = "tests/simple_sphere.obj"
                # output_path = "tests/simple_sphere.usd"
                
                # ui.Button("Import", clicked_fn=asyncio.ensure_future(convert(input_path, output_path)))

                # ui.Button("Debug", clicked_fn=lambda: get_extension_path("omni.kit.ui"))

                def on_click():
                    self._count += 1
                    label.text = f"count: {self._count}"

                def on_reset():
                    self._count = 0
                    label.text = "empty"

                on_reset()

                with ui.HStack():
                    ui.Button("Add", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)