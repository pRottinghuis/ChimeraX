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

from chimerax.core.state import State
from chimerax.core.models import Model
from chimerax.graphics.gsession import ViewState


class Scene(State):

    def __init__(self, session, *, session_data=None):
        self.session = session
        if session_data is None:
            self.model_data = {}
            for model in session.models:
                # If derived class does not implement restore_scene, use Model class
                if model.__class__.restore_scene == Model.restore_scene:
                    self.model_data[model] = Model.take_snapshot(model, session, State.SCENE)
                else:
                    self.model_data[model] = model.take_snapshot(session, State.SCENE)
            # TODO make sure this is the correct way to do snapshot for view state
            # See ssave() in Session
            from chimerax.core.session import _SaveManager
            mgr = _SaveManager(session, State.SCENE)
            mgr.discovery({'main_view': session.view})
            self.view_data = [(name, data) for name, data in mgr.walk()]
            return
        else:
            self.model_data = session_data['model_data']
            self.view_data = session_data['main_view']
        # need to save view data and lighting data

    def restore_scene(self):
        # See ssave() in Session
        from chimerax.core.session import _RestoreManager
        mgr = _RestoreManager()
        for name, data in self.view_data:
            data = mgr.resolve_references(data)
            if isinstance(name, str):
                if name == "main_view":
                    self.session.main_view = data
                else:
                    # TODO other session state managers.
                    pass
            else:
                cls = name.class_of(self.session)
                sm = self.session.snapshot_methods(cls, instance=False)
                obj = sm.restore_snapshot(self.session, data)
                mgr.add_reference(name, obj)

    @staticmethod
    def restore_snapshot(session, data):
        return Scene(session, session_data=data)

    def take_snapshot(self, session, flags):
        raise NotImplementedError("Scene saving in sessions not implemented")
        return {
            'version': 1,
            'model_data': self.model_data
        }
