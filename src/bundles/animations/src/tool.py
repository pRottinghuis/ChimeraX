from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget
from Qt.QtCore import QByteArray, Qt, QPointF
from Qt.QtGui import QPixmap


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

        self.tool_window.manage("side")

    def build_ui(self):
        vbox = QVBoxLayout()
        vbox.addWidget(TimelineWidget())
        self.tool_window.ui_area.setLayout(vbox)

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


class KeyframeItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, position):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(position)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Called before the position has changed.
            # set y to keep the keyframe on the timeline
            return QPointF(value.x(), 0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            pass
            # Called after the position has changed.
        return super().itemChange(change, value)


class TimelineWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.timeline_view = QGraphicsView(self)
        self.timeline_scene = QGraphicsScene(self)
        self.timeline_view.setScene(self.timeline_scene)
        self.layout.addWidget(self.timeline_view)

        # Example keyframes
        for i in range(5):
            pixmap = QPixmap(50, 50)
            pixmap.fill(Qt.red)
            keyframe = KeyframeItem(pixmap, QPointF(i * 60, 0))
            self.timeline_scene.addItem(keyframe)

        self.setLayout(self.layout)
