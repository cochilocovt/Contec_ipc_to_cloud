# Project log

What was asked, discussed and decided while setting up this project, organised so it can be read back later without the original chat.

| File | What's in it |
|---|---|
| [timeline.md](timeline.md) | Every working session in date order: the question, the answer in short, and what changed in the repo |
| [open-items.md](open-items.md) | Where things stand now, what's next, and questions still waiting on someone |
| [topics/01-ipc-and-os.md](topics/01-ipc-and-os.md) | Can the BX-220 do this job; its Windows version and support status; why it stays on Windows |
| [topics/02-remote-control.md](topics/02-remote-control.md) | Adding start/stop: safety rules, command flow, and how a dashboard button should work |
| [topics/03-hardware-options.md](topics/03-hardware-options.md) | Raspberry Pi for a POC, industrial alternatives, the spare RAM stick, the KV-8000, CFast storage and cost |
| [topics/04-plant-connectivity.md](topics/04-plant-connectivity.md) | How an edge device reaches the cloud on a real shop floor, and what to ask plant IT |
| [topics/05-cloud-hosting.md](topics/05-cloud-hosting.md) | The Docker home-lab stack versus Supabase and Vercel, including free-plan limits |
| [topics/06-remote-access.md](topics/06-remote-access.md) | Tailscale and Remote Desktop to the IPC: every error so far and its fix |
| [topics/07-pump-test-rig.md](topics/07-pump-test-rig.md) | The client machine: a pump test rig on a Keyence KV-X310, and what was checked about it |

Formal decisions live in [../decisions.md](../decisions.md); the log explains how we got to them.

## Keeping it up to date

After each working session, add an entry to the bottom of `timeline.md` and update `open-items.md`. When a topic gets new information, update its topic file rather than repeating it in the timeline. Prices and support dates are written with the date they were checked, because they change.
