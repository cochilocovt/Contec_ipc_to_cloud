export type DeviceId = "pc" | "laptop" | "ipc" | "kv";

export interface Device {
  id: DeviceId;
  name: string;
  short: string;
  role: string;
  runs: string[];
  ports: string;
  plant: string;
  ipKey?: "PC_IP" | "LAPTOP_IP" | "IPC_IP";
}

export const DEVICES: Device[] = [
  {
    id: "pc",
    name: "This PC",
    short: "This PC",
    role: "Stands in for the cloud",
    runs: [
      "Docker stack in cloud/: Mosquitto broker, TimescaleDB, ingest service, Grafana",
      "The ipc_connection repo, and send_command.py for test commands",
      "Your browser, for the Grafana dashboard",
    ],
    ports: "Listens on 1883 (MQTT) and 3000 (Grafana). Database on 5432, this PC only.",
    plant: "Becomes a cloud VM or a managed IoT service, with TLS and per-device certificates.",
    ipKey: "PC_IP",
  },
  {
    id: "laptop",
    name: "Spare laptop",
    short: "Laptop",
    role: "Stands in for the machine's PLC",
    runs: [
      "tools/sim_plc.py through run-sim.bat: a simulated PLC with the same register map as the example config",
      "It obeys the Local/Remote mode and stops the motor if the gateway heartbeat goes quiet, like a real PLC should",
    ],
    ports: "Listens on 5020 (Modbus TCP).",
    plant: "Replaced by the real PLC on the final machine. Make and model still to be confirmed.",
    ipKey: "LAPTOP_IP",
  },
  {
    id: "ipc",
    name: "Contec BX-220",
    short: "IPC",
    role: "The edge gateway, at home and at the plant",
    runs: [
      "The Python gateway in gateway/, later as a Windows service under NSSM",
      "Windows 10 IoT Enterprise 2016 LTSB, kept as it came",
    ],
    ports: "Listens on nothing. Connects out to the PLC (Modbus) and the broker (MQTT). RDP from your LAN only, for admin.",
    plant: "Same box. One LAN port faces the PLC, the other faces the internet, and nothing routes between them.",
    ipKey: "IPC_IP",
  },
  {
    id: "kv",
    name: "Keyence KV-8000",
    short: "KV-8000",
    role: "A real PLC for one later test session",
    runs: [
      "A small practice ladder program: Local/Remote bit, start/stop command bits, heartbeat watchdog",
      "Programmed from this PC with KV STUDIO",
    ],
    ports: "Keyence Host Link on 8501. Modbus TCP support on the built-in port is unconfirmed.",
    plant: "Not used. The final machine has a different PLC, so this is practice and a second protocol to support.",
  },
];

export interface Task {
  id: string;
  title: string;
  devices: DeviceId[];
  why: string;
  steps?: string[];
  code?: string;
  done?: string;
  hold?: boolean;
}

export interface Phase {
  id: string;
  title: string;
  intro: string;
  later?: boolean;
  tasks: Task[];
}

export const PHASES: Phase[] = [
  {
    id: "net",
    title: "Get the network straight",
    intro: "Every config file points at an IP address. Fix them first so nothing breaks when a machine reboots.",
    tasks: [
      {
        id: "net-ips",
        title: "Write down each machine's IP address",
        devices: ["pc", "laptop", "ipc"],
        why: "The gateway needs the laptop's address to read the PLC and this PC's address to reach the broker.",
        steps: [
          "On each machine open Command Prompt and run ipconfig.",
          "Use the IPv4 Address under the adapter that's connected (Ethernet or Wi-Fi).",
          "Type them into the device cards at the top of this page. Every command below then fills them in for you.",
        ],
        code: "ipconfig",
        done: "All three addresses are entered above.",
      },
      {
        id: "net-reserve",
        title: "Reserve those addresses on your router",
        devices: ["pc", "laptop", "ipc"],
        why: "Home routers hand out addresses that can change after a reboot. If one changes, the gateway silently loses the PLC or the broker.",
        steps: [
          "Run ipconfig /all on each machine and note its Physical Address (MAC).",
          "In your router's admin page, find DHCP or LAN settings, then Address Reservation.",
          "Bind each MAC to the IP address it has now.",
        ],
        code: "ipconfig /all",
        done: "After a restart, each machine still has the same address.",
      },
      {
        id: "net-private",
        title: "Set the home network to Private on every Windows machine",
        devices: ["pc", "laptop", "ipc"],
        why: "The firewall rules later in this list apply only to Private networks. On a Public network the gateway can't get through.",
        steps: [
          "Windows 10/11: Settings → Network & Internet → your connection → Network profile → Private.",
          "On the IPC (Windows 10 version 1607): Settings → Network & Internet → Ethernet → click the network → turn on \"Make this PC discoverable\".",
        ],
        code: "Get-NetConnectionProfile   # NetworkCategory should say Private",
        done: "Get-NetConnectionProfile shows Private on all three.",
      },
    ],
  },
  {
    id: "record",
    title: "IPC: record how it came",
    intro: "Read-only checks. Nothing here changes the IPC, so do it before anything else touches the box.",
    tasks: [
      {
        id: "rec-uwf",
        title: "Check whether the Unified Write Filter is on",
        devices: ["ipc"],
        why: "If it's on, every change is thrown away at reboot. That includes the Windows updates you're installing, which would quietly undo themselves.",
        steps: [
          "Open Command Prompt as administrator.",
          "If it says the filter is ON, pause updates and tell Claude before continuing. It gets turned off for setup and back on at the end.",
        ],
        code: "uwfmgr get-config",
        done: "You know whether UWF is ON or OFF, and it's written down.",
      },
      {
        id: "rec-system",
        title: "Save system details to a USB stick",
        devices: ["ipc"],
        why: "A record of the original setup, so you can always tell what you changed.",
        steps: ["Replace E: with your USB stick's drive letter."],
        code: "mkdir E:\\ipc\nwinver\nsysteminfo > E:\\ipc\\systeminfo.txt\nipconfig /all > E:\\ipc\\ipconfig.txt",
        done: "winver shows version 1607, and both text files are on the stick.",
      },
      {
        id: "rec-startup",
        title: "Note what starts automatically and what's installed",
        devices: ["ipc"],
        why: "Shows what else the box was doing, and whether Contec's RAS utility is already there.",
        steps: [
          "Task Manager → Startup tab.",
          "services.msc: note any service not made by Microsoft.",
          "Programs and Features: look for anything from Contec.",
        ],
        done: "A short list on the USB stick.",
      },
      {
        id: "rec-ports",
        title: "Note the COM ports, network adapters and accounts",
        devices: ["ipc"],
        why: "The final PLC may connect over RS-232, so you need to know which port is COM1 and COM2. Adapter names matter for the two-network setup at the plant.",
        steps: [
          "Device Manager → Ports (COM & LPT), and Network adapters.",
          "Run net user and note whether the box logs in by itself.",
        ],
        code: "net user",
        done: "COM port numbers, both adapter names and the account list are written down.",
      },
    ],
  },
  {
    id: "backup",
    title: "Back up the CFast card",
    intro: "The IPC's whole disk is one CFast card. An image of it means any mistake is a 15-minute restore.",
    tasks: [
      {
        id: "bk-image",
        title: "Image the CFast card on this PC",
        devices: ["ipc", "pc"],
        why: "Your undo button for everything that follows.",
        steps: [
          "Shut the IPC down and take the CFast card out.",
          "Put it in a USB CFast reader on this PC. A CompactFlash reader won't fit; it must be CFast.",
          "Use Win32 Disk Imager (Read) or Macrium Reflect to save a full image.",
          "If you've already run Windows Update, the image captures the updated state. That's fine; note it.",
        ],
        code: "certutil -hashfile bx220-original.img SHA256",
        done: "An image file and its SHA-256 checksum, saved together.",
      },
      {
        id: "bk-verify",
        title: "Prove the backup works",
        devices: ["ipc", "pc"],
        why: "A backup you haven't restored is a guess.",
        steps: ["Write the image to a spare CFast card, put that in the IPC and boot it."],
        done: "The IPC boots normally from the copy.",
      },
      {
        id: "bk-copies",
        title: "Keep two copies on different drives",
        devices: ["pc"],
        why: "One copy on the same disk as everything else isn't a backup.",
        done: "Image and checksum exist in two places.",
      },
      {
        id: "bk-hold",
        title: "Backup verified before changing anything else",
        devices: ["ipc"],
        hold: true,
        why: "From here on you change the IPC. Label the original card and keep it aside.",
        done: "Original card labelled and stored. You're working on a copy or a verified original.",
      },
    ],
  },
  {
    id: "house",
    title: "IPC: Windows housekeeping",
    intro: "Makes the box reliable to run unattended and reachable from this PC, so you stop walking over to it.",
    tasks: [
      {
        id: "hk-update",
        title: "Install updates until none are left",
        devices: ["ipc"],
        why: "Support for this Windows edition ended on 13 October 2026. The last security update is still worth having.",
        steps: ["Windows Update → Check for updates → install → restart. Repeat until nothing new appears."],
        done: "\"Your device is up to date\" after a fresh check.",
      },
      {
        id: "hk-power",
        title: "Stop it sleeping or hibernating",
        devices: ["ipc"],
        why: "A gateway that sleeps stops sending data, and the dashboard shows it offline.",
        code: "powercfg /change standby-timeout-ac 0\npowercfg /change hibernate-timeout-ac 0\npowercfg /h off",
        done: "Power Options shows \"Never\" for sleep.",
      },
      {
        id: "hk-time",
        title: "Turn on internet time sync",
        devices: ["ipc"],
        why: "Readings are stored with the gateway's own timestamp. A clock that's minutes off puts data in the wrong place on the charts.",
        steps: ["Settings → Time & language → Set time automatically: On. Then force a sync."],
        code: "w32tm /resync",
        done: "The clock matches your phone to the second.",
      },
      {
        id: "hk-rdp",
        title: "Turn on Remote Desktop, for your network only",
        devices: ["ipc", "pc"],
        why: "So you can work on the IPC from this PC. Version 1607 is too old for the built-in SSH server, so RDP is the way in.",
        steps: [
          "On the IPC: System Properties → Remote → Allow remote connections to this computer.",
          "Then, in an admin PowerShell on the IPC, limit RDP to your local network.",
          "From this PC: connect with the second command.",
        ],
        code: "Set-NetFirewallRule -DisplayGroup \"Remote Desktop\" -RemoteAddress LocalSubnet\n\n# on this PC\nmstsc /v:{IPC_IP}",
        done: "You can log in to the IPC from this PC.",
      },
      {
        id: "hk-firewall",
        title: "Lock down the firewall and turn off SMBv1",
        devices: ["ipc"],
        why: "An unpatched Windows box on your network should accept as little as possible. SMBv1 is the old file-sharing protocol behind several well-known worms.",
        code: "Set-NetFirewallProfile -All -DefaultInboundAction Block\nDisable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol",
        done: "Both commands succeed (the second may ask for a restart).",
      },
      {
        id: "hk-ras",
        title: "Install Contec's RAS utility",
        devices: ["ipc"],
        why: "It restarts the box if a program hangs, Windows fails to boot or it overheats, and keeps a fault log. It's Windows-only, so keeping Windows gets you this.",
        steps: ["Download it for the BX-220 from Contec's support site. We'll wire its heartbeat to the gateway later."],
        done: "Installed and opens without errors.",
      },
      {
        id: "hk-esu",
        title: "Ask Contec about Extended Security Updates",
        devices: ["pc"],
        why: "For this Windows edition, extended patches are sold only through the device maker. You need an answer before remote control goes live at the plant.",
        steps: ["Email Contec or their India distributor with the model number BX-220D-DC781724."],
        done: "Price and availability known, or a decision to plan a move off this OS.",
      },
    ],
  },
  {
    id: "cloud",
    title: "This PC: start the cloud stack",
    intro: "Four containers that play the cloud: they receive data, store it and draw the dashboard.",
    tasks: [
      {
        id: "cl-docker",
        title: "Install Docker Desktop",
        devices: ["pc"],
        why: "The whole cloud side runs as containers, so one command starts or stops all of it.",
        steps: ["Install from docker.com with the WSL 2 backend, restart, and start Docker Desktop."],
        code: "docker version",
        done: "docker version shows both a Client and a Server section.",
      },
      {
        id: "cl-env",
        title: "Set the three passwords",
        devices: ["pc"],
        why: "The database, Grafana's read-only database login and the Grafana admin account each need one. They live in .env, which git ignores.",
        code: "cd C:\\Users\\V.T\\Documents\\ipc_connection\\cloud\ncopy .env.example .env\nnotepad .env",
        done: ".env has your own passwords, not change-me.",
      },
      {
        id: "cl-up",
        title: "Start the stack",
        devices: ["pc"],
        why: "The first start builds the ingest service and creates the database tables.",
        code: "docker compose up -d --build\ndocker compose ps",
        done: "Four services are Up, and timescaledb says (healthy).",
      },
      {
        id: "cl-grafana",
        title: "Open the dashboard",
        devices: ["pc"],
        why: "Confirms Grafana is talking to the database before any data arrives.",
        steps: ["Go to http://localhost:3000 and log in as admin with GRAFANA_ADMIN_PASSWORD. Open Machine overview."],
        done: "The dashboard loads. Empty panels and \"No data\" are expected until the gateway runs.",
      },
      {
        id: "cl-fw",
        title: "Let the IPC reach the broker",
        devices: ["pc"],
        why: "Windows Firewall blocks incoming connections by default, including the gateway's MQTT connection.",
        code: "New-NetFirewallRule -DisplayName \"MQTT 1883 (home lab)\" -Direction Inbound -Protocol TCP -LocalPort 1883 -Profile Private -Action Allow",
        done: "The rule appears in Windows Defender Firewall → Inbound Rules.",
      },
      {
        id: "cl-python",
        title: "Install Python here for test commands",
        devices: ["pc"],
        why: "send_command.py plays the part of the web app's Start and Stop buttons for now.",
        code: "cd C:\\Users\\V.T\\Documents\\ipc_connection\npy -m pip install -r gateway\\requirements.txt",
        done: "The install finishes without errors.",
      },
    ],
  },
  {
    id: "sim",
    title: "Spare laptop: run the simulated PLC",
    intro: "The laptop pretends to be a PLC with a motor, so you can build everything without the real machine.",
    tasks: [
      {
        id: "sim-python",
        title: "Install Python 3.10 or newer",
        devices: ["laptop"],
        why: "The simulator is a Python script.",
        steps: ["From python.org. Tick \"Add python.exe to PATH\" in the installer."],
        code: "py --version",
        done: "py --version prints 3.10 or higher.",
      },
      {
        id: "sim-copy",
        title: "Copy the ipc_connection folder over",
        devices: ["laptop", "pc"],
        why: "The simulator and its register map come from the repo.",
        steps: ["USB stick or a shared folder. Skip the cloud folder if you like; the laptop doesn't need it."],
        done: "The folder is on the laptop with tools\\run-sim.bat inside.",
      },
      {
        id: "sim-sleep",
        title: "Stop the laptop sleeping while plugged in",
        devices: ["laptop"],
        why: "If the PLC goes to sleep, the gateway loses it and the readings stop.",
        code: "powercfg /change standby-timeout-ac 0",
        done: "Sleep is set to Never when plugged in.",
      },
      {
        id: "sim-fw",
        title: "Let the IPC reach the simulator",
        devices: ["laptop"],
        why: "Same reason as the broker: Windows Firewall blocks the gateway's Modbus connection otherwise.",
        code: "New-NetFirewallRule -DisplayName \"Simulated PLC 5020\" -Direction Inbound -Protocol TCP -LocalPort 5020 -Profile Private -Action Allow",
        done: "The rule appears under Inbound Rules.",
      },
      {
        id: "sim-run",
        title: "Start the simulated PLC",
        devices: ["laptop"],
        why: "The first run creates a virtual environment and installs what it needs.",
        code: "cd ipc_connection\ntools\\run-sim.bat",
        done: "The window says \"simulated PLC on 0.0.0.0:5020, mode REMOTE\". Leave it open.",
      },
    ],
  },
  {
    id: "gw",
    title: "IPC: run the gateway",
    intro: "This is where the three machines join up. When this phase is done, the dashboard on this PC goes live.",
    tasks: [
      {
        id: "gw-python",
        title: "Install Python 3.12 (64-bit)",
        devices: ["ipc"],
        why: "The gateway runs on Python. 3.12 is a safe choice for this older Windows build.",
        steps: ["From python.org, the 64-bit Windows installer. Tick \"Add python.exe to PATH\". If the installer refuses to run on version 1607, tell Claude."],
        code: "py --version",
        done: "py --version prints 3.12.",
      },
      {
        id: "gw-copy",
        title: "Copy the folder to C:\\ipc_connection",
        devices: ["ipc", "pc"],
        why: "A short path with no user name in it keeps the later service setup simple.",
        done: "C:\\ipc_connection\\gateway exists on the IPC.",
      },
      {
        id: "gw-venv",
        title: "Install the gateway's dependencies",
        devices: ["ipc"],
        why: "A virtual environment keeps the gateway's exact versions separate from anything else on the box.",
        code: "cd C:\\ipc_connection\\gateway\npy -m venv .venv\n.venv\\Scripts\\pip install -r requirements.txt",
        done: "pip finishes with \"Successfully installed\".",
      },
      {
        id: "gw-config",
        title: "Point the gateway at the laptop and this PC",
        devices: ["ipc"],
        why: "The example config points at the IPC itself. Change only these two hosts; everything else already matches the simulator.",
        code: "copy config\\gateway.example.yaml config\\gateway.yaml\nnotepad config\\gateway.yaml\n\n# change these lines:\nplc:\n  host: {LAPTOP_IP}\n  port: 5020\nmqtt:\n  host: {PC_IP}\n  port: 1883",
        done: "gateway.yaml saved with both addresses.",
      },
      {
        id: "gw-test",
        title: "Test both network paths",
        devices: ["ipc"],
        why: "If either test fails, the fix is a firewall rule or an IP address, not the gateway code.",
        code: "Test-NetConnection {LAPTOP_IP} -Port 5020\nTest-NetConnection {PC_IP} -Port 1883",
        done: "Both say TcpTestSucceeded : True.",
      },
      {
        id: "gw-run",
        title: "Start the gateway and watch the dashboard",
        devices: ["ipc", "pc"],
        why: "The moment the whole read path works end to end.",
        code: ".venv\\Scripts\\python -m ipc_gateway --config config\\gateway.yaml",
        done: "The IPC log says \"MQTT connected\". On this PC, Grafana shows Gateway: Online, Last reading under 5 s, and the charts start drawing.",
      },
    ],
  },
  {
    id: "write",
    title: "Try the write path",
    intro: "Sending start and stop through the whole chain, and proving that the wrong commands get refused.",
    tasks: [
      {
        id: "wr-enable",
        title: "Turn on control and the heartbeat",
        devices: ["ipc"],
        why: "Both are off by default so nothing can be written by accident.",
        steps: ["In gateway.yaml set the two lines below, save, then stop the gateway with Ctrl+C and start it again."],
        code: "control:\n  enabled: true\n  heartbeat:\n    enabled: true",
        done: "The startup log says \"control ENABLED\".",
      },
      {
        id: "wr-start",
        title: "Start and stop the motor from this PC",
        devices: ["pc"],
        why: "send_command.py does what the web app's buttons will do: publish a command with an id and a 10-second expiry.",
        code: "cd C:\\Users\\V.T\\Documents\\ipc_connection\npython tools\\send_command.py motor_start --host localhost --by vaibhav\npython tools\\send_command.py motor_stop --host localhost --by vaibhav",
        done: "Each prints accepted then executed. The Motor tile changes, and both commands appear under Recent commands.",
      },
      {
        id: "wr-expired",
        title: "Send a command that's already expired",
        devices: ["pc"],
        why: "A start that arrives late after a network hiccup must never run.",
        code: "python tools\\send_command.py motor_start --host localhost --ttl -5",
        done: "The ack says expired, and the motor doesn't move.",
      },
      {
        id: "wr-unknown",
        title: "Send a command that isn't on the allowlist",
        devices: ["pc"],
        why: "The cloud can only ask for named commands. Anything else is refused at the gateway.",
        code: "python tools\\send_command.py write_anything --host localhost",
        done: "The ack says rejected, \"command not allowed\".",
      },
      {
        id: "wr-local",
        title: "Put the machine in LOCAL mode and try to start it",
        devices: ["laptop", "pc"],
        why: "At the plant, the operator's Local/Remote switch must always win over the cloud.",
        steps: ["On the laptop press Ctrl+C, then restart the simulator in LOCAL mode. Send a start from this PC. Afterwards restart the simulator normally."],
        code: "tools\\run-sim.bat --mode local\n\n# on this PC\npython tools\\send_command.py motor_start --host localhost",
        done: "The ack says rejected, \"machine in LOCAL mode\". The Mode tile shows Local.",
      },
      {
        id: "wr-cable",
        title: "Pull the IPC's network cable while the motor runs",
        devices: ["ipc", "laptop", "pc"],
        why: "Tests what happens when the link drops mid-run: the PLC, not the cloud, makes the safe decision.",
        steps: ["Start the motor, unplug the IPC's cable for about a minute, then plug it back in."],
        done: "The simulator stops the motor within 6 s and logs fault 9. Grafana shows the gateway Offline after about 45 s, then Fault 9 once it reconnects.",
      },
      {
        id: "wr-broker",
        title: "Stop the broker for a minute",
        devices: ["pc"],
        why: "The gateway should hold readings in memory and send them all when the broker comes back.",
        code: "cd C:\\Users\\V.T\\Documents\\ipc_connection\\cloud\ndocker compose stop mosquitto\n# wait a minute\ndocker compose start mosquitto",
        done: "No gap in the charts for that minute.",
      },
    ],
  },
  {
    id: "perm",
    title: "IPC: make it permanent",
    intro: "From a script you start by hand to a service that survives power cuts.",
    tasks: [
      {
        id: "pm-nssm",
        title: "Install the gateway as a Windows service",
        devices: ["ipc"],
        why: "It then starts at boot without anyone logging in, and restarts if it ever exits.",
        steps: ["Download NSSM from nssm.cc and put nssm.exe somewhere on PATH. Run these in an admin prompt."],
        code: "nssm install ipc-gateway C:\\ipc_connection\\gateway\\.venv\\Scripts\\python.exe \"-m ipc_gateway --config config\\gateway.yaml --log-file logs\\gateway.log\"\nnssm set ipc-gateway AppDirectory C:\\ipc_connection\\gateway\nnssm set ipc-gateway Start SERVICE_AUTO_START\nnssm set ipc-gateway AppExit Default Restart\nnssm start ipc-gateway",
        done: "services.msc shows ipc-gateway Running, and the dashboard stays Online.",
      },
      {
        id: "pm-reboot",
        title: "Pull the power and plug it back in",
        devices: ["ipc"],
        why: "At the plant, power cuts happen. The gateway has to come back on its own.",
        steps: ["If it doesn't power on by itself, set the BIOS power-loss option to Power On."],
        done: "The dashboard goes Offline, then Online again without you touching the IPC.",
      },
      {
        id: "pm-uwf",
        title: "Turn the write filter back on, if it was on",
        devices: ["ipc"],
        why: "Protects the CFast card, but the gateway's config and logs must be excluded or they vanish at every reboot.",
        code: "uwfmgr file add-exclusion C:\\ipc_connection\\gateway\\config\nuwfmgr file add-exclusion C:\\ipc_connection\\gateway\\logs\nuwfmgr volume protect C:\nuwfmgr filter enable",
        done: "After a reboot, the gateway still starts and its log keeps growing.",
      },
      {
        id: "pm-golden",
        title: "Image the finished card",
        devices: ["ipc", "pc"],
        why: "A known-good image of the working setup. A dead card becomes a 15-minute swap.",
        done: "A second image, named so you can tell it from the original.",
      },
    ],
  },
  {
    id: "kv",
    title: "KV-8000 session",
    intro: "One session with a real PLC, after the simulator setup works. Don't sink more time than that into it: the final machine uses a different PLC.",
    later: true,
    tasks: [
      {
        id: "kv-power",
        title: "Power it and put it on the network",
        devices: ["kv"],
        why: "The CPU needs 24 V DC. No I/O has to be wired; internal registers are enough for testing.",
        done: "The CPU's power and run LEDs are on and it's connected to your switch or router.",
      },
      {
        id: "kv-studio",
        title: "Install KV STUDIO and set the PLC's IP address",
        devices: ["pc", "kv"],
        why: "Keyence's programming software is the only way to configure it.",
        steps: [
          "Set the IP in the Unit Editor and download it to the PLC.",
          "While you're there, check whether the built-in Ethernet settings offer a Modbus TCP server. That decides whether the gateway can use it unchanged.",
        ],
        done: "You can ping the PLC from this PC, and you know whether Modbus TCP is available.",
      },
      {
        id: "kv-read",
        title: "Read a few DM registers from the IPC",
        devices: ["ipc", "kv"],
        why: "Proves the network path and gives Claude what it needs to add a Keyence (Host Link, port 8501) option to the gateway.",
        steps: ["Write known values into DM0–DM9 from KV STUDIO, then bring the addresses and values to Claude."],
        done: "Known values written, ready to read back from the IPC.",
      },
      {
        id: "kv-ladder",
        title: "Write the practice ladder program",
        devices: ["kv", "pc"],
        why: "The final machine's PLC programmer will need exactly this. Building it once gives you a spec to hand over and a demo for the client.",
        steps: [
          "A Local/Remote bit that blocks remote commands when Local.",
          "Start and stop command bits that act on a rising edge.",
          "A heartbeat register the PLC watches: if it stops changing for 6 s, stop the motor and set a fault.",
        ],
        done: "All three behave like the simulator does.",
      },
    ],
  },
];

export const BRING_BACK = [
  "Whether the Unified Write Filter was on.",
  "Any step that failed, with the exact error text or a screenshot.",
  "Whether Python 3.12 installed on the IPC without complaint.",
  "For the KV-8000: whether Modbus TCP is available, plus the DM addresses and values you wrote.",
  "Anything you learn about the final machine's PLC: make, model, and Ethernet or RS-232.",
];
