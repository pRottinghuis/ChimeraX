from chimerax.core.triggerset import TriggerSet

from typing import Optional, Any, Callable

# Signals for once the animation manager has made an action
MGR_KF_ADDED, MGR_KF_DELETED, MGR_KF_EDITED, MGR_LENGTH_CHANGED, MGR_PREVIEWED = manager_triggers = (
    "animations mgr keyframe added", "animations mgr keyframe deleted", "animations mgr keyframe edited",
    "animations mgr length changed", "animations mgr previewed")

# Signals for if the animation manager needs to make an action
KF_ADD, KF_DELETE, KF_EDIT, LENGTH_CHANGE, PREVIEW = external_triggers = (
    "animations keyframe add", "animations keyframe delete", "animations keyframe edit", "animations length change",
    "animations preview")

_triggers = TriggerSet()

for trigger in manager_triggers:
    _triggers.add_trigger(trigger)

for trigger in external_triggers:
    _triggers.add_trigger(trigger)


def activate_trigger(trigger_name: str, data: Optional[Any] = None, absent_okay: bool = False) -> None:
    _triggers.activate_trigger(trigger_name, data)


def add_handler(trigger_name: str, func: Callable) -> None:
    _triggers.add_handler(trigger_name, func)
