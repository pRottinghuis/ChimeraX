from chimerax.core.state import StateManager


class Animation(StateManager):

    version = 0
    fps = 60

    def __init__(self, session, *, animation_data=None):
        self.session = session
        # dict of steps to interpolate animation. Each step is a tuple of (scene_name1, scene_name2, %) interpolation
        # steps
        self._lerp_steps: [(str, str, int | float)] = []
        if animation_data is None:
            # dict of scene_name to float for time in seconds. All animations will start at 0.
            self.keyframes: {str, float} = {}
            self.length = 5 # in seconds
        else:
            raise NotImplementedError("Restoring from snapshot not implemented yet.")
            self.animation_data = animation_data

    def add_keyframe(self, keyframe_name, time):
        """
        Add a keyframe to the animation. The keyframe will be created at the time specified.
        """
        if self.keyframe_exists(keyframe_name):
            self.session.logger.warning(f"Can't create keyframe {keyframe_name} because it already exists.")
            return
        scenes = self.session.scenes.get_scene(keyframe_name)
        if scenes is None:
            self.session.logger.warning(f"Can't create keyframe for scene {keyframe_name} because it doesn't exist.")
            return
        if not self.validate_time(time):
            self.logger.warning(f"Can't create keyframe {keyframe_name} because time {time} is invalid.")
            return
        self.keyframes[keyframe_name] = time
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

    def _gen_lerp_steps(self):
        if len(self.keyframes) < 1:
            self.session.logger.warning(f"Can't generate lerp steps because there are no keyframes.")
            return

        # tuple val to store previously iterated keyframe (keyframe name, time).
        prev_kf_name = None
        prev_kf_time = None
        # ittr all the keyframes
        for keyframe_name, time in self.keyframes.items():
            # calculate delta time between keyframes. If prev_kf is None, then delta t is keyframe time minus start of
            # animation time
            if prev_kf_time is None:
                d_time = time - 0
            else:
                d_time = time - prev_kf_time

            if prev_kf_name is None:
                # if prev_kf is None, then we are at the first keyframe. Assume the first keyframe is the state of
                # the animation between 0 and the first keyframe time, so we essentially make duplicate
                # frames from time 0 to the first keyframe
                kf_lerp_steps = self._gen_ntime_lerp_segment(keyframe_name, keyframe_name, d_time)
            else:
                kf_lerp_steps = self._gen_ntime_lerp_segment(prev_kf_name, keyframe_name, d_time)

            # append the lerp steps connecting the two keyframes to the main lerp steps list
            self._lerp_steps.extend(kf_lerp_steps)

            # reset previous ittr keyframe vars
            prev_kf_name = keyframe_name
            prev_kf_time = time

        # Still need to add the last keyframe to the end of the animation. Same deal as the 0:00 - first keyframe with
        # assuming the last keyframe is the state of the animation between the last keyframe and the end of the
        # animation

        # calculate delta time between last keyframe and end of animation time
        d_time = self.length - prev_kf_time
        # create lerp steps between last keyframe and end of animation. prev_kf will be the last keyframe bc of the loop
        kf_lerp_steps = self._gen_ntime_lerp_segment(prev_kf_name, prev_kf_name, d_time)
        # append the lerp steps connecting the last keyframe to the end of the animation to the main lerp steps list
        self._lerp_steps.extend(kf_lerp_steps)


    def _gen_ntime_lerp_segment(self, kf1, kf2, d_time):
        # calculate number of steps/frames between keyframes using delta time and fps. Must be whole number
        n_frames = round(d_time * self.fps)

        # create an array of % decimals that linearly range (0.0, 1.0) in n_frames steps
        fractions = [i / (n_frames - 1) for i in range(n_frames)]

        # return an array of tuples of (kf1, kf2, fraction) for each fraction in fractions
        return [(kf1, kf2, f) for f in fractions]

    def _sort_keyframes(self):
        """Sort keyframes by time. Should be called after any changes to keyframes."""
        self.keyframes = dict(sorted(self.keyframes.items(), key=lambda item: item[1]))

    def validate_time(self, time):
        if not isinstance(time, (int, float)):
            self.session.logger.warning(f"Time must be an integer or float")
            return False
        if time < 0 or time > self.length:
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

    def get_num_keyframes(self):
        return len(self.keyframes)

    def reset_state(self, session):
        self.clear()

    def take_snapshot(self, session, flags):
        return {
            'version': self.version
        }

    @staticmethod
    def restore_snapshot(session, data):
        return Animation(session, animation_data=data)
