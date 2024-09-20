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
from chimerax.graphics.gsession import ViewState, CameraState, LightingState, MaterialState, CameraClipPlaneState
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
            self.scene_visibility = SceneVisibility(session)
        else:
            # load a scene
            self.main_view_data = scene_data['main_view_data']
            self.named_view = NamedView.restore_snapshot(session, scene_data['named_view'])
            self.scene_colors = SceneColors(session, color_data=scene_data['scene_colors'])
            self.scene_visibility = SceneVisibility(session, visibility_data=scene_data['scene_visibility'])
        return

    def restore_scene(self):
        self.restore_main_view_data(self.main_view_data)
        # Restore the camera position and orientation, clipping planes, and model positions using the NamedView
        current_models = self.session.models.list()
        for model in current_models:
            if model in self.named_view.positions:
                model.positions = self.named_view.positions[model]
        self.scene_colors.restore_colors()
        self.scene_visibility.restore_visibility()

    def models_removed(self, models: [str]):
        for model in models:
            if model in self.named_view.positions:
                del self.named_view.positions[model]
        self.scene_colors.models_removed(models)
        self.scene_visibility.models_removed(models)
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

        # 'clip_planes in data is an array of clip planes objects. For now assume they are all CameraClipPlanes. We
        # need to convert them into raw data before storing them in the scene. Replace the 'clip_planes' key in data
        # with the raw data.
        clip_planes = data['clip_planes']
        clip_planes_data = []
        for clip_pane in clip_planes:
            clip_planes_data.append(CameraClipPlaneState.take_snapshot(clip_pane, self.session, State.SCENE))

        data['clip_planes'] = clip_planes_data

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

        # Restore the clip planes. The 'clip_planes' key in restore_data is an array of clip planes objects in snapshot
        # form. We need to convert them back into CameraClipPlane objects before restoring the main view data.
        clip_planes_data = restore_data['clip_planes']
        restored_clip_planes = []
        for clip_plane_data in clip_planes_data:
            restored_clip_planes.append(CameraClipPlaneState.restore_snapshot(self.session, clip_plane_data))

        restore_data['clip_planes'] = restored_clip_planes

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

    def get_visibility(self):
        return self.scene_visibility

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
        scene_visibility = SceneVisibility.interpolatable(scene1.get_visibility(), scene2.get_visibility())

        return named_views and scene_colors and scene_visibility

    @staticmethod
    def restore_snapshot(session, data):
        return Scene(session, scene_data=data)

    def take_snapshot(self, session, flags):

        return {
            'version': self.version,
            'main_view_data': self.main_view_data,
            'named_view': self.named_view.take_snapshot(session, flags),
            'scene_colors': self.scene_colors.take_snapshot(session, flags),
            'scene_visibility': self.scene_visibility.take_snapshot(session, flags)
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
            self.bond_colors = color_data['bond_colors']
            self.halfbonds = color_data['halfbonds']
            self.pseudobond_colors = color_data['pseudobond_colors']
            self.pbond_halfbonds = color_data['pbond_halfbonds']
            self.ribbon_colors = color_data['ribbon_colors']
            self.ring_colors = color_data['ring_colors']
        else:
            # Atom colors
            self.atom_colors = {}

            # Bond colors
            self.bond_colors = {}
            self.halfbonds = {}  # Boolean ndarray indicating half bond drawing style per bond

            # Pseudobond colors
            self.pseudobond_colors = {}
            self.pbond_halfbonds = {}  # Boolean ndarray indicating half bond drawing style per pseudobond

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

        # Pseudobonds colors
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            self.pseudobond_colors[pbond_group] = pseudobonds.colors
            self.pbond_halfbonds[pbond_group] = pseudobonds.halfbonds

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

        # Pseudobonds colors
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            if pbond_group in self.pseudobond_colors.keys():
                pseudobonds.colors = self.pseudobond_colors[pbond_group]
                pseudobonds.halfbonds = self.pbond_halfbonds[pbond_group]

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

            if model in self.pseudobond_colors:
                del self.pseudobond_colors[model]
            if model in self.pbond_halfbonds:
                del self.pbond_halfbonds[model]

            if model in self.ribbon_colors:
                del self.ribbon_colors[model]
            if model in self.ring_colors:
                del self.ring_colors[model]

    def get_atom_colors(self):
        return self.atom_colors

    def get_bond_colors(self):
        return self.bond_colors

    def get_halfbonds(self):
        return self.halfbonds

    def get_pseudobond_colors(self):
        return self.pseudobond_colors

    def get_pbond_halfbonds(self):
        return self.pbond_halfbonds

    def get_ribbon_colors(self):
        return self.ribbon_colors

    def get_ring_colors(self):
        return self.ring_colors

    @staticmethod
    def interpolatable(scene1_colors, scene2_colors):
        if scene1_colors.atom_colors.keys() != scene2_colors.atom_colors.keys():
            return False
        if scene1_colors.bond_colors.keys() != scene2_colors.bond_colors.keys():
            return False
        if scene1_colors.halfbonds.keys() != scene2_colors.halfbonds.keys():
            return False
        if scene1_colors.pseudobond_colors.keys() != scene2_colors.pseudobond_colors.keys():
            return False
        if scene1_colors.pbond_halfbonds.keys() != scene2_colors.pbond_halfbonds.keys():
            return False
        if scene1_colors.ribbon_colors.keys() != scene2_colors.ribbon_colors.keys():
            return False
        if scene1_colors.ring_colors.keys() != scene2_colors.ring_colors.keys():
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

        # Pseudobond colors
        pseudobond_colors_1 = scene1_colors.get_pseudobond_colors()
        pseudobond_colors_2 = scene2_colors.get_pseudobond_colors()
        pbond_halfbonds_1 = scene1_colors.get_pbond_halfbonds()
        pbond_halfbonds_2 = scene2_colors.get_pbond_halfbonds()
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            if pbond_group in pseudobond_colors_1 and pbond_group in pseudobond_colors_2:
                pseudobonds.colors = rgba_ndarray_lerp(pseudobond_colors_1[pbond_group], pseudobond_colors_2[pbond_group], fraction)
            if pbond_group in pbond_halfbonds_1 and pbond_group in pbond_halfbonds_2:
                pseudobonds.halfbonds = bool_ndarray_threshold_lerp(pbond_halfbonds_1[pbond_group], pbond_halfbonds_2[pbond_group], fraction)

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
        return {
            'version': self.version,
            'atom_colors': self.atom_colors,
            'bond_colors': self.bond_colors,
            'halfbonds': self.halfbonds,
            'pseudobond_colors': self.pseudobond_colors,
            'pbond_halfbonds': self.pbond_halfbonds,
            'ribbon_colors': self.ribbon_colors,
            'ring_colors': self.ring_colors
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


class SceneVisibility(State):

    version = 0

    def __init__(self, session, *, visibility_data=None):
        self.session = session
        if visibility_data:
            self.model_visibility = visibility_data['model_visibility']
            self.atom_displays = visibility_data['atom_displays']
            self.bond_displays = visibility_data['bond_displays']
            self.pseudobond_displays = visibility_data['pseudobond_displays']
            self.ribbon_displays = visibility_data['ribbon_displays']
            self.ring_displays = visibility_data['ring_displays']
        else:
            self.model_visibility = {}
            self.atom_displays = {}
            self.bond_displays = {}
            self.pseudobond_displays = {}
            self.ribbon_displays = {}
            self.ring_displays = {}
            self.initialize_visibility()
        return

    def initialize_visibility(self):
        objects = all_objects(self.session)

        for model in objects.models:
            self.model_visibility[model] = model.display
        for (structure, atom) in objects.atoms.by_structure:
            self.atom_displays[structure] = atom.displays
        for (structure, bond) in objects.bonds.by_structure:
            self.bond_displays[structure] = bond.displays
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            self.pseudobond_displays[pbond_group] = pseudobonds.displays
        for (structure, residues) in objects.residues.by_structure:
            self.ribbon_displays[structure] = residues.ribbon_displays
            self.ring_displays[structure] = residues.ring_displays

        return

    def restore_visibility(self):
        objects = all_objects(self.session)

        for model in objects.models:
            if model in self.model_visibility:
                model.display = self.model_visibility[model]
        for (structure, atom) in objects.atoms.by_structure:
            if structure in self.atom_displays:
                atom.displays = self.atom_displays[structure]
        for (structure, bond) in objects.bonds.by_structure:
            if structure in self.bond_displays:
                bond.displays = self.bond_displays[structure]
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            if pbond_group in self.pseudobond_displays:
                pseudobonds.displays = self.pseudobond_displays[pbond_group]
        for (structure, residues) in objects.residues.by_structure:
            if structure in self.ribbon_displays:
                residues.ribbon_displays = self.ribbon_displays[structure]
            if structure in self.ring_displays:
                residues.ring_displays = self.ring_displays[structure]

    def models_removed(self, models: [str]):
        for model in models:
            if model in self.model_visibility:
                del self.model_visibility[model]
            if model in self.atom_displays:
                del self.atom_displays[model]
            if model in self.bond_displays:
                del self.bond_displays[model]
            if model in self.pseudobond_displays:
                del self.pseudobond_displays[model]
            if model in self.ribbon_displays:
                del self.ribbon_displays[model]
            if model in self.ring_displays:
                del self.ring_displays[model]

    def get_model_visibility(self):
        return self.model_visibility

    def get_atom_displays(self):
        return self.atom_displays

    def get_bond_displays(self):
        return self.bond_displays

    def get_pbond_displays(self):
        return self.pseudobond_displays

    def get_ribbon_displays(self):
        return self.ribbon_displays

    def get_ring_displays(self):
        return self.ring_displays

    @staticmethod
    def interpolatable(scene1_visibility, scene2_visibility):
        if scene1_visibility.model_visibility.keys() != scene2_visibility.model_visibility.keys():
            return False
        if scene1_visibility.atom_displays.keys() != scene2_visibility.atom_displays.keys():
            return False
        if scene1_visibility.bond_displays.keys() != scene2_visibility.bond_displays.keys():
            return False
        if scene1_visibility.pseudobond_displays.keys() != scene2_visibility.pseudobond_displays.keys():
            return False
        if scene1_visibility.ribbon_displays.keys() != scene2_visibility.ribbon_displays.keys():
            return False
        if scene1_visibility.ring_displays.keys() != scene2_visibility.ring_displays.keys():
            return False
        return True

    @staticmethod
    def interpolate(session, scene1_visibility, scene2_visibility, fraction):
        objects = all_objects(session)

        model_visibility_1 = scene1_visibility.get_model_visibility()
        model_visibility_2 = scene2_visibility.get_model_visibility()
        for model in objects.models:
            if model in model_visibility_1 and model in model_visibility_2:
                model.display = bool_ndarray_threshold_lerp(model_visibility_1[model], model_visibility_2[model], fraction)

        atom_displays_1 = scene1_visibility.get_atom_displays()
        atom_displays_2 = scene2_visibility.get_atom_displays()
        for (structure, atom) in objects.atoms.by_structure:
            if structure in atom_displays_1 and structure in atom_displays_2:
                atom.displays = bool_ndarray_threshold_lerp(atom_displays_1[structure], atom_displays_2[structure], fraction)

        bond_displays_1 = scene1_visibility.get_bond_displays()
        bond_displays_2 = scene2_visibility.get_bond_displays()
        for (structure, bond) in objects.bonds.by_structure:
            if structure in bond_displays_1 and structure in bond_displays_2:
                bond.displays = bool_ndarray_threshold_lerp(bond_displays_1[structure], bond_displays_2[structure], fraction)

        pseudobond_displays_1 = scene1_visibility.get_pbond_displays()
        pseudobond_displays_2 = scene2_visibility.get_pbond_displays()
        for (pbond_group, pseudobonds) in objects.pseudobonds.by_group:
            if pbond_group in pseudobond_displays_1 and pbond_group in pseudobond_displays_2:
                pseudobonds.displays = bool_ndarray_threshold_lerp(pseudobond_displays_1[pbond_group], pseudobond_displays_2[pbond_group], fraction)

        ribbon_displays_1 = scene1_visibility.get_ribbon_displays()
        ribbon_displays_2 = scene2_visibility.get_ribbon_displays()
        ring_displays_1 = scene1_visibility.get_ring_displays()
        ring_displays_2 = scene2_visibility.get_ring_displays()
        for (structure, residues) in objects.residues.by_structure:
            if structure in ribbon_displays_1 and structure in ribbon_displays_2:
                residues.ribbon_displays = bool_ndarray_threshold_lerp(ribbon_displays_1[structure], ribbon_displays_2[structure], fraction)
            if structure in ring_displays_1 and structure in ring_displays_2:
                residues.ring_displays = bool_ndarray_threshold_lerp(ring_displays_1[structure], ring_displays_2[structure], fraction)

    def take_snapshot(self, session, flags):
        return {
            'version': self.version,
            'model_visibility': self.model_visibility,
            'atom_displays': self.atom_displays,
            'bond_displays': self.bond_displays,
            'pseudobond_displays': self.pseudobond_displays,
            'ribbon_displays': self.ribbon_displays,
            'ring_displays': self.ring_displays
        }

    @staticmethod
    def restore_snapshot(session, data):
        if SceneVisibility.version != data['version']:
            raise ValueError("Cannot restore SceneVisibility data with version %d" % data['version'])
        return SceneVisibility(session, visibility_data=data)
