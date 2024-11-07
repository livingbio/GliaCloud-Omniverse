import omni.ext
import omni.ui as ui
import omni.kit.ui

import carb
import asyncio
from functools import partial

import omni.kit.asset_converter as converter
from .window import USDNucleusOrganizerWindow

# def progress_callback(current_step: int, total: int):
#     # Show progress
#     print(f"{current_step} of {total}")

# async def convert(input_asset_path, output_asset_path):
#     task_manager = omni.kit.asset_converter.get_instance()
#     task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
#     success = await task.wait_until_finished()
#     if not success:
#         detailed_status_code = task.get_status()
#         detailed_status_error_string = task.get_error_message()


# # Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
# def some_public_function(x: int):
#     print(f"[omni.hello.world] some_public_function was called with {x}")
#     return x ** x

# def get_extension_path(module_name: str):
#     import omni.kit.app

#     manager = omni.kit.app.get_app().get_extension_manager()
#     ext_id = manager.get_extension_id_by_module(module_name)

#     carb.log_info("Ext ID: " + str(ext_id) + " Path: " + str(manager.get_extension_path(ext_id)))


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class USDNucleusOrganizerExtension(omni.ext.IExt):
    WINDOW_NAME = "USD Nucleus Organizer"
    MENU_PATH = f"Window/GliaCloud Custom/{WINDOW_NAME}"

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self):
        carb.log_info("Extension startup")

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        # C:\Users\gliacloud\AppData\Local\ov\pkg\create-2023.2.5\extscache\omni.kit.renderer.imgui-0.0.0+ece658d9.wx64.r.cp310\omni\kit\ui\editor_menu.py
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                USDNucleusOrganizerExtension.MENU_PATH, self.show_window, toggle=True, value=True
            )

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
