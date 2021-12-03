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
              R01               1500   R02               200
              R03                 12
BOUNDS
    UP        BOUND             C01    2
    FR        BOUND             C03
    UP        BOUND             C02    0
ENDATA
