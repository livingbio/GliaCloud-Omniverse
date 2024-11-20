import omni.ui as ui
import omni.kit.tool.asset_importer as ai
from omni.kit.asset_converter import AssetConverterContext
from .asset_import import CustomBuiltInImporterDelegate

class OrganizedAssetModel():
    
    
    
    def __init__(self, input_path):    
        asset_importer_ext = ai.AssetImporterExtension.get_instance()
        
        custom_delegate = CustomBuiltInImporterDelegate(asset_importer_ext._importers_manager._builtin_importer)
        
        asset_importer_ext._convert_file([input_path])
        