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

from chimerax.core.toolshed import BundleAPI

class _MyAPI(BundleAPI):

    @staticmethod
    def register_command(command_name):
        # 'register_command' is lazily called when the command is referenced
        from . import test
        from chimerax.core.commands import register, CmdDesc
        desc = CmdDesc(synopsis = 'Run through test sequence of commands to check for errors')
        register('test', desc, test.run_commands)

bundle_api = _MyAPI()
