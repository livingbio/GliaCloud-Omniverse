from omni import ui
from omni.kit.browser.core import DetailItem
from omni.kit.browser.folder.core import FolderDetailDelegate
from .model import ReshadeBrowserModel, ReshadeDetailItem
import webbrowser
import asyncio
from typing import Optional
from pathlib import Path
import carb.settings
# from typing import Optional

CURRENT_PATH = Path(__file__).parent
ICON_PATH = CURRENT_PATH.parent.parent.parent.parent.joinpath("icons")
__DEBUG_MENU__ = False


class ReshadeDetailDelegate(FolderDetailDelegate):
    """
    Delegate to show reshade item in detail view
    Args:
        model (ReshadeBrowserModel): Reshade browser model
    """

    def __init__(self, model: ReshadeBrowserModel):
        super().__init__(model)
        self._action_item: ReshadeDetailItem = None
        self._context_menu: ui.Menu = None

    def destory(self) -> None:
        self._context_menu = None
        super().destroy()

    def get_thumbnail(self, item: ReshadeDetailItem) -> Optional[str]:
        """Get default thumbnail if none found"""
        if item.thumbnail is None:
            """Can't publish dotfolders with the extension; so instead of "/.thumbs/"
            so, let's put manually created thumbnails into /thumbs/, and,
            if such thumbnail exists, return its url"""
            preset_ini_name = "".join(item.file.url.split("/")[-1:])
            preset_folder = "/".join(item.file.url.split("/")[:-1])
            static_thumb_url = preset_folder + "/thumbs" + "/256x256/" + preset_ini_name + ".png"
            if Path(static_thumb_url).exists():
                return static_thumb_url
            else:
                return f"{ICON_PATH}/reshade_preset.png"
        else:
            return item.thumbnail

    def on_right_click(self, item: ReshadeDetailItem) -> None:
        """Reshade browser context menu"""
        self._action_item = item
        # Show context menu to apply sky
        if self._context_menu is None:
            self._context_menu = ui.Menu("Reshade context menu", name="this")
            with self._context_menu:
                ui.MenuItem("Apply preset", triggered_fn=self._apply_preset)
                ui.MenuItem("Edit this preset", triggered_fn=self._edit_preset)
                ui.MenuItem("Disable Reshade", triggered_fn=self._disable_reshade)
                

                if __DEBUG_MENU__:
                    ui.MenuItem("Make thumbnail", triggered_fn=self._make_thumbnail)

                # TODO: temp disabled since thumbnail generation does not work now.
                # ui.MenuItem("Generate thumbnail", triggered_fn=self._on_generate_thumbnail)
        self._context_menu.show()

    def _apply_preset(self) -> None:
        self._model.execute(self._action_item)
    
    def _disable_reshade(self) -> None:
        self._model.disable_reshade()

    def _edit_preset(self) -> None:
        webbrowser.open(self._action_item.url)




    def _make_thumbnail(self) -> None:

        asyncio.ensure_future(self._model._save_thumbnail(self._action_item.url))

        self.item_changed(None, self._action_item)

    def _on_generate_thumbnail(self) -> None:
        # TODO: generate thumbnail for self._action_item
        # If done, call self._model.folder_changed(self._action_item.file) to update UI
        pass
