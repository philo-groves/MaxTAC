# QEMU Virtualization

Use QEMU for reproducible Linux virtual machines, especially on Linux hosts with
KVM acceleration. For DAST work, treat QEMU as a precise VM launcher and device
model, not as a full lab manager. Make the command line, disk chain, network
mode, and management sockets explicit enough that another agent can reproduce
the same guest boundary.

Do not treat QEMU TCG emulation as a security isolation boundary. QEMU's own
security guidance distinguishes accelerated virtualization from non-virtualized
emulation. For hostile or untrusted guests, use KVM/HVF/WHPX with a supported
machine type, run QEMU unprivileged, and keep management interfaces local.

## Contents

- [Quick Commands](#quick-commands)
- [Host and Accelerator Probes](#host-and-accelerator-probes)
- [Isolation Boundaries](#isolation-boundaries)
- [Machine, CPU, Firmware, and Identity](#machine-cpu-firmware-and-identity)
- [Base Images and Cloud Images](#base-images-and-cloud-images)
- [Disk Images and Overlay Strategy](#disk-images-and-overlay-strategy)
- [Snapshot and Commit Discipline](#snapshot-and-commit-discipline)
- [Block Devices and I/O Options](#block-devices-and-io-options)
- [Running VMs](#running-vms)
- [Headless, Serial, Display, and VNC](#headless-serial-display-and-vnc)
- [Networking Modes](#networking-modes)
- [User Networking and Passt](#user-networking-and-passt)
- [Tap, Bridge, and Isolated NAT](#tap-bridge-and-isolated-nat)
- [Guest Execution](#guest-execution)
- [File Transfer and Shared Directories](#file-transfer-and-shared-directories)
- [QMP and HMP](#qmp-and-hmp)
- [QEMU Guest Agent](#qemu-guest-agent)
- [Secrets, Sandboxing, and Privileges](#secrets-sandboxing-and-privileges)
- [TPM, UEFI, and Secure Boot](#tpm-uefi-and-secure-boot)
- [Nested KVM](#nested-kvm)
- [Kernel and Device Debugging](#kernel-and-device-debugging)
- [DAST Repro Patterns](#dast-repro-patterns)
- [Evidence Capture](#evidence-capture)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Host sanity:

```bash
uname -a
lscpu
qemu-system-x86_64 --version
qemu-system-x86_64 -accel help
qemu-system-x86_64 -machine help
qemu-system-x86_64 -cpu help
qemu-img --version
qemu-img info --help
ls -l /dev/kvm
grep -E 'vmx|svm' /proc/cpuinfo | head
```

Create a qcow2 base disk:

```bash
qemu-img create -f qcow2 -o compat=1.1,lazy_refcounts=on,preallocation=metadata \
  images/ubuntu-base.qcow2 80G
```

Install from ISO with KVM, virtio disk, user-mode NAT, and local SSH forwarding:

```bash
qemu-system-x86_64 \
  -name ubuntu-install,process=ubuntu-install \
  -machine q35,accel=kvm \
  -cpu host \
  -smp 4 \
  -m 8192 \
  -drive if=virtio,file=images/ubuntu-base.qcow2,format=qcow2,cache=none,discard=unmap \
  -cdrom iso/ubuntu-live-server-amd64.iso \
  -boot d \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22 \
  -display gtk
```

Create a disposable case overlay:

```bash
CASE="case-$(date +%Y%m%d-%H%M%S)"
mkdir -p "cases/$CASE/run" "cases/$CASE/evidence"
qemu-img create -f qcow2 -b "$(realpath images/ubuntu-base.qcow2)" -F qcow2 \
  "cases/$CASE/$CASE.qcow2"
```

Run a headless case VM with stable sockets:

```bash
qemu-system-x86_64 \
  -name "$CASE",process="$CASE" \
  -machine q35,accel=kvm \
  -cpu host \
  -smp 4 \
  -m 8192 \
  -drive if=virtio,file="cases/$CASE/$CASE.qcow2",format=qcow2,cache=none,discard=unmap \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22 \
  -display none \
  -serial mon:stdio \
  -qmp unix:"cases/$CASE/run/qmp.sock",server=on,wait=off \
  -pidfile "cases/$CASE/run/qemu.pid"
```

SSH into the guest through user networking:

```bash
ssh -p 2222 user@127.0.0.1
scp -P 2222 seed.tgz user@127.0.0.1:/tmp/seed.tgz
```

Inspect an image chain:

```bash
qemu-img info --backing-chain "cases/$CASE/$CASE.qcow2"
qemu-img check -f qcow2 "cases/$CASE/$CASE.qcow2"
```

Speak QMP over a local Unix socket:

```bash
printf '{"execute":"qmp_capabilities"}\n{"execute":"query-status"}\n' |
  socat - UNIX-CONNECT:"cases/$CASE/run/qmp.sock"
```

Throw away the case:

```bash
pkill -F "cases/$CASE/run/qemu.pid"
rm -rf "cases/$CASE"
```

## Host and Accelerator Probes

Start by proving whether the run is accelerated or emulated. This determines
performance, guest-visible CPU behavior, and whether QEMU's virtualization
security assumptions apply.

```bash
qemu-system-x86_64 --version
qemu-system-x86_64 -accel help
qemu-system-x86_64 -machine help
qemu-system-x86_64 -cpu help
ls -l /dev/kvm
groups
grep -E 'vmx|svm' /proc/cpuinfo | head
lsmod | grep '^kvm'
```

Linux/KVM checks:

```bash
test -r /dev/kvm && test -w /dev/kvm && echo "KVM usable"
cat /sys/module/kvm_intel/parameters/nested 2>/dev/null || true
cat /sys/module/kvm_amd/parameters/nested 2>/dev/null || true
dmesg | grep -i kvm | tail -50
```

Common accelerators:

- `kvm`: Linux hardware virtualization. Prefer this for Linux DAST labs.
- `hvf`: macOS Hypervisor.Framework. Useful on macOS, but device and CPU details
  differ from KVM.
- `whpx`: Windows Hypervisor Platform. Useful for Windows hosts, but less common
  in Linux DAST automation.
- `tcg`: QEMU Tiny Code Generator. Useful for cross-architecture testing and
  firmware work. Do not rely on it for guest isolation or realistic timing.

Use an explicit accelerator:

```bash
-machine q35,accel=kvm
```

or:

```bash
-accel kvm
```

Use fallback only when the test can tolerate the changed boundary:

```bash
-accel kvm -accel tcg
```

For evidence, record whether QEMU actually launched with KVM. If the guest logs
or QEMU stderr show a TCG fallback, call that out.

## Isolation Boundaries

QEMU exposes a large guest-facing attack surface: virtual devices, firmware,
network backends, display backends, block drivers, and optional host-device
passthrough. Keep the VM command line minimal for hostile guests.

Prefer:

```bash
-machine q35,accel=kvm
-cpu host
-device virtio-net-pci,...
-drive if=virtio,...
-display none
-serial mon:stdio
```

Avoid by default:

- Running QEMU as root.
- Passing through USB, PCI, host block devices, or host directories writeable.
- Exposing QMP/HMP on TCP.
- Binding VNC/SPICE to non-loopback interfaces.
- Using `-netdev tap` scripts from unreviewed locations.
- Mounting guest-owned filesystems directly on the host.
- Reusing a dirty overlay as a new base without inspection.

Run QEMU as an unprivileged user. If `/dev/kvm` or `/dev/net/tun` requires
privileges, fix group membership or pass file descriptors through a launcher
rather than running the whole emulator as root.

```bash
id
ls -l /dev/kvm /dev/net/tun
sudo usermod -aG kvm "$USER"
newgrp kvm
```

Use supported machine types for security-sensitive virtualization. For x86_64
Linux DAST, `q35` is usually the right default. `microvm` can reduce device
surface for highly constrained guests, but it changes hardware enough that it is
not a general desktop/server substitute.

## Machine, CPU, Firmware, and Identity

Pin the machine type when regression stability matters:

```bash
qemu-system-x86_64 -machine help | grep q35
```

Example:

```bash
-machine pc-q35-9.2,accel=kvm
```

Use unversioned `q35` when you deliberately want the host's current QEMU default.
Use a versioned machine type when evidence must survive host upgrades.

CPU choices:

```bash
-cpu host
-cpu max
-cpu qemu64
```

Use `-cpu host` for KVM performance and realistic host feature exposure. It is
not migration-friendly and can make results host-specific. Use a named CPU model
when comparing across hosts.

Set SMP explicitly:

```bash
-smp 4
-smp sockets=1,cores=4,threads=1
```

Set memory explicitly:

```bash
-m 8192
```

UEFI with per-VM mutable NVRAM:

```bash
mkdir -p "cases/$CASE/firmware"
cp /usr/share/OVMF/OVMF_VARS.fd "cases/$CASE/firmware/OVMF_VARS.fd"

qemu-system-x86_64 \
  -machine q35,accel=kvm \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \
  -drive if=pflash,format=raw,file="cases/$CASE/firmware/OVMF_VARS.fd" \
  ...
```

The OVMF vars file is mutable guest state. Keep it case-specific. Reusing one
vars file across clones can leak boot variables, enrollment state, Secure Boot
changes, and boot order changes between tests.

Set deterministic VM identity only when useful:

```bash
-uuid 11111111-2222-3333-4444-555555555555
-smbios type=1,manufacturer=MaxTAC,product=DAST-Lab,serial=case-001,uuid=11111111-2222-3333-4444-555555555555
```

Use unique identity for parallel or target-visible cases:

```bash
UUID="$(uuidgen)"
MAC="$(printf '52:54:00:%02x:%02x:%02x' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)))"
```

MAC prefix `52:54:00` is the common QEMU locally administered range. Record
guest identity if target behavior keys on hostname, MAC, machine-id, SMBIOS, or
license state.

## Base Images and Cloud Images

Prefer a boring, patched base image plus per-case overlays. Do not mutate the
base during tests.

Base lifecycle:

```bash
qemu-img create -f qcow2 images/ubuntu-base.qcow2 80G
# install OS, users, SSH, tools, CA certs, browser/proxy, then shut down cleanly
qemu-img info images/ubuntu-base.qcow2
qemu-img check images/ubuntu-base.qcow2
chmod 0444 images/ubuntu-base.qcow2
```

Cloud images are faster than ISO installs. Use cloud-init seed media to make the
first boot explicit.

Minimal `user-data`:

```yaml
#cloud-config
users:
  - name: analyst
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... analyst
package_update: true
packages:
  - openssh-server
  - qemu-guest-agent
runcmd:
  - systemctl enable --now ssh
  - systemctl enable --now qemu-guest-agent || true
```

Minimal `meta-data`:

```yaml
instance-id: iid-case-base
local-hostname: qemu-base
```

Create seed ISO:

```bash
cloud-localds seed.iso user-data meta-data
```

Run cloud image:

```bash
qemu-img create -f qcow2 -b "$(realpath jammy-server-cloudimg-amd64.img)" -F qcow2 \
  cases/cloud-firstboot.qcow2

qemu-system-x86_64 \
  -machine q35,accel=kvm \
  -cpu host \
  -m 4096 \
  -drive if=virtio,file=cases/cloud-firstboot.qcow2,format=qcow2 \
  -drive if=virtio,file=seed.iso,format=raw,readonly=on \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22 \
  -display none \
  -serial mon:stdio
```

Cloud-init state persists inside the guest. Before promoting a cloud-firstboot VM
to a base, remove or reset machine identity if clone uniqueness matters:

```bash
sudo cloud-init clean --logs --machine-id
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id
sudo poweroff
```

## Disk Images and Overlay Strategy

Use qcow2 overlays for per-case mutability:

```bash
qemu-img create -f qcow2 -b "$(realpath images/linux-base.qcow2)" -F qcow2 \
  "cases/$CASE/$CASE.qcow2"
```

Inspect backing chain:

```bash
qemu-img info --backing-chain "cases/$CASE/$CASE.qcow2"
```

Never use `qemu-img` to modify an image that is in use by a running VM. Even
queries can be inconsistent; writes can destroy the image.

Safe query while running is limited:

```bash
qemu-img info -U --backing-chain "cases/$CASE/$CASE.qcow2"
```

`-U` opens shared and can produce inconsistent metadata. Use it only for
low-stakes observation, and record that the VM was running.

Convert a case overlay into a standalone evidence image:

```bash
qemu-img convert -p -O qcow2 "cases/$CASE/$CASE.qcow2" \
  "evidence/$CASE/$CASE-standalone.qcow2"
```

Commit an overlay into its base only when promoting a new base:

```bash
qemu-img commit -f qcow2 "cases/promote/promote.qcow2"
```

Do not commit exploit evidence into the shared base. For evidence, export or
convert the overlay to a standalone image.

If a backing path moved, repair metadata only after verifying content:

```bash
qemu-img info --backing-chain "cases/$CASE/$CASE.qcow2"
qemu-img rebase -u -f qcow2 -b "$(realpath images/linux-base.qcow2)" -F qcow2 \
  "cases/$CASE/$CASE.qcow2"
```

`rebase -u` changes metadata without checking data compatibility. Use it only
when you know the backing content is identical and only the path changed.

Resize:

```bash
qemu-img resize "cases/$CASE/$CASE.qcow2" +20G
```

Then expand partitions/filesystems inside the guest. The image resize alone does
not grow the guest filesystem.

Check and repair:

```bash
qemu-img check -f qcow2 "cases/$CASE/$CASE.qcow2"
qemu-img check -r leaks -f qcow2 "cases/$CASE/$CASE.qcow2"
```

Avoid `-r all` unless you are salvaging a copy. It can hide corruption history.

## Snapshot and Commit Discipline

QEMU has three different concepts that people casually call snapshots. Keep them
separate.

Temporary write-discard mode:

```bash
qemu-system-x86_64 ... -snapshot
```

`-snapshot` treats disk images as read-only and writes changes to temporary
storage. Changes disappear when QEMU exits unless explicitly committed from the
monitor. This is good for quick destructive tests and bad for evidence you need
to preserve.

Internal VM snapshots:

```text
(qemu) savevm clean
(qemu) info snapshots
(qemu) loadvm clean
(qemu) delvm clean
```

Internal snapshots require qcow2 writable storage and include VM state. They are
convenient for manual debugging, but have device limitations and are less clear
than external overlays for evidence.

External overlay snapshots:

```bash
qemu-img create -f qcow2 -b "$(realpath images/base.qcow2)" -F qcow2 \
  "cases/$CASE/$CASE.qcow2"
```

Prefer external overlays for repeatable DAST. The parent is the baseline, the
overlay is the case mutation, and deletion/revert is just file lifecycle.

Promote a warmed image:

```bash
qemu-img convert -p -O qcow2 "cases/warmed/warmed.qcow2" images/linux-warmed.qcow2
qemu-img check images/linux-warmed.qcow2
chmod 0444 images/linux-warmed.qcow2
```

Record whether a base is clean OS, warmed browser, proxy-preconfigured,
certificate-preloaded, or target-app-preinstalled. Those differences change
DAST outcomes.

## Block Devices and I/O Options

Simple disk syntax:

```bash
-drive if=virtio,file="$DISK",format=qcow2,cache=none,discard=unmap
```

Use explicit `format=...` for every image. Letting QEMU probe format can create
unsafe or surprising behavior, especially for raw images with controlled content.

More explicit block graph with stable node names:

```bash
-blockdev driver=file,filename="$DISK",node-name=os_file,cache.direct=on,cache.no-flush=off \
-blockdev driver=qcow2,file=os_file,node-name=os_qcow2 \
-device virtio-blk-pci,drive=os_qcow2,bootindex=0
```

Stable node names make QMP block operations and evidence logs easier to read.

Read-only fixture disk:

```bash
-drive if=virtio,file=fixtures/sample.raw,format=raw,readonly=on
```

Attach an ISO:

```bash
-cdrom iso/installer.iso
```

or:

```bash
-drive file=iso/seed.iso,format=raw,media=cdrom,readonly=on
```

Direct host block devices are risky:

```bash
-drive if=virtio,file=/dev/sdb,format=raw,readonly=on
```

Use read-only unless the test explicitly requires guest writes to the host
device. A writeable raw host disk can corrupt host data.

Optional IOThread:

```bash
-object iothread,id=iothread0 \
-blockdev driver=file,filename="$DISK",node-name=os_file,cache.direct=on \
-blockdev driver=qcow2,file=os_file,node-name=os_qcow2 \
-device virtio-blk-pci,drive=os_qcow2,iothread=iothread0
```

For timing-sensitive findings, record cache mode, storage backend, and whether
IOThreads were used.

## Running VMs

Use a run directory per case:

```bash
CASE="case-$(date +%Y%m%d-%H%M%S)"
RUN="cases/$CASE/run"
mkdir -p "$RUN" "cases/$CASE/evidence"
```

Foreground run:

```bash
qemu-system-x86_64 ... -serial mon:stdio
```

Background run:

```bash
qemu-system-x86_64 ... \
  -display none \
  -daemonize \
  -pidfile "$RUN/qemu.pid" \
  -D "$RUN/qemu.log"
```

Use `-pidfile` and per-case sockets for automation:

```bash
-pidfile "$RUN/qemu.pid" \
-qmp unix:"$RUN/qmp.sock",server=on,wait=off \
-monitor unix:"$RUN/hmp.sock",server=on,wait=off
```

Stop gracefully through QMP when possible:

```bash
printf '{"execute":"qmp_capabilities"}\n{"execute":"system_powerdown"}\n' |
  socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

Hard stop only for disposable state:

```bash
kill "$(cat "$RUN/qemu.pid")"
```

Use `-no-reboot` when crashes should return control to automation:

```bash
-no-reboot
```

Use `-S` when a debugger or QMP setup must attach before guest code executes:

```bash
-S -qmp unix:"$RUN/qmp.sock",server=on,wait=off
```

Then continue:

```bash
printf '{"execute":"qmp_capabilities"}\n{"execute":"cont"}\n' |
  socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

## Headless, Serial, Display, and VNC

Headless Linux-friendly:

```bash
-display none -serial mon:stdio
```

Full terminal mode:

```bash
-nographic
```

For `-nographic`, configure guest kernel console to serial:

```text
console=ttyS0,115200n8
```

GTK display:

```bash
-display gtk
```

SDL display:

```bash
-display sdl
```

VNC bound to loopback:

```bash
-display vnc=127.0.0.1:1
```

or with the legacy spelling:

```bash
-vnc 127.0.0.1:1
```

Do not bind VNC to `0.0.0.0` for research VMs unless a separate access-control
layer is in place. If credentials are needed, provide secrets through QEMU secret
objects, not command-line literals.

Serial log file:

```bash
-serial file:"$RUN/serial.log"
```

Debug console:

```bash
-debugcon file:"$RUN/debugcon.log"
```

When using interactive `mon:stdio`, remember that the monitor is privileged.
Commands such as `commit`, `savevm`, device hotplug, and host file access can
change evidence.

## Networking Modes

Choose the network backend by the test's threat model:

- `user`: unprivileged NAT through SLIRP. Best default for quick DAST with local
  host forwarding.
- `passt`: unprivileged user-mode networking with better performance, IPv6, and
  a separate daemon context.
- `tap`: L2 interface connected to a host bridge, namespace, or custom NAT.
  Strongest control, more setup.
- `bridge`: QEMU helper-managed bridge connection.
- `socket` / `stream`: VM-to-VM or custom backend wiring.
- `none`: no network. Use for offline exploit replay.

Disable QEMU's implicit default NIC:

```bash
-nic none
```

Set a unique MAC explicitly:

```bash
-netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22 \
-device virtio-net-pci,netdev=net0,mac="$MAC"
```

Do not use a LAN-facing backend just because the guest needs internet. Use
`user`, `passt`, or a dedicated NAT unless the test requires true LAN presence.

## User Networking and Passt

User-mode networking requires no privileges and puts the guest behind a NAT-like
backend. The default guest network is `10.0.2.0/24`, the guest-visible host
address is usually `10.0.2.2`, and the first DHCP address is commonly
`10.0.2.15`.

Basic:

```bash
-nic user,model=virtio-net-pci
```

SSH forwarding bound to loopback:

```bash
-nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22
```

Multiple forwards:

```bash
-netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8080-:8080 \
-device virtio-net-pci,netdev=net0
```

Custom guest network:

```bash
-netdev user,id=net0,net=10.44.0.0/24,host=10.44.0.1 \
-device virtio-net-pci,netdev=net0
```

Disable IPv6 when a test needs IPv4-only behavior:

```bash
-nic user,ipv6=off,model=virtio-net-pci
```

User networking caveats:

- Incoming connections are blocked unless forwarded.
- ICMP is limited. Do not use missing `ping` as proof of no connectivity.
- It is not a LAN peer. mDNS, ARP, broadcasts, and some discovery protocols do
  not behave like bridged networking.
- Host port conflicts fail QEMU launch or silently break automation depending
  on wrapper behavior. Preflight ports.

Passt basic:

```bash
-nic passt,model=virtio-net-pci
```

Passt with explicit netdev:

```bash
-netdev passt,id=net0 \
-device virtio-net-pci,netdev=net0
```

Passt can be used as an unprivileged replacement for SLIRP and runs outside the
QEMU process. Prefer it when available for IPv6-heavy testing or when reducing
QEMU process attack surface matters.

Forward selected ports through passt:

```bash
-net passt,tcp-ports=2222,udp-ports=5353
```

For complex passt behavior, start `passt` yourself and connect QEMU to its Unix
socket:

```bash
passt --socket "$RUN/passt.sock" --log-file "$RUN/passt.log" --daemon
qemu-system-x86_64 ... \
  -device virtio-net-pci,netdev=net0 \
  -netdev stream,id=net0,server=off,addr.type=unix,addr.path="$RUN/passt.sock"
```

## Tap, Bridge, and Isolated NAT

Use tap when the guest must behave like a real L2 participant or when you need
host firewall and packet capture controls.

Single isolated bridge:

```bash
sudo ip link add br-dast type bridge
sudo ip addr add 192.168.120.1/24 dev br-dast
sudo ip link set br-dast up

sudo ip tuntap add tap-case0 mode tap user "$USER"
sudo ip link set tap-case0 master br-dast
sudo ip link set tap-case0 up
```

Run QEMU on that tap:

```bash
-netdev tap,id=net0,ifname=tap-case0,script=no,downscript=no \
-device virtio-net-pci,netdev=net0,mac=52:54:00:12:34:56
```

Add NAT with nftables:

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo nft add table ip qemu_dast
sudo nft add chain ip qemu_dast postrouting '{ type nat hook postrouting priority srcnat; policy accept; }'
sudo nft add rule ip qemu_dast postrouting ip saddr 192.168.120.0/24 oifname != "br-dast" masquerade
```

Add a tight forward policy if the host firewall defaults to drop. Keep firewall
rules case-specific and remove them by table name:

```bash
sudo nft delete table ip qemu_dast
```

Use dnsmasq if DHCP is useful:

```bash
dnsmasq --interface=br-dast --bind-interfaces \
  --dhcp-range=192.168.120.50,192.168.120.150,12h \
  --dhcp-option=3,192.168.120.1 \
  --dhcp-option=6,1.1.1.1 \
  --log-dhcp \
  --pid-file="$RUN/dnsmasq.pid"
```

Use a private network namespace when the whole lab should be separate from host
network policy:

```bash
sudo ip netns add dastns
sudo ip link add veth-host type veth peer name veth-ns
sudo ip link set veth-ns netns dastns
sudo ip addr add 192.168.130.1/24 dev veth-host
sudo ip link set veth-host up
sudo ip netns exec dastns ip addr add 192.168.130.2/24 dev veth-ns
sudo ip netns exec dastns ip link set veth-ns up
```

Bridge mode through `qemu-bridge-helper` can be cleaner on managed hosts, but
its allowlist is host policy. Record `/etc/qemu/bridge.conf` if it affects the
case.

## Guest Execution

Use SSH for Linux guest commands:

```bash
ssh -p 2222 -o StrictHostKeyChecking=no user@127.0.0.1 'uname -a'
ssh -p 2222 user@127.0.0.1 'sudo journalctl -b --no-pager'
```

Use serial for early boot and broken networking:

```bash
-display none -serial mon:stdio
```

Use QEMU Guest Agent only when installed and explicitly wired. It is powerful
and should be treated as a privileged host-to-guest management channel.

Avoid deriving exploit preconditions from SSH or QGA unless the attacker path has
equivalent guest privileges. Host-side control is a test harness, not the threat
actor.

## File Transfer and Shared Directories

Prefer SSH/SCP for ordinary guest file movement:

```bash
scp -P 2222 seed.tgz user@127.0.0.1:/tmp/seed.tgz
scp -P 2222 -r user@127.0.0.1:/tmp/evidence "evidence/$CASE/"
```

Use cloud-init seed media for first-boot configuration:

```bash
cloud-localds "cases/$CASE/seed.iso" user-data meta-data
-drive file="cases/$CASE/seed.iso",format=raw,media=cdrom,readonly=on
```

Use 9p for simple host directory sharing. Make inputs read-only:

```bash
-fsdev local,id=seeds,path="$PWD/seeds",security_model=mapped-xattr,readonly=on \
-device virtio-9p-pci,fsdev=seeds,mount_tag=seeds
```

Guest mount:

```bash
sudo mkdir -p /mnt/seeds
sudo mount -t 9p -o trans=virtio,version=9p2000.L,ro seeds /mnt/seeds
```

Writeable evidence share:

```bash
-fsdev local,id=evidence,path="$PWD/evidence/$CASE",security_model=mapped-xattr \
-device virtio-9p-pci,fsdev=evidence,mount_tag=evidence
```

Guest mount:

```bash
sudo mkdir -p /mnt/evidence
sudo mount -t 9p -o trans=virtio,version=9p2000.L evidence /mnt/evidence
```

9p security models affect ownership mapping. If host file ownership matters,
test the mapping before relying on it for evidence. For hostile guests, prefer
one-way ingress through read-only media and egress through SSH copy-out.

Virtiofs is faster and more Linux-native, but requires a separate `virtiofsd`
process and shared memory:

```bash
virtiofsd --socket-path="$RUN/virtiofs.sock" \
  --shared-dir="$PWD/evidence/$CASE" \
  --sandbox=namespace \
  --cache=auto &

qemu-system-x86_64 ... \
  -object memory-backend-memfd,id=mem,size=8G,share=on \
  -numa node,memdev=mem \
  -chardev socket,id=char_vfs,path="$RUN/virtiofs.sock" \
  -device vhost-user-fs-pci,chardev=char_vfs,tag=evidence
```

Guest mount:

```bash
sudo mkdir -p /mnt/evidence
sudo mount -t virtiofs evidence /mnt/evidence
```

Treat shared folders as a host exposure. Do not mount the repository root
writeable into an untrusted guest.

## QMP and HMP

QMP is the JSON management interface. HMP is the human monitor. Both are
privileged QEMU control interfaces.

Expose QMP on a Unix socket:

```bash
-qmp unix:"$RUN/qmp.sock",server=on,wait=off
```

Expose HMP on a Unix socket:

```bash
-monitor unix:"$RUN/hmp.sock",server=on,wait=off
```

Do not expose QMP/HMP on TCP for DAST guests unless protected with a real
authorization boundary. QEMU's security docs treat monitor access as equivalent
to the QEMU process privileges.

QMP handshake and status:

```bash
{
  printf '{"execute":"qmp_capabilities"}\n'
  printf '{"execute":"query-status"}\n'
  printf '{"execute":"query-block"}\n'
} | socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

Power down:

```bash
printf '{"execute":"qmp_capabilities"}\n{"execute":"system_powerdown"}\n' |
  socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

Pause and continue:

```bash
printf '{"execute":"qmp_capabilities"}\n{"execute":"stop"}\n' |
  socat - UNIX-CONNECT:"$RUN/qmp.sock"

printf '{"execute":"qmp_capabilities"}\n{"execute":"cont"}\n' |
  socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

HMP through a socket:

```bash
printf 'info status\ninfo block\nquit\n' | socat - UNIX-CONNECT:"$RUN/hmp.sock"
```

Interactive monitor through stdio:

```bash
-serial mon:stdio
```

Use `Ctrl-a c` to switch between serial and monitor when using the character
backend multiplexer.

## QEMU Guest Agent

QEMU Guest Agent (QGA) lets the host ask the guest to run agent-supported
operations such as ping, time, filesystem freeze, network queries, and sometimes
guest command execution. It requires guest installation and a virtio serial
channel.

Wire the channel:

```bash
-device virtio-serial-pci \
-chardev socket,path="$RUN/qga.sock",server=on,wait=off,id=qga0 \
-device virtserialport,chardev=qga0,name=org.qemu.guest_agent.0
```

Install in the Linux guest:

```bash
sudo apt install -y qemu-guest-agent
sudo systemctl enable --now qemu-guest-agent
```

Ping:

```bash
printf '{"execute":"guest-ping"}\n' | socat - UNIX-CONNECT:"$RUN/qga.sock"
```

Get guest time:

```bash
printf '{"execute":"guest-get-time"}\n' | socat - UNIX-CONNECT:"$RUN/qga.sock"
```

Run a guest command through QGA:

```bash
printf '{"execute":"guest-exec","arguments":{"path":"/usr/bin/id","capture-output":true}}\n' |
  socat - UNIX-CONNECT:"$RUN/qga.sock"
```

`guest-exec` returns a pid. Poll for output:

```bash
printf '{"execute":"guest-exec-status","arguments":{"pid":1234}}\n' |
  socat - UNIX-CONNECT:"$RUN/qga.sock"
```

For robust clients, synchronize first with `guest-sync-delimited`; stale bytes
can remain on an agent channel after client timeouts.

QGA caveats:

- The socket is a privileged host-to-guest channel.
- Guest command execution depends on agent support and policy.
- Filesystem freeze is useful for consistent disk capture, but can hang
  workloads if not thawed.
- Do not expose QGA sockets to untrusted local users.

## Secrets, Sandboxing, and Privileges

Do not pass secrets inline:

```bash
-object secret,id=bad,data=supersecret
```

Command-line arguments are visible through process listings, logs, crash reports,
and shell history.

Use file-backed secrets with restrictive permissions:

```bash
install -m 0600 /dev/null "$RUN/vnc-password.txt"
printf '%s' "$VNC_PASSWORD" > "$RUN/vnc-password.txt"

-object secret,id=secvnc0,file="$RUN/vnc-password.txt"
```

For production-like or shared labs, use an encrypted secret object with a
per-instance master key or the Linux keyring.

Use QEMU's seccomp sandbox when available:

```bash
--sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny
```

Use `-run-with` when a root-started wrapper must drop privileges:

```bash
-run-with user=qemu
```

Avoid root QEMU. If tap setup requires root, create tap devices before launch and
give the unprivileged QEMU process access to the existing tap.

Disable default devices for tight hostile-sample runs:

```bash
-nodefaults -no-user-config
```

Then add back only required devices:

```bash
-device virtio-net-pci,netdev=net0
-device virtio-blk-pci,drive=os_qcow2
-device virtio-rng-pci,rng=rng0
```

Entropy device:

```bash
-object rng-random,filename=/dev/urandom,id=rng0 \
-device virtio-rng-pci,rng=rng0
```

Record all passthrough and host bridges. PCI, USB, block devices, shared
directories, QMP, QGA, VNC, and SPICE are all deliberate trust-boundary changes.

## TPM, UEFI, and Secure Boot

Use `swtpm` when guest behavior depends on TPM presence:

```bash
mkdir -p "$RUN/tpm"
swtpm socket --tpm2 \
  --tpmstate dir="$RUN/tpm" \
  --ctrl type=unixio,path="$RUN/swtpm.sock" \
  --daemon

qemu-system-x86_64 ... \
  -chardev socket,id=chrtpm,path="$RUN/swtpm.sock" \
  -tpmdev emulator,id=tpm0,chardev=chrtpm \
  -device tpm-tis,tpmdev=tpm0
```

TPM state is case state. Preserve the TPM directory with evidence if findings
depend on measured boot, disk encryption, attestation, or sealed secrets.

UEFI vars are also case state:

```bash
cp /usr/share/OVMF/OVMF_VARS.fd "$RUN/OVMF_VARS.fd"
```

Secure Boot files vary by distribution. Common locations include:

```bash
/usr/share/OVMF/OVMF_CODE.fd
/usr/share/OVMF/OVMF_CODE.secboot.fd
/usr/share/OVMF/OVMF_VARS.fd
/usr/share/OVMF/OVMF_VARS.ms.fd
```

Record the exact OVMF code and vars files used:

```bash
sha256sum /usr/share/OVMF/OVMF_CODE*.fd "$RUN/OVMF_VARS.fd"
```

If a finding depends on measured boot or hardware TPM properties, retest on the
target hardware class. `swtpm` is a useful lab TPM, not a physical TPM.

## Nested KVM

Use nested KVM only when the guest must run its own VMs, Android emulator, WSL2
equivalent, or KVM-backed tooling.

Check host nested state:

```bash
cat /sys/module/kvm_intel/parameters/nested 2>/dev/null || true
cat /sys/module/kvm_amd/parameters/nested 2>/dev/null || true
```

Persist nested KVM on Intel:

```bash
echo 'options kvm-intel nested=Y' | sudo tee /etc/modprobe.d/kvm-intel.conf
```

Persist nested KVM on AMD:

```bash
echo 'options kvm-amd nested=1' | sudo tee /etc/modprobe.d/kvm-amd.conf
```

Reloading KVM modules disrupts running VMs. Do it only on a lab host:

```bash
sudo modprobe -r kvm_intel kvm
sudo modprobe kvm_intel
```

Expose virtualization features to the L1 guest:

```bash
-cpu host
```

or, for a named Intel model:

```bash
-cpu Haswell-noTSX-IBRS,vmx=on
```

Inside the L1 guest:

```bash
ls -l /dev/kvm
grep -E 'vmx|svm' /proc/cpuinfo | head
```

Do not save, migrate, or snapshot nested workloads casually. Kernel KVM docs
call out platform-specific instability risks, especially around live nested
guests. Treat nested mode as a separate base image and record L0, L1, and L2
QEMU/kernel versions.

## Kernel and Device Debugging

Pause CPU at startup and expose a local GDB server:

```bash
-S -gdb tcp:127.0.0.1:1234
```

Connect:

```bash
gdb vmlinux
(gdb) target remote 127.0.0.1:1234
(gdb) continue
```

`-s` is shorthand for a GDB server on TCP port 1234, but explicit loopback is
clearer:

```bash
-gdb tcp:127.0.0.1:1234
```

Direct Linux boot:

```bash
qemu-system-x86_64 \
  -machine q35,accel=kvm \
  -cpu host \
  -m 4096 \
  -kernel arch/x86/boot/bzImage \
  -initrd initramfs.cpio.gz \
  -append "console=ttyS0 root=/dev/vda rw panic=-1" \
  -drive if=virtio,file=rootfs.qcow2,format=qcow2 \
  -display none \
  -serial mon:stdio
```

QEMU debug logs:

```bash
qemu-system-x86_64 -d help
qemu-system-x86_64 ... -d guest_errors,unimp -D "$RUN/qemu-debug.log"
```

Use record/replay only for workflows built around it. It is powerful for
deterministic debugging, but it changes launch requirements and has device
support constraints. Record it explicitly if used.

## DAST Repro Patterns

Clean Linux web repro:

```bash
BASE="$(realpath images/linux-web-base.qcow2)"
CASE="web-$(date +%Y%m%d-%H%M%S)"
RUN="cases/$CASE/run"
mkdir -p "$RUN" "evidence/$CASE"

qemu-img create -f qcow2 -b "$BASE" -F qcow2 "cases/$CASE/$CASE.qcow2"

qemu-system-x86_64 \
  -name "$CASE",process="$CASE" \
  -machine q35,accel=kvm \
  -cpu host \
  -smp 4 \
  -m 8192 \
  -drive if=virtio,file="cases/$CASE/$CASE.qcow2",format=qcow2,cache=none,discard=unmap \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8080-:8080 \
  -display none \
  -serial file:"$RUN/serial.log" \
  -qmp unix:"$RUN/qmp.sock",server=on,wait=off \
  -pidfile "$RUN/qemu.pid" \
  -daemonize \
  -D "$RUN/qemu.log"
```

Offline exploit replay:

```bash
qemu-system-x86_64 \
  -machine q35,accel=kvm \
  -cpu host \
  -m 4096 \
  -drive if=virtio,file="cases/$CASE/$CASE.qcow2",format=qcow2 \
  -drive if=virtio,file=fixtures/payloads.raw,format=raw,readonly=on \
  -nic none \
  -display none \
  -serial mon:stdio
```

Isolated NAT lab:

```bash
sudo ip link add br-dast type bridge
sudo ip addr add 192.168.120.1/24 dev br-dast
sudo ip link set br-dast up
sudo ip tuntap add "tap-$CASE" mode tap user "$USER"
sudo ip link set "tap-$CASE" master br-dast
sudo ip link set "tap-$CASE" up

qemu-system-x86_64 ... \
  -netdev tap,id=net0,ifname="tap-$CASE",script=no,downscript=no \
  -device virtio-net-pci,netdev=net0,mac="$MAC"
```

Readonly seed and writeable evidence share:

```bash
-fsdev local,id=seeds,path="$PWD/seeds",security_model=mapped-xattr,readonly=on \
-device virtio-9p-pci,fsdev=seeds,mount_tag=seeds \
-fsdev local,id=evidence,path="$PWD/evidence/$CASE",security_model=mapped-xattr \
-device virtio-9p-pci,fsdev=evidence,mount_tag=evidence
```

Hostile guest minimum:

```bash
qemu-system-x86_64 \
  -nodefaults -no-user-config \
  --sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny \
  -machine q35,accel=kvm \
  -cpu host \
  -m 4096 \
  -blockdev driver=file,filename="$DISK",node-name=os_file,cache.direct=on \
  -blockdev driver=qcow2,file=os_file,node-name=os_qcow2 \
  -device virtio-blk-pci,drive=os_qcow2 \
  -nic none \
  -display none \
  -serial file:"$RUN/serial.log" \
  -qmp unix:"$RUN/qmp.sock",server=on,wait=off
```

## Evidence Capture

Create evidence directories first:

```bash
CASE="case-$(date +%Y%m%d-%H%M%S)"
mkdir -p "evidence/$CASE"
```

Capture host and QEMU facts:

```bash
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  uname -a
  lscpu
  qemu-system-x86_64 --version
  qemu-img --version
  ls -l /dev/kvm
  lsmod | grep '^kvm' || true
} > "evidence/$CASE/host.txt"
```

Capture image chain:

```bash
qemu-img info --backing-chain "cases/$CASE/$CASE.qcow2" \
  > "evidence/$CASE/qemu-img-backing-chain.txt"
sha256sum images/*.qcow2 "cases/$CASE/$CASE.qcow2" \
  > "evidence/$CASE/image-sha256.txt" 2>/dev/null || true
```

Capture launch command:

```bash
tr '\0' ' ' < "/proc/$(cat "$RUN/qemu.pid")/cmdline" \
  > "evidence/$CASE/qemu-cmdline.txt"
```

Capture QMP state:

```bash
{
  printf '{"execute":"qmp_capabilities"}\n'
  printf '{"execute":"query-status"}\n'
  printf '{"execute":"query-version"}\n'
  printf '{"execute":"query-kvm"}\n'
  printf '{"execute":"query-current-machine"}\n'
  printf '{"execute":"query-block"}\n'
  printf '{"execute":"query-netdev"}\n'
  printf '{"execute":"query-chardev"}\n'
} | socat - UNIX-CONNECT:"$RUN/qmp.sock" > "evidence/$CASE/qmp.jsonl"
```

Capture guest state through SSH:

```bash
ssh -p 2222 user@127.0.0.1 '
  set -x
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  uname -a
  cat /etc/os-release
  ip addr
  ip route
  systemctl --failed || true
  journalctl -b --no-pager | tail -500
' > "evidence/$CASE/guest-state.txt"
```

Copy artifacts:

```bash
scp -P 2222 -r user@127.0.0.1:/tmp/evidence "evidence/$CASE/guest-evidence"
```

Preserve case disk:

```bash
qemu-img convert -p -O qcow2 "cases/$CASE/$CASE.qcow2" \
  "evidence/$CASE/$CASE-standalone.qcow2"
qemu-img check "evidence/$CASE/$CASE-standalone.qcow2" \
  > "evidence/$CASE/standalone-check.txt"
```

Capture networking setup:

```bash
ip addr > "evidence/$CASE/host-ip-addr.txt"
ip route > "evidence/$CASE/host-ip-route.txt"
nft list ruleset > "evidence/$CASE/nft-ruleset.txt" 2>/dev/null || true
brctl show > "evidence/$CASE/bridges.txt" 2>/dev/null || true
```

If libvirt launched QEMU, also preserve the generated command line and XML:

```bash
virsh dumpxml "$VM" > "evidence/$CASE/libvirt-domain.xml"
cp "/var/log/libvirt/qemu/$VM.log" "evidence/$CASE/" 2>/dev/null || true
```

## Failure Modes

`Could not access KVM kernel module`

Check device node and group membership:

```bash
ls -l /dev/kvm
groups
sudo usermod -aG kvm "$USER"
```

Log out/in or use `newgrp kvm`. Do not switch to root QEMU as the first fix.

QEMU silently falls back to TCG

Use explicit accelerator and fail fast:

```bash
-machine q35,accel=kvm
```

Avoid `-accel kvm -accel tcg` unless fallback is acceptable and recorded.

Guest is extremely slow

Likely TCG, missing virtio drivers, no KVM, wrong CPU model, nested KVM off, or
heavy host overcommit. Check QEMU stderr, `/dev/kvm`, and guest drivers.

Image format warning or raw probing warning

Specify image format:

```bash
-drive file="$DISK",format=qcow2,if=virtio
```

`qemu-img: Could not open backing file`

Inspect and repair backing path:

```bash
qemu-img info --backing-chain "$DISK"
qemu-img rebase -u -f qcow2 -b "$(realpath images/base.qcow2)" -F qcow2 "$DISK"
```

Only use unsafe rebase when content is known identical.

`qemu-img` reports image in use or lock failure

Stop the VM or use QMP block operations. Do not modify an active image offline.

Host port forwarding fails

Check port ownership:

```bash
ss -ltnp | grep ':2222'
```

Bind forwards to loopback and use per-case port allocation:

```bash
hostfwd=tcp:127.0.0.1:2223-:22
```

Guest has user-networking but no ping

ICMP is limited under user-mode networking. Test TCP or DNS instead:

```bash
curl -I https://example.com
ssh -p 2222 user@127.0.0.1
```

Tap guest has no network

Check tap is up, enslaved to bridge, guest has IP, host forwarding is enabled,
and firewall rules allow forwarding.

```bash
ip link show tap-case0
bridge link
ip addr show br-dast
sysctl net.ipv4.ip_forward
nft list ruleset
```

QMP commands do nothing

You probably did not negotiate capabilities:

```bash
printf '{"execute":"qmp_capabilities"}\n' | socat - UNIX-CONNECT:"$RUN/qmp.sock"
```

QGA returns stale JSON or parse errors

Synchronize with `guest-sync-delimited` and ignore bytes before the sentinel
response.

9p mount fails

Check the guest kernel has 9p/virtio support and the mount tag matches exactly:

```bash
grep 9p /proc/filesystems
sudo mount -t 9p -o trans=virtio,version=9p2000.L seeds /mnt/seeds
```

OVMF boot order or Secure Boot state leaks between cases

Use a fresh copy of `OVMF_VARS.fd` per case. The vars file is mutable.

Nested KVM unavailable inside guest

Check L0 nested parameter and L1 CPU exposure:

```bash
cat /sys/module/kvm_intel/parameters/nested 2>/dev/null
grep -E 'vmx|svm' /proc/cpuinfo
ls -l /dev/kvm
```

Host disk corrupted after test

Check whether a host block device or shared directory was attached writeable.
Prefer `readonly=on`, read-only 9p, read-only ISO, or overlay disks.

## Evidence Checklist

Before run:

- QEMU version, qemu-img version, host kernel, CPU, and accelerator recorded.
- Machine type, CPU model, SMP, memory, firmware, UUID, and MAC recorded.
- Base image hash and overlay backing chain recorded.
- Network backend chosen: user, passt, tap, bridge, private, or none.
- QMP/HMP/QGA sockets local and access-controlled.
- Shared directories mounted read-only unless write access is required.
- TPM, OVMF vars, and cloud-init seed state scoped per case.

During run:

- QEMU command line captured from `/proc/<pid>/cmdline`.
- QMP `query-status`, `query-block`, and network/chardev state captured.
- Guest OS version, IP config, logs, and test artifacts captured.
- Packet captures or firewall/NAT state captured when network behavior matters.
- Serial/debug logs preserved for boot, kernel, and crash evidence.

After run:

- Guest shut down through QMP or stopped with method recorded.
- Case overlay preserved, converted, or deleted intentionally.
- Base image remains unchanged and read-only.
- No active image was modified with `qemu-img`.
- Temporary tap, bridge, nftables, dnsmasq, passt, swtpm, and socket artifacts
  removed or retained as evidence deliberately.

## References

- [QEMU system emulation](https://www.qemu.org/docs/master/system/index.html)
- [QEMU invocation](https://www.qemu.org/docs/master/system/invocation.html)
- [QEMU disk images](https://www.qemu.org/docs/master/system/images.html)
- [qemu-img](https://www.qemu.org/docs/master/tools/qemu-img.html)
- [QEMU network emulation](https://www.qemu.org/docs/master/system/devices/net.html)
- [QEMU monitor](https://www.qemu.org/docs/master/system/monitor.html)
- [QEMU Machine Protocol specification](https://www.qemu.org/docs/master/interop/qmp-spec.html)
- [QEMU Guest Agent protocol reference](https://www.qemu.org/docs/master/interop/qemu-ga-ref)
- [QEMU security](https://www.qemu.org/docs/master/system/security.html)
- [QEMU secrets](https://www.qemu.org/docs/master/system/secrets.html)
- [QEMU GDB usage](https://www.qemu.org/docs/master/system/gdb.html)
- [Linux KVM nested guests](https://docs.kernel.org/virt/kvm/x86/running-nested-guests.html)
