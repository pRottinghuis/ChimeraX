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
import numpy as np
from chimerax.core.objects import all_objects

import copy


class Scene(State):

    version = 0

    def __init__(self, session, *, scene_data=None):
        """
        A Scene object saves a copy of the data that ViewState takes snapshot of, and also a NamedView object which
        is a different type of state save used by chimerax.core.std_commands bundle for interpolating the camera
        position, camera orientation, clipping planes and model positions.
        """
        self.session = session
        if scene_data is None:
            # Want a new scene
            self.main_view_data = self.create_main_view_data()
            models = session.models.list()
            self.named_view = NamedView(self.session.view, self.session.view.center_of_rotation, models)
            self.scene_colors = SceneColors(session)
        else:
            # load a scene
            self.main_view_data = scene_data['main_view_data']
            self.named_view = NamedView.restore_snapshot(session, scene_data['named_view'])
            self.atom_colors = scene_data['atom_colors']
            self.scene_colors = SceneColors(session, color_data=scene_data['scene_colors'])
        return

    def restore_scene(self):
        self.restore_main_view_data(self.main_view_data)
        # Restore the camera position and orientation, clipping planes, and model positions using the NamedView
        current_models = self.session.models.list()
        for model in current_models:
            if model in self.named_view.positions:
                model.positions = self.named_view.positions[model]
        self.scene_colors.restore_colors()

    def models_removed(self, models: [str]):
        for model in models:
            if model in self.named_view.positions:
                del self.named_view.positions[model]
        self.scene_colors.models_removed(models)
        return

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

    def get_colors(self):
        return self.scene_colors

    @staticmethod
    def interpolatable(scene1, scene2):
        """
        Check if two scenes are interpolatable. Scenes are interpolatable if they have the same models in
        their named_views.
        """
        scene1_models = scene1.named_view.positions.keys()
        scene2_models = scene2.named_view.positions.keys()
        # Sets to disregard order
        named_views = set(scene1_models) == set(scene2_models)

        scene_colors = SceneColors.interpolatable(scene1.get_colors(), scene2.get_colors())

        return named_views and scene_colors

    @staticmethod
    def restore_snapshot(session, data):
        return Scene(session, scene_data=data)

    def take_snapshot(self, session, flags):

        return {
            'version': self.version,
            'main_view_data': self.main_view_data,
            'named_view': self.named_view.take_snapshot(session, flags),
            'scene_colors': self.scene_colors.take_snapshot(session, flags)
        }


class SceneColors(State):

    """
    SceneColors is a class that stores color data for session objects. See chimerax.atomic.molarray.py to see the c++
    layer objects that this SceneColors interacts with. See chimerax.std_commands.color.py to see examples of changing
    colors.
    """

    version = 0

    def __init__(self, session, color_data=None):
        self.session = session

        if color_data:
            self.atom_colors = color_data['atom_colors']
            self.ribbon_colors = color_data['ribbons_colors']
        else:
            # Atom colors
            self.atom_colors = {}

            # Bond colors
            self.bond_colors = {}
            self.halfbonds = {}

            # Residue colors
            self.ribbon_colors = {}
            self.ring_colors = {}

            self.initialize_colors()
        return

    def initialize_colors(self):
        """
        Initialize values for the color attributes. Collections from the c++ layer have a by_structure attribute which
        maps models to their respective object pointers. For example atoms.by_structure is a dictionary mapping models
        to their respective atoms objects. We can use this to store the colors for each model and then restore them
        later using the same mapping. Keeping track of what colors belong to what model allow us to handle models being
        closed.
        """

        objects = all_objects(self.session)

        # Atoms Colors
        for (model, atoms) in objects.atoms.by_structure:
            self.atom_colors[model] = atoms.colors

        # Bonds colors
        for (model, bonds) in objects.bonds.by_structure:
            self.bond_colors[model] = bonds.colors
            self.halfbonds[model] = bonds.halfbonds  # Boolean ndarray indicating half bond drawing style per bond

        # Residue Colors
        for (model, residues) in objects.residues.by_structure:
            self.ribbon_colors[model] = residues.ribbon_colors
            self.ring_colors[model] = residues.ring_colors

    def restore_colors(self):
        """
        Move through by_structure for each object type and restore the colors.
        """

        objects = all_objects(self.session)

        # Atoms colors
        for (model, atoms) in objects.atoms.by_structure:
            if model in self.atom_colors.keys():
                atoms.colors = self.atom_colors[model]

        # Bonds colors
        for (model, bonds) in objects.bonds.by_structure:
            if model in self.bond_colors.keys():
                bonds.colors = self.bond_colors[model]
                bonds.halfbonds = self.halfbonds[model]

        # Residue Colors
        for (model, residues) in objects.residues.by_structure:
            if model in self.ribbon_colors.keys():
                residues.ribbon_colors = self.ribbon_colors[model]
                residues.ring_colors = self.ring_colors[model]

    def models_removed(self, models: [str]):
        for model in models:
            if model in self.atom_colors:
                del self.atom_colors[model]
            if model in self.bond_colors:
                del self.bond_colors[model]
            if model in self.halfbonds:
                del self.halfbonds[model]
            if model in self.ribbon_colors:
                del self.ribbon_colors[model]
            if model in self.ring_colors:
                del self.ring_colors[model]

    def get_atom_colors(self):
        return self.atom_colors

    def set_atom_colors(self, colors):
        self.atom_colors = colors

    def get_bond_colors(self):
        return self.bond_colors

    def get_halfbonds(self):
        return self.halfbonds

    def get_ribbon_colors(self):
        return self.ribbon_colors

    def get_ring_colors(self):
        return self.ring_colors

    @staticmethod
    def interpolatable(scene1_colors, scene2_colors):
        # TODO update with all attrs
        if scene1_colors.atom_colors.keys() != scene2_colors.atom_colors.keys():
            return False
        if scene1_colors.ribbon_colors.keys() != scene2_colors.ribbon_colors.keys():
            return False
        return True

    @staticmethod
    def interpolate(session, scene1_colors, scene2_colors, fraction):
        """
        Linear interpolation of two SceneColors objects.
        """

        objects = all_objects(session)

        atom_colors_1 = scene1_colors.get_atom_colors()
        atom_colors_2 = scene2_colors.get_atom_colors()
        for (model, atoms) in objects.atoms.by_structure:
            if model in atom_colors_1 and model in atom_colors_2:
                atoms.colors = rgba_ndarray_lerp(atom_colors_1[model], atom_colors_2[model], fraction)

        # Bond colors
        bond_colors_1 = scene1_colors.get_bond_colors()
        bond_colors_2 = scene2_colors.get_bond_colors()
        halfbonds_1 = scene1_colors.get_halfbonds()
        halfbonds_2 = scene2_colors.get_halfbonds()
        for (model, bonds) in objects.bonds.by_structure:
            if model in bond_colors_1 and model in bond_colors_2:
                bonds.colors = rgba_ndarray_lerp(bond_colors_1[model], bond_colors_2[model], fraction)
            if model in halfbonds_1 and model in halfbonds_2:
                bonds.halfbonds = bool_ndarray_threshold_lerp(halfbonds_1[model], halfbonds_2[model], fraction)

        # Residues colors
        ribbon_colors_1 = scene1_colors.get_ribbon_colors()
        ribbon_colors_2 = scene2_colors.get_ribbon_colors()
        ring_colors_1 = scene1_colors.get_ring_colors()
        ring_colors_2 = scene2_colors.get_ring_colors()
        for (model, ribbons) in objects.residues.by_structure:
            if model in ribbon_colors_1 and model in ribbon_colors_2:
                ribbons.ribbon_colors = rgba_ndarray_lerp(ribbon_colors_1[model], ribbon_colors_2[model], fraction)
            if model in ring_colors_1 and model in ring_colors_2:
                ribbons.ring_colors = rgba_ndarray_lerp(ring_colors_1[model], ring_colors_2[model], fraction)

    def take_snapshot(self, session, flags):
        # TODO make sure to save all attrs here
        return {
            'version': self.version,
            'atom_colors': self.atom_colors,
            'ribbons_colors': self.ribbon_colors,
        }

    @staticmethod
    def restore_snapshot(session, data):
        if data['version'] != SceneColors.version:
            raise ValueError("Cannot restore SceneColors data with version %d" % data['version'])
        return SceneColors(session, color_data=data)


def bool_ndarray_threshold_lerp(bool_arr1, bool_arr2, fraction):
    """
    Threshold lerp for bool numpy arrays. Fraction 0.5 is the threshold.
    """
    return bool_arr1 if fraction < 0.5 else bool_arr2


def rgba_ndarray_lerp(rgba_arr1, rgba_arr2, fraction):
    """
    Linear interpolation of two RGBA numpy arrays. Fraction is the weight of the second array.
    """
    rgba_arr1_copy = np.copy(rgba_arr1)
    rgba_arr2_copy = np.copy(rgba_arr2)
    interpolated = rgba_arr1_copy * (1 - fraction) + rgba_arr2_copy * fraction
    # Convert back to uint8. This is necessary because the interpolation may have created floats which is not supported
    # by the colors attribute in the atoms object.
    return interpolated.astype(np.uint8)