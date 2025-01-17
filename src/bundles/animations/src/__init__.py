from chimerax.core.toolshed import BundleAPI
from .tool import AnimationsTool


class _MyAPI(BundleAPI):
    api_version = 0

    # Override method
    @staticmethod
    def start_tool(session, bi, ti):
        if ti.name == "Animations":
            return AnimationsTool(session, ti.name)
        raise ValueError("trying to start unknown tool: %s" % ti.name)

    @staticmethod
    def get_class(class_name):
        # class_name will be a string
        if class_name == "AnimationsTool":
            return AnimationsTool
        elif class_name == "Animation":
            from .animation import Animation
            return Animation
        raise ValueError("Unknown class name '%s'" % class_name)

    @staticmethod
    def initialize(session, bundle_info):
        """Install scene manager into existing session"""
        from .animation import Animation
        session.add_state_manager("animations", Animation(session))
        return

    @staticmethod
    def register_command(command_name, logger):
        from . import cmd
        cmd.register_command(command_name, logger)


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _MyAPI()
