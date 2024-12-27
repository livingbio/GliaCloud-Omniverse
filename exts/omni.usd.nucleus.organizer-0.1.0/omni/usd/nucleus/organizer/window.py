import omni.ui as ui
import omni.kit.app
import omni.kit.ui
from omni.kit.ui.editor_menu import EditorMenu

import carb
from functools import partial
import asyncio

from .file_picker_window import CustomFilePickerWindow
from .organized_asset_model import OrganizedAssetModel

import omni.asset_validator.core as av


class USDNucleusOrganizerWindow(ui.Window):
    WINDOW_STATES = ["startup", "convert", "validate", "tag", "finished", "destroyed"]

    @classmethod
    def change_window_state(cls, new_state: str = ""):
        _settings = carb.settings.get_settings()
        _settings.set("exts/omni.usd.nucleus.organizer/window_state", new_state)
        carb.log_warn(f'Window state changed to {_settings.get("exts/omni.usd.nucleus.organizer/window_state")}')

    def __init__(self, title: str, menu_path, **kwargs):
        # PRE-SETUP
        super().__init__(title, width=400, height=400, **kwargs, visible=True)
        self.deferred_dock_in("Property", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)

        self.menu_path = f"{menu_path}/{title}/Window"
        self._menu_item = None

        self.file_picker_window = CustomFilePickerWindow("Select File", self._on_file_submitted)
        self._engine = av.ValidationEngine(initRules=False)

        # CLASS MEMBERS
        self.asset_model = OrganizedAssetModel("", self._engine)

        # SUBSCRIPTIONS AND REGISTRATIONS
        self._window_state_sub = omni.kit.app.SettingChangeSubscription(
            "exts/omni.usd.nucleus.organizer/window_state", self._on_window_state_changed
        )
        self.set_visibility_changed_fn(partial(self.change_visibility, self.menu_path))

        # OPERATIONS
        # Adds a menu item to toggle visibility of this window from the application menu
        _editor_menu = omni.kit.ui.get_editor_menu()
        if _editor_menu:
            self._menu_item: EditorMenu.EditorMenuItem = _editor_menu.add_item(
                menu_path=self.menu_path,
                toggle=True,
                on_click=self.change_visibility,
                value=True,
                auto_release=True,
            )

        USDNucleusOrganizerWindow.change_window_state("startup")

    def destroy(self):
        # Call before deleting _menu_item to ensure window is properly cleaned up
        self.change_visibility(self.menu_path, False)

        self.asset_model = None
        self.file_picker_window = None
        self._engine = None

        # setting to None to unsubscribe (i.e. not recieve callbacks anymore)
        self._window_state_sub = None
        self._menu_item = None
        self.menu_path = ""

        super().destroy()

        USDNucleusOrganizerWindow.change_window_state("destroyed")

    def change_visibility(self, menu_path, visible):
        carb.log_warn("VISIBILITY CALLED")
        self.visible = visible

        # Set the checkmark in the menu that shows whether this window is visible or not
        _editor_menu = omni.kit.ui.get_editor_menu()
        if _editor_menu and self._menu_item:
            _editor_menu.set_value(menu_path, visible)

    def _on_window_state_changed(self, value: carb.dictionary.Item, _cet: carb.settings.ChangeEventType) -> None:
        _state = str(value)

        if _state == "startup":
            self.frame.set_build_fn(self._build_startup_frame)
        elif _state == "convert":
            self.frame.set_build_fn(self._build_convert_frame)
        elif _state == "validate":
            self.frame.set_build_fn(self._build_validate_frame)

        self.frame.rebuild()

    def _on_file_submitted(self, file_name: str, dir_name: str) -> None:
        carb.log_warn("CALLED")
        dir_name = dir_name.strip()
        if dir_name and not dir_name.endswith("/"):
            dir_name += "/"

        self.asset_model._input_path = f'{dir_name}{file_name}'

        self.change_window_state("convert")

    def _build_startup_frame(self):
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("GET STARTED", clicked_fn=self.file_picker_window.show, height=ui.Percent(0.25))

    def _build_convert_frame(self):
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("CONVERT", clicked_fn=self.asset_model.apply_conversion, height=ui.Percent(0.25))

    # TODO: fix frame change error
    def _build_validate_frame(self):
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("VALIDATE", clicked_fn=self.asset_model.apply_validation, height=ui.Percent(0.25))
