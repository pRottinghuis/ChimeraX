from chimerax.core.toolshed import BundleAPI
from tool import AnimationsTool


class _MyAPI(BundleAPI):
    api_version = 0

    # Override method
    @staticmethod
    def start_tool(session, bi, ti):
        if ti.name == "Animations":
            from . import tool
            return AnimationsTool(session, ti.name)
        raise ValueError("trying to start unknown tool: %s" % ti.name)

    @staticmethod
    def get_class(class_name):
        # class_name will be a string
        if class_name == "AnimationsTool":
            return AnimationsTool
        raise ValueError("Unknown class name '%s'" % class_name)

    @staticmethod
    def register_command(bi, ci, logger):
        from chimerax.core.commands import register
        from . import cmd
        pass


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _MyAPI()
