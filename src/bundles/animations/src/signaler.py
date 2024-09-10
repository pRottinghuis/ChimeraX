from Qt.QtCore import QObject, Signal


class KFESignalManager(QObject):
    _instance = None
    inst_check = -1

    keyframe_time_edit = Signal(tuple)  # (keyframe_name, new_time)
    preview_time_changed = Signal(float)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KFESignalManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance
