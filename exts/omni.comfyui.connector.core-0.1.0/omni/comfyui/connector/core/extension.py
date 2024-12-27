import omni.ext
import omni.ui as ui
import omni.kit.ui
from omni.services.core import main

import carb
import os
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .services.viewport_capture import router as capture_router
from .services.viewport_record import router as record_router
from .ext_utils import join_with_replace

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
    COMFY_WINDOWS_PATH = "C:/Users/gliacloud/Documents/ComfyUI_windows_portable/ComfyUI"
    COMFY_PYTHON_WINDOWS_PATH = "C:/Users/gliacloud/Documents/ComfyUI_windows_portable/python_embeded/python.exe"

    def on_startup(self, ext_id):
        carb.log_warn("Extension started")
        global _global_instance
        _global_instance = self

        # TODO: Add UI field & button to optionally start ComfyUI web server from within Omniverse.
        self.comfy_path = ComfyUIConnectorExtension.COMFY_WINDOWS_PATH
        self.comfy_python_path = ComfyUIConnectorExtension.COMFY_PYTHON_WINDOWS_PATH

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

        self._link_comfy()

    def on_shutdown(self):
        global _global_instance
        _global_instance = None

        self._unlink_comfy()

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

        carb.log_warn("Extension shut down.")

    def _link_comfy(self):
        carb.log_info("Linking custom Omniverse nodes to ComfyUI")
        _comfy_custom_node_path = join_with_replace(self.comfy_path, "custom_nodes/omni_nodes.py")

        if os.path.isfile(_comfy_custom_node_path):
            os.unlink(_comfy_custom_node_path)

        os.symlink(ComfyUIConnectorExtension.COMFY_NODES_FILE_PATH, _comfy_custom_node_path)

    def _unlink_comfy(self):
        _comfy_custom_node_path = join_with_replace(self.comfy_path, "custom_nodes/omni_nodes.py")

        if os.path.isfile(_comfy_custom_node_path):
            os.unlink(_comfy_custom_node_path)
        carb.log_info("Unlinked ComfyUI")

    @staticmethod
    def get_instance():
        global _global_instance
        return _global_instance
