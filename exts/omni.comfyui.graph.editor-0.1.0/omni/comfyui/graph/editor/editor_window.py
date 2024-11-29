__all__ = ["ComfyUIWindow"]

import omni.ui as ui
import omni.kit.app

import asyncio

from .graph_widget import GraphWidget


class ComfyUIWindow(ui.Window):
    """The Graph window"""

    def __init__(self, title, **kwargs):
        flags = kwargs.pop("flags", 0) | ui.WINDOW_FLAGS_NO_SCROLLBAR

        self._main_widget = None
        super().__init__(title, flags=flags, **kwargs)

        self.frame.set_build_fn(self.on_build_window)

        self.deferred_dock_in("Viewport")
        # make sure the window is docked when viewport doesn't exist
        self._build_task = asyncio.ensure_future(self.__dock_window())

    async def __dock_window(self):
        await omni.kit.app.get_app().next_update_async()
        viewport = ui.Workspace.get_window("Viewport")
        if not viewport:
            window_handle = ui.Workspace.get_window(self.title)
            main_dockspace = ui.Workspace.get_window("DockSpace")
            window_handle.dock_in(main_dockspace, ui.DockPosition.BOTTOM)

    def destroy(self):
        if self._main_widget:
            self._main_widget.destroy()
        self._main_widget = None

        super().destroy()

    def on_build_window(self):
        self._main_widget = GraphWidget()
