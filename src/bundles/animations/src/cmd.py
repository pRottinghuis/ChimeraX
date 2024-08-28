from chimerax.core.commands import run, CmdDesc, register, StringArg, FloatArg

from typing import Optional


def register_command(command_name, logger):
    if command_name == "animations keyframe":
        func = keyframe
        desc = keyframe_desc
    elif command_name == "animations timeline":
        func = timeline
        desc = timeline_desc
    elif command_name == "animations play":
        func = play
        desc = play_desc
    else:
        raise ValueError("trying to register unknown command: %s" % command_name)
    register(command_name, desc, func)


def keyframe(session, action: str, keyframe_name: str, time: int | float):
    """
    Chimnerax Command for edit actions on a keyframe in the animation StateManager. add/edit/delete keyframes.
    Add keyframe will use the scenes scene command to create a new scene to add to the state manager.
    :param session: The current session.
    :param action: The action to take on the keyframe. Options are add, edit, delete.
    :param keyframe_name: Name of the keyframe for the action to be applied to. This will also be used for the scene name.
    :param time: The time in seconds for the keyframe.
    """

    animation_mgr = session.get_state_manager("animations")

    if action == "add":
        if not isinstance(time, (int, float)):
            print("Time must be an integer or float")
            return
        if animation_mgr.keyframe_exists(keyframe_name):
            print(f"Keyframe {keyframe_name} already exists")
            return
        run(session, f"scenes scene {keyframe_name}")
        animation_mgr.add_keyframe(keyframe_name, time)
    elif action == "edit":
        if not animation_mgr.keyframe_exists(keyframe_name):
            print(f"Keyframe {keyframe_name} does not exist")
            return
        if not isinstance(time, (int, float)):
            print("Time must be an integer or float")
            return
        animation_mgr.edit_keyframe_time(keyframe_name, time)
    elif action == "delete":
        if not animation_mgr.keyframe_exists(keyframe_name):
            print(f"Keyframe {keyframe_name} does not exist")
            return
        animation_mgr.delete_keyframe(keyframe_name)
    else:
        print(f"Action {action} not recognized. Options are add, edit, delete.")


keyframe_desc = CmdDesc(
    required=[
        ("action", StringArg),
        ("keyframe_name", StringArg),
        ("time", FloatArg)
    ],
    synopsis="Create a keyframe in the animation StateManager."
)


def timeline(session):
    """
    ChimeraX command to list all keyframes in the animation StateManager in the log.
    """
    animation_mgr = session.get_state_manager("animations")
    keyframes = animation_mgr.list_keyframes()
    for keyframe in keyframes:
        print(keyframe)


timeline_desc = CmdDesc(
    synopsis="List all keyframes in the animation StateManager."
)


def play(session):
    """
    Play the animation in the StateManager.
    :param session: The current session.
    """
    animation_mgr = session.get_state_manager("animations")
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to play the animation.")
        return
    animation_mgr.play()


play_desc = CmdDesc(
    synopsis="Play the animation."
)


def preview(session, time: int | float):
    """
    Preview the animation at a specific time.
    :param session: The current session.
    :param time: The time in seconds to preview the animation.
    """
    animation_mgr = session.get_state_manager("animations")
    if not isinstance(time, (int, float)):
        print("Time must be an integer or float")
        return
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to preview the animation.")
        return
    if not animation_mgr.time_in_range(time):
        print(f"Time must be between 0 and {animation_mgr.get_time_length()}")
        return
    animation_mgr.preview(time)


preview_desc = CmdDesc(
    required=[
        ("time", FloatArg)
    ],
    synopsis="Preview the animation at a specific time."
)