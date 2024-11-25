import omni.ext
import omni.kit.ui
from .window import ReshadeBrowserWindow
from .reshade_menu import ReshadeMenuHookExt

RESHADE_BROWSER_MENU_PATH = "Window/Browsers/Reshade"


class ReshadeBrowserExtension(omni.ext.IExt):


    def on_startup(self, ext_id):
        self._menu = omni.kit.ui.get_editor_menu().add_item(
            RESHADE_BROWSER_MENU_PATH, self._on_click, toggle=True, value=True
        )
        self._window = ReshadeBrowserWindow(ext_id)
        self._reshade_menu = ReshadeMenuHookExt()

        self._window.set_visibility_changed_fn(self._on_visibility_changed)

        global _extension_instance
        _extension_instance = self

    def on_shutdown(self):
        if self._window is not None:
            self._window.destroy()
            self._window = None
        global _extension_instance
        _extension_instance = None

    def _on_click(self, *args):
        self._window.visible = not self._window.visible

    def _on_visibility_changed(self, visible):
        omni.kit.ui.get_editor_menu().set_value(RESHADE_BROWSER_MENU_PATH, visible)
    
def get_instance():
    return _extension_instance


