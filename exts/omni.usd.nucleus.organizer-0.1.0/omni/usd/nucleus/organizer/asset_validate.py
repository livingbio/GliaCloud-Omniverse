from omni.asset_validator.core import BaseRuleChecker, Suggestion, registerRule
from pxr import Usd, UsdGeom, Sdf
import carb


@registerRule("GliaCloudRules")
class RotationChecker(BaseRuleChecker):

    @classmethod
    def _add_up_axis(cls, stage: Usd.Stage, _location: Usd.Prim) -> None:
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)

        if stage.HasAuthoredMetadata(UsdGeom.Tokens.upAxis) and UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
            carb.log_warn("Add Up-axis started")

    @classmethod
    def _handle_upAxis_change(cls, stage: Usd.Stage, _location: Usd.Prim) -> None:
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)

        orig_default = stage.GetDefaultPrim()
        new_default = UsdGeom.Xform.Define(stage, "/World")

        edits = Sdf.BatchNamespaceEdit()
        edits.Add(Sdf.NamespaceEdit.ReparentAndRename(orig_default.GetPath(), new_default.GetPath(), "SubRoot", 0))

        if stage.GetRootLayer().Apply(edits):
            carb.log_warn("Up-axis changed successfully")

        orig_default_xformable = UsdGeom.Xformable(orig_default)
        orig_default_xform_op = orig_default_xformable.AddRotateXOp()
        orig_default_xform_op.Set(90)

    def CheckStage(self, stage: Usd.Stage):

        if not stage.HasAuthoredMetadata(UsdGeom.Tokens.upAxis):
            self._AddFailedCheck(
                message="Stage does not specify an upAxis.",
                at=stage.GetDefaultPrim(),
                suggestion=Suggestion(
                    message="adds Z upAxis to file metadata",
                    callable=self._add_up_axis,
                ),
            )
        elif UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            self._AddFailedCheck(
                message="UpAxis should be Z",
                at=stage.GetDefaultPrim(),
                suggestion=Suggestion(
                    message="Changes upAxis to Z and rotates prim accordingly",
                    callable=self._handle_upAxis_change,
                ),
            )
