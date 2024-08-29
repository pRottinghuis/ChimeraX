from chimerax.core.state import StateManager
from chimerax.core.commands.motion import CallForNFrames
from chimerax.core.triggerset import TriggerSet


class Animation(StateManager):
    version = 0
    fps = 144

    FINISHED = trigger_names = ("finished",)

    def __init__(self, session, *, animation_data=None):

        # TODO - Define a trigger for when the animation is done playing. Connect a handdler that checks if a recording
        #  is active and stops it if it is.

        self.session = session
        self.triggers = TriggerSet()
        for trig_name in self.trigger_names:
            self.triggers.add_trigger(trig_name)
        # dict of steps to interpolate animation. Each step is a tuple of (scene_name1, scene_name2, %) interpolation
        # steps
        self._lerp_steps: [(str, str, int | float)] = []
        self._need_frames_update = True
        if animation_data is None:
            # dict of scene_name to float for time in seconds. All animations will start at 0.
            self.keyframes: {str, float} = {}
            self.length = 5  # in seconds
        else:
            self.keyframes = animation_data['keyframes']
            self.length = animation_data['length']

    def add_keyframe(self, keyframe_name: str, time: int | float | None = None):
        """
        Add a keyframe to the animation. The keyframe will be created at the time specified.
        """

        # If there is no time param specified, then the keyframe should be created 1 second after the last keyframe or
        # 1 second after the start of the animation if there are no keyframes.
        if time is None:
            kf_time = self._last_kf_time() + 1
            if kf_time > self.length:
                self.length = kf_time
                self.session.logger.info(f"Updated animation length to {self._format_time(self.length)}")
        else:
            kf_time = time

        if self.keyframe_exists(keyframe_name):
            self.session.logger.warning(f"Can't create keyframe {keyframe_name} because it already exists.")
            return
        scenes = self.session.scenes.get_scene(keyframe_name)
        if scenes is None:
            self.session.logger.warning(f"Can't create keyframe for scene {keyframe_name} because it doesn't exist.")
            return
        if not self.validate_time(kf_time):
            self.session.logger.warning(f"Can't create keyframe {keyframe_name} because time {kf_time} is invalid.")
            return
        self.keyframes[keyframe_name] = kf_time
        self._sort_keyframes()
        self._need_frames_update = True
        self.session.logger.info(f"Created keyframe: {keyframe_name} at time: {self._format_time(kf_time)}")

    def edit_keyframe_time(self, keyframe_name, time):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't edit keyframe {keyframe_name} because it doesn't exist.")
            return
        if not self.validate_time(time):
            self.logger.warning(f"Can't create keyframe {keyframe_name} because time {time} is invalid.")
            return
        self.keyframes[keyframe_name] = time
        self._sort_keyframes()
        self._need_frames_update = True
        self.session.logger.info(f"Edited keyframe {keyframe_name} to time: {self._format_time(time)}")

    def delete_keyframe(self, keyframe_name):
        if keyframe_name not in self.keyframes:
            self.session.logger.warning(f"Can't delete keyframe {keyframe_name} because it doesn't exist.")
            return
        del self.keyframes[keyframe_name]
        self._need_frames_update = True
        self.session.logger.info(f"Deleted keyframe {keyframe_name}")

    def list_keyframes(self) -> list[str]:
        """List all keyframes in the animation with this format: keyframe_name: time(min:sec:millisecond)"""
        keyframe_list = []
        for keyframe_name, time in self.keyframes.items():
            keyframe_list.append(f"{keyframe_name}: {self._format_time(time)}")
        return keyframe_list

    def preview(self, time):
        if not isinstance(time, (int, float)):
            self.session.logger.warning(f"Time must be an integer or float")
            return
        if time < 0 or time > self.length:
            self.session.logger.warning(f"Time must be between 0 and {self.length}")
            return

        # make sure the interpolation steps are up to date
        self._try_frame_refresh()

        step = round(self.fps * time)
        if step >= len(self._lerp_steps):
            self.session.logger.warning(f"Can't preview animation at time {self._format_time(time)} because trying to "
                                        f"access frame: {step} out of range: {len(self._lerp_steps)}.")
            return
        scene1, scene2, fraction = self._lerp_steps[step]
        self.session.scenes.interpolate_scenes(scene1, scene2, fraction)
        self.session.logger.info(f"Previewing animation at time {self._format_time(time)}")

    def play(self, reverse=False):
        self._try_frame_refresh()

        self.session.logger.status(f"Playing animation...")

        # callback function for each frame
        def frame_cb(session, f):
            if reverse:
                frame_num = len(self._lerp_steps) - f - 1
            else:
                frame_num = f
            # get the lerp step for this frame
            lerp_step = self._lerp_steps[frame_num]
            scene1, scene2, fraction = lerp_step
            self.session.scenes.interpolate_scenes(scene1, scene2, fraction)

        # CallForNFrames s frame_cb for each frame in self._lerp_steps with a frame number param and the session.
        CallForNFrames(frame_cb, len(self._lerp_steps), self.session)

    def _gen_lerp_steps(self):
        if len(self.keyframes) < 1:
            self.session.logger.warning(f"Can't generate lerp steps because there are no keyframes.")
            return

        self.session.logger.info(f"Generating interpolation steps for animation...")

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

        self.session.logger.info(f"Finished generating interpolation steps for animation.")

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

    def _try_frame_refresh(self):
        if self._need_frames_update:
            self._gen_lerp_steps()
            self._need_frames_update = False

    def _last_kf_time(self):
        """
        Get the time of the last keyframe. If there are no keyframes, return 0
        """
        if len(self.keyframes) < 1:
            return 0
        return list(self.keyframes.values())[-1]

    def validate_time(self, time):
        """
        Validate time for keyframe. Time must be a number, between 0 and the length of the animation, and not already
        taken
        """
        if not isinstance(time, (int, float)):
            self.session.logger.warning(f"Time must be an integer or float")
            return False
        if not self.time_in_range(time):
            self.session.logger.warning(f"Time must be between 0 and {self.length}")
            return False
        if time in self.keyframes.values():
            self.session.logger.warning(f"Time {time} is already taken by a different keyframe.")
            return False
        return True

    def time_in_range(self, time):
        return 0 <= time <= self.length

    def get_time_length(self):
        return self.length

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

    def get_frame_rate(self):
        return self.fps

    def reset_state(self, session):
        self._lerp_steps: [(str, str, int | float)] = []
        self._need_frames_update = True
        self.keyframes: {str, float} = {}
        self.length = 5  # in seconds

    def take_snapshot(self, session, flags):
        return {
            'version': self.version,
            'keyframes': self.keyframes,
            'length': self.length,
        }

    @staticmethod
    def restore_snapshot(session, data):
        if Animation.version != data['version']:
            raise ValueError(f"Can't restore snapshot version {data['version']} to version {Animation.version}")

        for scene_name in data['keyframes'].keys():
            if not session.scenes.get_scene(scene_name):
                session.logger.warning(f"Can't restore keyframe {scene_name} because the scene doesn't exist.")
                del data['keyframes'][scene_name]

        return Animation(session, animation_data=data)
