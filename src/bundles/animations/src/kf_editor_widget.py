from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem, QGraphicsItemGroup, QPushButton
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF
from Qt.QtGui import QPixmap, QPen


class KeyframeEditorWidget(QWidget):
    def __init__(self, length, keyframes):
        """
        :param length: Length of the timeline in seconds
        :param keyframes: List of animation.Keyframe objects
        """
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.kfe_view = QGraphicsView(self)
        self.kfe_scene = KeyframeEditorScene(length, keyframes)
        self.kfe_view.setScene(self.kfe_scene)

        self.sample_button = QPushButton("Sample Button")
        self.sample_button.clicked.connect(self.sample_button_clicked)
        self.layout.addWidget(self.sample_button)

        self.layout.addWidget(self.kfe_view)

    def sample_button_clicked(self):
        len_update = self.kfe_scene.timeline.length + 100
        self.kfe_scene.set_timeline_length(len_update)


class KeyframeEditorScene(QGraphicsScene):
    def __init__(self, length, keyframes):
        super().__init__()
        self.timeline = Timeline(length=length * 60)  # TODO remove *60 temp fix by scaling in the timeline object
        self.addItem(self.timeline)
        self.cursor = TimelineCursor(QPointF(0, 0), 70, self.timeline)
        self.addItem(self.cursor)
        self.keyframes = []

        for kf in keyframes:
            thumbnail_bytes = kf.get_thumbnail()
            pixmap = QPixmap()
            pixmap.loadFromData(thumbnail_bytes, "JPEG")
            pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            keyframe_item = KeyframeItem(pixmap, QPointF(kf.get_time() * 60, 0), self.timeline)  # TODO remove *60 scaling once timeline is fixed
            self.keyframes.append(keyframe_item)
            self.addItem(keyframe_item)

    def update_scene_size(self):
        scene_width = self.timeline.length + 20  # Slightly wider than the timeline
        self.setSceneRect(0, 0, scene_width, self.height())

    def set_timeline_length(self, length):
        self.timeline.set_length(length)
        self.update_scene_size()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            clicked_pos = event.scenePos()
            if self.timeline.contains(clicked_pos):
                self.cursor.setPos(clicked_pos)
        super().mousePressEvent(event)


class Timeline(QGraphicsItemGroup):
    def __init__(self, length=600, interval=6, major_interval=60, tick_length=10, major_tick_length=20):
        # TODO convert length param into seconds and update the tick marks accordingly
        super().__init__()
        self.length = length
        self.interval = interval
        self.major_interval = major_interval
        self.tick_length = tick_length
        self.major_tick_length = major_tick_length
        self.update_tick_marks()

    def update_tick_marks(self):
        y_position = 60  # Top positions of the tick marks and labels on the y-axis

        # Clear existing tick marks and labels
        for item in self.childItems():
            self.removeFromGroup(item)
            self.scene().removeItem(item)

        for i in range(0, self.length + 1, self.interval):
            position = QPointF(i, y_position)
            if i % self.major_interval == 0:
                tick_mark = QGraphicsLineItem(
                    QLineF(position, QPointF(position.x(), position.y() + self.major_tick_length)))
                tick_mark.setPen(QPen(Qt.gray, 1))
                self.addToGroup(tick_mark)

                time_label = QGraphicsTextItem(f"{i // self.major_interval}")
                text_rect = time_label.boundingRect()
                time_label.setPos(position.x() - text_rect.width() / 2, y_position + self.major_tick_length)
                self.addToGroup(time_label)
            else:
                tick_mark = QGraphicsLineItem(QLineF(position, QPointF(position.x(), position.y() + self.tick_length)))
                tick_mark.setPen(QPen(Qt.gray, 1))
                self.addToGroup(tick_mark)

    def set_length(self, length):
        self.length = length
        self.update_tick_marks()


class KeyframeItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, position, timeline: Timeline):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        # hold onto a reference to the timeline so that update each keyframe based on the timeline.
        # Timeline must be initialized before any itemChange like position is made.
        self.timeline = timeline

        # Add tick mark at the bottom middle of the keyframe box
        half_width = self.boundingRect().width() / 2
        tick_position = QPointF(half_width, self.boundingRect().height())
        self.tick_mark = TickMarkItem(tick_position, 10)  # Length of the tick mark
        self.tick_mark.setPen(QPen(Qt.red, 1))
        self.tick_mark.setParentItem(self)

        # Create hover info item
        self.hover_info = QGraphicsTextItem(f"info text", self)
        self.hover_info.setDefaultTextColor(Qt.white)
        self.hover_info.setPos(0, -20)  # Position above the keyframe
        self.hover_info.hide()  # Hide initially

        self.setPos(position)

    def hoverEnterEvent(self, event):
        self.hover_info.show()  # Show hover info
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hover_info.hide()  # Hide hover info
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            half_width = self.boundingRect().width() / 2
            if value.x() < self.timeline.x() - half_width:
                new_x = self.timeline.x() - half_width
            elif value.x() > self.timeline.x() + self.timeline.length - half_width:
                new_x = self.timeline.x() + self.timeline.length - half_width
            else:
                new_x = value.x()
            return QPointF(new_x, 0)
        return super().itemChange(change, value)


class TimelineCursor(QGraphicsLineItem):
    def __init__(self, position, length, timeline: Timeline):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPen(QPen(Qt.red, 2))
        self.timeline = timeline
        self.setZValue(1)  # Render in front of other items

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Called before the position has changed.

            # Clamp the cursor to the timeline
            if value.x() < self.timeline.x():
                return QPointF(self.timeline.x(), self.y())
            elif value.x() > self.timeline.x() + self.timeline.length:
                return QPointF(self.timeline.x() + self.timeline.length, self.y())
            return QPointF(value.x(), self.y())
        return super().itemChange(change, value)


class TickMarkItem(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setPen(QPen(Qt.gray, 1))


class TickIntervalLabel(QGraphicsTextItem):
    def __init__(self, text):
        super().__init__(text)
