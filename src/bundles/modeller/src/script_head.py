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

# This script is generated by the 'modeller' command in ChimeraX, 
# incorporating the settings from the command options. User can revise 
# this script and submit the modified one as the 'customScript' arg of
# that command. 


# Import the Modeller module
from modeller import *
from modeller.automodel import *


# ---------------------- namelist.dat --------------------------------
# A "namelist.dat" file contains the file names, which was output from 
# the ChimeraX modeller command based on the command arguments.
# The first line is the name of the target sequence, the remaining 
# lines are name of the template structures
namelist = open( 'namelist.dat', 'r' ).read().split('\n')
tarSeq = namelist[0]
template = tuple( [ x.strip() for x in namelist[1:] if x != '' ] )
# ---------------------- namelist.dat --------------------------------

# This instructs Modeller to display all log output. 
log.verbose()

# create a new Modeller environment
env = environ()

# Directory of atom/PDB/structure files. It is a relative path, inside 
# a temp folder generated by Chimera. User can modify it and add their 
# absolute path containing the structure files.
env.io.atom_files_directory = ['.', './template_struc']


