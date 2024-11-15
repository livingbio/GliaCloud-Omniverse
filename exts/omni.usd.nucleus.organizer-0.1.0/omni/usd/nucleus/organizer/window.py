import omni.ui as ui
import omni.kit.app

import carb

from .file_picker_window import CustomFilePickerWindow



class USDNucleusOrganizerWindow(ui.Window):
    WINDOW_STATES = [
        "startup",
        "confirmation",
        "processing",
        "finished"
    ]
    
    def __init__(self, title: str):
        super().__init__(title)

        self.selected_file_path = ""
        self.file_picker_window = CustomFilePickerWindow("Select File")
        self.file_picker_window.set_click_apply_handler(self.set_selected_file_path)
        
        self._state_subscription = omni.kit.app.SettingChangeSubscription(
            "exts/omni.usd.nucleus.organizer/window_state", self._on_window_state_changed)
        
        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/window_state", "startup")
        
    
    def destroy(self):
        self.file_picker_window = None
        
        # setting to None to unsubscribe (i.e. not recieve callbacks anymore)
        self._state_subscription = None
        
        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/window_state", "")
        
        super().destroy()
        
    def _on_window_state_changed(self, value: carb.dictionary.Item, change_type: carb.settings.ChangeEventType) -> None:
        _state = str(value)
        
        if _state == "startup":
            self.frame.set_build_fn(self._build_startup_frame)
        elif _state == "confirmation":
            self.frame.set_build_fn(self._build_confirmation_frame)
            
        self.frame.call_build_fn()
    
    def set_selected_file_path(self, file_name: str, dir_name: str) -> None:
        if not file_name or file_name == "":
            carb.log_warn("Select a valid file!")
            return
        self.file_picker_window.hide()
        settings = carb.settings.get_settings()
        settings.set("exts/omni.usd.nucleus.organizer/window_state", "confirmation")
        
        dir_name = dir_name.strip()
        if dir_name and not dir_name.endswith("/"):
            dir_name += "/"
        self.selected_file_path = f"{dir_name}{file_name}"
        carb.log_warn(f'Selected file path is {self.selected_file_path}')
        
    def _build_startup_frame(self):
        with ui.ScrollingFrame():
            with ui.VStack():
                ui.Button("Get Started in start", 
                          clicked_fn=self.file_picker_window.show, 
                          height=ui.Percent(0.25))
                
    def _build_confirmation_frame(self):
        ui.Label(self.selected_file_path)