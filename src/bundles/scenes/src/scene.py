# vim: set expandtab shiftwidth=4 softtabstop=4:
import io

# === UCSF ChimeraX Copyright ===
# Copyright 2022 Regents of the University of California. All rights reserved.
# The ChimeraX application is provided pursuant to the ChimeraX license
# agreement, which covers academic and commercial uses. For more details, see
# <https://www.rbvi.ucsf.edu/chimerax/docs/licensing.html>
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

from chimerax.core.state import State
from chimerax.graphics.gsession import ViewState, CameraState, LightingState, MaterialState
from chimerax.geometry.psession import PlaceState
from chimerax.std_commands.view import NamedView

import copy


class Scene(State):

    version = 0
    thumbnail_size = (200, 200)

    def __init__(self, session, *, scene_data=None):
        """
        A Scene object saves a copy of the data that ViewState takes snapshot of, and also a NamedView object which
        is a different type of state save used by chimerax.core.std_commands bundle for interpolating the camera
        position, camera orientation, clipping planes and model positions.
        """
        self.session = session
        self._thumbnail_data = None
        if scene_data is None:
            # Want a new scene
            self.main_view_data = self.create_main_view_data()
            models = session.models.list()
            self.named_view = NamedView(self.session.view, self.session.view.center_of_rotation, models)
            self.take_thumbnail()
        else:
            # load a scene
            self.main_view_data = scene_data['main_view_data']
            self.named_view = NamedView.restore_snapshot(session, scene_data['named_view'])
            self._thumbnail_data = scene_data['thumbnail_data']

    def restore_scene(self):
        self.restore_main_view_data(self.main_view_data)
        # Restore the camera position and orientation, clipping planes, and model positions using the NamedView
        current_models = self.session.models.list()
        for model in current_models:
            if model in self.named_view.positions:
                model.positions = self.named_view.positions[model]

    def create_main_view_data(self):
        """
        Created nested dictionary of the main view data using variation of the ViewState take_snapshot method.
        """
        main_view = self.session.view

        view_state = self.session.snapshot_methods(main_view)
        data = view_state.take_snapshot(main_view, self.session, State.SCENE)

        # By default, ViewState take_snapshot uses class name references and uids to store data for object attrs stored
        # in the View. For the simplicity of Scenes we want to convert all the nested objects into raw data.
        v_camera = main_view.camera
        data['camera'] = CameraState.take_snapshot(v_camera, self.session, State.SCENE)
        c_position = v_camera.position
        data['camera']['position'] = PlaceState.take_snapshot(c_position, self.session, State.SCENE)

        v_lighting = main_view.lighting
        data['lighting'] = LightingState.take_snapshot(v_lighting, self.session, State.SCENE)

        v_material = main_view.material
        data['material'] = MaterialState.take_snapshot(v_material, self.session, State.SCENE)

        return data

    def restore_main_view_data(self, data):
        """
        Restore the main view data using ViewState. Convert all nested data back into objects before using ViewState
        restore_snapshot.
        """

        # We need to be mindful that we convert all nested dicts back into the proper objects
        # Data is a pass by reference to a dict we are storing in our scene. We should not overwrite it
        restore_data = copy.deepcopy(data)

        restore_data['camera']['position'] = PlaceState.restore_snapshot(self.session, restore_data['camera']['position'])
        restore_data['camera'] = CameraState.restore_snapshot(self.session, restore_data['camera'])

        restore_data['lighting'] = LightingState.restore_snapshot(self.session, restore_data['lighting'])

        restore_data['material'] = MaterialState.restore_snapshot(self.session, restore_data['material'])

        # The ViewState by default skips resetting the camera because session.restore_options.get('restore camera')
        # is None. We set it to True, let the camera be restored, and then delete the option, so it reads None again in
        # case it is an important option for other parts of the code. We don't need to use the NamedView stored in the
        # scene to restore camera because the camera position is stored/restored using ViewState take and restore
        # snapshot.
        self.session.restore_options['restore camera'] = True
        ViewState.restore_snapshot(self.session, restore_data)
        del self.session.restore_options['restore camera']

    def take_thumbnail(self):
        # Take a thumbnail of the scene
        pil_image = self.session.view.image(*self.thumbnail_size)
        byte_stream = io.BytesIO()
        pil_image.save(byte_stream, format='JPEG')
        self._thumbnail_data = byte_stream.getvalue()

    def get_thumbnail(self):
        return self._thumbnail_data

    @staticmethod
    def restore_snapshot(session, data):
        return Scene(session, scene_data=data)

    def take_snapshot(self, session, flags):
        return {
            'version': self.version,
            'main_view_data': self.main_view_data,
            'named_view': self.named_view.take_snapshot(session, flags),
            'thumbnail_data': self._thumbnail_data
        }
