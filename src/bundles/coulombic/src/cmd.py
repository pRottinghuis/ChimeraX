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

from chimerax.core.errors import UserError

chargeable_residues = set(['ILE', 'DG', 'DC', 'DA', 'GLY', 'ATP', 'TRP', 'DT', 'GLU', 'NH2', 'ASP', 'NAD', 'LYS', 'PRO', 'ASN', 'A', 'CYS', 'C', 'G', 'THR', 'HOH', 'GTP', 'HIS', 'U', 'NDP', 'SER', 'GDP', 'PHE', 'ALA', 'MET', 'ACE', 'NME', 'ADP', 'LEU', 'ARG', 'VAL', 'TYR', 'GLN', 'HID', 'HIP', 'HIE', 'MSE'])

def cmd_coulombic(session, atoms, *, surfaces=None, his_scheme=None, surf_dist=1.4, spacing=1.0,
        padding=5.0, map=False, palette=None, range=None, dist_dep=True, dielectric=4.0):
    session.logger.status("Computing Coulombic charge volume/surface")
    if palette is None:
        from chimerax.core.colors import BuiltinColormaps
        cmap = BuiltinColormaps["red-white-blue"]
    if not cmap.values_specified:
        rmin, rmax = (-10.0, 10.0) if range is None else range
        print("setting cmap range")
        cmap = cmap.linear_range(rmin, rmax)
    session.logger.status("Matching atoms to surfaces", secondary=True)
    atoms_per_surf = []
    from chimerax.atomic import all_atomic_structures, MolecularSurface, all_atoms
    if atoms is None:
        if surfaces is None:
            # surface all chains
            for struct in all_atomic_structures(session):
                # don't create surface until charges checked
                if struct.num_chains == 0:
                    atoms_per_surf.append((struct.atoms, None))
                else:
                    for chain in struct.chains:
                        atoms_per_surf.append((chain.existing_residues.atoms, None))
        else:
            for srf in surfaces:
                if isinstance(srf, MolecularSurface):
                    atoms_per_surf.append((srf.atoms, srf))
                else:
                    atoms_per_surf.append((all_atoms(session), srf))
    else:
        if surfaces is None:
            # on a per-structure basis, determine if the atoms contain any polymers, and if so then
            # surface those chains (and not non-polymers); otherwise surface the atoms
            by_chain = {}
            for struct, chain_id, chain_atoms in atoms.by_chain:
                by_chain.setdefault(struct, {})[chain_id] = chain_atoms
            for struct, struct_atoms in atoms.by_structure:
                try:
                    for chain_atoms in by_chain[struct].values():
                        atoms_per_surf.append((chain_atoms, None))
                except KeyError:
                    atoms_per_surf.append((struct_atoms, None))
        else:
            for srf in surfaces:
                atoms_per_surf.append((atoms, srf))

    # check whether the atoms have charges, and if not, that we know how to assign charges
    # to the requested atoms
    problem_residues = set()
    needs_assignment = set()
    for atoms, srf in atoms_per_surf:
        for r in atoms.unique_residues:
            if getattr(r, '_coulombic_his_scheme', his_scheme) != his_scheme:
                # should only be set on HIS residues
                needs_assignment.add(r)
            else:
                for a in r.atoms:
                    try:
                        a.charge + 1.0
                    except (AttributeError, TypeError):
                        if r.name in chargeable_residues:
                            needs_assignment.add(r)
                        else:
                            problem_residues.add(r.name)
                        break
    if problem_residues:
        session.logger.status("")
        from chimerax.core.commands import commas
        raise UserError("Don't know how to assign charges to the following residue types: %s"
            % commas(problem_residues, conjunction='and'))

    if needs_assignment:
        session.logger.status("Assigning charges", secondary=True)
        from .coulombic import assign_charges, ChargeError
        try:
            assign_charges(session, needs_assignment, his_scheme)
        except ChargeError as e:
            session.logger.status("")
            raise UserError(str(e))

    session.logger.status("Computing electrostatics", secondary=True)
    # Since electrostatics are long range, unlike mlp, don't compute a map (with a distance cutoff)
    # by default.  Instead, compute the values at the surface vertices directly.  Only compute a
    # map afterward if requested.
    from chimerax.core.undo import UndoState
    undo_state = UndoState('coulombic')
    for atoms, srf in atoms_per_surf:
        if srf is None:
            from chimerax.surface import surface
            data = [(surf.atoms, surf) for surf in surface(session, atoms)]
        else:
            data = [(atoms, srf)]
        for charged_atoms, target_surface in data:
            if target_surface.normals is None:
                session.logger.warning("Surface %s has no vertex normals set, using distance from surface"
                    " of 0 instead of %g" % (target_surface, surf_dist))
                target_points = target_surface.vertices
            else:
                target_points = target_surface.vertices + surf_dist * target_surface.normals
            import numpy, os
            from ._esp import potential_at_points
            cpu_count = os.cpu_count()
            vertex_values = potential_at_points(
                target_surface.scene_position.transform_points(target_points), charged_atoms.scene_coords,
                numpy.array([a.charge for a in charged_atoms], dtype=numpy.double), dist_dep, dielectric,
                1 if cpu_count is None else cpu_count)
            rgba = cmap.interpolated_rgba(vertex_values)
            from numpy import uint8
            rgba8 = (255*rgba).astype(uint8)
            target_surface.vertex_colors = rgba8
    session.undo.register(undo_state)

    session.logger.status("Finished computing Coulombic charge volume/surface")

"""
def coulombic_map(session, charged_atoms, target_surface, surf_dist, spacing, padding, vol_name):
    data, bounds = calculate_map(target_surface, charged_atoms, spacing, surf_dist + padding)
    #TODO
"""

def register_command(logger):
    from chimerax.core.commands import CmdDesc, register, Or, EmptyArg, SurfacesArg, EnumOf, FloatArg
    from chimerax.core.commands import BoolArg, ColormapArg, ColormapRangeArg
    from chimerax.atomic import AtomsArg
    desc = CmdDesc(
        required = [('atoms', Or(AtomsArg, EmptyArg))],
        keyword = [
            ('surfaces', SurfacesArg),
            ('his_scheme', EnumOf(['HIP', 'HIE', 'HID'])),
            ('surf_dist', FloatArg),
            ('spacing', FloatArg),
            ('padding', FloatArg),
            ('map', BoolArg),
            ('palette', ColormapArg),
            ('range', ColormapRangeArg),
            ('disp_dep', BoolArg),
            ('dielectric', FloatArg),
        ],
        synopsis = 'Color surfaces by coulombic potential'
    )
    register("coulombic", desc, cmd_coulombic, logger=logger)
