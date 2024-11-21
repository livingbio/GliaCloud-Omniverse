import omni.ui as ui
import omni.kit.tool.asset_importer as ai

from typing import List
import carb
import os
    
class OrganizedAssetModel():
    
    @staticmethod
    def set_checkbox_value(val: bool) -> ui.CheckBox:
        checkbox = ui.CheckBox()
        checkbox.model.set_value(val)
        return checkbox
        
    
    @staticmethod
    def set_converter_options(options_manager):
        options_manager._built = False
        options_manager._export_context = options_manager.get_import_options()
        if options_manager._refresh_default_folder:
            options_manager._export_context.export_folder = options_manager._default_folder
            options_manager._default_folder = None
            options_manager._refresh_default_folder = False

        options_manager._built = True
        options_manager._mat_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._preview_surface_checkbox = OrganizedAssetModel.set_checkbox_value(False)
        options_manager._animation_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._camera_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._light_checkbox = OrganizedAssetModel.set_checkbox_value(False) # not default
        options_manager._bones_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._smooth_normals_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._meters_as_world_unit_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._create_world_as_default_root_prim_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._merge_all_meshes_checkbox = OrganizedAssetModel.set_checkbox_value(False)
        options_manager._rotation_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        
    
    def __init__(self, input_path):
        self._input_path = input_path
        self._output_path = ""
        
    def apply_conversion(self):
        asset_importer_ext = ai.AssetImporterExtension.get_instance()
        built_in_options_manager = asset_importer_ext._importers_manager._builtin_importer._options_builder
        
        OrganizedAssetModel.set_converter_options(built_in_options_manager)
        
        asset_importer_ext.add_import_complete_callback(self._set_output_path_callback)
        
        asset_importer_ext._convert_file([self._input_path])
        
    def apply_optimization(self):
        # open file
        
    
    def _set_output_path_callback(self, file_paths: List[str]):
        root, _ext = os.path.splitext(file_paths[0])
        self._output_path = root + ".usd"
        
        carb.log_warn(f'Output path has been set to {self._output_path}')
        
        
        
        