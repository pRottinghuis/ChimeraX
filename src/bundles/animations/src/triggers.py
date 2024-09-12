from chimerax.core.triggerset import TriggerSet

from typing import Optional, Any, Callable

# Signals for once the animation manager has made an action
MGR_KF_ADDED, MGR_KF_DELETED, MGR_KF_EDITED, MGR_LENGTH_CHANGED, MGR_PREVIEWED, MGR_FRAME_PLAYED = manager_triggers = (
    "animations mgr keyframe added", "animations mgr keyframe deleted", "animations mgr keyframe edited",
    "animations mgr length changed", "animations mgr previewed", "animations mgr frame played")

"""
All MGR_ prefix commands are triggered by the animations manager once an action has been completed.

MGR_KF_ADDED: Triggered when a keyframe is added to the animation manager. Data is reference to the 
animation.Keyframe object that was added.

MGR_KF_DELETED: Triggered when a keyframe is deleted from the animation manager. Data is reference to the 
animation.Keyframe object that was removed from the animation manager.

MGR_KF_EDITED: Triggered when a keyframe is edited in the animation manager. Data is reference to the 
animation.Keyframe object that was edited.

MGR_LENGTH_CHANGED: Triggered when the length of the animation is changed. Data is the new length of the animation in 
seconds. int/float.

MGR_PREVIEWED: Triggered when the animation manager previews a frame. Data is the time in seconds (int/float) that is 
getting previewed.

MGR_FRAME_PLAYED: Triggered when the animation manager plays a frame. Data is the time in seconds (int/float) of the
frame that is being shown.
"""

# Signals for if the animation manager needs to make an action
KF_ADD, KF_DELETE, KF_EDIT, LENGTH_CHANGE, PREVIEW, PLAY, RECORD, STOP_PLAYING = external_triggers = (
    "animations keyframe add", "animations keyframe delete", "animations keyframe edit", "animations length change",
    "animations preview", "animations play", "animations record", "animations stop playing")

_triggers = TriggerSet()

for trigger in manager_triggers:
    _triggers.add_trigger(trigger)

for trigger in external_triggers:
    _triggers.add_trigger(trigger)


def activate_trigger(trigger_name: str, data: Optional[Any] = None, absent_okay: bool = False) -> None:
    _triggers.activate_trigger(trigger_name, data)


def add_handler(trigger_name: str, func: Callable) -> None:
    _triggers.add_handler(trigger_name, func)
