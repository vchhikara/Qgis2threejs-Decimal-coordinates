# Qgis2threejs Decimal Coordinates

Show Qgis2threejs query coordinates in decimal degrees, add a heading and choose a north arrow for the live viewer and new HTML exports.

## Requirements

Install and enable Qgis2threejs alongside this plugin. Use the edition that matches your QGIS major version:

- **0.2.3:** QGIS 3.34–3.99; targets Qgis2threejs 2.8–2.10.2.
- **0.2.4:** QGIS 4.0–4.99; targets Qgis2threejs 2.10.2 and 3.0–3.3.

Compatibility is limited to versions that have been tested. QGIS 3.34.14 and 3.44.12 were exercised with Qgis2threejs 2.10.2; QGIS 3.44.12 was also exercised with Qgis2threejs 2.8 and 2.9. QGIS 4.2.3 was exercised with Qgis2threejs 3.2.1 and 3.3 in embedded and external-browser previews, and with 3.1.3 using a direct query call. Its web exports were exercised with Qgis2threejs 2.10.2, 3.0, 3.1.3, 3.2.1 and 3.3. Additional scene, version and platform testing is needed before publication.

## Install and use

1. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP** and select the ZIP for your QGIS version.
2. Enable Qgis2threejs and Qgis2threejs Decimal Coordinates.
3. Open the Qgis2threejs viewer. In scene properties choose **World → Coordinate Display → Latitude and longitude** and apply the setting.
4. Click a queryable object. Use the **Decimal degrees** checkbox beside its coordinates to switch between decimal degrees and the original display. You can also use the plugin's toolbar button or menu action.
5. Open **Plugins → Qgis2threejs Decimal Coordinates → Heading and north arrow…** to configure an optional centred heading and north arrow.

The heading supports font, size, colour, bold and italic. The north-arrow list includes 11 QGIS designs and a custom SVG or PNG option; custom images should point upward. Set the arrow's size and position in the same dialog. Browsers use an available fallback when the chosen font is not installed.

Coordinates use latitude, longitude order, for example `28.613900° N, 77.209000° E, Elev. 200.00`. South and west values are negative. N and E identify the geographic axes; they are not projected northing and easting. Elevation, map data, measurements and camera controls are unchanged.

## Export a web scene

Set the heading and arrow, then create a new web export in Qgis2threejs. The export adds a settings-specific JavaScript file next to the HTML and embeds the selected arrow in that file. Keep the HTML, JavaScript and the rest of the exported scene together when sharing it. Existing exports do not change.

The arrow turns as the camera bearing changes. When projection information is available, the viewer attempts to account for the difference between grid north and geographic north; otherwise it uses grid north. Verify orientation for your projection and scene before sharing an export.

## What's new since 0.2.2

- A checkbox in the query result switches decimal coordinates on or off.
- A viewer settings dialog adds a centred heading and a choice of north arrows, including custom artwork.
- New web exports carry the viewer settings and selected arrow.
- A welcome window explains the changes and can be reopened from the plugin menu.
- Separate editions target QGIS 3 and QGIS 4, with adapters for older and newer Qgis2threejs viewer structures.

## Troubleshooting

- **Coordinates do not change:** Enable the plugin and select **Latitude and longitude** in Qgis2threejs scene settings. Click a queryable object and check the checkbox beside the result.
- **Viewer warning:** Check the Qgis2threejs version. The plugin refuses versions outside its edition's target range.
- **A heading or arrow is missing from an existing export:** Create a new export after changing the settings. Keep the generated files together.
- **The custom arrow is missing:** Choose an existing SVG or PNG no larger than 2 MB.
- Open **View → Panels → Log Messages** and select **Qgis2threejs Decimal Coordinates** for plugin warnings.

This plugin wraps internal Qgis2threejs viewer and exporter functions. Upstream changes or other extensions wrapping the same functions may cause conflicts. The original exporter may already have created files if the companion's export step fails.

## License and author

Plugin: GPL-3.0-or-later; see [LICENSE](LICENSE). For the bundled arrow artwork, see [north_arrows/NOTICE.md](north_arrows/NOTICE.md).

Vipul Chhikara, India · vipul.chhikara@gmail.com
