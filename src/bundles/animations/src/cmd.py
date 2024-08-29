from chimerax.core.commands import run, CmdDesc, register, ListOf, StringArg, FloatArg, BoolArg, IntArg, \
    SaveFileNameArg, EnumOf
from .animation import Animation
from chimerax.movie.movie import RESET_CLEAR, RESET_KEEP, RESET_NONE
from chimerax.movie.formats import formats, qualities

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
    elif command_name == "animations preview":
        func = preview
        desc = preview_desc
    elif command_name == "animations record":
        func = record
        desc = record_desc
    else:
        raise ValueError("trying to register unknown command: %s" % command_name)
    register(command_name, desc, func)


def keyframe(session, action: str, keyframe_name: str, time: int | float | None = None):
    """
    Chimnerax Command for edit actions on a keyframe in the animation StateManager. add/edit/delete keyframes.
    Add keyframe will use the scenes scene command to create a new scene to add to the state manager.
    :param session: The current session.
    :param action: The action to take on the keyframe. Options are add, edit, delete.
    :param keyframe_name: Name of the keyframe for the action to be applied to. This will also be used for the scene name.
    :param time: The time in seconds for the keyframe.
    """

    animation_mgr: Animation = session.get_state_manager("animations")

    if action == "add":
        if time is not None and not isinstance(time, (int, float)):
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
    ],
    keyword=[
        ("time", FloatArg)
    ],
    synopsis="Create a keyframe in the animation StateManager."
)


def timeline(session):
    """
    ChimeraX command to list all keyframes in the animation StateManager in the log.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    keyframes = animation_mgr.list_keyframes()
    for keyframe in keyframes:
        print(keyframe)


timeline_desc = CmdDesc(
    synopsis="List all keyframes in the animation StateManager."
)


def play(session, reverse=False):
    """
    Play the animation in the StateManager.
    :param session: The current session.
    :param reverse: Play the animation in reverse.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to play the animation.")
        return
    animation_mgr.play(reverse)


play_desc = CmdDesc(
    keyword=[
        ("reverse", BoolArg)
    ],
    synopsis="Play the animation."
)


def preview(session, time: int | float):
    """
    Preview the animation at a specific time.
    :param session: The current session.
    :param time: The time in seconds to preview the animation.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
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


def record(session, output=None, format=None, quality=None, qscale=None, bitrate=None,
           framerate=25, round_trip=False, reset_mode=RESET_CLEAR, wait=False, verbose=False):
    """
    Record the animation using the movie bundle.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to record the animation.")
        return

    encode_params = {
        'session': session,
        'output': output,
        'format': format,
        'quality': quality,
        'qscale': qscale,
        'bitrate': bitrate,
        'framerate': framerate,
        'round_trip': round_trip,
        'reset_mode': reset_mode,
        'wait': wait,
        'verbose': verbose
    }

    animation_mgr.record(encode_data=encode_params)


fmts = tuple(formats.keys())
reset_modes = (RESET_CLEAR, RESET_KEEP, RESET_NONE)
record_desc = CmdDesc(
    optional=[('output', ListOf(SaveFileNameArg))],
    keyword=[('format', EnumOf(fmts)),
             ('quality', EnumOf(qualities)),
             ('qscale', IntArg),
             ('bitrate', FloatArg),
             ('framerate', FloatArg),
             ('reset_mode', EnumOf(reset_modes)),
             ('round_trip', BoolArg),
             ('wait', BoolArg),
             ('verbose', BoolArg),
             ],
    synopsis="Record the animation."
)
