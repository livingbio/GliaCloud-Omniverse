import asyncio
import os
import shutil
from typing import Optional, Tuple
import carb

import omni.kit.actions.core
import omni.kit.app
import omni.usd
from omni.kit.viewport.utility import get_active_viewport

def get_extension_name() -> str:
    """
    Return the name of the Extension where the module is defined.

    Args:
        None

    Returns:
        str: The name of the Extension where the module is defined.

    """
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    # TODO: change this if I change extension's name
    extension_id = extension_manager.get_extension_id_by_module(__name__)
    extension_name = extension_id.split("-")[0]
    return extension_name


def get_setting_service_path() -> str:
    extension_name = get_extension_name()
    settings = carb.settings.get_settings()
    return settings.get_as_string(f"exts/{extension_name}/service_path")


def get_setting_service_resource_subpath() -> str:
    extension_name = get_extension_name()
    settings = carb.settings.get_settings()
    return settings.get_as_string(f"exts/{extension_name}/service_resource_subpath")


def get_full_resource_path() -> str:
    """
    Returns the formatted join of the 'service_path' setting and the 'service_resource_subpath' setting, like so: 
    f'{service_path}{service_resource_subpath}'

    Args:
        None

    Returns:
        str: A path that is denoted by the 'service_path' setting and the 'service_resource_subpath' setting.
    """

    _service_path = get_setting_service_path()
    _service_resource_subpath = get_setting_service_resource_subpath()
    return f'{_service_path}{_service_resource_subpath}'


def get_local_resource_directory() -> str:
    """
    Returns the location on the server where resources will be stored and the web server will register a mount. 
    In order to avoid growing the size of this static folder indefinitely, 
    images will be stored under the '${temp}' folder of the running USD Composer application instance, which is then
    emptied when the instance is shut down.

    Args:
        None

    Returns:
        str: The local path to the directory that contains the captured images.

    """
    
    _resource_path = get_full_resource_path().lstrip("/")
    temp_kit_directory = carb.tokens.get_tokens_interface().resolve("${temp}")
    _local_resource_directory = os.path.join(temp_kit_directory, _resource_path).replace(os.sep, "/")

    carb.log_warn(f'The local resource directory is {_local_resource_directory}')
    return _local_resource_directory

# This is the main utility method of our collection so far. This small helper builds on the existing capability of the
# "Edit > Capture Screenshot" feature already available in the menu to capture an image from the Omniverse application
# currently running. Upon completion, the captured image is moved to the storage location that is mapped to a
# web-accessible path so that clients are able to retrieve the screenshot once they are informed of the image's unique
# name when our Service issues its response.
async def capture_viewport(usd_stage_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Capture the viewport, by executing the action already registered in the "Edit > Capture Screenshot" menu.

    Args:
        usd_stage_path (str): Path of the USD stage to open in the application's viewport.

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: A tuple containing a flag indicating the success of the operation,
            the path of the captured image on the web server, along with an optional error message in case of error.

    """
    success: bool = omni.usd.get_context().open_stage(usd_stage_path)
    output_url_path: Optional[str] = None
    error_message: Optional[str] = None

    if success:
        _viewport = get_active_viewport()

        if _viewport.frame_info.get('viewport_handle', None) is None:
            error_message = "Viewport has not loaded yet."
            success = False
        else:
            event = asyncio.Event()

            menu_action_is_success: bool = False
            _default_output_filepath: Optional[str] = None

            def callback(success: bool, filepath: str) -> None:
                nonlocal menu_action_is_success, _default_output_filepath
                menu_action_is_success = success
                _default_output_filepath = filepath

                event.set()

            omni.kit.actions.core.execute_action("omni.kit.menu.edit", "capture_screenshot", callback)
            await event.wait()
            await asyncio.sleep(delay=1.0)

            if menu_action_is_success:
                # Move the screenshot to the location from where it can be served over the network:
                _filename = os.path.basename(_default_output_filepath)
                _local_resource_directory = get_local_resource_directory()
                _destination_filepath = os.path.join(_local_resource_directory, _filename).replace(os.sep, "/")

                if not os.path.exists(_local_resource_directory):
                    os.makedirs(_local_resource_directory)

                try:
                    shutil.move(src=_default_output_filepath, dst=_destination_filepath)
                    # Record the url path where the captured image will be served from
                    output_url_path = os.path.join(get_full_resource_path(), _filename).replace(os.sep, "/")
                    success = menu_action_is_success
                except OSError as err:
                    error_message = f'Error occurred when moving file: {err}'
                    success = False

    else:
        error_message = f'Unable to open stage "{usd_stage_path}".'

    return (success, output_url_path, error_message)
