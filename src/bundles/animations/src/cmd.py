from chimerax.core.commands import run, CmdDesc, register, StringArg, FloatArg


def register_command(command_name, logger):
    if command_name == "animations keyframe":
        func = keyframe
        desc = keyframe_desc
    else:
        raise ValueError("trying to register unknown command: %s" % command_name)
    register(command_name, desc, func)


def keyframe(session, scene_name, time):
    """
    Chimnerax Command to create a keyframe in the animation StateManager. First step is to call the scene command to
    Save a scene. Then call an Animation function to save the scene with a timestamp.
    """
    if not isinstance(time, (int, float)):
        print("Time must be an integer or float")

    run(session, f"scenes scene {scene_name}")
    session.get_state_manager("animations").add_keyframe(scene_name, time)


keyframe_desc = CmdDesc(
    required=[
        ("scene_name", StringArg),
        ("time", FloatArg)
    ],
    synopsis="Create a keyframe in the animation StateManager."
)
