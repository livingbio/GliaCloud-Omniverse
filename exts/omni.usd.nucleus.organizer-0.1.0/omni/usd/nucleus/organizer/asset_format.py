import omni.kit.tool.asset_importer as ai
import omni.ui as ui
import omni.kit.app

from typing import List, Union, Dict

# TODO: determine how OBJs, etc are handled
#   uses client from omni.kit.asset_converter extension

class CustomAssetFormatter(ai.AbstractImporterDelegate):

    def __init__(self) -> None:
        self._name = "GliaCloud Asset Formatter"
        
        # Currently allowed file formats
        self._filters = [            
            ".*\\.fbx$",
            ".*\\.obj$",
            ".*\\.gltf$",
            ".*\\.*glb$",
            ".*\\.usdc$",
            ".*\\.usda$",
        ]

        self._descriptions = [
            "FBX Files (*.fbx)",
            "OBJ Files (*.obj)",
            "glTF Files (*.gltf)",
            "glb Files (*.glb)",
            "USDA (human-readable format) Files (*.usda)",
            "USDC (binary format) Files (*.usdc)",
            "USD Files (with incorrect properties (*.usd)",
        ]

    @property
    def name(self) -> str:
        return self._name
    @property
    def filter_regexes(self) -> List[str]:
        return self._filters
    
    @property
    def filter_descriptions(self) -> List[str]:
        return self._descriptions
    
    def destroy(self) -> None:
        # TODO: edit if any objects are added to class' instance variables
        pass

    def build_options(self, paths: List[str]) -> None:
        with ui.HStack(height=0):
            ui.Spacer(width=10)
            with ui.VStack(height=0):
                ui.Label("")
                with ui.HStack(width=0, spacing=15):
                    ui.CheckBox(enabled=False).model.set_value(True)
                    ui.Label("Z-Up")
                    
                ui.Spacer(height=5)
                    
                with ui.HStack(width=0, spacing=15):
                    ui.CheckBox(enabled=False).model.set_value(True)
                    ui.Label("Set Units in Meters")
                    
                ui.Spacer(height=15)
                    
                ui.Label("Outputted USD Properties:")
                
                with ui.HStack():
                    ui.Spacer(width=15)
                    ui.Label("Dimensions (in meters): ")
                    ui.MultiFloatField(0.75, 0.75, 1.75, enabled=False)
                    
                ui.Spacer(height=15)
                
                with ui.HStack():
                    ui.Spacer(width=15)
                    ui.Label("Preview:")
                    
                

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = ext_manager.get_extension_path_by_module('omni.usd.nucleus.organizer')
        
        with ui.HStack():
            ui.Spacer(width=40)
            img = ui.Image( width=ui.Percent(85), alignment=ui.Alignment.CENTER)
            img.source_url = ext_path + "/data/temp_output_visual.png"
        return True

    async def convert_assets(self, paths: List[str]) -> Dict[str, Union[str, None]]:
        return []

