#!/usr/bin/env python3
'''
Example script showing the useage of the pymps library.

License:
--------

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

Usage:
------
    python parse.py -i example_dat/afiro.mps
    python parse.py -i example_dat/afiro.mps -o afiro.json
    python parse.py -i example_dat/afiro.mps --summarize
    python parse.py -i example_dat/afiro.mps --fill --verbose
    python parse.py -i example_dat/afiro.mps -o afiro_dual.mps --dual


Reference:
----------
    http://lpsolve.sourceforge.net/5.5/mps-format.htm
    http://plato.asu.edu/cplex_mps.pdf
    http://www.gurobi.com/documentation/8.0/refman/mps_format.html

Output:
-------
    If the --output is provided, the parsed data will be written to a JSON
    file with the format:
    {
        "NAME": "AFIRO",
            "ROWS": {
                "R09": "E",
                "R10": "E",
                "X05": "L",
                "COST": "N"
            },
            "COLUMNS": {
                "X01": {
                    "X48": 0.301,
                    "R09": -1.0,
                    "R10": -1.06,
                    "X05": 1.0
                },
                "X02": {
                    "X21": -1.0,
                    "R09": 1.0,
                    "COST": -0.4
                }
            },
            "RHS": {
                "X50": 310.0,
                "X51": 300.0,
                "X05": 80.0,
                "X17": 80.0,
                "X27": 500.0,
                "R23": 44.0,
                "X40": 500.0
            },
            "BOUNDS": {
                "X01": {
                    "upper": np.Inf,
                    "lower": 0
                }
            },
            "RANGES": {
                "R90": {
                    "upper": 12,
                    "lower": 2
                }
            },
            "OBJ_ROW": "COST",
            "RHS_id": "RHS1",
            "RANGES_id": "RG",
            "BOUNDS_id": "BND1"
    }
'''

__author__ = "Constantino Schillebeeckx"
__version__ = "0.1.0"
__license__ = "MIT License"
__summary__ = "Example for using pymps"

import argparse
import json
import numpy as np
from numpy import array, inf
from pymps import parse_mps, summarize, make_dual, parsed_as_mps

def from_mpsformat(dat):
    """
    Reads a dict-serialized .mps file and emits the semantics
    in a tableau representation

    Parameters
    ----------
    dat : Dict[str, Any]
        Dictionary serialization of a .mps file

    Returns
    -------
    Tucker tableau representation
    """
    rows = array(list(dat['ROWS'].keys()))
    columns = array(dat['ALL_COLUMNS'])
    o = True
    row_offset = {}

    lb = np.full(len(columns), 0.)
    ub = np.full(len(columns), inf)
    lhs = np.full(len(rows), -inf)
    rhs = np.full(len(rows), 0.)
    Ac = np.zeros((len(rows), len(columns)))

    # swap the objective row to the bottom
    i, = np.where(rows == dat['OBJ_ROW'])
    rows[i[0]], rows[-1] = rows[-1], rows[i[0]]

    for m, row in enumerate(rows):
        if row in dat['RANGES']:
            lhs[m] = dat['RANGES'][row]['lower']
            rhs[m] = dat['RANGES'][row]['upper']
        else:
            if row in dat['RHS']:
                rhs[m] = dat['RHS'][row]
            sense = dat['ROWS'][row]
            if sense == 'G':
                lhs[m], rhs[m] = rhs[m], -lhs[m]
            elif sense == 'E':
                lhs[m] = rhs[m]
            elif sense == 'N':
                lhs[m] = -inf
                row_offset[rows[m]] = rhs[m]
                rhs[m] = inf

    assert rhs[-1] == inf

    for n, col in enumerate(columns):
        if col in dat['BOUNDS']:
            bnd = dat['BOUNDS'][col]
            if 'lower' in bnd:
                lb[n] = bnd['lower']
            if 'upper' in bnd:
                ub[n] = bnd['upper']
    return (lb, ub, lhs, rhs, Ac)

def main(args):

    if args.dual:
        args.fill = True

    parsed_data = parse_mps(args.input, args.verbose, args.fill)
    (lb, ub, lhs, rhs, Ac) = from_mpsformat(parsed_data)

    # SUMMARIZE
    if args.summarize:
        summarize(parsed_data)

    # OUTPUT
    if args.output:

        if args.dual:
            dual = make_dual(parsed_data, args.sense)
            out_dat = parsed_as_mps(dual)
        else:
            out_dat = json.dumps(parsed_data, indent=2)

        with open(args.output, 'w') as fout:
            fout.write(out_dat)
        print(f"Data saved to {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    required = parser.add_argument_group('required arguments')

    required.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="MPS file to parse",
    )

    parser.add_argument(
        "-o",
        "--output",
        action="store",
        help=(
            "Output file to write parsed MPS to. NOTE, this will be in JSON format "
            "unless the --dual flag is provided."
        )
    )
    parser.add_argument(
        "--verbose",
        action='store_true',
        default=False,
        help="Show verbose warnings."
    )
    parser.add_argument(
        "--fill",
        action='store_true',
        default=False,
        help=(
            "When provided, default values which aren't explicitly will be filled out. "
            "If a RHS isn't specified, it will be filled with 0; if a BOUND is missing, "
            "it will be set as 0 < var < +inf."
        )
    )
    parser.add_argument(
        "--dual",
        action='store_true',
        default=False,
        help=(
            "Instead of outputting a JSON with the --output flag; output the dual "
            "reprentation of the primal problem. NOTE: this flag implies fill=True."
        )
    )
    parser.add_argument(
        "--sense",
        action='store',
        default='MAX',
        choices=['MIN', 'MAX'],
        help=(
            "Optimization sense of dual output."
        )
    )
    parser.add_argument(
        "-s",
        "--summarize",
        action='store_true',
        default=False,
        help=(
            "Print summary of parsed data to STDOUT."
        )
    )

    args = parser.parse_args()
    main(args)
