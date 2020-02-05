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

from chimerax.core.toolshed import ProviderManager
class FormatsManager(ProviderManager):
    """Manager for data formats"""

    CAT_SCRIPT = "Command script"
    CAT_GENERAL = "General"

    def __init__(self, session):
        self.session = session
        self._formats = {}
        from chimerax.core.triggerset import TriggerSet
        self.triggers = TriggerSet()
        self.triggers.add_trigger("data formats changed")
        from chimerax.core import io
        for format_name, category, fmt_kw in io._used_register:
            self.add_format(format_name, category, **fmt_kw)
        io._user_register = self.add_format

    def add_format(self, name, category, *, suffixes=None, nicknames=None, bundle_info=None,
            mime_types=None, reference_url=None, insecure=None, encoding=None, synopsis=None,
            allow_directory=False, raise_trigger=True):

        def convert_arg(arg, default=None):
            if arg and isinstance(arg, str):
                return arg.split(',')
            return [] if default is None else default
        suffixes = convert_arg(suffixes)
        nicknames = convert_arg(nicknames, [name.lower()])
        mime_types = convert_arg(mime_types)
        insecure = category == self.CAT_SCRIPT if insecure is None else insecure

        if name in self._formats:
            registrant = lambda bi: "unknown registrant" if bi is None else "%s bundle" % bi.name
            self.session.logger.info("Replacing data format '%s' as defined by %s with definition from %s"
                % (name, registrant(self._formats[name][0]), registrant(bundle_info)))
        from .format import DataFormat
        self._formats[name] = (bundle_info, DataFormat(name, category, suffixes, nicknames, mime_types,
            reference_url, insecure, encoding, synopsis, allow_directory))
        if raise_trigger:
            self.triggers.activate_trigger("data formats changed", self)

    def add_provider(self, bundle_info, name, *, category=None, suffixes=None, nicknames=None,
            mime_types=None, reference_url=None, insecure=None, encoding=None, synopsis=None,
            allow_directory=False, **kw):
        logger = self.session.logger
        if kw:
            logger.warning("Data format provider '%s' supplied unknown keywords with format description: %s"
                % (name, repr(kw)))
        if suffixes is None:
            if allow_directory:
                suffixes = []
            else:
                logger.error("Data format provider '%s' didn't specify any suffixes." % name)
            return
        if category is None:
            logger.warning("Data format provider '%s' didn't specify a category."
                "  Using catch-all category '%s'" % (name, self.CAT_GENERAL))
            category = self.CAT_GENERAL
        self.add_format(name, category, suffixes=suffixes, nicknames=nicknames, bundle_info=bundle_info,
            mime_types=mime_types, reference_url=reference_url, insecure=insecure, encoding=encoding,
            synopsis=synopsis, allow_directory=allow_directory, raise_trigger=False)

    def end_providers(self):
        self.triggers.activate_trigger("data formats changed", self)

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Data format key is not a string")
        if key in self._formats:
            return self._formats[key][1]
        for bi, format_data in self.formats.values():
            if key in format_data.suffixes:
                return format_data
        raise KeyError("No known data format '%s'" % key)
