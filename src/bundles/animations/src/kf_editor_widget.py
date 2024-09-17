from Qt.QtWidgets import (QGraphicsPixmapItem, QGraphicsItem, QGraphicsView, QGraphicsScene,
                          QVBoxLayout, QWidget, QGraphicsTextItem, QGraphicsLineItem, QGraphicsItemGroup, QPushButton,
                          QSizePolicy, QLabel,
                          QHBoxLayout, QStyle, QGraphicsRectItem)
from Qt.QtCore import QByteArray, Qt, QPointF, QLineF, QObject, Signal, QSize, QTimer, QRectF
from Qt.QtGui import QPixmap, QPen, QTransform, QBrush
from .animation import Animation
from .animation import format_time
from .triggers import (MGR_KF_ADDED, MGR_KF_DELETED, MGR_KF_EDITED, MGR_LENGTH_CHANGED, MGR_PREVIEWED, KF_ADD,
                       KF_DELETE, KF_EDIT, LENGTH_CHANGE, PREVIEW, PLAY, add_handler, activate_trigger,
                       MGR_FRAME_PLAYED, RECORD, STOP_PLAYING, REMOVE_TIME, INSERT_TIME, remove_handler, STOP_RECORDING, MGR_RECORDING_STOP, MGR_RECORDING_START)


class KeyframeEditorWidget(QWidget):
    def __init__(self, length, keyframes):
        """
        :param length: Length of the timeline in seconds
        :param keyframes: List of animation.Keyframe objects
        """
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.handlers = []

        # Time label
        self.time_label_layout = QHBoxLayout()
        self.time_label = QLabel()
        self.time_label_layout.addWidget(self.time_label)
        self.layout.addLayout(self.time_label_layout)

        # Keyframe editor graphics view widget
        self.kfe_view = KFEGraphicsView(self)
        self.kfe_scene = KeyframeEditorScene(length, keyframes)
        self.kfe_view.setScene(self.kfe_scene)
        self.layout.addWidget(self.kfe_view)

        # Connect time label triggers. Must be done after the KeyframeEditor widget is created because depends on
        # the keyframe editor scene.
        self.update_time_label(0)
        self.handlers.append(add_handler(MGR_PREVIEWED, lambda trigger_name, time: self.update_time_label(time)))
        self.handlers.append(add_handler(MGR_FRAME_PLAYED, lambda trigger_name, time: self.update_time_label(time)))
        # This handler is needed for when the cursor is moved but there is no manager preview call. This happens if
        # There are no keyframes in the animation.
        self.handlers.append(add_handler(PREVIEW, lambda trigger_name, time: self.update_time_label(time)))

        # Horizontal layout for navigation buttons
        self.button_layout = QHBoxLayout()

        # Rewind button
        self.rewind_button = QPushButton()
        self.rewind_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.button_layout.addWidget(self.rewind_button)
        self.rewind_button.clicked.connect(self.rewind)

        # Play button
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.button_layout.addWidget(self.play_button)
        self.play_button.clicked.connect(
            lambda: activate_trigger(PLAY, (self.kfe_scene.get_cursor().get_time(), False)))

        # Pause button
        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.button_layout.addWidget(self.pause_button)
        self.pause_button.clicked.connect(lambda: activate_trigger(STOP_PLAYING, None))

        # Fast forward button
        self.fast_forward_button = QPushButton()
        self.fast_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.button_layout.addWidget(self.fast_forward_button)
        self.fast_forward_button.clicked.connect(self.fast_forward)

        # Record button
        self.record_button = QPushButton("Record")
        self.record_button.setCheckable(True)
        self.button_layout.addWidget(self.record_button)
        self.record_button.clicked.connect(self.recording_toggle)
        self.handlers.append(add_handler(MGR_RECORDING_START, lambda trigger_name, data: self.record_button.setChecked(True)))
        self.handlers.append(add_handler(MGR_RECORDING_STOP, lambda trigger_name, data: self.record_button.setChecked(False)))

        # Add button
        self.add_button = QPushButton("Add")
        self.button_layout.addWidget(self.add_button)
        self.add_button.clicked.connect(lambda: activate_trigger(KF_ADD, self.kfe_scene.get_cursor().get_time()))

        # Delete button
        self.delete_button = QPushButton("Delete")
        self.button_layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(lambda: self.delete_keyframes())

        self.layout.addLayout(self.button_layout)

        # Layout for all the time adjustment buttons
        self.time_buttons_layout = QHBoxLayout()

        remove_large = -5
        remove_medium = -2
        remove_small = -0.5

        insert_small = 0.5
        insert_medium = 2
        insert_large = 5

        # Remove buttons
        for adjustment in [remove_large, remove_medium, remove_small, insert_small, insert_medium, insert_large]:
            self.add_time_adjustment_button(adjustment)

        self.layout.addLayout(self.time_buttons_layout)

    def add_time_adjustment_button(self, d_time):
        button = QPushButton(f"{d_time}s")
        if d_time < 0:
            trigger_activation = lambda: activate_trigger(
                REMOVE_TIME, (self.kfe_scene.get_cursor().get_time(), d_time * -1))
        else:
            trigger_activation = lambda: activate_trigger(
                INSERT_TIME, (self.kfe_scene.get_cursor().get_time(), d_time))
        button.clicked.connect(trigger_activation)
        self.time_buttons_layout.addWidget(button)

    def update_time_label(self, time):
        self.time_label.setText(f"{format_time(time)} / {format_time(self.kfe_scene.timeline.get_time_length())}")

    def rewind(self):
        activate_trigger(STOP_PLAYING, None)
        cursor = self.kfe_scene.get_cursor()
        cursor.set_pos_from_time(0)
        self.kfe_view.horizontalScrollBar().setValue(0)
        self.kfe_scene.get_cursor().activate_preview_trigger()

    def fast_forward(self):
        activate_trigger(STOP_PLAYING, None)
        cursor = self.kfe_scene.get_cursor()
        timeline_len = self.kfe_scene.timeline.get_time_length()
        cursor.set_pos_from_time(timeline_len)
        self.kfe_view.horizontalScrollBar().setValue(self.kfe_view.horizontalScrollBar().maximum())
        self.kfe_scene.get_cursor().activate_preview_trigger()

    def delete_keyframes(self):
        keyframes = self.kfe_scene.get_selected_keyframes()
        for keyframe in keyframes:
            activate_trigger(KF_DELETE, keyframe.get_name())

    def recording_toggle(self):
        """
        Recording toggle is called when the record button is clicked.
        """
        if self.record_button.isChecked():
            # Clicking on the button flips the checked state automatically. We don't want automatic because we only
            # want it checked if the animation has actually started recording. It is important that this reset happens
            # before we trigger a start or stop recording because the handlers for the managers start stop recording
            # will set the checked state properly and that code is run as soon as the trigger is activated. If the
            # manager start stop doesn't get called we need to make sure that our button is set to unchecked.
            self.record_button.setChecked(False)
            activate_trigger(RECORD, None)
        else:
            # Same reset situation here as above
            self.record_button.setChecked(False)
            activate_trigger(STOP_RECORDING, None)

    def remove_handlers(self):
        for handler in self.handlers:
            remove_handler(handler)
        self.kfe_scene.remove_handlers()


class KFEGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.auto_scroll)
        self.scroll_timer.start(50)  # Check every 50 ms
        self._is_dragging_cursor = False

    def sizeHint(self):
        # Get the current scene rectangle
        scene_rect = self.scene().sceneRect()
        width = min(700, int(scene_rect.width()))
        height = int(scene_rect.height() + 400)
        return QSize(width, height)

    def auto_scroll(self):
        if not self._is_dragging_cursor:
            return

        cursor_pos = self.mapFromGlobal(self.cursor().pos())

        # slow scroll margin must be > fast scroll margin. Refers to how many pixels from the edge into the view
        slow_scroll_margin = 20  # Margin in pixels to start slow scrolling
        fast_scroll_margin = -20  # Margin in pixels to start fast scrolling

        scroll_speed = 10  # Pixels per scroll
        fast_scroll_speed = 50  # Pixels per scroll

        if cursor_pos.x() < fast_scroll_margin:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - fast_scroll_speed)
        if cursor_pos.x() < slow_scroll_margin:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - scroll_speed)
        elif cursor_pos.x() > self.viewport().width() - fast_scroll_margin:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + fast_scroll_speed)
        elif cursor_pos.x() > self.viewport().width() - slow_scroll_margin:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + scroll_speed)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging_cursor = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging_cursor = False
        super().mouseReleaseEvent(event)


class KeyframeEditorScene(QGraphicsScene):
    def __init__(self, length, keyframes):
        super().__init__()
        self.handlers = []
        self.timeline = Timeline(time_length=length)
        self.addItem(self.timeline)
        self.cursor = TimelineCursor(QPointF(0, 0), 70, self.timeline)
        self.addItem(self.cursor)
        self.keyframes = {}  # Dictionary of keyframe name to KeyframeItem

        # Box for highlight drag.
        self.selection_box = None
        self.selection_start_pos = None

        for kf in keyframes:
            self.add_kf_item(kf)

        # Connect triggers from the animation manager in the session to the keyframe editor
        self.handlers.append(add_handler(MGR_KF_ADDED, lambda trigger_name, data: self.add_kf_item(data)))
        self.handlers.append(add_handler(MGR_KF_EDITED, lambda trigger_name, data: self.handle_keyframe_edit(data)))
        self.handlers.append(add_handler(MGR_KF_DELETED, lambda trigger_name, data: self.delete_kf_item(data)))
        self.handlers.append(add_handler(MGR_LENGTH_CHANGED, lambda trigger_name, data: self.animation_len_changed(data)))
        self.handlers.append(add_handler(MGR_PREVIEWED, lambda trigger_name, data: self.cursor.set_pos_from_time(data)))
        self.handlers.append(add_handler(MGR_FRAME_PLAYED, lambda trigger_name, data: self.cursor.set_pos_from_time(data)))

        self.selectionChanged.connect(self.on_selection_changed)

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

    def handle_keyframe_edit(self, kf):
        """
        Move a keyframe item to a new time.
        :param kf: animations.Keyframe object
        """
        keyframe_item = self.keyframes[kf.get_name()]
        if keyframe_item is None:
            raise ValueError(f"Keyframe graphics item with name {kf.get_name()} not found.")
        keyframe_item.set_position_from_time(kf.get_time())
        self.cursor.activate_preview_trigger()

    def delete_kf_item(self, kf):
        """
        Delete a keyframe item from the scene.
        :param kf: animations.Keyframe object
        """
        keyframe_item = self.keyframes.pop(kf.get_name())
        self.removeItem(keyframe_item)

    def update_scene_size(self):
        margin = 10  # Margin in pixels on each side
        scene_width = self.timeline.get_pix_length() + 2 * margin  # Total width including margins
        self.setSceneRect(-margin, 0, scene_width, self.height())

    def animation_len_changed(self, length):
        self.timeline.set_time_length(length)
        if self.cursor.x() > self.timeline.x() + self.timeline.get_pix_length():
            self.cursor.setX(self.timeline.x() + self.timeline.get_pix_length())
        self.cursor.activate_preview_trigger()
        self.update_scene_size()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            clicked_pos = event.scenePos()
            if not isinstance(self.itemAt(clicked_pos, QTransform()), KeyframeItem):
                self.clearSelection()
            if self.timeline.contains(clicked_pos):
                self.cursor.setPos(clicked_pos)

            # Activate a selection box if click happened in blank space.
            if not self.itemAt(clicked_pos, QTransform()):
                self.start_selection_box(clicked_pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Adjust the selection box if it has been started.
        if self.selection_box:
            current_pos = event.scenePos()
            rect = QRectF(self.selection_start_pos, current_pos).normalized()
            self.selection_box.setRect(rect)
            for keyframe_item in self.keyframes.values():
                if rect.intersects(keyframe_item.sceneBoundingRect()):
                    keyframe_item.setSelected(True)
                else:
                    keyframe_item.setSelected(False)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event, QGraphicsSceneMouseEvent=None):
        if event.button() == Qt.LeftButton:
            keyframes = self.get_selected_keyframes()
            for keyframes in keyframes:
                keyframes.trigger_for_edit()

            # End the selection box if it has been started.
            if self.selection_box:
                self.end_selection_box(event.scenePos())
        super().mouseReleaseEvent(event)

    def start_selection_box(self, pos):
        self.selection_start_pos = pos
        self.selection_box = QGraphicsRectItem(QRectF(pos, pos))
        self.selection_box.setPen(QPen(Qt.yellow, 1, Qt.DashLine))
        self.selection_box.setBrush(QBrush(Qt.transparent))
        self.addItem(self.selection_box)

    def end_selection_box(self, pos):
        self.removeItem(self.selection_box)
        self.selection_box = None
        self.selection_start_pos = None

    def on_selection_changed(self):
        selected_keyframes = self.get_selected_keyframes()
        for item in self.items():
            if isinstance(item, KeyframeItem):
                if item not in selected_keyframes:
                    item.hide_info()
                else:
                    item.show_info()

    def remove_handlers(self):
        for handler in self.handlers:
            remove_handler(handler)

    def get_selected_keyframes(self):
        selected_keyframes = []
        for item in self.selectedItems():
            if isinstance(item, KeyframeItem):
                selected_keyframes.append(item)
        return selected_keyframes

    def get_cursor(self):
        return self.cursor


class Timeline(QGraphicsItemGroup):
    SCALE = 60  # Scale factor. Pixels per second.

    def __init__(self, time_length=5, interval=0.1, major_interval=1, tick_length=10, major_tick_length=20):
        """
        :param time_length: Length of the timeline in seconds
        :param interval: Interval between tick marks in seconds
        :param major_interval: Interval between major tick marks in seconds
        :param tick_length: Length of the tick marks in pixels
        :param major_tick_length: Length of the major tick marks in pixels
        """
        # TODO convert interval from pixels to time and do the same for major_interval
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

        pixel_interval = int(self.interval * self.SCALE)
        pixel_major_interval = int(self.major_interval * self.SCALE)

        # Clear existing tick marks and labels
        for item in self.childItems():
            self.removeFromGroup(item)
            self.scene().removeItem(item)

        for i in range(0, self.pix_length + 1, pixel_interval):
            position = QPointF(i, y_position)
            if i % pixel_major_interval == 0:
                tick_mark = QGraphicsLineItem(
                    QLineF(position, QPointF(position.x(), position.y() + self.major_tick_length)))
                tick_mark.setPen(QPen(Qt.gray, 1))
                self.addToGroup(tick_mark)

                time_label = QGraphicsTextItem(f"{i // pixel_major_interval}")
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

    def get_time_length(self):
        return self.time_length


class KeyframeItem(QGraphicsPixmapItem):
    SIZE = 50

    def __init__(self, name, pixmap, position, timeline: Timeline):
        super().__init__(pixmap)
        self.setFlags(
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges | QGraphicsItem.ItemIsSelectable)
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
        self.show_info()  # Show hover info
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.isSelected():
            self.hide_info()
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
                    return old_x
        return new_x

    def trigger_for_edit(self):
        new_time = (float(self.timeline.get_time_for_pos(self.x() + self.boundingRect().width() / 2)))
        activate_trigger(KF_EDIT, (self.name, new_time))

    def show_info(self):
        self.hover_info.show()

    def hide_info(self):
        self.hover_info.hide()

    def set_position_from_time(self, time):
        new_x = self.timeline.get_pos_for_time(time) - self.boundingRect().width() / 2
        self.setX(new_x)

    def set_info_time(self, time: int | float):
        self.hover_info.setPlainText(format_time(time))

    def get_name(self):
        return self.name


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
            rtn_point = QPointF(value.x(), self.y())
            if value.x() < self.timeline.x():
                rtn_point = QPointF(self.timeline.x(), self.y())
            elif value.x() > self.timeline.x() + self.timeline.get_pix_length():
                rtn_point = QPointF(self.timeline.x() + self.timeline.get_pix_length(), self.y())
            return rtn_point

        return super().itemChange(change, value)

    def set_pos_from_time(self, time):
        new_x = self.timeline.get_pos_for_time(time)
        self.setX(new_x)

    def get_time(self):
        return self.timeline.get_time_for_pos(self.x())

    def mouseReleaseEvent(self, event):
        self.activate_preview_trigger()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event, QGraphicsSceneMouseEvent=None):
        self.activate_preview_trigger()
        super().mouseMoveEvent(event)

    def activate_preview_trigger(self):
        activate_trigger(PREVIEW, round(self.get_time(), 2))


class TickMarkItem(QGraphicsLineItem):
    def __init__(self, position, length):
        super().__init__(QLineF(position, QPointF(position.x(), position.y() + length)))
        self.setPen(QPen(Qt.gray, 1))


class TickIntervalLabel(QGraphicsTextItem):
    def __init__(self, text):
        super().__init__(text)