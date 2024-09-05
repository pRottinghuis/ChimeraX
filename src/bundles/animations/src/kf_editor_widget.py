from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem, QGraphicsItemGroup
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF
from Qt.QtGui import QPixmap, QPen


class KeyframeEditorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.kfe_view = QGraphicsView(self)
        self.kfe_scene = KeyframeEditorScene()
        self.kfe_view.setScene(self.kfe_scene)
        self.layout.addWidget(self.kfe_view)


class KeyframeEditorScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        for i in range(5):
            pixmap = QPixmap(50, 50)
            pixmap.fill(Qt.blue)
            keyframe = KeyframeItem(pixmap, QPointF(i * 60, 0))
            self.addItem(keyframe)

        self.timeline = Timeline()
        self.addItem(self.timeline)
        self.cursor = TimelineCursor(QPointF(0, 0), 70)
        self.addItem(self.cursor)

    def update_scene_size(self):
        scene_width = self.timeline.length + 20  # Slightly wider than the timeline
        self.setSceneRect(0, 0, scene_width, self.height())

    def set_timeline_length(self, length):
        self.timeline.set_length(length)
        self.update_scene_size()


class KeyframeItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, position):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(position)
        # hold onto a reference to the timeline so that update each keyframe based on the timeline.

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Called before the position has changed.
            # set y to keep the keyframe on the timeline
            return QPointF(value.x(), 0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            pass
            # Called after the position has changed.
        return super().itemChange(change, value)


class TimelineCursor(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPen(QPen(Qt.red, 2))
        self.setZValue(1)  # Render in front of other items

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Called before the position has changed.
            # set y to keep the keyframe on the timeline
            return QPointF(value.x(), 0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            pass
            # Called after the position has changed.
        return super().itemChange(change, value)


class Timeline(QGraphicsItemGroup):
    def __init__(self, length=600, interval=10, major_interval=100, tick_length=10, major_tick_length=20):
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

        for i in range(0, self.length, self.interval):
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


class TickMarkItem(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setPen(QPen(Qt.gray, 1))


class TickIntervalLabel(QGraphicsTextItem):
    def __init__(self, text):
        super().__init__(text)
