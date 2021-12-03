NAME          EXAMPLE
ROWS
 L  R01
 G  R02
 E  R03
 N  COST
COLUMNS
    C01       R01                  1   R02                  4
    C01       R03                  7  COST                 10
    C02       R01                  2   R02                  5
    C02       R03                  8  COST                 11
    C03       R01                  3   R02                  6
    C03       R03                  9  COST                 12
RHS
    B         R01                 13   R02                 14
    B         R03                 15
BOUNDS
    LO        BOUND             C01    1
    UP        BOUND             C01    5
    UP        BOUND             C02    0
    FR        BOUND             C03
ENDATA
