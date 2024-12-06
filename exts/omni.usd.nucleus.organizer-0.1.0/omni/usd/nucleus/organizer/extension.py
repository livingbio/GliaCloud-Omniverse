import omni.ext
import omni.ui as ui
import omni.usd
import omni.kit.app

import carb
import asyncio

from .window import USDNucleusOrganizerWindow

__global_instance = None


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class USDNucleusOrganizerExtension(omni.ext.IExt):
    EXTENSION_NAME = "USD Nucleus Organizer"
    MENU_PATH = "Window/GliaCloud Custom"

    def on_startup(self, ext_id):
        # PRE-STARTUP
        carb.log_warn(f'{USDNucleusOrganizerExtension.EXTENSION_NAME} extension starting')

        global __global_instance
        __global_instance = self

        # CLASS MEMBERS
        self._window = None

        # SUBSCRIPTIONS AND REGISTRATIONS
        # Registers extension id in Carbonite
        _settings = carb.settings.get_settings()
        _settings.set("exts/omni.usd.nucleus.organizer/ext_id", str(ext_id))

        # Registers the callback to create our window in omni.ui. Useful for if we want to use QuickLayout.
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.EXTENSION_NAME, self.__ui_workspace_callback)

        # Subscribes extension to stage events
        self._stage_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop(self._on_stage_event, name=USDNucleusOrganizerExtension.EXTENSION_NAME)
        )

        # OPERATIONS
        # initialize window
        self.initialize_window()

    def on_shutdown(self):
        global __global_instance
        __global_instance = None

        # Deregister the function that shows the window from omni.ui
        ui.Workspace.set_show_window_fn(USDNucleusOrganizerExtension.EXTENSION_NAME, None)

        self._stage_sub.unsubscribe()

        self.destroy_window()

    def __ui_workspace_callback(self, value: bool):
        if value and not self._window:
            self.initialize_window()
        else:
            self._window.change_visibility(self._window.menu_path, visible=value)

    async def _close_and_reopen_window(self):
        self.destroy_window()

        await omni.kit.app.get_app().next_update_async()

        self.initialize_window()

    def _on_stage_event(self, e: carb.events.IEvent):
        if e.type == int(omni.usd.StageEventType.CLOSING):
            asyncio.ensure_future(self._close_and_reopen_window())

    def destroy_window(self):
        if self._window:
            self._window.destroy()
            self._window = None

    def initialize_window(self):
        # initialize window
        self.window = USDNucleusOrganizerWindow(
            USDNucleusOrganizerExtension.EXTENSION_NAME, USDNucleusOrganizerExtension.MENU_PATH
        )

    @staticmethod
    def get_instance():
        # Other extensions can retrieve this extension's instance during runtime.
        global __global_instance
        return __global_instance
