#!/usr/bin/env python3
'''
Library to parse fixed formatted MPS files.

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

Description:
------------

Will parse the record indicators:
    - NAME
    - ROWS
    - COLUMNS
    - RHS
    - BOUNDS
    - RANGES

Will return a JSON-like data structure like:
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
__summary__ = "Python-based parser for MPS formatted linear program files"


from collections import OrderedDict, defaultdict, Counter
import numpy as np
import copy
import pandas as pd

COUNTS = {
    'LO': 0,
    'UP': 0,
    'FX': 0,
    'FR': 0,
    'MI': 0,
    'PL': 0
}

ALLOWED_ROW_SENSE = ['N', 'G', 'L', 'E']
ALLOWED_RANGES = ['G', 'L', 'E']
ALLOWED_BOUNDS = ['LO', 'UP', 'FX', 'FR', 'MI', 'PL']
REQUIRED_INDICATORS = ['NAME', 'ROWS', 'COLUMNS']
ALLOWED_INDICATORS = set(REQUIRED_INDICATORS) | set(
    ['RHS', 'BOUNDS', 'RANGES'])


def parse_mps(mps_file, verbose=False, fill=False):
    '''
    Parse a fixed-format MPS file into a JSON-like dictionary structure

    Params:
    -------
    mps_file (str) - MPS file to parse
    verbose (bool, default False) - print messages about assumptions being made
    fill (bool, default False) - fill missing values

    Yields:
    -------
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
    parsed_data = {
        'NAME': None,
        'ROWS': OrderedDict(),
        'COLUMNS': OrderedDict(),
        'RHS': OrderedDict(),
        'BOUNDS': defaultdict(dict),
        'RANGES': OrderedDict(),
        'ALL_COLUMNS': set()
    }

    current_indicator = None

    # READ IN FILE
    with open(mps_file, 'r') as fin:
        dat = fin.readlines()

    # ITERATE OVER EACH LINE, PARSING IT
    for l in dat:
        current_indicator, data = parse_line(
            l,
            current_indicator,
        )

        # IF ON A DATA INDICATOR
        if data:
            if current_indicator == 'NAME':
                assert not parsed_data['NAME'], f"NAME already specified as {parsed_data['NAME']}"

                parsed_data['NAME'] = data
            elif current_indicator == 'ROWS':
                parsed_data = add_row(
                    data,
                    parsed_data,
                    verbose
                )
            elif current_indicator == 'COLUMNS':
                parsed_data = add_col(data, parsed_data)
            elif current_indicator == 'RHS':
                parsed_data = add_rhs(data, parsed_data, verbose)
            elif current_indicator == 'BOUNDS':
                parsed_data = add_bound(
                    data,
                    parsed_data,
                    verbose
                )
            elif current_indicator == 'RANGES':
                parsed_data = add_range(data, parsed_data, verbose)

    # ENSURE ALL REQUIRED RECORDS EXIST
    for l in REQUIRED_INDICATORS:
        if not len(parsed_data[l]):
            raise ValueError(f"Indicator record '{l}' is missing!")

    # CONFORM DATA
    parsed_data = conform_bounds(parsed_data, verbose, fill)
    parsed_data = conform_rhs(parsed_data, verbose, fill)
    parsed_data = conform_cols(parsed_data, fill)
    conform_objective(parsed_data)

    return parsed_data


def make_dual(dat, sense='MAX'):
    '''
    Covert a parsed MPS into its dual formulation

    NOTE: must use parse_mps(fill=True)

    Before generating the dual representation of the problem, all row
    contstraints are changed into >= ('G') by multipling the row & RHS
    through by -1. This prevents us from having a dual variable of the
    form dual_var <= 0.

    Furthermore, the original problem variable constraints must be reformatted
    to be in standard canonical form. That is, they must all be in the form
    x >= 0.

    We handle these situations as follows:

    x = a (FX row):
        Evaluate the column by multiplying a by the coefficient and subtracting
        that value from the RHS.

    x <= a (UP):
        Shift all the row constraints by a: x' = a - x

    x >= a (LO):
        Shift all the row constraints by a: x' = x - a

    a <= x <= b (LO & UP):
        Add a new 'G' row constraint with a 1 coefficient in the column for x
        and a RHS of a. Also, shift all the row constraints (including the
        newly added one from UP) by b.

    NOTE: we should also be modifying RANGES, but I'm not implementing that
    at the moment since no NETLIB files have them. These would be handled by
    adding a new row constraints for every lower bound range expression.

    Params:
    -------
    dat (dict) - output from parse_mps
    sense (str, default MAX) - sense of dual MPS, will add a OBJSENSE and
        OBJNAME section.
    negate (bool, default False) - whether to negate the objective function
    '''

    # Although this code works, there seems to be a more optimal way of generating
    # the dual. For example, when generating the dual for shell.mps, ROSE reports
    # an answer correct to only 6 digits. When generating the dual file with CPLEX,
    # ROSE reports all correct digits. Perhaps this has to do with the objective
    # offset value.

    assert sense in ['MAX', 'MIN'], "Wrong sense supplied."

    if len(dat['RANGES']):
        raise ValueError("Haven't implemented ranges!")

    num_cols = len(dat['ALL_COLUMNS'])
    for l in dat['COLUMNS'].values():
        assert len(l) == num_cols, "Ensure you've used fill=True"

    dat_cp = copy.deepcopy(dat)
    dat_cp['ALL_COLUMNS'] = set(dat_cp['ALL_COLUMNS'])
    obj = dat_cp['OBJ_ROW']

    dual = {}
    obj_lb = 'DL'
    dual['OBJSENSE'] = sense
    dual['NAME'] = dat['NAME'] + '_DUAL'
    dual['ROWS'] = {}
    dual['COLUMNS'] = {}
    dual['RHS'] = {}
    dual['BOUNDS'] = {}

    # shifting variables will generate an offset in the RHS of the obj row
    # we need to add a placeholder for it
    if not obj in dat_cp['RHS']:
        dat_cp['RHS'][obj] = 0

    # convert all 'L' row constraints into 'G' and multiply row by -1
    for rl, sense in dat_cp['ROWS'].items():
        if sense == 'L':
            dat_cp['ROWS'][rl] = 'G'
            dat_cp['COLUMNS'][rl] = {k: (-1*v)
                                     for k, v in dat_cp['COLUMNS'][rl].items()}
            dat_cp['RHS'][rl] = -1 * dat_cp['RHS'][rl]

    for cl, v in dat_cp['BOUNDS'].items():
        ub, lb = v.get('upper', None), v.get('lower', None)

        # x >= 0
        if lb == 0 and (ub == None or ub == np.Inf):
            dual['ROWS'][cl] = 'L'
        # x <= 0
        elif (lb == None or lb == np.NINF) and ub == 0:
            dual['ROWS'][cl] = 'L'
            for rl in dat['ROWS'].keys():
                dat_cp['COLUMNS'][rl][cl] = -1 * dat_cp['COLUMNS'][rl][cl]
        # x is free
        elif lb == np.NINF and ub == np.Inf:
            dual['ROWS'][cl] = 'E'
        else:
            # non standard constraints (e.g. x <= 4) are shifted
            # NOTE: this will create an objective row "offset"

            # a <= x <= a -> x = a
            if ub == lb:
                dat_cp = shift_var(dat_cp, cl, lb, 'FX')
            else:
                # a <= x <= +INF (LO)
                if lb and np.isfinite(lb) and ub == np.Inf:
                    dual['ROWS'][cl] = 'L'
                    dat_cp = shift_var(dat_cp, cl, lb, 'LO')
                # -INF <= x <= a (UP)
                elif ub and np.isfinite(ub) and lb == np.NINF:
                    # this converts variable into a lower bound, so we set
                    # it's dual row into an 'L'
                    dual['ROWS'][cl] = 'L'
                    dat_cp = shift_var(dat_cp, cl, ub, 'UP')
                # a <= x <= b (LO & UP)
                elif np.isfinite(ub) and np.isfinite(lb):
                    label = cl + '_db'

                    # add new row constraint for the LO bound
                    dat_cp['RHS'][label] = lb
                    dat_cp['ROWS'][label] = 'G'
                    dat_cp['COLUMNS'][label] = {
                        c: (0 if c != cl else 1) for c in dat_cp['ALL_COLUMNS']}

                    # shift
                    dual['ROWS'][cl] = 'L'

                    dat_cp = shift_var(dat_cp, cl, ub, 'UP')
                else:
                    raise ValueError('issue')

    # dual RHS
    dual['RHS'] = dat_cp['COLUMNS'][obj]

    # move obj offset to RHS
    offset = dat_cp['RHS'].pop(obj, None)
    if offset:
        dual['RHS'][obj_lb] = offset

    # transpose A
    A = pd.DataFrame.from_dict(dat_cp['COLUMNS'], orient='index')
    A.drop([obj], inplace=True)  # remove obj row
    dual['COLUMNS'] = A.transpose().to_dict(orient='index')

    # dual objective
    dual['COLUMNS'][obj_lb] = dat_cp['RHS']
    dual['ROWS'][obj_lb] = 'N'
    dual['OBJNAME'] = obj_lb

    # dual bounds
    for rl, sense in dat_cp['ROWS'].items():
        if sense == 'L':
            dual['BOUNDS'][rl] = {'upper': 0}
        elif sense == 'G':
            dual['BOUNDS'][rl] = {'lower': 0}
        elif sense == 'E':
            dual['BOUNDS'][rl] = {'lower': np.NINF, 'upper': np.Inf}

    return dual


def shift_var(dat, var, val, bound):
    '''
    Shift a variable `var` by a value `val`; this has the effect of changing
    the RHS values for each row constraint.

    For example, for the LO bound x >= 5, x would be shifted by 5:
        3x + y <= 10 --> 3x + y <= -5 (10-3*5)
    For example, for the UP bound x <= 5, x would be shifted by 5:
        3x + y <= 10 --> -3x + y <= -5 (10-3*5)
    For example, for the FX bound x = 5, RHS would be shifted by 5:
        3x + y <= 10 --> y <= -5 (10-3*5)

    Params:
    -------
    dat (dict) - output from parse_mps
    var (str) - variable label, must exist in each dat['COLUMNS'][row label]
    val (int) - bound value, row constraints get shifted by this times the
        row/col coefficient
    bound (str) - bound type, either UP or FX. UP will negate the column for
        the given var, FX will remove the column all together

    Return:
    -------
    updated dat with updated dat['RHS']
    '''
    for i, rl in enumerate(dat['ROWS'].keys()):
        coef = dat['COLUMNS'][rl][var]
        dat['RHS'][rl] = dat['RHS'][rl] - coef * val

        if bound == 'UP':
            dat['COLUMNS'][rl][var] = -1*coef
        elif bound == 'FX':
            del dat['COLUMNS'][rl][var]
            if var in dat['ALL_COLUMNS']:
                dat['ALL_COLUMNS'].remove(var)

    return dat


def parsed_as_mps(dat):
    '''
    Take a parsed MPS and reformat it as a single string formatted as
    valid MPS; that is, it can be written to file and used as a fixed
    MPS file.

    Params:
    -------
    dat (dict) - output of make_dual() or parse_mps()
    '''

    mps_str = f"NAME          {dat['NAME']}\n"

    if 'OBJSENSE' in dat:
        mps_str += "OBJSENSE\n"
        mps_str += f"  {dat['OBJSENSE']}\n"
        mps_str += "OBJNAME\n"
        mps_str += f"  {dat['OBJNAME']}\n"

    mps_str += "ROWS\n"
    for rl, sense in dat['ROWS'].items():
        mps_str += f" {sense}  {rl}\n"

    '''
    Apparently MPS wants all of the same COLUMNS specified one line after
    another; e.g. cannot do this:
    COLUMNS
        C01    R01   4
        C02    R01   5
        C01    R02   6
    We have to group all of the same column labels together.
    '''
    A = pd.DataFrame.from_dict(dat['COLUMNS'], orient='index')
    mps_str += "COLUMNS\n"
    for cl, v in A.to_dict().items():
        for rl, coef in v.items():
            sp1 = " " * 4
            sp2 = " " * (14 - len(sp1) - len(cl))
            sp3 = " " * (24 - len(sp1) - len(cl) - len(sp2) - len(rl))
            mps_str += f"{sp1}{cl}{sp2}{rl}{sp3}{str(coef)}\n"

    mps_str += "RHS\n"
    for rl, v in dat['RHS'].items():
        sp1 = " " * 4
        label = 'RHS'
        sp2 = " " * (14 - len(sp1) - len(label))
        sp3 = " " * (24 - len(sp1) - len(label) - len(sp2) - len(rl))
        mps_str += f"{sp1}{label}{sp2}{rl}{sp3}{str(v)}\n"

    mps_str += "BOUNDS\n"
    for rl, v in dat['BOUNDS'].items():
        lb, ub = v.get('lower', None), v.get('upper', None)
        bound_val = None
        vector = 'BOUND'

        if lb == np.NINF and ub == np.Inf:
            label = 'FR'
        elif lb == ub and not lb is None:
            label = 'FX'
            bound_val = lb
        elif not lb is None:
            label = 'LO'
            bound_val = lb
        elif not ub is None:
            label = 'UP'
            bound_val = ub

        sp1 = " " * 4
        sp2 = " " * (14 - len(sp1) - len(label))
        sp3 = " " * (24 - len(sp1) - len(label) - len(sp2) - len(vector))

        if label != 'FR':
            sp4 = " " * (39 - len(sp1) - len(label) -
                         len(sp2) - len(vector) - len(sp3) - len(rl))
            mps_str += f"{sp1}{label}{sp2}{vector}{sp3}{rl}{sp4}{str(bound_val)}\n"
        else:
            mps_str += f"{sp1}{label}{sp2}{vector}{sp3}{rl}\n"

    mps_str += "ENDATA\n"

    return mps_str


def make_numeric(n):
    '''
    Convert string into a float.

    NOTE: this automatically handles the cases:
    - 1D-3 -> 1e-3
    - 1e -> 1e0

    Params:
    -------
    n (str) - string to convert to a flaot

    Yields:
    -------
    float representation of input
    '''

    n = n.lower()

    # handle FORTRAN formats with 'D'
    if 'd' in n:
        n = n.replace('d', 'e')

    # add missing exponent
    if 'e' in n and n[-1] == 'e':
        n += '0'

    return float(n)


def summarize(data):
    '''
    Print out a summary of the parsed MPS.
    '''

    # count of each row constraint type
    group_rows = Counter(list(data['ROWS'].values()))

    print(f"Number of columns: {len(data['COLUMNS'])}")
    print(f"Number of rows: {len(data['ROWS'])}")
    print('\n'.join([f'  - {k}: {str(v)}' for k, v in group_rows.items()]))

    print(f"Number of ranges: {len(data['RANGES'])}")
    print(f"Number of bounds: {len(data['BOUNDS'])}")
    print(f"Number of RHS: {len(data['RHS'])}")
    for k, v in COUNTS.items():
        print(f"Number of {k} bounds: {v}")


def conform_objective(parsed_data):
    '''
    Assert that an objective function was provided.

    Params:
    -------
    parsed_data (dict) - current state of all parsed data, must have 'ROWS' key
    '''

    assert 'N' in parsed_data['ROWS'].values(
    ), f"No objective function was specified!"


def conform_cols(parsed_data, fill):
    '''
    Check all row references in the COLUMNS data records to ensure that all references exist in
    the ROWS records.

    Params:
    -------
    parsed_data (dict) - current state of all parsed data, must have 'ROWS' & 'COLUMNS' keys
    fill (bool) - if True, fill unspecified COLUMNS/ROWS with 0

    Yield:
    ------
    parsed_data, with filled zereos in the COLUMNS section if `fill` specified.
    '''

    all_rows = set(parsed_data['ROWS'])
    referenced_rows = set(parsed_data['COLUMNS'].keys())

    # assert all referenced rows exist in ROWS
    bad_rows = referenced_rows - all_rows
    assert not len(
        bad_rows), f"COLUMNS makes reference to non-existant ROW(s) {bad_rows}!"

    # fill missing coeff with 0 if needed
    if fill:
        for r in all_rows:

            if not parsed_data['COLUMNS'].get(r, None):
                parsed_data['COLUMNS'][r] = {}

            for c in parsed_data['ALL_COLUMNS']:
                if not parsed_data['COLUMNS'][r].get(c, None):
                    parsed_data['COLUMNS'][r][c] = 0

    # in order to output to JSON
    parsed_data['ALL_COLUMNS'] = sorted(list(parsed_data['ALL_COLUMNS']))

    return parsed_data


def conform_rhs(parsed_data, verbose, fill):
    '''
    Conform RHS by specifying missing values so that each ROW has a value; if not specified,
    assume it to be 0.

    Params:
    -------
    parsed_data (dict) - current state of all parsed data, must have 'BOUNDS' & 'COLUMNS' keys
    verbose (bool) - if True, print out statement about unspecified bound.
    fill (bool) - if True, fill unspecified bound with RHS = 0

    Yield:
    ------
    updated parsed_data['RHS'] section where every variable in 'COLUMNS' has a value.
    '''

    for row_id, row_type in parsed_data['ROWS'].items():
        if row_type != 'N':
            if not row_id in parsed_data['RHS']:
                if verbose:
                    if fill:
                        print(
                            f"ROW {row_id} has no RHS value; setting it to 0.")
                    else:
                        print(f"ROW {row_id} has no RHS value.")

                if fill:
                    parsed_data['RHS'][row_id] = 0

    return parsed_data


def conform_bounds(parsed_data, verbose, fill):
    '''
    Conform bounds by specifying missing upper/lower bounds so that each bound has both an upper
    and lower bound.

    If no bounds are specified, assume a lower bound of 0 (zero) and an upper bound of +Inf.
    If only a single bound is specified, the unspecified bound remains at 0 or +∞, whichever
    applies, with one exception. If an upper bound of less than 0 is specified and no other
    bound is specified, the lower bound is automatically set to -Inf.

    Set the lower bound to -Inf only if the upper bound is less than 0. A warning message is
    issued when this exception is encountered.

    Finally, check that all columns referenced in bounds exist in the COLUMNS records.

    Upper |  Lower   | Result
    -----------------------
    > 0   |   None   | lower= 0
    <= 0  |   None   | lower=-Inf
    None  | >0 or <0 | upper=+Inf
    None  |   None   | upper=+Inf, lower=0

    Params:
    -------
    parsed_data (dict) - current state of all parsed data, must have 'BOUNDS' & 'COLUMNS' keys
    verbose (bool) - if True, print out statement about unspecified bound.
    fill (bool) - if True, fill unspecified bound with 0 < var < +inf

    Yield:
    ------
    updated parsed_data['BOUNDS'] section where every variable in 'COLUMNS' has an upper and
    lower bound.
    '''

    # for the unspecified bounds, set them all to 0 < col < +inf
    all_cols = parsed_data['ALL_COLUMNS']
    all_bounds = parsed_data['BOUNDS'].keys()
    for c in all_cols:

        # if bound not specified on column
        if not c in parsed_data['BOUNDS']:

            if verbose:
                if fill:
                    print(
                        f"BOUND unspecified for '{c}'; setting it to 0 <= {c} <= +inf")
                else:
                    print(f"BOUND unspecified for '{c}'")

            if fill:
                parsed_data['BOUNDS'][c] = {
                    'upper': np.Inf,
                    'lower': 0
                }
        else:

            ub = parsed_data['BOUNDS'][c].get('upper', None)
            lb = parsed_data['BOUNDS'][c].get('lower', None)

            if fill:
                # missing lower bound
                if lb == None and ub != None:

                    if ub > 0:
                        parsed_data['BOUNDS'][c]['lower'] = 0
                        if verbose:
                            print(
                                f"Lower bound unspecified for {c}, setting it to 0")
                    elif ub <= 0:
                        parsed_data['BOUNDS'][c]['lower'] = np.NINF
                        if verbose:
                            print(
                                f"Lower bound unspecified for {c}, setting it to -Inf")
                # missing upper bound
                elif ub == None and lb != None:
                    parsed_data['BOUNDS'][c]['upper'] = np.Inf
                    if verbose:
                        print(
                            f"Upper bound unspecified for {c}, setting it to +Inf.")
                elif ub == None and lb == None:
                    # should never happend
                    raise ValueError(
                        f"BOUNDS issue {parsed_data['BOUNDS'][c]}")

            # ensure lower bound below upper bound
            if ub != None and lb != None and lb > ub:
                err = "Lower bound is greater than upper bound: "
                err += f"lower -> {lb}, upper -> {ub}"
                raise ValueError(err)

    # assert we have a column for all specified bounds
    bad_bounds = all_bounds - all_cols
    assert not len(
        bad_bounds), f"BOUNDS specified for which no COLUMNS exist: {bad_bounds}"

    return parsed_data


def parse_wrap_cols(data, indicator):
    '''
    Parse a generic data record which may potentially wrap to the next line. Note that sometimes
    a data indicator like RHS will have something in field2, sometimes it'll be blank.

    NOTE: this should only be used on indicator records COLUMNS, RHS and RANGE

    Example:
    --------
    for the line: RHS1      LIM1                 5   LIM2                10
    parsed as: RHS1, [[LIM1, 5], [LIM2, 10]]

    for the line: RHS1      LIM1                 5
    parsed as: RHS1, [[LIM1, 5]]

    for the line:           LIM1                 5   LIM2                10
    parsed as: None, [[LIM1, 5], [LIM2, 10]]

    for the line:           LIM1                 5
    parsed as: None, [[LIM1, 5]]

    Params:
    -------
    data (list) - split line for data indicator
    indicator (str) - inidicator name

    Yield:
    ------
    (tuple)
    - field2 id (may be None if not provided)
    - list of tuples [[field3, field4], [field5, field6]]  [field5, field6] is optional.
    '''

    assert indicator in ALLOWED_INDICATORS, f"Indicator '{indicator}' not valid."

    assert 2 <= len(
        data) <= 5, f"{indicator} data record must only contain 2, 3, 4 or 5 fields, found: {data}"

    if len(data) in [2, 4]:
        id = None

        assert indicator != 'COLUMNS', "field 2 is required in the COLUMNS indicator"

        row_data = [data[0:2]]
        if len(data) == 4:
            row_data.append(data[2:4])

    else:
        id = data[0]

        row_data = [data[1:3]]
        if len(data) == 5:
            row_data.append(data[3:5])

    return id, row_data


def add_range(data, parsed_data, verbose):
    '''
    Parse RANGE data inidicator line. Assert that only 3 or 5 fields are available and that the
    RHS value is a float. If more than one RANGE inditifier is provided, it will be skipped; only
    keep the first one.

    Function assumes that parsed_data['RHS'] & parsed_data['ROWS'] already exists.

    The RANGES section is for constraints of the form:  h <= constraint <= u .
    The range of the constraint is  r = u - h .  The value of r is specified
    in the RANGES section, and the value of u or h is specified in the RHS
    section.  If b is the value entered in the RHS section, and r is the
    value entered in the RANGES section, then u and h are thus defined:

        row type       sign of r       h          u
        ----------------------------------------------
           G            + or -         b        b + |r|
           L            + or -       b - |r|      b
           E              +            b        b + |r|
           E              -          b - |r|      b
    '''
    range_id, range_data = parse_wrap_cols(data, 'RANGES')

    assert len(parsed_data['RHS']), 'You must provided RHS before RANGES.'
    assert len(parsed_data['ROWS']), 'You must provided ROWS before RANGES.'

    if not 'RANGES_id' in parsed_data or range_id == parsed_data.get('RANGES_id', None):
        parsed_data['RANGES_id'] = range_id
    else:
        if verbose:
            print(
                f'More than one RANGE vector specified, skipping {range_id}.')
        return parsed_data

    for row_id, r in range_data:

        assert not row_id in parsed_data['RANGES'], f"RANGE for ROW {row_id} specified twice!"

        r = make_numeric(r)

        b = parsed_data['RHS'].get(row_id, None)
        assert b != None, f"You must specify a RHS for {row_id} if setting a RANGE on it."

        # get row_type, will be one of L, G, E
        row_type = parsed_data['ROWS'].get(row_id, None)
        assert row_type, f"You must specify a ROW for {row_id} if setting a RANGE on it."

        if row_type == 'G':
            h = b
            u = b + abs(r)
        elif row_type == 'L':
            h = b - abs(r)
            u = b
        elif row_type == 'E':
            if r > 0:
                h = b
                u = b + abs(r)
            else:
                h = b - abs(r)
                u = b

        assert h < u, f'RANGES invalid, {h} must be less than {u}.'

        parsed_data['RANGES'][row_id] = {
            'upper': u,
            'lower': h
        }

    return parsed_data


def add_bound(data, parsed_data, verbose):
    '''
    Parse BOUND data inidicator line. Assert that only 3 or 4 fields are
    available and that the bound types are one of allowed. If more than one
    BOUND is provided, it will be skipped; only keep the first one.

    NOTE: if bound value not provided for types UP, LO or FX it is assumed to be 0

    UP bound will set upper bound to bound_val
    LO bound will set lower bound to bound_val
    FX bound will set upper & lower bound to bound_val
    FR bound will set lower bound to -INF and upper to INF
    MI bound will set lower bound to -INF
    PL bound will set upper bound to INF


    Params:
    -------
    data (list) - split line for data indicator, will be either len 4 or 3
      len 4: [bound_type, bound_id, col_id, bound_val]
      len 3: [bound_type, col_id, bound_val] OR [bound_type, bound_id, col_id]
    parsed_data (dict) - current state of all parsed data, must have 'BOUNDS' key
    verbose (bool) - if True, print out statement about ignored bound vector.

    Yield:
    ------
    updated parsed_data['BOUNDS'] section in form of OrderedDict():
      "BOUNDS": {
        "B0100210": {
          "upper": 1550.0,
          "lower": 0.0
        },
        "B0100260": {
          "upper": np.Inf
        },
    '''

    global COUNTS

    assert len(data) in [
        3, 4], f"Supplied BOUND row must only have 3 or 4 fields, found: {data}"

    # when only 3 fields available, the bound_id OR bound_val is ommited
    # e.g. capri.mps has a "FR BNDS1     RVAD72" (note no bound_val)
    # e.g. dfl0001.mps has a "UP           C03609             14." (note no bound_id)
    # other examples like this: gfrd-pnc, greenbeb, modszk1, perold, pilot4
    # pilot_ja, pilot_we, sierra, stair, tuff, vtp_base
    if len(data) == 3:
        if data[0] == 'FR':
            bound_type, bound_id, col_id, bound_val = data[0], data[1], data[
                2], None
        else:
            try:
                make_numeric(data[-1])
            except:
                # bound_value was omitted, set it to 0 if bound type UP, LO, or FX
                bound_val = None
                if data[0] in ['UP', 'LO', 'FX']:
                    bound_val = 0
                bound_type, bound_id, col_id, bound_val = data[0], data[1], data[2], bound_val
            else:
                # bound_id was (maybe) omitted

                # ensure we don't have a case like [FR 12 14] where it's ambiguous which
                # is the bound_id and which is the bound_val
                # if we are in an unambiguous case, this try should fail
                try:
                    make_numeric(data[1])
                except:
                    bound_type, bound_id, col_id, bound_val = data[0], '', data[1], data[2]
                else:
                    raise ValueError(f"The BOUND {data} is ambiguous.")

    else:
        bound_type, bound_id, col_id, bound_val = data

    if bound_val:
        bound_val = make_numeric(bound_val)

    assert bound_type in ALLOWED_BOUNDS, f"Supplied BOUND type is not accepted, found: {ALLOWED_BOUNDS}"

    if col_id in parsed_data['BOUNDS']:
        if (
            ('upper' in parsed_data['BOUNDS'][col_id] and bound_type == 'UP') or
            ('lower' in parsed_data['BOUNDS'][col_id] and bound_type == 'LO') or
            (bound_type in ['FX', 'MI', 'PL', 'FR'])
        ):
            raise ValueError(f"BOUND on COLUMN {col_id} specified twice!")

    if not 'BOUNDS_id' in parsed_data or bound_id == parsed_data['BOUNDS_id']:
        parsed_data['BOUNDS_id'] = bound_id
    else:
        if verbose:
            print(
                f'More than one BOUND vector specified, skipping {bound_id}.')
        return parsed_data

    if bound_type == 'UP':
        COUNTS['UP'] += 1
        parsed_data['BOUNDS'][col_id]['upper'] = bound_val
    elif bound_type == 'LO':
        COUNTS['LO'] += 1
        parsed_data['BOUNDS'][col_id]['lower'] = bound_val
    elif bound_type == 'FX':
        COUNTS['FX'] += 1
        parsed_data['BOUNDS'][col_id]['upper'] = bound_val
        parsed_data['BOUNDS'][col_id]['lower'] = bound_val
    elif bound_type == 'FR':
        COUNTS['FR'] += 1
        if verbose and bound_val != None:
            print(f"BOUNDS value of {bound_val} on {col_id} was ignored")
        parsed_data['BOUNDS'][col_id]['upper'] = np.Inf
        parsed_data['BOUNDS'][col_id]['lower'] = np.NINF
    elif bound_type == 'MI':
        COUNTS['MI'] += 1
        if verbose and bound_val != None:
            print(f"BOUNDS value of {bound_val} on {col_id} was ignored")
        parsed_data['BOUNDS'][col_id]['lower'] = np.NINF
        # upper bound cannot be assumed to be 0
    elif bound_type == 'PL':
        COUNTS['PL'] += 1
        if verbose and bound_val != None:
            print(f"BOUNDS value of {bound_val} on {col_id} was ignored")
        parsed_data['BOUNDS'][col_id]['upper'] = np.Inf
        parsed_data['BOUNDS'][col_id]['lower'] = 0

    return parsed_data


def add_rhs(data, parsed_data, verbose):
    '''
    Parse RHS data inidicator line. Assert that:
      - only 3 or 5 fields are available
      - RHS value is a float.

    If more than one RHS inditifier is provided, it will be skipped; only keep the
    first one.

    Params:
    -------
    data (list) - split line for data indicator
    parsed_data (dict) - current state of all parsed data, must have 'RHS' key
    verbose (bool) - if True, print out statement about ignored RHS vector.

    Yield:
    ------
    updated parsed_data['RHS'] section in form of OrderedDict(): {row_id: row_val, ...} as well
    as a parsed_data['RHS_id'] which is used to match the RANGES
    '''

    rhs_id, row_data = parse_wrap_cols(data, 'RHS')

    # only keep first RHS vector
    if not 'RHS_id' in parsed_data or rhs_id == parsed_data['RHS_id']:
        parsed_data['RHS_id'] = rhs_id
    else:
        if verbose:
            print(
                f'More than one RHS vector specified, skipping RHS {rhs_id}.')
        return parsed_data

    # add data to parsed_data
    for row_id, row_val in row_data:

        try:
            row_val = make_numeric(row_val)
        except:
            raise ValueError(f"RHS value must be a float, found: {row_val}")

        assert not row_id in parsed_data['RHS'], f'RHS for {row_id} specified twice!'
        parsed_data['RHS'][row_id] = row_val

    return parsed_data


def add_col(data, parsed_data):
    '''
    Parse a COLUMN data indicator line. Will assert that:
      - only 3 or 5 fields are available
      - the row value is a float
      - only 1 value for row_id and col_id

    Params:
    -------
    data (list) - split line for data indicator
    parsed_data (dict) - current state of all parsed data, must have 'COLUMNS' key

    Yield:
    ------
    updated parsed_data['COLUMNS'] section in form of Dict():
        {col_id: [{row_id, row_val}], ...}
    '''

    col_id, row_data = parse_wrap_cols(data, 'COLUMNS')

    # add data to parsed_data
    for row_id, row_val in row_data:

        try:
            row_val = make_numeric(row_val)
        except:
            raise ValueError(f"ROW value must be a float, found: {row_val}")

        if not row_id in parsed_data['COLUMNS']:
            parsed_data['COLUMNS'][row_id] = {}

        assert not col_id in parsed_data['COLUMNS'][row_id], (
            f"COLUMN {col_id} specified twice in ROW {row_id}!"
        )

        parsed_data['COLUMNS'][row_id][col_id] = row_val
        parsed_data['ALL_COLUMNS'].add(col_id)

    return parsed_data


def add_row(data, parsed_data, verbose):
    '''
    Parse a ROW data indicator line. Asserts that only two fields are available and that
    the row names are unique. If more than one free row ('N') is specified, only the first
    is stored.

    Params:
    -------
    data (list) - split line for data indicator
    parsed_data (dict) - current state of all parsed data, must have 'ROWS' key
    verbose (bool) - if True, print out statement about ignored objective rows.

    Yeild:
    ------
    updated parsed_data['ROWS'] section in form of OrderedDict():
        {row_name: sense}
    also adds a parsed_data['OBJ_ROW'] section which contains the name of the objective row
    '''

    assert len(
        data) == 2, f"ROW data record must only contain two fields, found: {data}."

    sense, row_name = data

    assert sense in ALLOWED_ROW_SENSE, f'ROW sense indidcator must be one of {ALLOWED_ROW_SENSE}'
    assert not row_name in parsed_data['ROWS'], f"ROW name {row_name} is duplicated!"

    # If more than one free row (N) is specified, the first one is used as the objective
    # function and the others are discarded.
    if sense == 'N' and 'N' in parsed_data['ROWS'].values():
        if verbose:
            print(f'Free row already specified, skipping data: {data}')
    else:
        assert not row_name in parsed_data['ROWS'], f"ROW {row_name} already specified"
        parsed_data['ROWS'][row_name] = sense

        if sense == 'N':
            parsed_data['OBJ_ROW'] = row_name

    return parsed_data


def parse_line(l, current_indicator):
    '''
    Parse a given line of an fixed-format MPS file into its components. A
    line will be either a delimiter for the indicator record (e.g. RHS)
    or will be a data record.

    Params:
    -------
    l (str) - a given line in the MPS file
    current_indicator (str) - the current indicator record currently being
        parsed; will be one of ALLOWED_INDICATORS

    Yields:
    -------
    tuple (indicator, data)
      - indicator will either be the same as `current_indicator` or will be
        updated to the indicator found in the line `l`; either way it will
        be one of ALLOWED_INDICATORS
      - data will either be the NAME of the MPS if on `l` is the NAME
        indicator, will be a list of the data records if on a data record
        line, or will be None

    NOTE:
      - comment lines beginning with '*' are skipped
    '''

    data, parts = None, None

    # comment or blank line
    if l[0] == '*' or l.strip() == '':
        return None, None

    # if on a indicator record (e.g. COLUMNS), update it
    if l[0] != ' ':
        parts = l.strip().split()
        indicator = parts[0]

        # if on NAME indicator, grab the name
        if parts[0] == 'NAME':
            data = parts[1]

    # if on a data record
    else:
        parts = l.split()
        indicator = current_indicator
        data = parts

    # ensure indicator is allowed
    if indicator != 'ENDATA' and not indicator in ALLOWED_INDICATORS:
        raise ValueError(f"Unknown indicator {indicator} found.")

    return indicator, data
