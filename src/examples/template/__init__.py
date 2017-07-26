# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI


class _MyAPI(BundleAPI):
    # FIXME: only implement methods that the metadata says should be there

    @staticmethod
    def get_class(class_name):
        # 'get_class' is called by session code to get class from bundle that
        # was saved in a session
        # FIXME: remove if not providing a tool
        # FIXME: rename if ToolUI has different class name
        if class_name == 'ToolUI':
            from . import tool
            return tool.ToolUI
        return None

    @staticmethod
    def start_tool(session, tool_name):
        # 'start_tool' is called to start an instance of the tool
        # If providing more than one tool in package,
        # look at 'tool_name' to see which is being started.
        raise NotImplementedError  # FIXME: remove method if unneeded
        from .tool import ToolUI
        # UI should register itself with tool state manager
        return ToolUI(session, tool_name)

    @staticmethod
    def register_command(command_name, logger):
        # 'register_command' is lazily called when the command is referenced
        raise NotImplementedError  # FIXME: remove method if unneeded
        from . import cmd
        from chimerax.core.commands import register
        register(command_name + " SUBCOMMAND_NAME",
                 cmd.subcommand_desc, cmd.subcommand_function, logger=logger)
        # TODO: Register more subcommands here

    @staticmethod
    def register_selector(selector_name, logger):
        # 'register_selector' is lazily called when the selector is referenced
        raise NotImplementedError  # FIXME: remove method if unneeded

    @staticmethod
    def open_file(session, stream_or_path, optional_format_name, optional_file_name, **kw):
        # 'open_file' is called by session code to open a file;
        # returns (list of models, status message).
        #
        # Second arg must be 'stream' or 'path'.  Depending on the name, either an
        # open data stream or a filesystem path will be provided.  The third and
        # fourth arguments are optional (remove 'optional_' from their names if you
        # provide them).  'format_name' will be the first nickname of the format
        # (reminder: the nickname of a format that provides no explicit nicknames
        # is the lower-case version of the full format name).  'file_name' is the
        # name of the input file, with compression suffix and path components
        # stripped.
        # 
        # You shouldn't actually use "**kw" but instead declare the actual keyword
        # args that your format supports (as per your bundle_info.xml file).
        raise NotImplementedError     # FIXME: remove method if unneeded

    @staticmethod
    def save_file(session, name, format):
        # 'save_file' is called by session code to save a file
        # add any supported keyword arguments
        # if you want to do your own argument checking, add **kw
        # otherwise, core will make sure only your keywords are present
        raise NotImplementedError     # FIXME: remove method if unneeded

    @staticmethod
    def fetch_from_database(session, identifier, ignore_cache=False, database_name=None, format_name=None, **kw):
        # 'fetch_from_database' is called by session code to fetch data with give identifier
        raise NotImplementedError     # FIXME: remove method if unneeded

    @staticmethod
    def initialize(session, bi):
        # bundle-specific initialization (causes import)
        raise NotImplementedError     # FIXME: remove method if unneeded

    @staticmethod
    def finish(session, bi):
        # deinitialize bundle in session (causes import)
        raise NotImplementedError

bundle_api = _MyAPI()
