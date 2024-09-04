from chimerax.core.tools import ToolInstance
from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF
from Qt.QtGui import QPixmap, QPen


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
        vbox.addWidget(KeyframeEditorWidget())
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


class TickMarkItem(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setPen(QPen(Qt.gray, 1))


class TickIntervalLabel(QGraphicsTextItem):
    def __init__(self, text):
        super().__init__(text)


class KeyframeEditorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.length = 600
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

        self.add_tick_marks()

        self.setLayout(self.layout)

    def add_tick_marks(self):
        y_position = 60  # Top positions of the tick marks and labels on the y-axis
        interval = 10  # Interval between tick marks in pixels
        major_interval = 100  # Interval between major tick marks in pixels
        tick_length = 10  # Length of minor tick marks
        major_tick_length = 20  # Length of major tick marks

        # Clear existing tick marks and labels
        for item in self.timeline_scene.items():
            if isinstance(item, (TickMarkItem, TickIntervalLabel)):
                self.timeline_scene.removeItem(item)

        for i in range(0, self.length, interval):
            position = QPointF(i, y_position)
            if i % major_interval == 0:
                tick_mark = TickMarkItem(position, major_tick_length)
                time_label = TickIntervalLabel(f"{i // major_interval}")
                # Use the boundingRect dimensions to center the text under a major tick mark
                text_rect = time_label.boundingRect()
                time_label.setPos(position.x() - text_rect.width() / 2, y_position + major_tick_length)
                self.timeline_scene.addItem(time_label)
            else:
                tick_mark = TickMarkItem(position, tick_length)
            self.timeline_scene.addItem(tick_mark)
