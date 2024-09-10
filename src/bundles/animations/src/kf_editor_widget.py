from Qt.QtWidgets import QGridLayout, QLabel, QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene, \
    QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem, QGraphicsItemGroup, QPushButton
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF, QObject, Signal
from Qt.QtGui import QPixmap, QPen
from .animation import Animation
from .animation import format_time
from .triggers import (MGR_KF_ADDED, MGR_KF_DELETED, MGR_KF_EDITED, MGR_LENGTH_CHANGED, MGR_PREVIEWED, KF_ADD,
                       KF_DELETE, KF_EDIT, LENGTH_CHANGE, PREVIEW, add_handler, activate_trigger)


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
        len_update = self.kfe_scene.timeline.time_length + 1
        self.kfe_scene.set_timeline_length(len_update)


class KeyframeEditorScene(QGraphicsScene):
    def __init__(self, length, keyframes):
        super().__init__()
        self.timeline = Timeline(time_length=length)
        self.addItem(self.timeline)
        self.cursor = TimelineCursor(QPointF(0, 0), 70, self.timeline)
        self.addItem(self.cursor)
        self.keyframes = {}

        for kf in keyframes:
            self.add_kf_item(kf)

        # Connect triggers from the animation manager in the session to the keyframe editor
        add_handler(MGR_KF_ADDED, lambda trigger_name, data: self.add_kf_item(data))
        add_handler(MGR_KF_EDITED, lambda trigger_name, data: self.move_keyframe_item(data))
        add_handler(MGR_KF_DELETED, lambda trigger_name, data: self.delete_kf_item(data))
        add_handler(MGR_LENGTH_CHANGED, lambda trigger_name, data: self.set_timeline_length(data))
        add_handler(MGR_PREVIEWED, lambda trigger_name, data: self.cursor.set_pos_from_time(data))

    def add_kf_item(self, kf):
        """
        Add a keyframe item to the scene.
        :param kf: animations.Keyframe object
        """
        thumbnail_bytes = kf.get_thumbnail()
        pixmap = QPixmap()
        pixmap.loadFromData(thumbnail_bytes, "JPEG")
        pixmap = pixmap.scaled(KeyframeItem.SIZE, KeyframeItem.SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        kf_item_x = self.timeline.get_pos_for_time(kf.get_time()) - KeyframeItem.SIZE / 2
        keyframe_item = KeyframeItem(kf.get_name(), pixmap, QPointF(kf_item_x, 0),
                                     self.timeline)
        # Need to update the info label on the keyframe graphic item. Placing on the timeline
        # automatically does a pos to time conversion based on the timeline.
        # However, 1 pixel change may be a 0.02 change in time.
        keyframe_item.set_info_time(kf.get_time())
        self.keyframes[kf.get_name()] = keyframe_item
        self.addItem(keyframe_item)

    def move_keyframe_item(self, kf):
        """
        Move a keyframe item to a new time.
        :param kf: animations.Keyframe object
        """
        keyframe_item = self.keyframes[kf.get_name()]
        if keyframe_item is None:
            raise ValueError(f"Keyframe graphics item with name {kf.get_name()} not found.")
        keyframe_item.set_position_from_time(kf.get_time())

    def delete_kf_item(self, kf):
        """
        Delete a keyframe item from the scene.
        :param kf: animations.Keyframe object
        """
        keyframe_item = self.keyframes.pop(kf.get_name())
        self.removeItem(keyframe_item)

    def update_scene_size(self):
        scene_width = self.timeline.get_pix_length() + 20  # Slightly wider than the timeline
        self.setSceneRect(0, 0, scene_width, self.height())

    def set_timeline_length(self, length):
        self.timeline.set_time_length(length)
        self.update_scene_size()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            clicked_pos = event.scenePos()
            if self.timeline.contains(clicked_pos):
                self.cursor.setPos(clicked_pos)
        super().mousePressEvent(event)


class Timeline(QGraphicsItemGroup):

    SCALE = 60  # Scale factor. Pixels per second.

    def __init__(self, time_length=5, interval=6, major_interval=60, tick_length=10, major_tick_length=20):
        # TODO convert length param into seconds and update the tick marks accordingly
        super().__init__()
        self.time_length = time_length  # Length of the timeline in seconds
        # Length of the timeline in pixels. Can only be a whole number of pixels.
        self.pix_length = round(time_length * self.SCALE)
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

        for i in range(0, self.pix_length + 1, self.interval):
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

    def get_pix_length(self):
        return self.pix_length

    def get_pos_for_time(self, time):
        return round(time * self.SCALE)

    def get_time_for_pos(self, pos_x):
        """
        Convert a position on the timeline to a time in seconds.
        :param pos_x: X position on the timeline
        """
        calc_time = pos_x / self.SCALE
        if calc_time < 0:
            return 0
        elif calc_time > self.time_length:
            return self.time_length
        else:
            return calc_time

    def set_time_length(self, length):
        """
        Set the length of the timeline.
        :param length: Length of the timeline in seconds
        """
        self.time_length = length
        self.pix_length = round(self.time_length * self.SCALE)
        self.update_tick_marks()


class KeyframeItem(QGraphicsPixmapItem):

    SIZE = 50

    def __init__(self, name, pixmap, position, timeline: Timeline):
        super().__init__(pixmap)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.name = name
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
            elif value.x() > self.timeline.x() + self.timeline.get_pix_length() - half_width:
                new_x = self.timeline.x() + self.timeline.get_pix_length() - half_width
            else:
                new_x = value.x()

            new_x = self.avoid_collision(new_x, self.x())

            # Update the info text
            time = self.timeline.get_time_for_pos(new_x + half_width)
            self.hover_info.setPlainText(format_time(time))

            return QPointF(new_x, 0)

        return super().itemChange(change, value)

    def avoid_collision(self, new_x, old_x):
        """
        Check if the new x position is taken by another keyframe item.
        If it is, move this item over the blocking item in the direction that the drag was initiated.
        :param new_x: New x position trying to move to
        :param old_x: Old x position moving from
        """

        # First time this is called is from the constructor so this GraphicsItem has not been added to the scene yet.
        if self.scene() is None:
            return new_x

        # Iterate over all items in the scene
        for item in self.scene().items():
            # Check if the item is a KeyframeItem and is not the current item
            if isinstance(item, KeyframeItem) and item is not self:
                # Check if the x position is taken by another item
                if item.x() == new_x:
                    # Move this item over the blocking item in the direction that the drag was initiated.
                    if old_x < new_x:
                        new_x += 1
                    else:
                        new_x -= 1
        return new_x

    def mouseReleaseEvent(self, event):
        new_time = (float(self.timeline.get_time_for_pos(self.x() + self.boundingRect().width() / 2)))
        activate_trigger(KF_EDIT, (self.name, new_time))
        super().mouseReleaseEvent(event)

    def set_position_from_time(self, time):
        new_x = self.timeline.get_pos_for_time(time) - self.boundingRect().width() / 2
        self.setX(new_x)

    def set_info_time(self, time: int | float):
        self.hover_info.setPlainText(format_time(time))


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
            elif value.x() > self.timeline.x() + self.timeline.get_pix_length():
                return QPointF(self.timeline.x() + self.timeline.get_pix_length(), self.y())
            return QPointF(value.x(), self.y())
        return super().itemChange(change, value)

    def set_pos_from_time(self, time):
        new_x = self.timeline.get_pos_for_time(time)
        self.setX(new_x)

    def mouseReleaseEvent(self, event):
        new_time = round(float(self.timeline.get_time_for_pos(self.x())), 2)
        activate_trigger(PREVIEW, new_time)
        super().mouseReleaseEvent(event)


class TickMarkItem(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setPen(QPen(Qt.gray, 1))


class TickIntervalLabel(QGraphicsTextItem):
    def __init__(self, text):
        super().__init__(text)
