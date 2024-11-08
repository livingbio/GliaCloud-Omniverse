import omni.ext
import omni.ui as ui
import omni.kit.ui

import carb
import asyncio
from functools import partial

from .window import USDNucleusOrganizerWindow
from .asset_import import CustomAssetImporter
import omni.kit.tool.asset_importer

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class USDNucleusOrganizerExtension(omni.ext.IExt):
    WINDOW_NAME = "USD Nucleus Organizer"
    MENU_PATH = f"Window/GliaCloud Custom/{WINDOW_NAME}"

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    # TODO: ext_id store somewhere
    # TODO: better comments & make sure functions are all named properly with _
    def on_startup(self, ext_id):
        carb.log_info("Extension startup")

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                USDNucleusOrganizerExtension.MENU_PATH, self.show_window, toggle=True, value=True
            )
            
        # register objects
        self._custom_importer = CustomAssetImporter()
        omni.kit.tool.asset_importer.register_importer(self._custom_importer)
        
        

        ui.Workspace.show_window(USDNucleusOrganizerExtension.WINDOW_NAME)
        
    def on_shutdown(self):
        self._menu = None
        if self._window:
            self._window.destroy()
            self._window = None

        # Deregister the function that shows the window from omni.ui
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.WINDOW_NAME, None)

    def _set_menu(self, value):
        """Set the menu to create this window on and off"""
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(USDNucleusOrganizerExtension.MENU_PATH, value)

    async def _destroy_window_async(self):
        # wait one frame, this is due to the one frame defer
        # in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _visiblity_changed_fn(self, visible):
        # Called when the user pressed "X"
        self._set_menu(visible)
        if not visible:
            # Destroy the window, since we are creating new window
            # in show_window
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, menu, value):
        # value is true if the window should be shown. set automatically by our registered callback function
        if value:
            self._window = USDNucleusOrganizerWindow(USDNucleusOrganizerExtension.WINDOW_NAME, width=300, height=300)
            
            # handles change in visibility of window gracefully
            self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False
