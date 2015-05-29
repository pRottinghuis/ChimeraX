# vi: set expandtab shiftwidth=4 softtabstop=4:
import wx
from chimera.core.tools import ToolInstance


class ShellUI(ToolInstance):

    # shell tool does not participate in sessions
    SESSION_ENDURING = True
    SESSION_SKIP = True
    SIZE = (500, 500)
    VERSION = 1

    def __init__(self, session, tool_info):
        super().__init__(session, tool_info)
        # 'display_name' defaults to class name with spaces inserted
        # between lower-then-upper-case characters (therefore "Tool UI"
        # in this case), so only override if different name desired
        self.display_name = "Chimera 2 Python Shell"
        self.tool_window = session.ui.create_main_tool_window(
            self, size=self.SIZE)
        parent = self.tool_window.ui_area
        # UI content code
        from wx.py.shell import Shell
        self.shell = Shell(parent, -1, locals={
                'Chimera2_session': session
            })
        self.shell.redirectStdin(True)
        self.shell.redirectStdout(True)
        self.shell.redirectStderr(True)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.shell, 1, wx.EXPAND)
        parent.SetSizerAndFit(sizer)
        self.tool_window.manage(placement="right")
        # Add to running tool list for session if tool should be saved
        # in and restored from session and scenes
        session.tools.add([self])

    #
    # Implement session.State methods if deriving from ToolInstance
    #
    def take_snapshot(self, phase, session, flags):
        pass

    def restore_snapshot(self, phase, session, version, data):
        pass

    def reset_state(self):
        pass

    #
    # Override ToolInstance delete method to clean up
    #
    def delete(self):
        session = self.session()
        self.tool_window.shown = False
        self.tool_window.destroy()
        self.session.tools.remove([self])
        super().delete()

    def display(self, b):
        self.tool_window.shown = b
