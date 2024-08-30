# vim: set expandtab ts=4 sw=4:

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

def foldseek_fetch_coordinates(session, min_aligned_coords = 10):

    from .foldseek import foldseek_results
    results = foldseek_results(session)
    if results is None:
        return

    keep_hits = []
    nc = 0
    nhits = len(results.hits)
    from time import time
    t0 = time()
    from .foldseek import open_hit, structure_chain_with_id
    for hnum, hit in enumerate(results.hits):
        if 'tca' in hit:
            keep_hits.append(hit)
            continue	# Already has coordinates
        structures = open_hit(session, hit, query_chain = None, trim = False, align = False,
                              in_file_history = False, log = False)
        
        hit_chain = structure_chain_with_id(structures[0], hit.get('chain_id'))
        catoms = hit_chain.existing_residues.find_existing_atoms('CA')
        hit['tca'] = catoms.coords
        rindex = {r:i for i,r in enumerate(hit_chain.residues) if r is not None}
        hit['tca_index'] = [rindex[r] for r in catoms.residues]
        session.models.close(structures)
        nc += 1

        if min_aligned_coords == 0 or _num_aligned_coords(hit) >= min_aligned_coords:
            keep_hits.append(hit)
            
        hname = hit['database_full_id']
        telapse = _minutes_and_seconds_string(time() - t0)
        session.logger.status(f'Finding coordinates for {hname} ({hnum+1} of {nhits}, time {telapse})')

    nremove = len(results.hits) - len(keep_hits)
    if nremove:
        results.replace_hits(keep_hits)
        msg = f'Removed {nremove} hits that had less than {min_aligned_coords} aligned residues with coordinates.  Kept {len(keep_hits)} hits.'
        session.logger.info(msg)

    telapse = _minutes_and_seconds_string(time() - t0)
    session.logger.status(f'Fetched coordinates for {nc} hits, time {telapse}', log = True)

def _num_aligned_coords(hit):
    return len(set(hit['tca_index']) & set(hit['aligned_residue_offsets']))

def _minutes_and_seconds_string(tsec):
    tmin = int(tsec/60)
    ts = int(tsec - tmin*60)
    return '%d:%02d' % (tmin, ts)

def register_foldseek_fetchcoords_command(logger):
    from chimerax.core.commands import CmdDesc, register, IntArg
    desc = CmdDesc(
        keyword = [('min_aligned_coords', IntArg),
                   ],
        synopsis = 'Fetch structures and get C-alpha coordinates for clustering and backbone trace display.'
    )
    register('foldseek fetchcoords', desc, foldseek_fetch_coordinates, logger=logger)
