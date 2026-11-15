# Test package status

The two ZIPs in this folder are test builds, not publication-ready releases. They are based on version 0.2.2 and target versions 0.2.3 (QGIS 3) and 0.2.4 (QGIS 4).

## Checks completed

- Windows QGIS 3.34.14 and 3.44.12, with Qgis2threejs 2.10.2 and WebKit; also QGIS 3.44.12 with the official Qgis2threejs 2.8 package and the upstream 2.9 source tag: the live scene displayed a heading, selected arrow and decimal query coordinates. The menu/toolbar action and viewer checkbox synchronized; unload removed the hooks. The settings dialog created previews for all 11 arrows, and custom PNG loading was exercised. The What's New window and its automatic-display preference were exercised.
- Windows QGIS 3.44.12 with Qgis2threejs 2.8, 2.9 and 2.10.2: created web exports and opened them in headless Chrome. The heading, embedded arrow, coordinate checkbox, original-coordinate restoration and arrow rotation were exercised on flat scenes.
- Chrome fixtures exercised the actual Qgis2threejs 3.2.1 and 3.3 JavaScript bundles, including the query adapter. They are not tests of the QGIS 4 viewer or full real-world exports.
- Windows QGIS 4.2.3 with Qgis2threejs 3.2.1 and 3.3: isolated embedded and external-browser live preview tests exercised the query, heading, arrow, settings and cleanup. A 3.1.3 embedded viewer passed the direct query call, but a simulated canvas click did not produce a result in the isolated flat-scene test.
- Windows QGIS 4.2.3 exports with Qgis2threejs 2.10.2, the 3.0 source tag, 3.1.3, 3.2.1 and 3.3 were opened in Chrome and passed the heading, arrow, rotation and coordinate-toggle checks.
- Unit tests cover version routing, cancellation, script filenames, viewer checkbox behavior, projected-coordinate preservation and overlay cleanup. The 11 bundled SVG Git blob hashes match the QGIS `release-3_44` sources.

## Work remaining before publication

- Test the QGIS 3 build with other 2.x releases as needed, WebEngine and real project data. WebEngine was unavailable in the tested QGIS 3.44.12 environment.
- Investigate the isolated Qgis2threejs 3.0 live-viewer click test, which did not return a result, and the 3.1.3 canvas click, which produced no coordinate despite its direct query passing. Test Qgis2threejs 2.10.2 in a QGIS 4 live viewer, and exercise additional real project data and QGIS 4 versions.
- Check compass direction on rotated scenes and representative projected CRSs, especially projection convergence and steep camera angles. The implementation falls back to grid north if geographic projection data is unavailable.
- Review redistribution rights and notices for each bundled QGIS arrow. Check how custom SVGs, fonts and mobile layouts behave in the browsers to be supported.
- Recheck package metadata, version ranges and QGIS repository requirements after testing. Do not upload a test ZIP as a stable release.

QGIS 3.34.14 logged an authentication-database directory warning in the isolated smoke-test profile; the viewer assertions passed. That warning was not investigated further.

An isolated QGIS 4 in-process WebEngine viewer process exited while starting the upstream viewer, before the companion plugin was constructed. Normal Windows embedded-process and external-browser preview modes worked in the checks above.
