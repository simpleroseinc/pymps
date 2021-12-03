* comment ignored!
NAME          EXAMPLE
ROWS
 L  R01
 E  R02
 G  R03
 E  R04
 N  COST
 N  COST2
COLUMNS
    C01       R01                30e   R02                5d3
    C01       R03                0.2
    C01       COST                10
    C02       R01                -10   R02                  0
    C02       R03                0.1   R04                0.2
    C02       COST                 5
    C03       R01                 50   R02                 -3
    C03       R03                  0   R04                0.3
    C03       COST               5.5
RHS
    B         R01               1500   R02               200
    B         R03                 12   R04                 0
    B2        R03                 12   R04                 9
BOUNDS
    MI        BOUND             C01    2
    PL        BOUND             C03    0
RANGES
    rhs       R01                14
    rhs       R02                14
    rhs       R03                14
    rhs       R04               -14
ENDATA
