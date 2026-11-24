# cloud-sheets

One reference sheet per datasheet for the parts in cloud-parts: the pins,
tables, graphs as data points, application circuits and register maps, as
data files.

## Layout

- `datasheets/<kind>/<name>.json` a sheet (`FORMAT.md`)
- `datasheets/<kind>/<name>.<circuit>.svg` a circuit's drawing
- `datasheets/<kind>/<name>.pinout.html`, `<name>.land.html` the package outline and land pattern
- `registers/<kind>/<name>.json` a microcontroller's registers (`REGISTERS-FORMAT.md`), `<name>.html` the same as a page
- `index.csv` one row per sheet: part numbers, manufacturer, kind, path, source revision and pages, circuits
- `render.py` writes a sheet as an HTML page

## Pages

    python3 render.py all         # every sheet as datasheets/<kind>/<name>.html, and index.html, which lists them
    python3 render.py <name>      # one

A few seconds; Python 3, standard library. cloud-parts' `install.sh` runs it.
Open `index.html` to browse.

A page is one HTML file that loads nothing else. Each part of it is a
`<section>` with an id, and each graph a `<figure>` with one, to link to or
lift out: `LM317DCYR.html#absolute-maximum-ratings`, `#circuit-adjustable`,
`#curve-<title>`.

Beside cloud-parts (or at `$CLOUD_SHEETS`), `cloud-parts show MPN` gives a
part's sheet and its page.

## Licence

Sheets and drawings CC0-1.0, `render.py` Apache-2.0 (`LICENSES/`).
