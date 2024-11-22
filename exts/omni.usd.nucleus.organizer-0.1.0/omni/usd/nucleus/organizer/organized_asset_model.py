import omni.ui as ui
import omni.kit.tool.asset_importer as ai
import omni.asset_validator.core as av
from pxr import Usd
import omni.kit.app as app

from typing import List
import carb
import os
import asyncio

from .asset_validate import RotationChecker
    
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
        options_manager._meters_as_world_unit_checkbox = OrganizedAssetModel.set_checkbox_value(False) # not default
        options_manager._create_world_as_default_root_prim_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        options_manager._merge_all_meshes_checkbox = OrganizedAssetModel.set_checkbox_value(False)
        options_manager._rotation_checkbox = OrganizedAssetModel.set_checkbox_value(True)
        
    
    def __init__(self, input_path: str, _engine: av.ValidationEngine):
        self._input_path = input_path
        self._output_path = ""
        self._engine = _engine
        
    async def apply_conversion(self):
        importer = ai.AssetImporterExtension.get_instance()
        built_in_options_manager = importer._importers_manager._builtin_importer._options_builder
        
        OrganizedAssetModel.set_converter_options(built_in_options_manager)

        settings = carb.settings.get_settings()
        default_settings_path = settings.get_as_string("/exts/omni.kit.tool.asset_importer/appSettings")
        directory_ori = settings.get_as_string(f"{default_settings_path}/directory")
        settings.set(f"{default_settings_path}/directory", "C:/Users/gliacloud/Documents/Omniverse-Projects/usd-nucleus-organizer/exts/omni.usd.nucleus.organizer-0.1.0/data")
        
        all_asset_paths = [self._input_path]

        importer._on_icon_menu_click([False, False])
        await app.get_app().next_update_async()
        await app.get_app().next_update_async()
        importer._converter_file_picker._on_file_open(all_asset_paths)
        await asyncio.sleep(5.0)
        importer._converter_file_picker.destroy()
        
        directory = settings.get_as_string(f"{default_settings_path}/directory")
        settings.set(f"{default_settings_path}/directory", directory_ori)
        
        carb.log_warn("Directory: " + str(directory))
        
    def apply_standardization(self):
        
        carb.log_warn(self._output_path)
        
        self._engine.enableRule(RotationChecker)
        
        _asset_stage = Usd.Stage.Open(self._output_path)
        
        results = self._engine.validate(_asset_stage)
        
        fixer = av.IssueFixer(asset=_asset_stage)
        fix_result = fixer.fix(results.issues())
        
        fixer.save()
        _asset_stage = None
        
        carb.log_warn(fix_result)
        
        
        
    
    def _set_output_path_callback(self, file_paths: List[str]):
        root, _ext = os.path.splitext(file_paths[0])
        self._output_path = root + ".usd"
        
        carb.log_warn(f'Output path has been set to {self._output_path}')
        
        
        
        