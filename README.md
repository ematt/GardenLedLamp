# GardenLedLamp

WS2812 led strip controller based on [STM32L432KC](https://www.st.com/en/microcontrollers-microprocessors/stm32l432kc.html)

## How to compile

Import the project in STM32CubeIDE.

## Schematic
```

                                                      .-------.
                                     +3V3             |       |
                                       +         .----|--USB--|----. VCC(+12V)
    .---.    .---------------------.   |         |    '-------'    |  +
    |A  |o--o|A     XY-017     +3V3|o--o         |                 |  |
    |   |    |                     |o-----Tx----o|D1(PA9)       VIN|o-o
    |B  |o--o|B   RS485<->TTL      |o-----Rx----o|D0(PA10)      GND|
    '---'    '---------------------'             |NRST         NRST|
     RS485                                       |GND           +5V|
     CON                                         |D2(PA12)  (PA2)A7|
                                              ++ |D3(PB0)   (PA7)A6|
            VCC  VCC          +3V3    ADDRESS |  |D4(PB7)   (PA6)A5|
             +    +             +     PINS    |  |D5(PB6)   (PA3)A4|
    .----.   |    |  .-------.  |             ++ |D6(PB1)   (PA4)A3|         __    +5V  .---.
    |+12V|o--o    o-o|IN     |  |                |D7(PC14)  (PA3)A2|   GND-o|  |o-------o+5V|
    |    |           |   +3V3|o-o                |D8(PC15)  (PA1)A1o-------o|  |        |  ||
    |GND |o--o       '-------'                   |D9(PA8)   (PA0)A0|   GND-o|  |o-------oDI||
    '----'   |                                   |D10(PA11)    AREF|         --         '---'
     POWER  ===  VCC           +5V               |D11(PB5)     +3V3|       74LV1T125    LED STRIP
     CON    GND   +             +                |D12(PB4) (PB3)D13|                    ws2812
                  |  .-------.  |                |                 |
                  o-o|IN     |  |                |                 |
                     |    +5V|o-o                | NUCLEO-32       |
                     '-------'                   | STM32L432       |
                  Step-Down Voltage Regulator    '-----------------'
                       Regulator

```