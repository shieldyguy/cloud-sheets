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

## Use

    python3 render.py <name>      # writes datasheets/<kind>/<name>.html
    python3 render.py all

Python 3, standard library. Beside cloud-parts (or at `$CLOUD_SHEETS`),
`cloud-parts show MPN` names a part's sheet and `cloud-parts sheet MPN`
writes its page.

## Licence

Sheets and drawings CC0-1.0, `render.py` Apache-2.0 (`LICENSES/`).
