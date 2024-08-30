from chimerax.core.commands import run, CmdDesc, register, ListOf, StringArg, FloatArg, BoolArg, IntArg, \
    SaveFileNameArg, EnumOf
from .animation import Animation
from chimerax.movie.movie import RESET_CLEAR, RESET_KEEP, RESET_NONE
from chimerax.movie.formats import formats, qualities, image_formats

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
    elif command_name == "animations setLength":
        func = set_length
        desc = set_length_desc
    elif command_name == "animations record":
        func = record
        desc = record_desc
    elif command_name == "animations insertTime":
        func = insert_time
        desc = insert_time_desc
    elif command_name == "animations clear":
        func = clear
        desc = clear_desc
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
        run(session, f"scenes scene {keyframe_name}", log=False)
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


def play(session, start_time=0, reverse=False):
    """
    Play the animation in the StateManager.
    :param session: The current session.
    :param reverse: Play the animation in reverse.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to play the animation.")
        return
    animation_mgr.play(start_time, reverse)


play_desc = CmdDesc(
    keyword=[
        ("start_time", FloatArg),
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


def set_length(session, length: int | float):
    """
    Set the length of the animation.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    animation_mgr.set_length(length)


set_length_desc = CmdDesc(
    required=[
        ("length", FloatArg)
    ],
    synopsis="Set the length of the animation."
)


def record(session, r_directory=None, r_pattern=None, r_format=None,
           r_size=None, r_supersample=1, r_transparent_background=False,
           r_limit=90000, e_output=None, e_format=None, e_quality=None, e_qscale=None, e_bitrate=None,
           e_round_trip=False, e_reset_mode=RESET_CLEAR, e_wait=False, e_verbose=False):
    """
    Record the animation using the movie bundle. The params are mirrored of what the movie record and encode command
    expects and get directly passed to the movie command inside the Animation class.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    if animation_mgr.get_num_keyframes() < 1:
        print("Need at least 1 keyframes to record the animation.")
        return

    record_params = {
        'directory': r_directory,
        'pattern': r_pattern,
        'format': r_format,
        'size': r_size,
        'supersample': r_supersample,
        'transparent_background': r_transparent_background,
        'limit': r_limit
    }

    # Framerate is omitted from the movie encoding param list because the animation manager will handle it.
    encode_params = {
        'output': e_output,
        'format': e_format,
        'quality': e_quality,
        'qscale': e_qscale,
        'bitrate': e_bitrate,
        'round_trip': e_round_trip,
        'reset_mode': e_reset_mode,
        'wait': e_wait,
        'verbose': e_verbose
    }

    animation_mgr.record(record_data=record_params, encode_data=encode_params)


ifmts = image_formats
fmts = tuple(formats.keys())
reset_modes = (RESET_CLEAR, RESET_KEEP, RESET_NONE)
record_desc = CmdDesc(
    optional=[('e_output', ListOf(SaveFileNameArg))],
    keyword=[('r_directory', SaveFileNameArg),
             ('r_pattern', StringArg),
             ('r_format', EnumOf(fmts)),
             ('r_size', ListOf(IntArg)),
             ('r_supersample', IntArg),
             ('r_transparent_background', BoolArg),
             ('r_limit', IntArg),
             ('e_output', ListOf),
             ('e_format', EnumOf(fmts)),
             ('e_quality', EnumOf(qualities)),
             ('e_qscale', IntArg),
             ('e_bitrate', FloatArg),
             ('e_reset_mode', EnumOf(reset_modes)),
             ('e_round_trip', BoolArg),
             ('e_wait', BoolArg),
             ('e_verbose', BoolArg),
             ],
    synopsis="Record the animation."
)


def insert_time(session, target_time: int | float, time: int | float):
    """
    Insert a segment of time at a target point on the timeline. Shift keyframes accordingly.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    animation_mgr.insert_time(target_time, time)


insert_time_desc = CmdDesc(
    required=[
        ("target_time", FloatArg),
        ("time", FloatArg)
    ],
    synopsis="Insert a segment of time at a target point on the timeline. Shift keyframes accordingly."
)


def clear(session):
    """
    Remove all keyframes from the animations StateManager.
    """
    animation_mgr: Animation = session.get_state_manager("animations")
    animation_mgr.delete_all_keyframes()


clear_desc = CmdDesc(
    synopsis="Remove all keyframes from the animations StateManager."
)
