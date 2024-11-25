from typing import Optional, List
import os
import asyncio
import carb.settings
import omni.kit.commands
import omni.kit.undo
import omni.usd
from omni.kit.browser.folder.core import FolderBrowserModel, FileDetailItem, BrowserFile
from PIL import Image

SETTING_COLLECTION_ROOTS = "/exts/omni.kit.browser.reshade/presets"


class PresetType:
    INI = "ini"


class ReshadeDetailItem(FileDetailItem):
    """
    Represent reshade detail item
    Args:
        file (BrowserFile): BrowserFile object to create detail item
        type (PresetTupe): Reshade Preset ini.
    """

    def __init__(self, file: BrowserFile, type: PresetType):
        dirs = file.url.split("/")
        name = dirs[-1]
        super().__init__(name, file.url, file, file.thumbnail)
        self.type = type


class ReshadeBrowserModel(FolderBrowserModel):
    """
    Represent reshade browser model.
    Please reference FolderBrowserModel for args and keyword args.
    """

    def __init__(self, ext_folder, **kwargs):
        super().__init__(setting_folders=SETTING_COLLECTION_ROOTS, **kwargs)        
        self._ext_folder=ext_folder


        

    def destroy(self):
        super().destroy()

    def create_detail_item(self, file: BrowserFile) -> ReshadeDetailItem:
        if file.url.lower().endswith(".ini"):
            type = PresetType.INI
        return ReshadeDetailItem(file, type)
    
    def disable_reshade(self) ->None:
        s = carb.settings.get_settings()
        s.set("/rtx/reshade/enable", False)


    def execute(self, item: ReshadeDetailItem) -> None:
        fp = os.path.normpath(item.url).replace("\\", "/")  # preset is a full path to ini file
               
        fx_path=self._ext_folder + "/presets/fx/"
        s = carb.settings.get_settings()
        s.set("/rtx/reshade/presetFilePath", fp)
        s.set("/rtx/reshade/effectSearchDirPath", fx_path)
        s.set("/rtx/reshade/textureSearchDirPath", fx_path)
        s.set("/rtx/reshade/enable", True)

    # def capture_frame(self, frame_path):
    #     _renderer = omni.renderer_capture.acquire_renderer_capture_interface()
    #     _viewport_interface = omni.kit.viewport.acquire_viewport_interface()
    #     viewport_ldr_rp = _viewport_interface.get_viewport_window(None).get_drawable_ldr_resource()
    #     _renderer.capture_next_frame_rp_resource(frame_path, viewpo t_ldr_rp)

    async def _save_thumbnail(self, preset):
        source_path = os.path.dirname(preset) + "/temp.png"
        carb.log_warn(source_path)
        # source_path = "w:/temp.png"
        self.capture_frame(source_path)
        await asyncio.sleep(0.5)
        await omni.kit.app.get_app().next_update_async()

        img = Image.open(source_path)
        # new_image = img.crop((720, 720))
        boxsize = (720, 720)
        box = (
            int((img.size[0] - boxsize[0]) / 2),
            int((img.size[1] - boxsize[1]) / 2),
            int((img.size[0] + boxsize[0]) / 2),
            int((img.size[1] + boxsize[1]) / 2),
        )
        new_image = img.crop(box)
        new_image = new_image.resize((256, 256))

        def ensure_dir(file_path):
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

        preset_name = os.path.basename(preset)
        thumbs_dir = os.path.dirname(preset)
        thumbs_dir = os.path.join(thumbs_dir, ".thumbs/256x256/")
        ensure_dir(thumbs_dir)
        new_image.save(os.path.join(thumbs_dir, preset_name + ".png"))

    async def _save_thumbnails_dir(self, folder):
        await omni.kit.app.get_app().next_update_async()
        counter = 0
        for preset in self.presets_dict[folder]:
            if counter < 19:
                counter += 1
            else:
                s = carb.settings.get_settings()
                fp = preset.replace("\\", "/")
                sd = os.path.dirname(preset)
                # s.set("/rtx/reshade/presetFilePath", fp)
                # s.set("/rtx/reshade/enable", False)
                # await omni.kit.app.get_app().next_update_async()
                # await asyncio.sleep(1.0)
                s.set("/rtx/reshade/presetFilePath", fp)
                s.set("/rtx/reshade/effectSearchDirPath", sd)
                s.set("/rtx/reshade/textureSearchDirPath", sd)
                s.set("/rtx/reshade/enable", True)

                await asyncio.sleep(1.0)
                await omni.kit.app.get_app().next_update_async()
                asyncio.ensure_future(self._save_thumbnail(preset))
                await omni.kit.app.get_app().next_update_async()
                await asyncio.sleep(2.0)
                await omni.kit.app.get_app().next_update_async()

            # print(preset)
