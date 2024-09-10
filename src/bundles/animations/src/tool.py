from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import QVBoxLayout, QStyle, QPushButton
from .triggers import add_handler, KF_EDIT, PREVIEW, PLAY
from chimerax.core.commands import run


class AnimationsTool(ToolInstance):
    SESSION_ENDURING = False  # Does this instance persist when session closes
    SESSION_SAVE = True  # We do save/restore in sessions

    def __init__(self, session, tool_name):
        # 'session'   - chimerax.core.session.Session instance
        # 'tool_name' - string

        super().__init__(session, tool_name)

        # Set name displayed on title bar (defaults to tool_name)
        # Must be after the superclass init, which would override it.
        self.display_name = "Animations"

        from chimerax.ui import MainToolWindow
        self.tool_window = MainToolWindow(self)

        # test scene thumbnails
        self.build_ui()

        # Register handlers for the triggers
        add_handler(PREVIEW, lambda trigger_name, time: run(self.session, f"animations preview {time}"))
        add_handler(KF_EDIT, lambda trigger_name, data: run(self.session, f"animations keyframe edit {data[0]} time {data[1]}"))
        add_handler(PLAY, lambda trigger_name, data: run(self.session, f"animations play start {data[0]} reverse {data[1]}"))

        self.tool_window.manage("side")

    def build_ui(self):
        main_vbox_layout = QVBoxLayout()

        # Keyframe editor graphics view widget.
        from .kf_editor_widget import KeyframeEditorWidget
        animation_mgr = self.session.get_state_manager("animations")
        kf_editor_widget = KeyframeEditorWidget(animation_mgr.get_time_length(), animation_mgr.get_keyframes())
        main_vbox_layout.addWidget(kf_editor_widget)

        self.tool_window.ui_area.setLayout(main_vbox_layout)

    def take_snapshot(self, session, flags):
        return {
            'version': 1
        }

    @classmethod
    def restore_snapshot(class_obj, session, data):
        # Instead of using a fixed string when calling the constructor below, we could
        # have saved the tool name during take_snapshot() (from self.tool_name, inherited
        # from ToolInstance) and used that saved tool name.  There are pros and cons to
        # both approaches.
        inst = class_obj(session, "Animations")
        return inst
