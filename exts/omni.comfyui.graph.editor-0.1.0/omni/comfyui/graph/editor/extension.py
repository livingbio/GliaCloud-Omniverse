__all__ = ["ComfyUIEditorExtension"]

import omni.ext
import omni.ui as ui
import omni.kit.ui

import asyncio
from functools import partial
import carb
import os
from fastapi.staticfiles import StaticFiles

from .editor_window import ComfyUIWindow
from .node_registry_model import NodeRegistryQuickSearchModel
from .services.viewport_capture import router

# For convenience, let's also reuse the utility methods we already created to handle and format the storage location of
# the captured images so they can be accessed by clients using the server, once API responses are issued from our
# Service:
from . import ext_utils

from omni.services.core import main
from omni.kit.graph.editor.core.graph_editor_core_tree_delegate import GraphEditorCoreTreeDelegate

_global_instance = None
count = 0


class ComfyUIEditorExtension(omni.ext.IExt):
    """Comfy UI Graph Editor Extension"""

    WINDOW_NAME = "ComfyUI Graph Editor"
    MENU_PATH = f"Window/GliaCloud Custom/{WINDOW_NAME}"

    def on_startup(self, ext_id):
        global _global_instance
        _global_instance = self

        self._window = None
        self._menu = None

        # store extension id in Carbonite
        _settings = carb.settings.get_settings()
        _settings.set("exts/omni.comfyui.graph.editor/ext_id", str(ext_id))

        # At this point, we register our Service's `router` under the path we gave our API using the settings system,
        # to facilitate its configuration and to ensure it is unique from all other extensions we may have enabled:
        _path = ext_utils.get_setting_service_path()
        global count
        main.register_router(
            router=router,
            prefix=_path,
        )
        count += 1

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
        ui.Workspace.set_show_window_fn(ComfyUIEditorExtension.WINDOW_NAME, partial(self.show_window, None))

        # Adds our extension window to the application menu under MENU_PATH
        _editor_menu = omni.kit.ui.get_editor_menu()
        if _editor_menu:
            self._menu = _editor_menu.add_item(
                ComfyUIEditorExtension.MENU_PATH, on_click=self.show_window, toggle=True, value=True
            )

        self.show_window(None, True)

        # Quick Search subscription
        self._sub = None

        _app = omni.kit.app.get_app_interface()
        _ext_manager = _app.get_extension_manager()
        self.__extensions_subscription = []

        self.__extensions_subscription.append(
            _ext_manager.subscribe_to_extension_enable(
                partial(self._on_extensions_changed, True),
                partial(self._on_extensions_changed, False),
                ext_name="omni.kit.window.quicksearch",
                hook_name="omni.comfyui.graph.editor listener",
            )
        )

    def on_shutdown(self):
        global _global_instance
        _global_instance = None

        self.__extensions_subscription = None

        # deregister quick search model
        if self._sub is not None:
            del self._sub
            self._sub = None

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
            router=router,
            prefix=_path,
        )

        main.deregister_mount(path=ext_utils.get_full_resource_path())

        global count
        count = 0

    def _is_window_focused(self) -> bool:
        """Returns True if the example Graph window exists and focused"""
        return self._window and self._window.focused

    def _on_menu_click(self, menu, toggled):
        self.show_window(menu, toggled)

    async def _destroy_window_async(self, visible):
        # wait one frame, this is due to the one frame defer in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(ComfyUIEditorExtension.MENU_PATH, visible)

        if self._window:
            self._window.destroy()
            self._window = None

    def show_window(self, _menu_path, show):
        if show:
            if self._window is None:
                self._window = ComfyUIWindow(ComfyUIEditorExtension.WINDOW_NAME)
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
    def add_node(mime_data: str):
        """Adds a node to the current ComfyUI Graph window"""
        if not _global_instance:
            return

        self = _global_instance
        if not self._window:
            return

        class CustomEvent:
            def __init__(self, mime_data):
                self.mime_data = mime_data
                self.x = None
                self.y = None

        if self._window._main_widget:
            self._window._main_widget.on_drop(CustomEvent(mime_data))

    def _on_extensions_changed(self, loaded: bool, _ext_id: str):
        """Called when the Quick Search extension is loaded/unloaded"""
        if loaded:
            from omni.kit.window.quicksearch import QuickSearchRegistry

            # Register simple model in Quick Search
            self._sub = QuickSearchRegistry().register_quick_search_model(
                "Graph editor nodes",
                NodeRegistryQuickSearchModel,
                GraphEditorCoreTreeDelegate,
                accept_fn=self._is_window_focused,
                priority=0,
            )
        else:
            # Deregister simple model in Quick Search
            del self._sub
            self._sub = None

    @staticmethod
    def get_instance():
        global _global_instance
        return _global_instance
