from chimerax.core.commands import register, CmdDesc, StringArg


def register_command(command_name, logger):
    if command_name == "scenes scene":
        register(command_name, scene_desc, scene)


def scene(session, scene_name):
    """Save the current scene as 'scene_name'."""
    session.scenes.save_scene(scene_name)
    return


scene_desc = CmdDesc(
    required=[("scene_name", StringArg)],
    synopsis="Save the current scene as 'scene_name'."
)
