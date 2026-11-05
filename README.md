# Qgis2threejs Decimal Coordinates

Show latitude and longitude in Qgis2threejs query results as decimal degrees, with six decimal places. The plugin applies to the live 3D viewer and to new HTML exports.

Coordinates appear in latitude, longitude order, for example:

```text
28.613900° N, 77.209000° E, Elev. 200.00
```

Values are signed: south and west are negative. For example, `-10.000000° N, -20.000000° E` identifies a point south and west of the origin. The N and E labels identify the geographic axes; these values are latitude and longitude, not projected northing and easting. Elevation is unchanged.

## Requirements

- QGIS 3.34 or later in the QGIS 3 series.
- Qgis2threejs **2.10.2**, installed and enabled. The plugin uses internal Qgis2threejs interfaces and will stay inactive with other versions.
- A scene with queryable objects and a coordinate system supported by the Qgis2threejs geographic transform.

Earlier local smoke tests reported QGIS 3.34.14, 3.42.2 and 3.44.12 with WebKit. Other versions, WebEngine and platforms have not been fully verified.

## Install and use

1. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP** and select the plugin ZIP.
2. Enable both Qgis2threejs and Qgis2threejs Decimal Coordinates.
3. Select **Plugins → Qgis2threejs Decimal Coordinates → Decimal degree coordinates**, or click the plugin's toolbar icon. A check mark or pressed icon shows that the setting is on. QGIS remembers the setting between sessions.
4. Open the Qgis2threejs viewer. In scene properties, choose **World → Coordinate Display → Latitude and longitude**, then apply the settings.
5. Click a queryable object in the 3D viewer. Its query result should show latitude and longitude to six decimal places.

The plugin reformats geographic query results. It does not change map data, projected X/Y display, measurements, height or camera controls. If a DMS result is already visible when you enable the plugin, its conversion uses the rounded text on screen. Click again to use the original geographic values.

## Export a web scene

Enable the plugin and select **Latitude and longitude** in the scene properties before creating a Qgis2threejs HTML export. Keep `q3d_decimal_degrees_companion.js` alongside the exported HTML when moving or sharing it.

Existing exports do not change. An export created while the plugin is off keeps the original coordinate display.

## Troubleshooting

- **Coordinates do not change:** Check that the plugin is enabled and that **Coordinate Display** is set to **Latitude and longitude**. Apply the scene settings and click a queryable object again.
- **Unsupported version warning:** Install and enable Qgis2threejs 2.10.2.
- **Menu or toolbar icon is missing:** Check that Qgis2threejs Decimal Coordinates is enabled in the QGIS Plugin Manager. If it failed to load, check the QGIS Python error message and log.
- **An export still shows the original format:** Create a new export with the plugin enabled and keep the companion JavaScript file beside the HTML. Check the browser console for messages.

For plugin warnings, open **View → Panels → Log Messages** and select **Qgis2threejs Decimal Coordinates**.

## Compatibility and limitations

The plugin wraps internal Qgis2threejs functions in memory. No supported extension hook for this behavior has been identified. The plugin does not edit Qgis2threejs files and removes its own hooks on unload where possible. Changes to Qgis2threejs or other extensions that wrap the same functions may cause conflicts.

The export integration rejects unexpected templates and conflicting companion scripts. If it fails, the original exporter may already have created output files. Earlier validation included simulated queries and exports; test your own scenes and browser before distribution.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE) for the full license text.

## Author

Vipul Chhikara, India  
Email: vipul.chhikara@gmail.com
