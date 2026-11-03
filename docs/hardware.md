# Hardware

## Contec BX-220D-DC781724 (the gateway)

| | |
|---|---|
| CPU | Intel Atom E3845, 1.91 GHz, 4 cores |
| Memory | 4 GB ECC (DDR3L platform) |
| Storage | 32 GB CFast card; two CFast slots |
| OS | Windows 10 IoT Enterprise 2016 LTSB, 64-bit (version 1607) |
| Ports | DVI-I, DisplayPort, 2× Gigabit LAN, 1× USB 3.0, 2× USB 2.0, 2× RS-232C |
| Power | 10.8–31.2 V DC |
| Build | Fanless, slitless; CFast retaining clamp |
| RAS | Contec utility: restarts on program hang, boot failure or overheating; keeps a fault log |

Plenty for collecting and forwarding data. Not enough to host the database or dashboards on the box. CFast flash has limited write endurance, so avoid heavy logging to disk.

### Operating system support

Windows 10 IoT Enterprise 2016 LTSB reached end of support on 13 October 2026; that was the last monthly security update. Extended Security Updates for this edition are sold only through device makers, so ask Contec (or its India distributor). Microsoft's upgrade paths are Windows 10 IoT Enterprise LTSC 2021 or Windows 11 IoT Enterprise LTSC 2024 if the hardware qualifies.

Decision: keep Windows for now (see decisions.md). Keep the box behind a deny-all inbound firewall and settle ESUs or a migration date before enabling remote control.

## Alternatives considered

Prices are what Indian resellers and distributors listed around October 2026 and move a lot. Get a GST quote from an authorised distributor for client work.

| Device | Role | Notes |
|---|---|---|
| Seeed reComputer R1000 | Pi-based gateway | Raspberry Pi CM4, dual Ethernet, isolated RS-485, DIN rail, -30 to 70 °C. About ₹32,000 (R1024). Same code as a Pi |
| Revolution Pi Connect 5 | Pi-based gateway + I/O | CM5, 24 V, IEC 61000-6-2/6-4. About €740 in Europe |
| Siemens SIMATIC IOT2050 | Gateway | Easiest sell to a Siemens plant. Basic about €364; Basic rated 0–50 °C |
| Moxa UC-1200A | Gateway | Debian 11 with support to 2031. About €575 |
| Teltonika TRB145 / TRB140 | Configure-only 4G gateway | Modbus-to-MQTT built in, own 4G link (no plant IT network). ₹14,999 / ₹16,099. Only 128 MB RAM |
| Arduino Opta | Micro PLC | For a machine with no PLC: runs interlocks in ladder. Opta Lite about ₹17,249 |

## Raspberry Pi for a proof of concept

Recommended: Raspberry Pi 5, 2 GB. Enough for the gateway, Docker and a local Mosquitto; get 4 GB only to run InfluxDB and Grafana on the Pi. Pi 5 has an RTC and PCIe, and its chip is the one in the CM5 used by industrial Pi gateways, so POC code carries over. In production until at least January 2036.

Robu.in listings (October 2026; check at checkout because of repeated memory-driven price rises): 1 GB ₹5,399 · 2 GB ₹9,059 · 4 GB ₹13,409 · 8 GB ₹19,999. Official 2 GB starter kit ₹12,399 (27 W supply, 32 GB card, case with fan).

POC extras: USB-to-RS-485 adapter if the PLC uses Modbus RTU; a relay module with an LED or 12 V fan to demo start/stop (no mains). Buy from approved resellers: Robocraze, Robu.in, Silverline Electronics.

Do not drive motors from a bare Pi's GPIO. For Pi-based control use an industrial variant (Revolution Pi) with a contactor, overload relay and hardwired E-stop.

## Spare RAM on hand

Samsung 8 GB DDR4-3200 SO-DIMM (M471A1K43DB1-CWE). Fits no Raspberry Pi (memory is soldered) and not the BX-220 (DDR3L). Usable in an x86 mini PC or thin client with a DDR4 SO-DIMM slot, such as a Dell Wyse 5070 or HP t630, as an alternative gateway.
