import omni.ext
import omni.ui as ui
import omni.kit.ui
from omni.services.core import main

import asyncio
from functools import partial
import carb
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .window import ComfyUIWindow
from .services.viewport_capture import router as capture_router
from .services.viewport_record import router as record_router

# For convenience, let's also reuse the utility methods we already created to handle and format the storage location of
# the captured images so they can be accessed by clients using the server, once API responses are issued from our
# Service:
from . import ext_utils

_global_instance = None


class ComfyUIConnectorExtension(omni.ext.IExt):
    """Comfy UI Connector Extension"""

    WINDOW_NAME = "ComfyUI"
    MENU_PATH = f"Window/GliaCloud Custom/{WINDOW_NAME}"

    COMFY_NODES_FILE_PATH = str(Path(__file__).parent.joinpath('omni_nodes.py'))
    COMFY_INSTALLATION_PATH = "C:/Users/gliacloud/Documents/ComfyUI_windows_portable/ComfyUI"

    def on_startup(self, ext_id):
        carb.log_warn("Extension started")
        global _global_instance
        _global_instance = self

        self._window = None
        self._menu = None

        # store extension id in Carbonite
        _settings = carb.settings.get_settings()
        _settings.set("exts/omni.comfyui.connector.core/ext_id", str(ext_id))

        # At this point, we register our Service's `router` under the path we gave our API using the settings system,
        # to facilitate its configuration and to ensure it is unique from all other extensions we may have enabled:
        _path = ext_utils.get_setting_service_path()

        main.register_router(
            router=capture_router,
            prefix=_path,
        )

        main.register_router(
            router=record_router,
            prefix=_path,
        )

        # Proceed to create a temporary directory in the USD Composer application file hierarchy where captured stage
        # images will be stored, until the application is shut down:
        _local_resource_directory = ext_utils.get_local_resource_directory()
        if not os.path.exists(_local_resource_directory):
            os.makedirs(_local_resource_directory)

        # Register this location as a mount, so its content is served by the web server bundled with the Omniverse
        # application instance, thus making the captured image available on the network:
        main.register_mount(
            path=ext_utils.get_full_resource_path(), app=StaticFiles(directory=_local_resource_directory, html=True)
        )

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(ComfyUIConnectorExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        _editor_menu = omni.kit.ui.get_editor_menu()
        if _editor_menu:
            self._menu = _editor_menu.add_item(
                ComfyUIConnectorExtension.MENU_PATH, on_click=self.show_window, toggle=True, value=True
            )

        self.show_window(None, True)

        self._startup_comfy(self.COMFY_INSTALLATION_PATH)

    def on_shutdown(self):
        global _global_instance
        _global_instance = None

        self._shutdown_comfy(self.COMFY_INSTALLATION_PATH)

        if self._menu:
            self._menu = None

        if self._window:
            self._window.destroy()
            self._window = None

        _path = ext_utils.get_setting_service_path()
        # When disabling the extension or shutting down the instance of the Omniverse application, let's make sure we
        # also deregister our Service's `router` in order to avoid our API being erroneously advertised as present as
        # part of the OpenAPI specification despite our handler function no longer being available:
        main.deregister_router(
            router=capture_router,
            prefix=_path,
        )

        main.deregister_router(
            router=record_router,
            prefix=_path,
        )

        main.deregister_mount(path=ext_utils.get_full_resource_path())

    def _startup_comfy(self, comfy_path):
        carb.log_warn("Starting Comfy")
        _comfy_custom_node_path = os.path.join(comfy_path, "custom_nodes/omni_nodes.py").replace(os.sep, "/")

        if os.path.isfile(_comfy_custom_node_path):
            os.unlink(_comfy_custom_node_path)

        os.symlink(self.COMFY_NODES_FILE_PATH, _comfy_custom_node_path)

    def _shutdown_comfy(self, comfy_path):
        _comfy_custom_node_path = os.path.join(comfy_path, "custom_nodes/omni_nodes.py").replace(os.sep, "/")

        if os.path.isfile(_comfy_custom_node_path):
            os.unlink(_comfy_custom_node_path)
        carb.log_warn("Shut down Comfy")

    def _on_menu_click(self, menu, toggled):
        self.show_window(menu, toggled)

    async def _destroy_window_async(self, visible):
        # wait one frame, this is due to the one frame defer in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(ComfyUIConnectorExtension.MENU_PATH, visible)

        if self._window:
            self._window.destroy()
            self._window = None

    def show_window(self, _menu_path, show):
        if show:
            if self._window is None:
                self._window = ComfyUIWindow(ComfyUIConnectorExtension.WINDOW_NAME)
                self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False

    def _visiblity_changed_fn(self, visible):
        # Called when the user pressed "X"
        # Set the checkmark in the menu that shows whether this window is visible or not
        if not visible:
            # Destroy the window, since we are creating new window in show_window
            asyncio.ensure_future(self._destroy_window_async(visible))

    @staticmethod
    def get_instance():
        global _global_instance
        return _global_instance
