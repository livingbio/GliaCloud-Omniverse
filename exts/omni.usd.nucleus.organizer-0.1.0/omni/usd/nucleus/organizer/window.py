import omni.ui as ui
import carb
from .asset_import import CustomAssetImporter

class USDNucleusOrganizerWindow(ui.Window):
    # TODO: model delegateZ
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
        
        # TODO: figure out where to instantiate this
        i = CustomAssetImporter()
    
        self._count = 0

        with ui.ScrollingFrame():
            with ui.VStack():
                i.build_options([])