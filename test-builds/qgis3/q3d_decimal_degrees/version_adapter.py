"""Identify known Qgis2threejs integration families without importing QGIS."""

import re


def exporter_module(version, edition):
    """Return an exporter import path only for versions targeted by an edition."""
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', version):
        return None
    number = tuple(int(part) for part in version.split('.'))
    number += (0,) * (3 - len(number))
    if edition == 3 and (2, 8, 0) <= number <= (2, 10, 2):
        return 'Qgis2threejs.export' if number < (2, 9, 0) else 'Qgis2threejs.core.export.export'
    if edition == 4 and (number == (2, 10, 2) or (3, 0, 0) <= number <= (3, 3, 0)):
        return 'Qgis2threejs.core.export.export'
    return None


def export_succeeded(result):
    """Version 2.8 returns False on cancellation; newer exporters raise."""
    return result is not False
