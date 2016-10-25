def save_binary_coordinates(session, filename, models, **kw):
    if models is None:
        from chimerax.core.errors import UserError
        raise UserError('Must specify models to save coordinates')
    from chimerax.core.atomic import Structure
    mlist = [m for m in models if isinstance(m, Structure)]
    if len(mlist) == 0:
        from chimerax.core.errors import UserError
        raise UserError('No structures to save')
    na = mlist[0].num_atoms
    for m in mlist[1:]:
        if m.num_atoms != na:
            from chimerax.core.errors import UserError
            raise UserError('Saving coordinates requires all structures have the same number of atoms, got %s'
                            % ', '.join('%d' % m.num_atoms for m in mlist))
    from chimerax.ihm import coordsets
    coordsets.write_coordinate_sets(filename, mlist)
    
# -----------------------------------------------------------------------------
#
def register_coord_format():
    from chimerax.core import io
    from chimerax.core.atomic import structure
    io.register_format("Raw binary coordinates", structure.CATEGORY, (".crd",), ("crd",),
                       export_func=save_binary_coordinates)
