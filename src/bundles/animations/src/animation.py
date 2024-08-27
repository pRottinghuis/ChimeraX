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
            self.session.logger.warning("Can't create keyframe because time must be an integer or float.")
            return
        self.keyframes[scene_name] = time

    def play(self):
        pass

    def reset_state(self, session):
        self.clear()

    def take_snapshot(self, session, flags):
        return {
            'version': self.version
        }

    @staticmethod
    def restore_snapshot(session, data):
        return Animation(session, animation_data=data)
