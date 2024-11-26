import omni.ext
import omni.ui as ui
import omni.kit.ui

import carb
from functools import partial
import asyncio

from .window import ReshadeBrowserWindow
from .reshade_menu import ReshadeMenuHookExt

_global_instance = None

class ReshadeBrowserExtension(omni.ext.IExt):
    WINDOW_NAME = "Reshade Preset Browser"
    MENU_PATH = f'Window/GliaCloud Custom/{WINDOW_NAME}'

    def on_startup(self, ext_id):
        carb.log_warn(f"{ext_id} extension started")

        global _global_instance
        _global_instance = self

        self._window = None
        self._menu = None

        # self._reshade_menu = ReshadeMenuHookExt()

        # store extension info in Carbonite
        _settings = carb.settings.get_settings()
        _settings.set("exts/omni.kit.reshade.browser/_ext_id", str(ext_id))

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(ReshadeBrowserExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        _editor_menu = omni.kit.ui.get_editor_menu()
        if _editor_menu:
            self._menu = _editor_menu.add_item(
                ReshadeBrowserExtension.MENU_PATH, on_click=self.show_window, toggle=True, value=True
            )

        self.show_window(None, True)

    def on_shutdown(self):
        global _global_instance
        _global_instance = None

        if self._menu:
            self._menu = None

        if self._window:
            self._window.destroy()
            self._window = None

        # Deregister the function that shows the window from omni.ui
        ui.Workspace.set_show_window_fn(ReshadeBrowserExtension.WINDOW_NAME, None)

    async def _destroy_window_async(self, visible):
        # wait one frame, this is due to the one frame defer in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(ReshadeBrowserExtension.MENU_PATH, visible)

        if self._window:
            self._window.destroy()
            self._window = None

    def _visibility_changed_fn(self, visible):
        # Called when the user pressed "X"
        # Set the checkmark in the menu that shows whether this window is visible or not
        if not visible:
            # Destroy the window, since we are creating new window in show_window
            asyncio.ensure_future(self._destroy_window_async(visible))

    def show_window(self, _menu_path, show: bool):
        # _menu_path is argument set automatically by EditorMenu functionalities
        # show is true if the window should be shown. set automatically by our registered callback function
        if show:
            self._window = ReshadeBrowserWindow(ReshadeBrowserExtension.WINDOW_NAME)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
        elif self._window:
            self._window.visible = False

    @staticmethod
    def get_instance():
        global _global_instance
        return _global_instance
