from chimerax.core.state import StateManager


class Animation(StateManager):

    version = 0
    fps = 60

    def __init__(self, session, *, animation_data=None):
        self.session = session
        if animation_data is None:
            # dict of scene_name to float for time in seconds. All animations will start at 0.
            self.keyframes: {str, float} = {}
        else:
            self.animation_data = animation_data

    def add_keyframe(self, scene_name, time):
        scenes = self.session.scenes.get_scene(scene_name)
        if scenes is None:
            self.session.logger.warning(f"Can't create keyframe for scene {scene_name} because it doesn't exist.")
            return
        if not isinstance(time, (int, float)):
            self.session.logger.warning(
                f"Can't create keyframe for scene {scene_name} because time must be an integer or float.")
            return
        if not self.is_time_available(time):
            self.session.logger.warning(
                f"Can't create keyframe for scene {scene_name} because time {time} is already taken by a different "
                f"keyframe.")
            return
        self.keyframes[scene_name] = time

    def edit_keyframe_time(self, keyframe_name, time):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't edit keyframe {keyframe_name} because it doesn't exist.")
            return
        if not isinstance(time, (int, float)):
            self.session.logger.warning(f"Can't edit keyframe {keyframe_name} because time must be an integer or float.")
            return
        if not self.is_time_available(time):
            self.session.logger.warning(
                f"Can't edit keyframe {keyframe_name} because time {time} is already taken by a different keyframe.")
            return
        self.keyframes[keyframe_name] = time

    def delete_keyframe(self, keyframe_name):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't delete keyframe {keyframe_name} because it doesn't exist.")
            return
        del self.keyframes[keyframe_name]
        self.session.logger.info(f"Deleted keyframe {keyframe_name}")


    def play(self):
        pass

    def keyframe_exists(self, keyframe_name):
        return keyframe_name in self.keyframes

    def is_time_available(self, time):
        """Check if the time is available for a new/move keyframe. Don't allow more than 1 keyframe at the same time."""
        return time not in self.keyframes.values()

    def reset_state(self, session):
        self.clear()

    def take_snapshot(self, session, flags):
        return {
            'version': self.version
        }

    @staticmethod
    def restore_snapshot(session, data):
        return Animation(session, animation_data=data)
