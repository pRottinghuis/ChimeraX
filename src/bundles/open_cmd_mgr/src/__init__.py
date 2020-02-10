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

from chimerax.core.toolshed import BundleAPI

class _OpenBundleAPI(BundleAPI):

    @staticmethod
    def init_manager(session, bundle_info, name, **kw):
        """Initialize open-command manager"""
        if name == "open command":
            from . import manager
            manager._manager = manager.OpenManager(session)
            return manager._manager

    @staticmethod
    def register_command(command_name, logger):
        from . import cmd
        cmd.register_command(command_name, logger)

    @staticmethod
    def run_provider(session, name, mgr, type=None, path=None, encoding=None, **kw):
        if type == "compression":
            from .providers import get_compression
            return get_compression(name, path, encoding)

bundle_api = _OpenBundleAPI()
