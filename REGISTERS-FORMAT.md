# Register files

`registers/<kind>/<name>.json` holds one microcontroller's registers: each
peripheral, its instances and base addresses, and each register's
address offset, width, reset value, access and fields, with each field's
bit positions and settings. `<name>.html` beside it shows the same file
as a page.

Names, addresses, bit positions, reset values and settings are the
maker's, as published. Each `text` is a line saying what a field, setting
or register does. A `page` is the page of the maker's document, counted
from 1.

## The file

UTF-8 JSON.

```json
{
  "registers": 1,
  "name": "ATSAMD21G18A-MU",
  "manufacturer": "Microchip",
  "source": {"document": "ATSAMD21G18A-MU.pdf", "revision": "DS40001882L", "pages": 1161},
  "peripherals": [
    {"name": "WDT", "title": "Watchdog Timer", "page": 226,
     "instances": [{"name": "WDT", "base": "0x40001000"}],
     "registers": [
       {"name": "CTRL", "title": "Control", "offset": "0x0", "bits": 8,
        "reset": "0bx0000xx0", "access": "R/W", "page": 227,
        "property": ["write-protected", "enable-protected", "write-synchronized"],
        "notes": ["Its reset state is copied from the NVM user row at start-up."],
        "fields": [
          {"name": "ALWAYSON", "bits": "7", "access": "R/W", "reset": "x",
           "text": "Locks the watchdog on until a power-on reset.",
           "values": [{"value": "0", "name": "", "text": "ENABLE turns the watchdog on and off."},
                      {"value": "1", "name": "", "text": "The watchdog runs and only a power-on reset stops it."}]}
        ]}
     ]}
  ]
}
```

- `source` names the maker's document the file is read from: its file
  name, its revision and its number of pages.
- `offset`, `base`, `reset`: as printed, hexadecimal with `0x`. A
  register the maker gives no address for anywhere has no `offset`, and
  a note says so. A reset value the maker gives per bit is the
  register's value assembled from them (`0b` and one character a bit);
  an undefined bit is `x`, a bit that differs by device keeps the maker's
  letter.
- A register whose value after other resets differs from its power-on
  value keeps the power-on value in `reset` and the other in
  `"reset_other"`.
- A register that also answers at a second address carries
  `"alias": ["0x200"]`.
- A reset that differs by instance keeps the common value in `reset`
  and carries `"reset_by_instance": {"WDT1": "0x8000.0000"}`, as printed.
- A register that also has an I/O address beside its data-memory address
  carries the data-memory address in `offset` and the other in `"io"`.
- A field with several settings tables, one for each mode, carries them
  as `"tables": [{"when": ..., "columns": [...], "rows": [[...]]}]`.
- `bits` on a register is its width; on a field it is `"7"` or `"12:8"`,
  high bit first. Reserved bits are not fields.
- `access` is the maker's own code (`R/W`, `R`, `W`, `R/W1C`); a
  register whose fields differ lists each code once (`"R, R/W"`).
- `property` lists the maker's properties of a register as printed, in
  lower case.
- `notes` are lines about the register as a whole.
- `values` is a field's table of settings where the maker gives one:
  `value` as printed (a number or a range such as `0xC-0xF`), `name` the
  maker's name for the setting where it gives one, `text` what it does.
  A row that holds only under another setting carries `"when"`. A
  settings table with more columns than value, name and meaning is
  `"table": {"columns": [...], "rows": [[...]]}` in place of `values`,
  cells as printed, a column of sentences written new.
- A family of one-bit fields written once (`EXTINTx`, bits 15 to 0) is
  one field with `"bits": "15:0"` and `"each": true`.
- A family of multi-bit fields written once (`INnACT`, two bits each,
  bits 9 to 0) is one field with `"bits": "9:0"`, `"each": true` and
  `"width": 2`, the bits of one member.
- A register that repeats (`n = 0..7`) is one register with
  `"repeat": {"count": 8, "step": "0x04"}`. Registers of a block that
  repeats (an endpoint, a port group) each carry
  `"group": {"name": "endpoint", "count": 8, "step": "0x20"}`; `count`
  and `step` are given where the maker prints them. A register may carry
  both `group` and `repeat`.
- A peripheral whose register map differs by mode is one entry per mode,
  each with `"mode"`, the maker's name for it. A field that exists in
  one mode only carries `"mode"`; fields never overlap within a mode. A
  register shared by several modes is carried in each mode's entry.
- A register printed as several views at one offset, by mode or by type
  (`US_IER (LIN_MODE)`), is one register per view, each with `"mode"`,
  the maker's name for the view; registers never overlap within a mode.
- `instances` lists the peripheral's instances and their base addresses.
  An instance may carry `"domain"`, the maker's name for the core or
  domain it belongs to, and `"secure": true` or `false` where the maker
  gives a secure and a non-secure base. A table that lives in RAM has no
  `instances` and its registers no `reset`.
- Where the maker's document gives one figure two ways (a reset value
  and the reset row of its bits, a register's name in two tables), the
  file carries one and a note gives the other.
