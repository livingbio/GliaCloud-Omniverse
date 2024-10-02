import carb.settings
import asyncio
from omni import ui
from .delegate import ReshadeDetailDelegate
from .model import ReshadeBrowserModel
from omni.kit.browser.folder.core import FolderBrowserWidget

import omni.ext
from omni.kit.menu.utils import MenuItemDescription
from .options_menu import ReshadeOptionsMenu

from typing import Union

SETTING_ROOT = "/exts/omni.kit.browser.reshade/"
SETTING_MAX_THUMBNAIL_SIZE = SETTING_ROOT + "max_thumbnail_size"
SETTING_MIN_THUMBNAIL_SIZE = SETTING_ROOT + "min_thumbnail_size"


class ReshadeBrowserWindow(ui.Window):
    """
    Represent a window to show skies.
    """

    def __init__(self, ext_id):
        super().__init__("Reshade", width=500, height=600)

        self.frame.set_build_fn(self._build_ui)
        self.deferred_dock_in("Console", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)
        self._extension_folder=omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._local_presets_folder = self._extension_folder+"/presets/"

    def _build_ui(self):
        settings = carb.settings.get_settings()
        min_thumbnail_size = settings.get(SETTING_MIN_THUMBNAIL_SIZE)
        max_thumbnail_size = settings.get(SETTING_MAX_THUMBNAIL_SIZE)
        self._browser_model = ReshadeBrowserModel(self._extension_folder, 
            filter_file_suffixes=[".ini"], ignore_folder_names=[""], show_empty_folders=False
        )

        
        
        self._delegate = ReshadeDetailDelegate(self._browser_model)
        self._options_menu = ReshadeOptionsMenu(self._delegate)
        self._options_menu._url = self._local_presets_folder

        with self.frame:
            self._widget = FolderBrowserWidget(
                self._browser_model,
                options_menu=self._options_menu,
                detail_delegate=self._delegate,
                min_thumbnail_size=min_thumbnail_size,
                max_thumbnail_size=max_thumbnail_size,
            )
        self.reload_local_presets()

    def reload_local_presets(self):
        url = self._local_presets_folder
        result = self._browser_model.append_root_folder(url)
        if result:            
            self._browser_model.folder_changed(None)
            collection_items = self._browser_model.get_collection_items()
            collection = collection_items[0]
            asyncio.ensure_future(collection.folder.start_traverse())

