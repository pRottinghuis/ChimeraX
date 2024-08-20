from chimerax.core.commands import register, CmdDesc, StringArg, FloatArg


def register_command(command_name, logger):
    if command_name == "scenes scene":
        func = scene
        desc = scene_desc
    elif command_name == "scenes restore":
        func = restore_scene
        desc = restore_scene_desc
    elif command_name == "scenes interpolate":
        func = interpolate_scenes
        desc = interpolate_scenes_desc
    else:
        raise ValueError("trying to register unknown command: %s" % command_name)
    register(command_name, desc, func)


def scene(session, scene_name):
    """Save the current scene as 'scene_name'."""
    session.scenes.save_scene(scene_name)


scene_desc = CmdDesc(
    required=[("scene_name", StringArg)],
    synopsis="Save the current scene as 'scene_name'."
)


def restore_scene(session, scene_name):
    """Restore the scene named 'scene_name'."""
    session.scenes.restore_scene(scene_name)


restore_scene_desc = CmdDesc(
    required=[("scene_name", StringArg)],
    synopsis="Restore the scene named 'scene_name'."
)


def interpolate_scenes(session, scene_name1, scene_name2, fraction):
    """Interpolate between two scenes."""
    if fraction < 0.0 or fraction > 1.0:
        print("Fraction must be between 0.0 and 1.0")
        return
    session.scenes.interpolate_scenes(scene_name1, scene_name2, fraction)


interpolate_scenes_desc = CmdDesc(
    required=[
        ("scene_name1", StringArg),
        ("scene_name2", StringArg),
        ("fraction", FloatArg)
    ],
    synopsis="Interpolate between two scenes."
)