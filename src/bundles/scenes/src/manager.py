# vim: set expandtab shiftwidth=4 softtabstop=4:

# === UCSF ChimeraX Copyright ===
# Copyright 2022 Regents of the University of California. All rights reserved.
# The ChimeraX application is provided pursuant to the ChimeraX license
# agreement, which covers academic and commercial uses. For more details, see
# <http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html>
#
# This particular file is part of the ChimeraX library. You can also
# redistribute and/or modify it under the terms of the GNU Lesser General
# Public License version 2.1 as published by the Free Software Foundation.
# For more details, see
# <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>
#
# THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
# EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. ADDITIONAL LIABILITY
# LIMITATIONS ARE DESCRIBED IN THE GNU LESSER GENERAL PUBLIC LICENSE
# VERSION 2.1
#
# This notice must be embedded in or attached to all copies, including partial
# copies, of the software or any revisions or derivations thereof.
# === UCSF ChimeraX Copyright ===

from chimerax.core.state import StateManager
from chimerax.graphics.gsession import ViewState
from .scene import Scene


class SceneManager(StateManager):
    """Manager for scenes"""

    ADDED, DELETED = trigger_names = ("added", "deleted")

    def __init__(self, session):

        self.scenes: {str, Scene} = {}  # name -> Scene
        self.session = session
        from chimerax.core.triggerset import TriggerSet
        self.triggers = TriggerSet()
        for trig_name in self.trigger_names:
            self.triggers.add_trigger(trig_name)
        from chimerax.core.models import REMOVE_MODELS
        session.triggers.add_handler(REMOVE_MODELS, self._remove_models_cb)

    def delete_scene(self, scene_name):
        del self.scenes[scene_name]
        self.triggers.activate_trigger(self.DELETED, scene_name)

    def clear(self):
        for scene_name in list(self.scenes.keys()):
            self.delete_scene(scene_name)

    def save_scene(self, scene_name):
        """Save scene named 'scene_name'"""
        if scene_name in self.scenes:
            self.delete_scene(scene_name)
        self.scenes[scene_name] = Scene(self.session)
        return

    def restore_scene(self, scene_name):
        """Restore scene named 'scene_name'"""
        if scene_name in self.scenes:
            self.scenes[scene_name].restore_scene()
        return

    def interpolate_scenes(self, scene_name1, scene_name2, fraction):
        """Interpolate between two scenes"""
        if scene_name1 in self.scenes and scene_name2 in self.scenes:
            scene1 = self.scenes[scene_name1]
            scene2 = self.scenes[scene_name2]
            ViewState.interpolate(
                self.session.view,
                scene1.main_view_data,
                scene2.main_view_data,
                fraction
            )

            # Use NamedViews to interpolate camera, clip planes, and model positions. See _InterpolateViews
            from chimerax.std_commands.view import _interpolate_views, _model_motion_centers
            view1 = scene1.named_view
            view2 = scene2.named_view
            centers = _model_motion_centers(view1.positions, view2.positions)
            _interpolate_views(view1, view2, fraction, self.session.main_view, centers)
        return

    def _remove_models_cb(self, trig_name, models):
        for scene in self.scenes.values():
            scene.models_removed(models)

    # session methods
    def reset_state(self, session):
        self.clear()

    @staticmethod
    def restore_snapshot(session, data):
        mgr = session.scenes
        mgr._ses_restore(data)
        return mgr

    def take_snapshot(self, session, flags):
        # viewer_info is "session independent"
        return {
            'version': 1,
            'scenes': self.scenes,
        }

    def _ses_restore(self, data):
        self.clear()
        self.scenes = data['scenes']
        for scene_name in self.scenes.keys():
            self.triggers.activate(self.ADDED, scene_name)
