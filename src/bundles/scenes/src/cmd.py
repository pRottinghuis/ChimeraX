from chimerax.core.commands import register, CmdDesc, StringArg


def register_command(command_name, logger):
    if command_name == "scenes scene":
        func = scene
        desc = scene_desc
    elif command_name == "scenes restore":
        func = restore_scene
        desc = restore_scene_desc
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