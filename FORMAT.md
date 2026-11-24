# A sheet

One JSON file per datasheet, `datasheets/<kind>/<name>.json`, UTF-8.
`render.py` draws it as a page. Every value is the maker's published figure; every
sentence is written new. A `page` is the page of the maker's datasheet the
item was read from, counted from 1.

```json
{
  "sheet": 1,
  "name": "LD39015",
  "kind": "ldo",
  "manufacturer": "STMicroelectronics",
  "title": "150 mA low-dropout voltage regulator",
  "source": {"revision": "Rev 9, March 2014", "pages": 15},
  "summary": "Two to four sentences: what the part is and does.",
  "key_figures": [["Output current", "150 mA"], ["Dropout", "80 mV typ at 100 mA"]],

  "part_numbers": {
    "page": 14,
    "columns": ["part number", "output voltage", "package", "marking", "packing"],
    "rows": [["LD39015M33R", "3.3 V", "SOT23-5L", "9033", "tape and reel, 3000"]]
  },

  "pins": [
    {"package": "SOT23-5L", "page": 3, "pins": [
      {"pin": "1", "name": "IN", "type": "power in", "function": "Supply input."}
    ]}
  ],

  "tables": [
    {"title": "Absolute maximum ratings", "page": 4,
     "conditions": "",
     "columns": ["parameter", "symbol", "conditions", "min", "typ", "max", "unit"],
     "rows": [["Input voltage", "VIN", "", "-0.3", "", "7", "V"]],
     "notes": ["Each note in new words."]}
  ],

  "curves": [
    {"title": "Dropout voltage against output current", "page": 8,
     "conditions": "VOUT = 3.3 V",
     "x": {"label": "Output current", "unit": "mA", "scale": "linear"},
     "y": {"label": "Dropout voltage", "unit": "mV", "scale": "linear"},
     "series": [{"label": "25 °C", "points": [[0, 0], [50, 40], [100, 80], [150, 120]]}]}
  ],

  "circuits": [
    {"id": "typical", "title": "Typical application", "page": 1,
     "description": "What the circuit does and why each part is there.",
     "parts": [
       {"ref": "U1", "type": "ic", "value": "LD39015"},
       {"ref": "C1", "type": "capacitor", "value": "1 µF", "note": "ceramic"}
     ],
     "notes": []}
  ],

  "equations": [
    {"name": "Output voltage", "expr": "VOUT = VREF × (1 + R1 / R2)",
     "where": {"VREF": "feedback reference, 1.23 V", "R1": "upper divider resistor"},
     "note": "", "page": 10}
  ],

  "operation": [
    {"topic": "Enable", "page": 9, "text": "How the part behaves, in new words."}
  ],

  "packages": [
    {"name": "SOT23-5L", "page": 12, "unit": "mm",
     "columns": ["symbol", "what", "min", "typ", "max"],
     "rows": [["A", "overall height", "0.90", "", "1.45"]]}
  ]
}
```

## Fields

- `tables`: any table of figures. Electrical tables use the columns above;
  another table names its own columns. Cells are strings as printed
  (`"-0.3"`, `"1.2"`, `""` for an empty cell). A table that runs over two
  pages is one table with the first page.
- `curves`: a graph as its data. `scale` is `linear` or `log`. A series is
  a list of `[x, y]` points in the axis units, enough of them that straight
  lines between them follow the curve. A graph with two vertical scales
  has a `y2` axis beside `y`, and each series on it carries `"axis": "y2"`.
- `circuits`: a maker's application circuit: its `title`, `page`, a
  `description` in words and `parts`, the parts the maker's circuit names
  with their values. A part's `type` is one of `ic`, `resistor`,
  `capacitor`, `inductor`, `diode`, `led`, `zener`, `schottky`, `npn`,
  `pnp`, `nmos`, `pmos`, `crystal`, `switch`, `connector`, `terminal`,
  `source`, `load`, `other`. A `terminal` is a place the circuit meets the
  outside (an input, an output). An IC that is not this sheet's part
  carries `"external": true`.
- A circuit's `id` is lower-case letters, digits and hyphens. Its drawing
  is the file `<name>.<id>.svg` beside the sheet, drawn with parts from
  the parts library; a position the library has no part for is marked
  `NO PART`. `fixture` is true on a circuit the maker measures the part in
  (a switching-time or gate-charge test circuit).
- A cell printed in parentheses (a reference dimension) keeps them.
- `name` is the file's stem.
- A sheet is about the part. Nothing in it is about the sheet, the
  maker's document or how either was made.
