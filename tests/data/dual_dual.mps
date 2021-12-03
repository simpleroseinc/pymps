NAME          EXAMPLE_DUAL
OBJSENSE
  MAX
OBJNAME
  DL
ROWS
 L  C01
 L  C02
 E  C03
 N  DL
COLUMNS
    R01       C01       -1.0
    R01       C02       2.0
    R01       C03       -3.0
    R01       DL        -13.0
    R02       C01       4.0
    R02       C02       -5.0
    R02       C03       6.0
    R02       DL        14.0
    R03       C01       7.0
    R03       C02       -8.0
    R03       C03       9.0
    R03       DL        15.0
RHS
    RHS       C01       10.0
    RHS       C02       -11.0
    RHS       C03       12.0
BOUNDS
    LO        BOUND     R01            0
    LO        BOUND     R02            0
    FR        BOUND     R03
ENDATA
