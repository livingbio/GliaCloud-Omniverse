import omni.ui as ui

from omni.kit.asset_converter import AssetConverterContext
import omni.kit.tool.asset_importer as ai

from typing import List, Union, Dict
import os


class CustomBuiltInImporterDelegate(ai.BuiltInImporterDelegate):

    def __init__(self, orig_delegate: ai.BuiltInImporterDelegate) -> None:
        super().__init__(
            orig_delegate._options_builder._usd_context,
            orig_delegate._builtin_importer,
            orig_delegate.__filter_regexes__,
            orig_delegate.__fiter_descriptions__,
        )

        self._name = "GliaCloud Customized Delegate for Built-in Importer"

    async def convert_assets(self, paths: List[str], customized=False, **kargs) -> Dict[str, Union[str, None]]:
        export_folder = kargs["export_folder"] if "export_folder" in kargs else ""

        absolute_paths = []
        relative_paths = []
        for file_path in paths:
            if self.is_supported_format(file_path):
                absolute_paths.append(file_path)
                filename = os.path.basename(file_path)
                relative_paths.append(filename)

        converter_context = AssetConverterContext()
        converter_context.ignore_light = True
        converter_context.use_meter_as_world_unit = True
        converter_context.convert_fbx_to_z_up = True

        converted_assets = await self._builtin_importer.create_import_task(
            True, absolute_paths, relative_paths, export_folder, converter_context.asset_import_context
        )

        return converted_assets
