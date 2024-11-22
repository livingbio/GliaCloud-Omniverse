from omni.asset_validator.core import BaseRuleChecker, Suggestion
from pxr import Usd, UsdGeom

class RotationChecker(BaseRuleChecker):
    
    @classmethod
    def _add_up_axis(cls, stage: Usd.Stage, _location: Usd.Prim):
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)
        
    @classmethod
    def _add_up_axis(cls, stage: Usd.Stage, _location: Usd.Prim):
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)
        
        default_prim = stage.GetDefaultPrim()
        default_prim_xformable = UsdGeom.Xformable(default_prim)
        default_prim_xform_op = default_prim_xformable.AddRotateXOp()
        default_prim_xform_op.Set(90)
        
    
    def CheckStage(self, stage: Usd.Stage):
        
        if not stage.HasAuthoredMetadata(UsdGeom.Tokens.upAxis):
            self._AddFailedCheck(
                message="Stage does not specify an upAxis.",
                suggestion=Suggestion(
                    message="adds Z upAxis to file metadata",
                    callable=self._add_up_axis,
                ))
        elif UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            self._AddFailedCheck(
                message="UpAxis should be Z",
                suggestion=Suggestion(
                    message="Changes upAxis to Z and rotates prim accordingly",
                    callable=self._handle_upAxis_change
                )
            )