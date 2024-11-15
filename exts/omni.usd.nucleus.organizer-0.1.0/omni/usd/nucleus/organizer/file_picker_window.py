from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.widget.filebrowser import FileBrowserItem

import carb
import os

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
      
    def __init__(self, title: str):
        super().__init__(title, 
                         file_extension_options=CustomFilePickerWindow.EXTENSION_OPTIONS,
                         item_filter_fn=lambda item: self._filter_out_files(item),
                         click_cancel_handler=lambda _fn, _dn: self.hide(),
                         apply_button_label="Submit"
                         )
        
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
        
    def _apply_handler(self, file_name: str, dir_name: str) -> None:
        # don't continue if selection is directory or nothing
        if not file_name or file_name == "":
            return
        
        self.hide()

        dir_name = dir_name.strip()
        if dir_name and not dir_name.endswith("/"):
            dir_name += "/"
        
        full_path = f"{dir_name}{file_name}"
        
        
        carb.log_warn(f'Selected file path is {self.selected_file_path}')
        
        
        
    
    