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
            print(f"Scene {scene_name} does not exist")
            return

        self.keyframes[scene_name] = time

    def play(self):
        pass

    def take_snapshot(self, session, flags):
        return {
            'version': self.version
        }

    @staticmethod
    def restore_snapshot(session, data):
        return Animation(session, animation_data=data)
