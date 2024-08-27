from chimerax.core.commands import run, CmdDesc, register, StringArg, FloatArg

from typing import Optional


def register_command(command_name, logger):
    if command_name == "animations keyframe":
        func = keyframe
        desc = keyframe_desc
    else:
        raise ValueError("trying to register unknown command: %s" % command_name)
    register(command_name, desc, func)


def keyframe(session, action: str, scene_name: str, time: int | float):
    """
    Chimnerax Command for edit actions on a keyframe in the animation StateManager. add/edit/delete keyframes.
    Add keyframe will use the scenes scene command to create a new scene to add to the state manager.
    :param session: The current session.
    :param action: The action to take on the keyframe. Options are add, edit, delete.
    :param scene_name: Name of the keyframe for the action to be applied to. This will also be used for the scene name.
    :param time: The time in seconds for the keyframe.
    """

    if action == "add":
        if not isinstance(time, (int, float)):
            print("Time must be an integer or float")

        run(session, f"scenes scene {scene_name}")
        session.get_state_manager("animations").add_keyframe(scene_name, time)


keyframe_desc = CmdDesc(
    required=[
        ("action", StringArg),
        ("scene_name", StringArg),
        ("time", FloatArg)
    ],
    synopsis="Create a keyframe in the animation StateManager."
)
