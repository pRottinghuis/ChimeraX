# vim: set expandtab shiftwidth=4 softtabstop=4:

# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

def hide(session, objects=None, what=None, target=None):
    '''Hide specified atoms, bonds or models.

    Parameters
    ----------
    objects : Objects or None
        Atoms, bonds or models to hide. If None then all are hidden.
    what : 'atoms', 'bonds', 'pseudobonds', 'pbonds', 'cartoons', 'ribbons', 'models' or None
        What to hide.  If None then 'atoms' if any atoms specified otherwise 'models'.
    target : set of "what" values, or None
        Alternative to the "what" option for specifying what to hide.
    '''
    if objects is None:
        from . import atomspec
        objects = atomspec.all_objects(session)

    what_to_hide = set() if target is None else set(target)
    if what is not None:
        what_to_hide.update([what])
    if len(what_to_hide) == 0:
        what_to_hide = set(['atoms' if objects.atoms else 'models'])

    undo_data = {}
    if 'atoms' in what_to_hide:
        atoms = objects.atoms
        undo_data['atoms'] = (atoms, atoms.displays, False)
        atoms.displays = False
    if 'bonds' in what_to_hide:
        bonds = objects.atoms.intra_bonds
        undo_data['bonds'] = (bonds, bonds.displays, False)
        bonds.displays = False
    if 'pseudobonds' in what_to_hide or 'pbonds' in what_to_hide:
        from .. import atomic
        pbonds = atomic.interatom_pseudobonds(objects.atoms)
        undo_data['pseudobonds'] = (pbonds, pbonds.displays, False)
        pbonds.displays = False
    if 'cartoons' in what_to_hide or 'ribbons' in what_to_hide:
        res = objects.atoms.unique_residues
        undo_data['cartoons'] = (res, res.ribbon_displays, False)
        res.ribbon_displays = False
    if 'surfaces' in what_to_hide:
        from ..atomic import molsurf
        # TODO: save undo data
        molsurf.hide_surface_atom_patches(objects.atoms, session.models)
    if 'models' in what_to_hide:
        hide_models(objects, undo_data)

    def undo(data=undo_data):
        _hide_undo(data)
    def redo(data=undo_data):
        _hide_redo(data)
    session.undo.register("hide", undo, redo)

def hide_models(objects, undo_data):
    minst = objects.model_instances
    ud_positions = {}
    ud_display = {}
    undo_data['models'] = (ud_positions, ud_display)
    if minst:
        from numpy import logical_and, logical_not
        for m,inst in minst.items():
            dp = m.display_positions
            ninst = logical_not(inst)
            if dp is None:
                dp = ninst
            else:
                logical_and(dp, ninst, dp)
            if m in ud:
                ud_positions[m][1] = dp
            else:
                ud_positions[m] = [m.display_positions, dp]
            m.display_positions = dp
    else:
        for m in objects.models:
            if m in ud:
                ud_display[m][1] = False
            else:
                ud_display[m] = [m.display, True]
            m.display = False

def _hide_undo(undo_data):
    def _update_attr(key, attr):
        try:
            container, old_values, new_values = undo_data[key]
        except KeyError:
            pass
        else:
            setattr(container, attr, old_values)
    _update_attr('atoms', 'displays')
    _update_attr('bonds', 'displays')
    _update_attr('pseudobonds', 'displays')
    _update_attr('cartoons', 'ribbon_displays')
    # TODO: Surfaces
    _update_models(undo_data, 0)

def _update_models(undo_data, which):
    try:
        ud_positions, ud_displays = undo_data['models']
    except KeyError:
        pass
    else:
        for m, v in ud_positions.items():
            m.display_positions = v[which]
        for m, v in ud_display.items():
            m.display = v[which]

def _hide_redo(undo_data):
    def _update_attr(key, attr):
        try:
            container, old_values, new_values = undo_data[key]
        except KeyError:
            pass
        else:
            setattr(container, attr, new_values)
    _update_attr('atoms', 'displays')
    _update_attr('bonds', 'displays')
    _update_attr('pseudobonds', 'displays')
    _update_attr('cartoons', 'ribbon_displays')
    # TODO: Surfaces
    _update_models(undo_data, 1)

def register_command(session):
    from . import CmdDesc, register, ObjectsArg, EnumOf, EmptyArg, Or, create_alias
    from .show import WhatArg, TargetArg
    desc = CmdDesc(
        optional=[('objects', Or(ObjectsArg, EmptyArg)),
                  ('what', WhatArg)],
        keyword=[('target', TargetArg)],
        url='help:user/commands/show.html#hide',
        synopsis='hide specified objects')
    register('hide', desc, hide, logger=session.logger)
    create_alias('~show', 'hide $*', logger=session.logger)
    create_alias('~display', 'hide $*', logger=session.logger)
