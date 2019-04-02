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

from chimerax.core.utils import CustomSortString

def register_builtin_presets(session):
    nospheres = "style (protein|nucleic|solvent) & @@draw_mode=0 stick"
    cardef = "surf hide; %s; cartoon; cartoon style modeh def arrows t arrowshelix f arrowscale 2 wid 2 thick 0.4" \
        " sides 12 div 20; cartoon style ~(nucleic|strand) x round; cartoon style (nucleic|strand) x rect" % nospheres
    cylinders = "%s; cartoon style protein modeh tube rad 2 sides 24 thick 0.6" % cardef
    licorice = "%s; cartoon style protein modeh default arrows f x round width 1 thick 1" % cardef
    preset_info = {
        "Cartoons/Nucleotides": [
            (CustomSortString("ribbons/slabs", sort_val=1), "%s; nucleotides tube/slab shape box" % cardef),
            (CustomSortString("cylinders/stubs", sort_val=2),
                "%s; cartoon style nucleic x round width 1.6 thick 1.6; nucleotides stubs" % cylinders),
            (CustomSortString("licorice/ovals", sort_val=3),
                "%s; cartoon style nucleic x round width 1.6 thick 1.6; nucleotides tube/slab"
                " shape ellipsoid" % licorice),
        ],
        "Molecular Surfaces": [
            ("ghostly white", "%s; surface; color white targ s trans 80" % nospheres),
            ("atomic coloring (transparent)", "%s; surface; color fromatoms targ s trans 70" % nospheres),
            ("chain ID coloring (opaque)", "%s; surface; color bychain targ s trans 0" % nospheres),
        ],
        "Overall Look": [
            ("publication", "set bg white; set silhouettes t"),
            ("interactive", "~set bg; set silhouettes f"),
        ],
    }
    from chimerax.core.commands import run
    for cat_name, cat_presets in preset_info.items():
        session.presets.add_presets(cat_name, cat_presets)

