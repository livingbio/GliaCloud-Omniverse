import omni.ext
import omni.ui as ui
import omni.kit.ui

import carb
import asyncio
from functools import partial
from pathlib import Path

from .window import USDNucleusOrganizerWindow

_global_instance = None

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class USDNucleusOrganizerExtension(omni.ext.IExt):
    WINDOW_NAME = "USD Nucleus Organizer"
    MENU_PATH = f"Window/GliaCloud Custom/{WINDOW_NAME}"

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    # TODO: better comments & make sure functions are all named properly with _
    def on_startup(self, ext_id):
        carb.log_warn("Extension started")
        global _global_instance
        _global_instance = self
        
        self._window = None
        self._menu = None
        
        # query extension path and derive data path
        manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = Path(manager.get_extension_path(ext_id))
        data_path = ext_path.joinpath("data")
        
        # store extension info in Carbonite
        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/_ext_id", str(ext_id))
        settings.set("exts/omni.usd.nucleus.organizer/_ext_path", str(ext_path))
        settings.set("exts/omni.usd.nucleus.organizer/_data_path", str(data_path))

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                USDNucleusOrganizerExtension.MENU_PATH, on_click=self.show_window, toggle=True, value=True
            )
            
        self.show_window(None, True)
        
    async def test(self):
        await omni.kit.app.get_app().next_update_async()
        ui.Workspace.show_window(USDNucleusOrganizerExtension.MENU_PATH)
    
    def on_shutdown(self):
        global _global_instance
        _global_instance = None
        
        if self._menu:
            self._menu = None
        
        if self._window:
            self._window.destroy()
            self._window = None
        
        # Deregister the function that shows the window from omni.ui
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.WINDOW_NAME, None)

    async def _destroy_window_async(self, visible):
        # wait one frame, this is due to the one frame defer in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()
        
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(USDNucleusOrganizerExtension.MENU_PATH, visible)
            
        if self._window:
            self._window.destroy()
            self._window = None

    def _visibility_changed_fn(self, visible):
        carb.log_warn(f'{visible} visible')
        # Called when the user pressed "X"
        # Set the checkmark in the menu that shows whether this window is visible or not
        if not visible:
            # Destroy the window, since we are creating new window in show_window
            asyncio.ensure_future(self._destroy_window_async(visible))

    def show_window(self, _menu_path, show: bool):
        carb.log_warn(f'{show} show')
        # _menu_path is argument set automatically by EditorMenu functionalities
        # show is true if the window should be shown. set automatically by our registered callback function
        if show:
            self._window = USDNucleusOrganizerWindow(USDNucleusOrganizerExtension.WINDOW_NAME, width=200, height=200)
            self._window.set_visibility_changed_fn(self._visibility_changed_fn)
        elif self._window:
            self._window.visible = False
            
    @staticmethod
    def get_instance():
        global _global_instance
        return _global_instance
