# Questions for the client

To send before building. Grouped so they can go to the right person. Answers go back into the other files in this folder.

## The test

1. What does one test run look like: how many strokes, how fast, how long?
2. Is output measured by weighing what each stroke dispenses? If not, how?
3. Which pumps and liquids will be tested? Nominal output per stroke and the tolerance for each.
4. What should a run report: mean, CV %, Cpk, pass/fail? Is there a pass/fail rule today?
5. How many priming strokes are normal, and should they be left out of the results?
6. Which runs should be compared: samples from one batch, batches over time, different settings?

## The servo

7. Make and model of the servo and drive, and how it connects to the PLC (EtherCAT, MECHATROLINK, pulse).
8. What does the servo do on the rig? What exactly should be adjustable remotely: stroke length, speed, dwell, something else? Limits and units for each.
9. Should settings change only between runs, or also during a run?
10. Is homing needed after power-up, and should that ever be done remotely?

## The load cell

11. Load cell capacity and model; the amplifier or weighing indicator; how it connects to the PLC.
12. What does "load cell adjustment" mean here: tare/zero, calibration with a known weight, filter or settling settings, or moving the load cell or cup?
13. Collection cup: capacity and how it is emptied. Should the rig stop when it is full?
14. Has the weighing been checked for repeatability with a reference weight?

## The PLC and panel

15. Is the KV-X310 ladder program written yet, and who maintains it? Can we get the KV STUDIO project?
16. Is the KV-X310's OPC UA server enabled? Which expansion units are fitted?
17. Is there a Local/Remote selector, or can one be added? Is there a local HMI or touch screen?
18. What should happen if the cloud link drops during a run that was started remotely?
19. Should a remote Stop work even when the panel is in LOCAL?
20. Guards, doors, E-stop: what is on the rig today?

## People and access

21. Who should see the dashboard, who may start and stop runs, who may change settings?
22. Where will the rig sit, and what network does it have: plant LAN with outbound internet, a proxy, or none (bring a 4G router)?
23. Any company rules on cloud hosting or where the data is stored?
24. How long should test data be kept?
