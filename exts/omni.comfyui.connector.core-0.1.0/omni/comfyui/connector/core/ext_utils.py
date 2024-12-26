import omni.kit.app
import omni.kit.actions.core
import omni.usd
import omni.kit.viewport.utility
import omni.kit.capture.viewport

import os
import shutil
from typing import Optional, Tuple
import carb


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
    return f"{_service_path}{_service_resource_subpath}"


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

    return _local_resource_directory


def get_extension_data_path() -> str:
    manager = omni.kit.app.get_app().get_extension_manager()
    settings = carb.settings.get_settings()
    ext_id = settings.get_as_string("exts/omni.comfyui.connector.core/ext_id")
    ext_path = manager.get_extension_path(ext_id)
    return os.path.join(ext_path, "data")


# This is the main utility method of our collection so far. This small helper builds on the existing capability of the
# "Edit > Capture Screenshot" feature already available in the menu to capture an image from the Omniverse application
# currently running. Upon completion, the captured image is moved to the storage location that is mapped to a
# web-accessible path so that clients are able to retrieve the screenshot once they are informed of the image's unique
# name when our Service issues its response.
async def capture_viewport(response) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Capture the viewport, by executing the action already registered in the "Edit > Capture Screenshot" menu.

    Args:
        usd_stage_path (str): Path of the USD stage to open in the application's viewport.

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: A tuple containing a flag indicating the success of the operation,
            the path of the captured image on the web server, along with an optional error message in case of error.

    """

    success: bool = False
    output_url_path: Optional[str] = None
    details_message: Optional[str] = None

    while True:
        if not omni.usd.get_context().get_stage():
            details_message = "Unable to open current USD stage."
            break

        viewport = omni.kit.viewport.utility.get_active_viewport()
        if not viewport:
            details_message = "Unable to find active viewport."
            break
        elif viewport.frame_info.get("viewport_handle", None) is None:
            details_message = "Active viewport is not currently loaded or not being rendered."
            break

        await viewport.wait_for_rendered_frames()

        _ext_data_path = get_extension_data_path()
        base_name = "screenshot.png"

        _temp_path = os.path.join(_ext_data_path, base_name).replace(os.sep, "/")

        if "jpeg" not in _temp_path and "jpg" not in _temp_path and "png" not in _temp_path:
            details_message = "Error capturing viewport screenshot: Please verify .png, .jpeg, .jpg file extension."
            break

        try:
            _helper = omni.kit.viewport.utility.capture_viewport_to_file(viewport_api=viewport, file_path=_temp_path, )
            
            # waits for viewport to be active
            await _helper.wait_for_result()
            carb.log_warn("Viewport Utility screenshot function completed successfully")
        except Exception as e:
            details_message = f"Error capturing viewport screenshot: {str(e)}"
            break

        _local_resource_directory = get_local_resource_directory()
        _destination_filepath = os.path.join(_local_resource_directory, base_name).replace(os.sep, "/")

        if not os.path.exists(_local_resource_directory):
            os.makedirs(_local_resource_directory)

        try:
            shutil.move(src=_temp_path, dst=_destination_filepath)
            # Record the url path where the captured image will be served from
            output_url_path = os.path.join(get_full_resource_path(), base_name).replace(os.sep, "/")
            success = True
            details_message = f"Screenshot available at {output_url_path} on the Omniverse App's web server"
            response.status_code = 200
        except OSError as err:
            details_message = f"Error occurred when moving file: {err}"
            break

        break

    return (success, output_url_path, details_message)

def test():
    capture_extension = omni.kit.capture.viewport.CaptureExtension.get_instance()
    capture_extension.show_default_progress_window = False
    capture_extension.forward_one_frame_fn = None
    capture_extension.options.output_folder = get_local_resource_directory()
    capture_extension.options.file_name = "sequence"
    capture_extension.options.file_type = ".mp4"
    capture_extension.options.end_frame = 80

    capture_extension.options.res_width = 1920
    capture_extension.options.res_height = 1080

    options_dict = capture_extension.options.to_dict()
    options_str = ''
    for k, v in options_dict.items():
        options_str += f'{k}: {v}\n'

    carb.log_warn(options_str)

    # capture_extension.start()

    import requests

    url = "https://api.comfy.org/publishers/mialana/nodes"

    headers = {"Authorization": "Bearer 93531bdf-e314-4a0e-b6d6-8ea0f3234723"}

    response = requests.request("GET", url, headers=headers)

    carb.log_warn(response.text)


def cancel_capture():
    capture_extension = omni.kit.capture.viewport.CaptureExtension.get_instance()
    capture_extension.progress._capture_status = omni.kit.capture.viewport.CaptureStatus.TO_START_ENCODING

def join_with_replace(path1: str, path2: str) -> str:
    return os.path.join(path1, path2).replace(os.sep, "/")
