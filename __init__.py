# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoIGN
                                 A QGIS plugin
 Geoservice de l'IGN
                             -------------------
        begin                : 2016-05-12
        copyright            : (C) 2016 by ENSG
        email                : errazkisibawaih@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeoIGN class from file GeoIGN.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geo_ign import GeoIGN
    return GeoIGN(iface)
