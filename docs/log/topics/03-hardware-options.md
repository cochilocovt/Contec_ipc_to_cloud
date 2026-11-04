# Hardware options

Prices are as seen online in India or Europe on the date given. They move a lot; get a GST quote for client work. More detail in [../../hardware.md](../../hardware.md).

## What "factory approved" means (2026-10-31)

There's no single certificate. Plant engineers look for: 24 V DC power and DIN-rail mounting, fanless, eMMC rather than SD storage, wide temperature range, industrial EMC compliance (IEC 61000-6-2/6-4), and a vendor committed to long availability and OS updates.

## Alternatives to a Raspberry Pi (2026-10-31)

| Device | Role | Notes |
|---|---|---|
| Seeed reComputer R1000 | Pi-based gateway | CM4, dual Ethernet, RS-485, DIN rail, -30 to 70 °C. About ₹32,000 (R1024). Same code as a Pi |
| Revolution Pi Connect 5 | Pi-based gateway + I/O | CM5, 24 V, IEC 61000-6-2/6-4. About €740 |
| Siemens SIMATIC IOT2050 | Gateway | Easiest sell to a Siemens plant. Basic about €364; rated 0–50 °C |
| Moxa UC-1200A | Gateway | Debian 11 supported to 2031. About €575 |
| Teltonika TRB145 / TRB140 | 4G gateway, configured not coded | Modbus-to-MQTT built in, own 4G link. ₹14,999 / ₹16,099. 128 MB RAM |
| Arduino Opta | Micro PLC | For a machine with no PLC. Opta Lite about ₹17,249 |

Suggested picks: reComputer R1000 for the cheapest path with a PLC; IOT2050 for a Siemens plant or strict IT; Teltonika if the plant network is off-limits; Opta plus a gateway if there's no PLC.

## Raspberry Pi for a POC (2026-10-31)

**Raspberry Pi 5, 2 GB.** Enough for the gateway, Docker and a local broker; 4 GB only to run InfluxDB/Grafana on the Pi. Has an RTC and PCIe, and the same chip as the CM5 used in industrial Pi gateways. In production until at least January 2036.

Robu.in prices (Oct 2026): 1 GB ₹5,399, 2 GB ₹9,059, 4 GB ₹13,409, 8 GB ₹19,999; official 2 GB starter kit ₹12,399. Raspberry Pi raised prices several times in 2026 because of memory costs, including on 2026-10-01 for 2 GB models.

Extras: USB-to-RS-485 adapter for Modbus RTU; a relay module with an LED or 12 V fan to demo start/stop (no mains). Buy from approved resellers (Robocraze, Robu.in, Silverline Electronics). Never drive motors from bare Pi GPIO.

Not bought yet; the BX-220 is being used instead.

## Spare RAM stick (2026-10-31)

Samsung 8 GB DDR4-3200 SO-DIMM (M471A1K43DB1-CWE). Fits no Raspberry Pi (memory is soldered) and not the BX-220 (DDR3L). Usable in a DDR4 mini PC or thin client such as a Dell Wyse 5070 or HP t630, or sell it while RAM prices are high.

## Keyence KV-8000 (2026-11-04)

Available at home; the final machine uses a different PLC. Decision: develop against the simulator on a spare laptop, and give the KV-8000 one session.
- Talks Keyence Host Link (upper link) on port 8501; the MIT-licensed `kv-hostlink` Python library uses it (tested on KV-7500/KV-X500, not KV-8000).
- Whether its built-in port can be a Modbus TCP server is unconfirmed; one guide shows it with the KV-XLE02 unit. Check in KV STUDIO.
- Needs KV STUDIO and 24 V DC; no I/O wiring needed to test registers.
- Worth doing: a second protocol (keeps the gateway pluggable), real network behaviour, and practising the Local/Remote, command-bit and heartbeat ladder logic the final PLC will need.

## IPC storage: CFast (2026-11-04)

The BX-220 boots from a 32 GB CFast card and has a second CFast slot.

Options:
1. **Clone to a larger industrial card (recommended):** 64 GB is enough. Image the original on the PC, restore to the new card (Macrium Reflect can enlarge C:), boot from it, run updates there, and keep the original as an untouched backup. That also proves the backup works. Check Contec's tested-card list; CFast 2.0 cards normally work in older slots at lower speed.
2. **Second card as D:** for logs, buffer and backups. Doesn't help Windows Update, which needs space on C:.
3. **Free space:** Disk Cleanup with system files, `compact /compactos:always` (about 2 GB), and after updates `Dism /Online /Cleanup-Image /StartComponentCleanup`.

### Why CFast is expensive

Each card is an SSD with a SATA controller; very few are made (cinema cameras and industrial PCs only); industrial cards use longer-lasting flash with power-loss protection, wide temperature ratings and fixed parts; and in India there are few sellers plus import duty.

Ways to spend less: buy only 64 GB; choose industrial 3D TLC or MLC rather than SLC (a gateway writes little); for the home lab only, a consumer CFast 2.0 camera card; surplus industrial cards after checking health in CrystalDiskInfo; or free space and skip buying for now. For the client, put an industrial card in the quote.
