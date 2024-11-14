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
                         item_filter_fn=lambda item: self.filter_files(item),
                         click_apply_handler=self.submit_clicked,
                         click_cancel_handler=lambda _fn, _dn: self.hide()
                         )
        
    def filter_files(self, item: FileBrowserItem) -> bool:
        if not item or item.is_folder:
            return True
        
        def _match_ext_to_filter(filter: str, item: FileBrowserItem) -> bool:
            _root, ext = os.path.splitext(item.path)
            if ext.lower() == filter[1::]:
                return True
            else:
                return False
        
        curr_selected_filter = self.get_file_extension()
        
        if curr_selected_filter == "All Supported Formats":
            # show all supported formats
            all_options = self.get_file_extension_options()[1::]
            all_filters = [filter for filter, _desc in all_options]
            
            return any(_match_ext_to_filter(f, item) for f in all_filters)
        else:
            # show only selected format
            return _match_ext_to_filter(curr_selected_filter, item)
                
    def submit_clicked(self, filename: str, dirname: str) -> None:
        self.hide()
        
        dirname = dirname.strip()
        if dirname and not dirname.endswith("/"):
            dirname += "/"
        fullpath = f"{dirname}{filename}"
        carb.log_warn(f"Opened file '{fullpath}'.")
        
    
    