from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF
from Qt.QtGui import QPixmap, QPen
from .kf_editor_widget import KeyframeEditorWidget, KFESignalManager


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

        KFESignalManager().preview_time_changed.connect(self.update_preview_time)

        self.tool_window.manage("side")

    def build_ui(self):
        vbox = QVBoxLayout()
        from .kf_editor_widget import KeyframeEditorWidget
        animation_mgr = self.session.get_state_manager("animations")
        kf_editor_widget = KeyframeEditorWidget(animation_mgr.get_time_length(), animation_mgr.get_keyframes(),
                                                 animation_mgr.get_triggers())
        vbox.addWidget(kf_editor_widget)
        self.tool_window.ui_area.setLayout(vbox)

    def update_preview_time(self, time: float):
        print("update preview time to", time)

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
