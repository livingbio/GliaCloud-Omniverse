from omni.kit.browser.core import OptionMenuDescription
from omni.kit.browser.folder.core import FolderBrowserModel, FolderOptionsMenu
import omni.client
import carb.settings
from .delegate import ReshadeDetailDelegate
import asyncio


class ReshadeOptionsMenu(FolderOptionsMenu):
    """
    Represent options menu used in material browser. 
    Args:
        delegate (ReshadeDetailDelegate): Detail delegate used in the window. 
    """

    def __init__(self, delegate: ReshadeDetailDelegate):
        self._delegate = delegate
        super().__init__(None)
        self._url=""
        self.append_menu_item(
            OptionMenuDescription(
                "Update Collection",
                clicked_fn=self._on_update,
                #enabled_fn=self._is_category_thumbnail_enabled,
            )
        )


    def _on_update(self) -> None:
        collection = self._browser_widget.collection_selection
        asyncio.ensure_future(collection.folder.start_traverse())
        self._browser_widget.model.folder_changed(collection.folder)

