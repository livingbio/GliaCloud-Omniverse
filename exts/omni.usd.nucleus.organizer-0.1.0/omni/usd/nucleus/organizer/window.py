import omni.ui as ui
import omni.kit.app

import carb

from .file_picker_window import CustomFilePickerWindow
from .organized_asset_model import OrganizedAssetModel

import omni.asset_validator.core


class USDNucleusOrganizerWindow(ui.Window):
    WINDOW_STATES = [
        "startup",
        "confirmation",
        "processing",
        "finished"
    ]
    
    @staticmethod
    def _change_window_state(new_state: str =""):
        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/window_state", new_state)
        carb.log_warn(f'Window state changed to {settings.get("exts/omni.usd.nucleus.organizer/window_state")}')
        
    
    def __init__(self, title: str, **kwargs):
        super().__init__(title, **kwargs)

        self.selected_file_path = ""
        self.file_picker_window = CustomFilePickerWindow("Select File", self._on_file_submitted)
        
        self._state_subscription = omni.kit.app.SettingChangeSubscription(
            "exts/omni.usd.nucleus.organizer/window_state", self._on_window_state_changed)
        
        self.curr_asset_model = None
        
        USDNucleusOrganizerWindow._change_window_state("startup")
        
    
    def destroy(self):
        self.selected_file_path = ""
        self.file_picker_window = None
        
        # setting to None to unsubscribe (i.e. not recieve callbacks anymore)
        self._state_subscription = None
        
        USDNucleusOrganizerWindow._change_window_state("startup")
        
        self.curr_asset_model = None
        
        super().destroy()
    
    def _on_window_state_changed(self, value: carb.dictionary.Item, change_type: carb.settings.ChangeEventType) -> None:
        _state = str(value)
        
        if _state not in USDNucleusOrganizerWindow.WINDOW_STATES:
            if _state == "":
                _state = '""'
            carb.log_warn(f'State is {_state}')
            return
        
        if _state == "startup":
            self.frame.set_build_fn(self._build_startup_frame)
        elif _state == "confirmation":
            self.frame.set_build_fn(self._build_confirmation_frame)
            
        self.frame.call_build_fn()
    
    def set_selected_file_path(self, file_path: str) -> None:
        self.selected_file_path = file_path
        carb.log_warn(f'Selected file path is {self.selected_file_path}')
    
    def _on_file_submitted(self, file_name: str, dir_name: str) -> None:
        dir_name = dir_name.strip()
        if dir_name and not dir_name.endswith("/"):
            dir_name += "/"
        self.set_selected_file_path(f"{dir_name}{file_name}")
        
        self.curr_asset_model = OrganizedAssetModel(self.selected_file_path)

        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/window_state", "confirmation")
        
    def _build_startup_frame(self):
        _enabled_settings = [
            "KindChecker",
            "ExtentsChecker",
            "UsdMaterialBindingApi",
            "SubdivisionSchemeChecker",
            "OmniDefaultPrimChecker",
            
        ]
        
        settings = carb.settings.get_settings()
        settings.set("exts/omni.asset_validator.core/disabledRules", ["*"])
        settings.set(
            "exts/omni.asset_validator.core/enabledRules",
            ["NormalMapTextureChecker","PrimEncapsulationChecker"]
        )
        
        for category in omni.asset_validator.core.ValidationRulesRegistry.categories():
            for rule in omni.asset_validator.core.ValidationRulesRegistry.rules(category=category, enabledOnly=True):
                carb.log_warn(rule.__name__)
        
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("GET STARTED", 
                          clicked_fn=self.file_picker_window.show, 
                          height=ui.Percent(0.25))
                
    def _build_confirmation_frame(self):
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("CONFIRM & CONVERT", clicked_fn=self.curr_asset_model.apply_conversion, height=ui.Percent(0.25))
                
                ui.Button("OPTIMIZE", clicked_fn=self.curr_asset_model.apply_standardization, height=ui.Percent(0.25))
        
        
        
        