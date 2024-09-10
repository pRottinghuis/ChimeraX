from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import QVBoxLayout, QStyle, QPushButton
from .triggers import add_handler, KF_EDIT, PREVIEW, PLAY, KF_ADD
from chimerax.core.commands import run
from .kf_editor_widget import KeyframeEditorWidget


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

        # Store a reference to the animation manager
        self.animation_mgr = self.session.get_state_manager("animations")

        from chimerax.ui import MainToolWindow
        self.tool_window = MainToolWindow(self)

        # test scene thumbnails
        self.build_ui()

        # Register handlers for the triggers
        add_handler(PREVIEW, lambda trigger_name, time: run(self.session, f"animations preview {time}"))
        add_handler(KF_EDIT, lambda trigger_name, data: run(self.session, f"animations keyframe edit {data[0]} time {data[1]}"))
        add_handler(PLAY, lambda trigger_name, data: run(self.session, f"animations play start {data[0]} reverse {data[1]}"))
        add_handler(KF_ADD, lambda trigger_name, time: self.add_keyframe(time))

        self.tool_window.manage("side")

    def build_ui(self):
        main_vbox_layout = QVBoxLayout()

        # Keyframe editor graphics view widget.
        kf_editor_widget = KeyframeEditorWidget(self.animation_mgr.get_time_length(), self.animation_mgr.get_keyframes())
        main_vbox_layout.addWidget(kf_editor_widget)

        self.tool_window.ui_area.setLayout(main_vbox_layout)

    def add_keyframe(self, time):
        base_name = "keyframe_"
        id = 0
        while any(kf.get_name() == f"{base_name}{id}" for kf in self.animation_mgr.get_keyframes()):
            id += 1
        kf_name = f"{base_name}{id}"
        run(self.session, f"animations keyframe add {kf_name} time {time}")

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
