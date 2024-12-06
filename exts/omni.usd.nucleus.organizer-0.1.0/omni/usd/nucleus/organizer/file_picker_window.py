from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem

import carb
import os

from typing import Callable, Type
from functools import partial


class CustomFilePickerWindow(FilePickerDialog):
    EXTENSION_OPTIONS = [
        ("All Supported Formats", "*.fbx, *.obj, ..."),
        ("*.fbx", "FBX Format"),
        ("*.obj", "OBJ Format"),
        ("*.glb", "glb Format"),
        ("*.gltf", "glTF Format"),
        ("*.usd", "USD Format"),
        ("*.usda", "USDA (human-readable) Format"),
        ("*.usdc", "USDC (binary) Format"),
        ("*.usdz", "USDZ (compressed) Format"),
    ]

    def __init__(self, title: str, external_callback: Callable = lambda f, d: None):
        super().__init__(
            title,
            file_extension_options=CustomFilePickerWindow.EXTENSION_OPTIONS,
            item_filter_fn=lambda item: self._filter_out_files(item),
            click_cancel_handler=lambda _fn, _dn: self.hide(),
            apply_button_label="Submit",
        )

        self._set_click_apply_handler_internal(external_callback)

        self.hide()

    def _match_item_path_to_filter(self, item_path: str) -> bool:
        def _match_helper(filter: str, path: str) -> bool:
            _root, ext = os.path.splitext(path)
            if ext.lower() == filter[1::]:
                return True
            else:
                return False

        curr_selected_filter = self.get_file_extension()

        if curr_selected_filter == "All Supported Formats":
            # show all supported formats
            all_options = self.get_file_extension_options()[1::]
            all_filters = [filter for filter, _desc in all_options]

            return any(_match_helper(f, item_path) for f in all_filters)
        else:
            # show only selected format
            return CustomFilePickerWindow._match_helper(curr_selected_filter, item_path)

    def _filter_out_files(self, item: FileBrowserItem) -> bool:
        if not item or item.is_folder:
            return True

        return self._match_item_path_to_filter(item.path)

    def _click_apply_handler_internal(self, external_callback: Callable, file_name: str, dir_name: str) -> None:

        if not file_name or file_name == "":
            carb.log_warn("Select a valid file!")
            return

        self.hide()

        external_callback(file_name, dir_name)

    def _set_click_apply_handler_internal(self, external_callback: Callable) -> None:
        self.set_click_apply_handler(partial(self._click_apply_handler_internal, external_callback))
