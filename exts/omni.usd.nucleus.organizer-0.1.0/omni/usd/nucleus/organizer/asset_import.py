import omni.kit.tool.asset_importer as ai
import omni.ui as ui
import omni.kit.app
import omni.kit.asset_converter as asset_converter


import asyncio
import carb
from typing import List, Union, Dict
from pathlib import Path

def progress_callback(current_step: int, total: int):
    # Show progress
    print(f"{current_step} of {total}")

async def convert(input_asset_path, output_asset_path):
    context = asset_converter.AssetConverterContext()
    context.ignore_light = True
    context.use_meter_as_world_unit = True
    
    task_manager = asset_converter.get_instance()
    task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback, context)
    success = await task.wait_until_finished()
    if not success:
        carb.log_error(task.get_status())
        carb.log_error(task.get_error_message())
    
    

# TODO: determine how OBJs, etc are handled
#   uses client from omni.kit.asset_converter extension

class CustomAssetImporter(ai.AbstractImporterDelegate):

    def __init__(self) -> None:
        self._name = "GliaCloud Asset Importer"
        
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
        with ui.VStack(height=0):

            with ui.HStack(width=0, spacing=15):
                ui.CheckBox(enabled=False).model.set_value(True)
                ui.Label("Z-Up")
                
            ui.Spacer(height=5)
                
            with ui.HStack(width=0, spacing=15):
                ui.CheckBox(enabled=False).model.set_value(True)
                ui.Label("Stage Units in Meters")
                
            ui.Spacer(height=15)
            
            data_path = Path(carb.settings.get_settings().get("exts/omni.usd.nucleus.organizer/curr_data_path"))
            input_path = str(data_path.joinpath("floor_lamp_1.fbx"))
            output_path = str(data_path.joinpath("output_floor_lamp_1.usd"))

    
            ui.Button("Submit", width=ui.Percent(0.5), clicked_fn=lambda: asyncio.ensure_future(convert(input_path, output_path)))
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
        converted_assets = {}

