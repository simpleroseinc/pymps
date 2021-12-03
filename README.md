# Python Parse MPS

Fixed-format MPS parser.

:warning: free-format MPS not supported!

## References

- http://plato.asu.edu/cplex_mps.pdf
- http://lpsolve.sourceforge.net/5.5/mps-format.htm

## Usage

```
from pymps import parse_mps, summarize

mps = parse_mps('afiro.mps')
summarize(mps)
```

## Unit tests

Unit tests are written in the `tests` subfolder and can be run with Python unittest.
For example:
```
python -m unittest
```

## Assumptions

When values are missing or omitted, some assumptions must be made about those data.

- only one free ('N') ROW is provided; any others are ignored
- only one vector descriptors is used for RANGE, BOUNDS and FREE; any others are ignored
- omitted bound values for UP, LO, FX are assumed to be 0
- missing RHS values as assumed to be 0, only when `fill=True`
- missing COLUMN/ROW coefficients are assume to be 0, only when `fill=True`
- missing BOUNDs are handled according to the table below, only when `fill=True`

Upper | Lower | Result
--- | --- | ---
 positive (>0) |  None | lower= 0
 negative incl. 0 (<= 0) |  None | lower=-Inf
None | >0 or <0 | upper=+Inf
None | None | upper=+Inf, lower=0


## Options

The function `parse_mps()` takes two optional arguments:

`verbose` (bool, default False) If provided, will print numerous messages regarding the parsing of the MPS file including:

- missing RHS values
- missing BOUNDS
- skipping RANGE vectors if multiple specified
- skipping BOUNDS vectors if multiple specified
- skipping RHS vectors if multiple specified
- skipping free (e.g. N) ROWS if multiple specified
- ignoring BOUNDS values if specified and bound type is FR, MI or PL
- missing upper/lower bound (when lower/upper is provided), applicable on when `fill=True`

`fill` (bool, default False) If provided, this will

- set unspecified COLUMN/ROW coefficients with 0
- set unspecified RHS values with 0
- set unspecified lower, upper BOUNDS with 0, +Inf (respectively)

## Output format

The function `parse_mps()` returns a JSON like dictionary with the format:

```
{
    "NAME": "EXAMPLE",
    "ROWS": {
        "R01": "L",
        "R02": "E",
        "R03": "G",
        "R04": "E",
        "COST": "N"
    },
    "COLUMNS": {
        "R01": {
            "C01": 30.0,
            "C02": -10.0,
            "C03": 50.0
        },
        "R02": {
            "C01": 5000.0,
            "C02": 0.0,
            "C03": -3.0
        },
        "R03": {
            "C01": 0.2,
            "C02": 0.1,
            "C03": 0.0
        },
        "COST": {
            "C01": 10.0,
            "C02": 5.0,
            "C03": 5.5
        },
        "R04": {
            "C02": 0.2,
            "C03": 0.3
        }
    },
    "RHS": {
        "R01": 1500.0,
        "R02": 200.0,
        "R03": 12.0,
        "R04": 0.0
    },
    "BOUNDS": {
        "C01": {
            "upper": 0.0
        },
        "C03": {
            "lower": 0.0
        },
        "C02": {
            "upper": 0.0,
            "lower": 0.0
        }
    },
    "RANGES": {
        "R01": {
            "upper": 1500.0,
            "lower": 1486.0
        },
        "R02": {
            "upper": 214.0,
            "lower": 200.0
        },
        "R03": {
            "upper": 26.0,
            "lower": 12.0
        },
        "R04": {
            "upper": 0.0,
            "lower": -14.0
        }
    },
    "ALL_COLUMNS": [
        "C01",
        "C02",
        "C03"
    ],
    "OBJ_ROW": "COST",
    "RHS_id": "B",
    "BOUNDS_id": "BOUND",
    "RANGES_id": "rhs"
}
```

:warning: Key order (e.g. of `COLUMNS` or `ROWS` is not guaranteed)

Where:
- `OBJ_ROW` is the ROW label identifies as the objective row (with 'N'), note is it also still present in the ROWS section.
- `RHS_id` is the RHS indtifier vector, note it may be None.
- `RANGES_id` is the RANGES indtifier vector, note it may be None.
- `BOUNDS_id` is the BOUNDS indtifier vector, note it may be None.
- `ALL_COLUMNS` is a list of all columns
- `COLUMNS` is indexes as ROW, COLUMN

## TODO

- assert all characters are ASCII
- assert names under 255 length
- handle $ comment symbol in fields 3 and 5

## License
Copyright © 2021 SimpleRose, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
