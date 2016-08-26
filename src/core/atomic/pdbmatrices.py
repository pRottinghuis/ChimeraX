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

# -----------------------------------------------------------------------------
# Routines to extract PDB transformation matrices from PDB file header.
#

# -----------------------------------------------------------------------------
#
def biological_unit_matrices(molecule):

    if hasattr(molecule, 'metadata') and 'REMARK' in molecule.metadata:
      s = pdb_biomt_matrices(molecule.metadata)
#    elif hasattr(molecule, 'mmCIFHeaders'):
#        s = PDBmatrices.mmcif_biounit_matrices(molecule.mmCIFHeaders)
    else:
      from ..geometry import Places
      s = Places([])
    return s


# -----------------------------------------------------------------------------
#
def pdb_smtry_matrices(pdb_headers):

  return pdb_remark_matrices(pdb_headers, '290', 'SMTRY')

# -----------------------------------------------------------------------------
#
def pdb_biomt_matrices(pdb_headers):

  return pdb_remark_matrices(pdb_headers, '350', 'BIOMT')
        
# -----------------------------------------------------------------------------
#
def pdb_remark_matrices(pdb_headers, remark_number, tag_name):

  h = pdb_headers
  if not 'REMARK' in h:
    return []

  remarks = h['REMARK']
  mtable = {}
  for r in remarks:
    fields = r.split()
    if (len(fields) < 8 or fields[0] != 'REMARK' or
	fields[1] != remark_number or fields[2][:-1] != tag_name):
      continue
    try:
      matrix_num = int(fields[3])
    except ValueError:
      continue
    if not matrix_num in mtable:
      mtable[matrix_num] = [None, None, None]
    try:
      row = int(fields[2][5]) - 1
    except ValueError:
      continue
    if row >= 0 and row <= 2:
      try:
        mtable[matrix_num][row] = tuple(float(f) for f in fields[4:8])
      except ValueError:
        continue

  # Order matrices by matrix number.
  msorted = [nm[1] for nm in sorted(mtable.items())]
  matrices = [mrows for mrows in msorted if mrows.count(None) == 0]
  from ..geometry import Place, Places
  ops = Places([Place(m) for m in matrices])

  return ops

# -----------------------------------------------------------------------------
# The "given" flag indicates which MTRIX records should be returned.
# The PDB MTRIX records have a "given" field which indicates whether or
# not the transformed coordinates are already given in the PDB entry.
#
def pdb_mtrix_matrices(pdb_headers, add_identity = True, given = False):

  h = pdb_headers
  have_matrix = ('MTRIX1' in h and
                 'MTRIX2' in h and
                 'MTRIX3' in h)
  if not have_matrix:
    if add_identity:
      from ..geometry import identity
      return [identity()]
    else:
      return []

  row1_list = h['MTRIX1']
  row2_list = h['MTRIX2']
  row3_list = h['MTRIX3']
  if len(row1_list) != len(row2_list) or len(row2_list) != len(row3_list):
    if add_identity:
      from ..geometry import identity
      return [identity()]
    else:
      return []
  
  row_triples = zip(row1_list, row2_list, row3_list)
  
  mlist = []
  from ..geometry import Place
  for row_triple in row_triples:
    matrix = []
    for line in row_triple:
      try:
        mrow = [float(f) for f in (line[10:20], line[20:30], line[30:40], line[45:55])]
      except ValueError:
        break
      mgiven = (len(line) >= 60 and line[59] == '1')
      if (mgiven and given) or (not mgiven and not given):
        matrix.append(mrow)
    if len(matrix) == 3:
      mlist.append(Place(matrix))

  if add_identity:
    if len([m for m in mlist if m.is_identity()]) == 0:
      # Often there is no MTRIX identity entry
      from ..geometry import identity
      mlist.append(identity())

  return Places(mlist)

# -----------------------------------------------------------------------------
#
def set_pdb_biomt_remarks(molecule, places):

  remarks = []
  if hasattr(molecule, 'metadata'):
    h = molecule.metadata
    if 'REMARK' in h:
      remarks = h['REMARK']

  template = \
'''REMARK 300 
REMARK 300 BIOMOLECULE: 1 
REMARK 300 SEE REMARK 350 FOR THE AUTHOR PROVIDED AND/OR PROGRAM 
REMARK 300 GENERATED ASSEMBLY INFORMATION FOR THE STRUCTURE IN 
REMARK 300 THIS ENTRY.  THE REMARK MAY ALSO  PROVIDE INFORMATION ON 
REMARK 300 BURIED SURFACE AREA.
REMARK 350
REMARK 350 COORDINATES FOR A COMPLETE MULTIMER  REPRESENTING THE KNOWN
REMARK 350 BIOLOGICALLY SIGNIFICANT OLIGOMERIZATION STATE  OF THE
REMARK 350 MOLECULE CAN BE GENERATED BY APPLYING BIOMT  TRANSFORMATIONS
REMARK 350 GIVEN BELOW.  BOTH NON-CRYSTALLOGRAPHIC  AND
REMARK 350 CRYSTALLOGRAPHIC OPERATIONS ARE GIVEN.
REMARK 350
REMARK 350 BIOMOLECULE: 1
REMARK 350 SOFTWARE USED: UCSF CHIMERAX %s.
REMARK 350 APPLY THE FOLLOWING TO CHAINS: %s
%s'''

  cids = list(set(r.id.chainId for r in molecule.residues))
  cids.sort()
  chains = ', '.join(cids[:10])
  for n in range(10, len(cids), 20):
    chains += ',\nREMARK 350   %s' % ', '.join(cids[n:n+20])

  biomt_template = 'REMARK 350   BIOMT%d %3d %9.6f %9.6f %9.6f   %12.5f'
  mlines = []
  for i, p in enumerate(places):
    tf = p.matrix
    mlines.extend(biomt_template % ((r+1,i+1,) + tuple(tf[r])) for r in (0,1,2))
  matrices = '\n'.join(mlines)

  from chimerax import app_dirs
  release = app_dirs.version

  rem = template % (release, chains, matrices)
  lines = padded_lines(rem, 80)
  rnew = replace_remarks(remarks, lines, (300,350))
  molecule.setPDBHeader('REMARK', rnew)

# -----------------------------------------------------------------------------
# xform maps global coordinates to new file coordinates.
#
def transform_pdb_biomt_remarks(molecule, xform):

  mxf = molecule.openState.xform
  mxf.premultiply(xform)
  import Matrix as M
  mtf = M.xform_matrix(mxf)
  if M.is_identity_matrix(mtf):
    return
  h = getattr(molecule, 'pdbHeaders', None)
  if h is None:
    return
  tflist = pdb_biomt_matrices(molecule.pdbHeaders)
  if len(tflist) == 0:
    return
  if len(tflist) == 1 and M.is_identity_matrix(tflist[0]):
    return

  if 'REMARK' in h:
      molecule.original_biomt_remarks = tuple(r for r in h['REMARK']
                                              if remark_number(r) in (300,350))
  tflist = M.coordinate_transform_list(tflist, M.invert_matrix(mtf))
  xforms = [M.chimera_xform(tf) for tf in tflist]
  set_pdb_biomt_remarks(molecule, xforms)

# -----------------------------------------------------------------------------
#
def restore_pdb_biomt_remarks(molecule):

  brem = getattr(molecule, 'original_biomt_remarks', None)
  if brem:
    rnew = replace_remarks(molecule.pdbHeaders['REMARK'], brem, (300,350))
    molecule.setPDBHeader('REMARK', rnew)
    delattr(molecule, 'original_biomt_remarks')

# -----------------------------------------------------------------------------
# Read REMARK 350 BIOMT matrices.  Handle matrices for multiple biomolecules
# and also cases where different chains have different matrices applied.
#
# Return a list of biomolecules
#
#  bmlist = (bm1, bm2, ...)
#
# where a biomolecule is groups of chains and transforms for those chains
#
#  bm = (bm_num, ((clist1,tflist1), (clist2,tflist2), ...))
#
# and transforms are numbered
#
# tflist = ((1,m1), (2,m2), ...)
#
def pdb_biomolecules(pdb_headers, remark_number = '350',
                     biomol_tag = 'BIOMOLECULE:', chains_tag = 'CHAINS:',
                     row_tags = {'BIOMT1':0, 'BIOMT2':1, 'BIOMT3':2}):

  rlines = remark_lines(pdb_headers, remark_number)

  mn = None
  tflist = []
  chains = []
  cglist = [(chains,tflist)]
  bmlist = [(1,cglist)]
  for line in rlines:

    # Find biomolecule lines
    i = line.find(biomol_tag)
    if i >= 0:
      i += len(biomol_tag)
      try:
        bm_num = int(line[i:])
      except:
        continue
      tflist = []
      mn = None
      chains = []
      cglist = [(chains,tflist)]
      bmlist.append((bm_num, cglist))   # Remember biomolecule

    # Find chain list lines.
    i = line.find(chains_tag)
    if i >= 0:
      i += len(chains_tag)
      cids = [cid.strip() for cid in line[i:].split(',') if cid.strip()]
      if len(tflist) == 0:
        chains.extend(cids)     # Chain list on multiple lines
      else:
        chains = cids
        tflist = []
        mn = None
        cglist.append((chains,tflist))  # Remember chain group

    # Find matrices
    fields = line.split(None,3)
    if len(fields) == 4 and fields[2] in row_tags:
      r = row_tags[fields[2]]
      rvals = fields[3].split()
      if len(rvals) >= 5:
        try:
          mnum = int(rvals[0])
          mrow = tuple(float(x) for x in rvals[1:5])
        except:
          continue
        if mnum != mn:
          m = [(1,0,0,0),(0,1,0,0),(0,0,1,0)]
          tflist.append((mnum,m))       # Remember transform
          mn = mnum
        m[r] = mrow

  # Remove empty biomolecules and chains with no matrices
  bml = []
  for bm_num, cglist in bmlist:
    cgl = [(chains, tflist) for chains, tflist in cglist if tflist]
    if cgl:
      bml.append((bm_num,cgl))
        
  return bml

# -----------------------------------------------------------------------------
#
def remark_lines(pdb_headers, remark_number):

  h = pdb_headers
  if not 'REMARK' in h:
    return []

  rlines = []
  remarks = h['REMARK']
  for r in remarks:
    fields = r.split()
    if len(fields) >= 2 and fields[0] == 'REMARK' and fields[1] == remark_number:
      rlines.append(r)
  return rlines

# -----------------------------------------------------------------------------
#
def padded_lines(string, width):

  pad = ' ' * width
  lines = [(line + pad)[:80] for line in string.split('\n')]
  return lines

# -----------------------------------------------------------------------------
#
def replace_remarks(remarks, lines, remove):

  rnew = [line for line in remarks if remark_number(line) not in remove]
  rnew.extend(lines)
  rnew.sort(lambda a,b: cmp(remark_number(a), remark_number(b)))
  return rnew

# -----------------------------------------------------------------------------
#
def remark_number(line):

  try:
    n = int(line[7:10])
  except:
    n = 1000
  return n
