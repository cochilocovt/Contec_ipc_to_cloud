# Reaching the cloud from a real shop floor (2026-11-04)

Usually the edge device does publish to the cloud, but rarely as directly as in the home lab. Three common patterns:

1. **Gateway → plant firewall → cloud.** Most common for one machine or a small plant. Outbound MQTT over TLS (8883). Plant IT must allow the broker's hostname and port. Many plants allow only 443, sometimes through a proxy with a login; MQTT over WebSockets on 443 works around that. Bigger plants keep machines on a separate network or a DMZ, with only the firewall deciding what leaves.
2. **Gateway → own 4G router → cloud.** Common for machine builders and service companies. Never touches the plant's IT network, so approval is fast. Costs a SIM, data, and needs signal near the machine (for example a Teltonika TRB140).
3. **Gateway → on-site server → cloud.** For bigger plants: each gateway publishes to an on-site broker or historian (Ignition, Kepware, Mosquitto), which forwards to the cloud over one connection. Local dashboards survive internet outages.

## What it means for this project

- The gateway only connects outward, so all three work by changing `mqtt.host`, port and TLS in `gateway.yaml`. Pattern 3 is a few lines of Mosquitto bridge config.
- Remote control is where plants push back. Many accept data leaving but not commands coming in, even outbound-initiated ones. That's why control is behind a switch and plant sign-off is a hold point.
- Real outages last hours. The in-memory buffer holds 10,000 readings, about 2.8 hours at one per second. For longer, add a small disk buffer, minding CFast wear.

## Questions for the client's IT team

1. Can we connect out to a cloud hostname on 8883, or only 443?
2. Is there a proxy?
3. Would you rather we bring our own 4G router?
4. Is Tailscale (or another remote-access tool) allowed, or must we use your VPN?
