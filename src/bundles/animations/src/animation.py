from chimerax.core.state import StateManager


class Animation(StateManager):

    version = 0
    fps = 60

    def __init__(self, session, *, animation_data=None):
        self.session = session
        if animation_data is None:
            # dict of scene_name to float for time in seconds. All animations will start at 0.
            self.keyframes: {str, float} = {}
            self.length = 5 # in seconds
        else:
            raise NotImplementedError("Restoring from snapshot not implemented yet.")
            self.animation_data = animation_data

    def add_keyframe(self, scene_name, time):
        scenes = self.session.scenes.get_scene(scene_name)
        if scenes is None:
            self.session.logger.warning(f"Can't create keyframe for scene {scene_name} because it doesn't exist.")
            return
        if not self.validate_time(time):
            self.logger.warning(f"Can't create keyframe {scene_name} because time {time} is invalid.")
            return
        self.keyframes[scene_name] = time
        self._sort_keyframes()

    def edit_keyframe_time(self, keyframe_name, time):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't edit keyframe {keyframe_name} because it doesn't exist.")
            return
        if not self.validate_time(time):
            self.logger.warning(f"Can't create keyframe {keyframe_name} because time {time} is invalid.")
            return
        self.keyframes[keyframe_name] = time
        self._sort_keyframes()

    def delete_keyframe(self, keyframe_name):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't delete keyframe {keyframe_name} because it doesn't exist.")
            return
        del self.keyframes[keyframe_name]
        self.session.logger.info(f"Deleted keyframe {keyframe_name}")

    def list_keyframes(self) -> list[str]:
        """List all keyframes in the animation with this format: keyframe_name: time(min:sec:millisecond)"""
        keyframe_list = []
        for keyframe_name, time in self.keyframes.items():
            keyframe_list.append(f"{keyframe_name}: {self._format_time(time)}")
        return keyframe_list

    def play(self):
        pass

    def _sort_keyframes(self):
        """Sort keyframes by time. Should be called after any changes to keyframes."""
        self.keyframes = dict(sorted(self.keyframes.items(), key=lambda item: item[1]))

    def validate_time(self, time):
        if not isinstance(time, (int, float)):
            self.session.logger.warning(f"Time must be an integer or float")
            return False
        if time < 0 | time > self.length:
            self.session.logger.warning(f"Time must be between 0 and {self.length}")
            return False
        if time in self.keyframes.values():
            self.session.logger.warning(f"Time {time} is already taken by a different keyframe.")
            return False
        return True

    def _format_time(self, time):
        """Convert time in seconds to min:sec.__ format."""
        minutes = int(time // 60)
        seconds = int(time % 60)
        fractional_seconds = round(time % 1, 2)
        return f"{minutes}:{seconds:02}.{int(fractional_seconds * 100):02}"

    def keyframe_exists(self, keyframe_name):
        return keyframe_name in self.keyframes

    def reset_state(self, session):
        self.clear()

    def take_snapshot(self, session, flags):
        return {
            'version': self.version
        }

    @staticmethod
    def restore_snapshot(session, data):
        return Animation(session, animation_data=data)
