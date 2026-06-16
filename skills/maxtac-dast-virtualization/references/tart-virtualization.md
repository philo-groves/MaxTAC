# Tart Virtualization

Use Tart for reproducible macOS and Linux virtual machines on Apple
Virtualization.Framework hosts. For DAST work, treat Tart as a clean, clonable
desktop OS lab, not as a physical-device substitute. It is strong for macOS app,
browser, proxy, toolchain, CI, and artifact-replay workflows; it is weak for
hardware-bound behavior, iOS behavior, Secure Enclave/T2 assumptions, Apple ID
flows, and anything where the vulnerability depends on physical device state.

## Contents

- [Quick Commands](#quick-commands)
- [Host and Version Probes](#host-and-version-probes)
- [Image Selection and Drift](#image-selection-and-drift)
- [Creating Base Images](#creating-base-images)
- [VM Configuration](#vm-configuration)
- [Clone Strategy](#clone-strategy)
- [Running VMs](#running-vms)
- [Headless, VNC, and UI Controls](#headless-vnc-and-ui-controls)
- [SSH and Script Execution](#ssh-and-script-execution)
- [Shared Directories](#shared-directories)
- [Additional Disks and Root Disk Options](#additional-disks-and-root-disk-options)
- [Networking Modes](#networking-modes)
- [Softnet Patterns](#softnet-patterns)
- [Bridged and Host-Only Patterns](#bridged-and-host-only-patterns)
- [Linux Guests](#linux-guests)
- [Rosetta in Linux Guests](#rosetta-in-linux-guests)
- [Nested Virtualization](#nested-virtualization)
- [Registry and Image Promotion](#registry-and-image-promotion)
- [Packer and CI](#packer-and-ci)
- [DAST Repro Patterns](#dast-repro-patterns)
- [Evidence Capture](#evidence-capture)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Host sanity:

```text
sw_vers
uname -m
command -v tart
tart --version
tart --help
tart run --help
tart set --help
```

Clone and run an upstream macOS image:

```text
tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base
tart set tahoe-base --cpu 4 --memory 8192 --disk-size 80 --display 1920x1080
tart run tahoe-base
```

Headless access:

```text
# Run this in a terminal or job step that owns the VM lifecycle.
tart run tahoe-base --no-graphics
tart ip tahoe-base
ssh admin@$(tart ip tahoe-base)
```

Repro clone:

```text
CASE="case-$(date +%Y%m%d-%H%M%S)"
tart clone tahoe-base "$CASE"
tart set "$CASE" --random-mac --random-serial
tart run "$CASE" --dir=evidence:"$PWD/evidence" --dir=seeds:"$PWD/seeds":ro
```

Network-restricted repro:

```text
tart run "$CASE" \
  --net-softnet \
  --net-softnet-block=0.0.0.0/0 \
  --net-softnet-allow=17.0.0.0/8 \
  --dir=evidence:"$PWD/evidence"
```

Expose a guest service through Softnet:

```text
tart run "$CASE" \
  --net-softnet-expose=8080:8080 \
  --net-softnet-allow=192.168.0.0/16
```

List and use bridged interfaces:

```text
tart run "$CASE" --net-bridged=list
tart run "$CASE" --net-bridged=en0
```

OCI registry workflow:

```text
tart login ghcr.io
tart push tahoe-base ghcr.io/acme/labs/tahoe-base:2026-06-16
tart pull ghcr.io/acme/labs/tahoe-base:2026-06-16
tart clone ghcr.io/acme/labs/tahoe-base:2026-06-16 repro
```

Cleanup:

```text
tart stop "$CASE"
tart delete "$CASE"
tart prune
```

## Host and Version Probes

Start with host facts. Many Tart flags are thin wrappers over Apple
Virtualization.Framework capabilities, so unsupported host versions fail even
when the CLI accepts the option.

```text
sw_vers
uname -m
tart --version
tart run --help
tart set --help
```

Important host gates:

- macOS 13.0 or newer is the normal floor for current Tart quick-start usage.
- Directory sharing requires macOS 13.0 or newer on the host.
- macOS guests need macOS 13.0 or newer to auto-mount Tart shared directories.
- Linux guests are supported on macOS 13.0 or newer hosts.
- Nested virtualization requires macOS 15 or newer and supported hardware. The
  current Tart source checks for M3-or-newer support before enabling it.
- Some emerging first-boot macOS guest provisioning flags exist only on newer
  host and guest combinations. Always confirm with `tart run --help` before
  writing automation around `--provisioning-opts`.

Install through Homebrew when possible:

```text
brew install cirruslabs/cli/tart
```

Manual archive installs have a non-obvious requirement:

```text
curl -LO https://github.com/cirruslabs/tart/releases/latest/download/tart.tar.gz
tar -xzvf tart.tar.gz
./tart.app/Contents/MacOS/tart --version
```

Use `./tart.app/Contents/MacOS/tart`, not a copied-out bare binary, when running
from a release archive. The app bundle carries the embedded provisioning profile
Tart needs for elevated virtualization privileges.

## Image Selection and Drift

Tart can clone local VMs and remote OCI images. Upstream public images usually
come in three practical families:

- `vanilla`: closest to a clean OS install.
- `base`: common CI/research conveniences such as SSH-friendly defaults.
- `xcode`: large, toolchain-bearing macOS images.

Examples:

```text
ghcr.io/cirruslabs/macos-tahoe-vanilla:latest
ghcr.io/cirruslabs/macos-tahoe-base:latest
ghcr.io/cirruslabs/macos-tahoe-xcode:latest
ghcr.io/cirruslabs/macos-sequoia-base:latest
ghcr.io/cirruslabs/ubuntu:latest
ghcr.io/cirruslabs/debian:latest
ghcr.io/cirruslabs/fedora:latest
```

Do not use `:latest` in evidence or regression automation unless the point of
the run is to track upstream drift. Pin a specific tag, and record the remote
name used to create the local VM.

```text
tart clone ghcr.io/cirruslabs/macos-sequoia-base:15.5 sequoia-15-5-base
```

Public Cirrus images use `admin` / `admin` credentials. That is convenient for
short-lived local clones and bad for shared networks, persistent labs, or any
VM that might be reachable from other machines. Rotate the password or use a
private image before exposing services.

Linux public images have small default disks. Resize immediately after clone if
the guest will install browsers, SDKs, corpora, or crash artifacts:

```text
tart clone ghcr.io/cirruslabs/ubuntu:24.04 ubuntu-24-04
tart set ubuntu-24-04 --disk-size 80
```

## Creating Base Images

Prefer cloning a pinned upstream image for fast iteration:

```text
tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base
```

Create macOS from an IPSW when you need a base that upstream images do not
provide, or when evidence requires a custom first-boot path:

```text
tart create --from-ipsw=latest tahoe-vanilla
tart run tahoe-vanilla
```

The initial macOS setup still matters for automation. Record exactly which of
these choices you made:

- Local user and password, usually `admin` / `admin` for compatibility with
  upstream Tart automation examples.
- Automatic login, if GUI automation or after-reboot capture needs it.
- Remote Login, if SSH is part of the workflow.
- Lock screen and screen saver settings, if unattended repro steps need the
  desktop to stay available.
- Sudo behavior, especially whether `admin` has passwordless sudo.

Create Linux from an installer ISO when the public images do not match the test:

```text
tart create --linux ubuntu --disk-size 80
tart run --disk=ubuntu-24.04.2-live-server-arm64.iso:ro ubuntu
```

Inside the Linux guest, enable SSH if automation depends on it:

```text
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```

## VM Configuration

Default Tart VMs use 2 CPUs, 4 GB of memory, and a 1024x768 display. Set sizing
explicitly in scripts so the repro does not depend on upstream image defaults.

```text
tart set "$VM" --cpu 4
tart set "$VM" --memory 8192
tart set "$VM" --display 1920x1080
tart set "$VM" --display 1200x800pt
tart set "$VM" --display 1920x1080px
tart set "$VM" --no-display-refit
```

Use point units for macOS UI-oriented testing when exact window geometry matters.
Use pixel units for Linux guests when HiDPI scaling would otherwise skew
screenshots.

Disk resizing only grows disks:

```text
tart set "$VM" --disk-size 120
```

If you need a smaller disk, rebuild or reclone from a smaller base. Do not expect
`--disk-size` to shrink a VM for artifact minimization.

Change identity when cloning persistent or concurrently running VMs:

```text
tart set "$VM" --random-mac
tart set "$VM" --random-serial
```

`--random-serial` is macOS-specific. Use it when clone identity could affect
licensing, MDM enrollment, hostname-derived telemetry, or target-side device
fingerprinting. It does not make the guest equivalent to a new physical Mac.

Replace the root disk only when you intentionally trust the replacement disk:

```text
tart set "$VM" --disk ./prepared-root-disk.img
```

For DAST evidence, record every `tart set` operation used to prepare the base.
The difference between an upstream image and a modified local base is often the
difference between reproducible and irreproducible findings.

## Clone Strategy

Use clones as disposable test subjects. Keep bases boring and immutable.

```text
tart clone tahoe-base case-clean
tart run case-clean
tart stop case-clean
tart delete case-clean
```

Tart local clones are APFS copy-on-write, so clone creation is fast and does not
immediately consume the full disk size. Disk usage grows as the clone writes.
This makes per-test clones cheap enough to prefer over hand-resetting a dirty VM.

Recommended pattern:

```text
BASE=tahoe-15-5-base
CASE="case-$(date +%Y%m%d-%H%M%S)"

tart clone "$BASE" "$CASE"
tart set "$CASE" --random-mac --random-serial
tart run "$CASE" --dir=evidence:"$PWD/evidence"
```

For tests that mutate system state, do not reuse a clone after exploitation. Stop
it, collect evidence, then delete it.

```text
tart stop "$CASE"
tart delete "$CASE"
```

When you need a warm state, use an intentionally named warmed clone:

```text
tart clone tahoe-base tahoe-browser-primed
tart run tahoe-browser-primed
# install browser certs, proxy profile, corp root CA, target app
tart stop tahoe-browser-primed
```

Then clone from that warmed image for cases:

```text
tart clone tahoe-browser-primed case-001
```

Avoid treating a warmed image as clean. Its installed certificates, cookies,
browser storage, keychains, SSH host keys, launch agents, and hostname can affect
vulnerability behavior.

## Running VMs

Default run opens Tart's built-in VM window:

```text
tart run "$VM"
```

Headless run:

```text
tart run "$VM" --no-graphics
```

`tart run` stays attached to the VM lifecycle. In shell automation, run it in a
managed background process, a separate terminal, or a CI job step that is
expected to hold the VM open:

```text
tart run "$VM" --no-graphics >"logs/$VM.tart.log" 2>&1 &
```

Boot macOS recovery:

```text
tart run "$VM" --recovery
```

Use a serial console for Linux kernel, bootloader, or early-boot debug:

```text
tart run "$VM" --serial
tart run "$VM" --serial-path /dev/ttys003
```

Use suspendable mode only when the VM state is intentionally suspend/resume
tested:

```text
tart run "$VM" --suspendable
tart suspend "$VM"
```

Suspendable mode changes device configuration. It disables audio and entropy
devices and switches input devices to a mode that can be suspended. Do not mix
suspendable and non-suspendable runs when validating timing, input, entropy, or
device enumeration behavior.

## Headless, VNC, and UI Controls

For automation, prefer SSH and shared directories over GUI automation. Use VNC
only when the repro requires visible desktop state.

```text
tart run "$VM" --no-graphics
tart ip "$VM"
ssh admin@$(tart ip "$VM")
```

Use VNC when built-in UI behavior is the wrong primitive:

```text
tart run "$VM" --vnc
tart run "$VM" --vnc-experimental
```

Notes:

- `--vnc` uses screen sharing instead of Tart's built-in UI.
- `--vnc-experimental` uses Virtualization.Framework VNC and can be useful in
  recovery or installer flows, but expect bugs.
- `--vnc` and `--vnc-experimental` are mutually exclusive.
- `--no-graphics` and forced UI graphics are mutually exclusive.
- `--capture-system-keys` only applies to the default VM view.

UI-focused flags:

```text
tart run "$VM" --capture-system-keys
tart run "$VM" --no-audio
tart run "$VM" --no-clipboard
tart run "$VM" --no-keyboard
tart run "$VM" --no-pointer
tart run "$VM" --no-trackpad
```

Clipboard sharing requires a guest agent on macOS and `spice-vdagent` on Linux.
Disable clipboard sharing for malware-adjacent payload replay, secrets handling,
or tests where host-to-guest clipboard leakage would pollute the result.

## SSH and Script Execution

Use `tart ip` as the source of truth for the guest address:

```text
IP="$(tart ip "$VM")"
ssh admin@"$IP" sw_vers
```

For public images:

```text
ssh admin@$(tart ip "$VM")
```

For one-off lab automation with the public default password:

```text
sshpass -p admin ssh \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  admin@$(tart ip "$VM") \
  "uname -a"
```

Prefer key-based SSH for shared labs. If `ssh-copy-id` is available:

```text
ssh-copy-id admin@$(tart ip "$VM")
ssh admin@$(tart ip "$VM") "mkdir -p ~/repro"
```

Run scripts through SSH when you want terminal logs:

```text
ssh admin@$(tart ip "$VM") 'bash -s' < ./guest-setup.sh
```

Run scripts through Cirrus CLI when you want a CI-like execution model with
artifacts rather than ad hoc SSH transcripts.

## Shared Directories

Use shared directories for seeds, tools, and evidence. Make inputs read-only and
outputs writeable.

```text
tart run "$VM" \
  --dir=seeds:"$PWD/seeds":ro \
  --dir=evidence:"$PWD/evidence"
```

The `--dir` grammar is:

```text
--dir=[name:]path[:options]
```

Useful options:

```text
ro
tag=<TAG>
```

Default mount tag:

```text
com.apple.virtio-fs.automount
```

macOS guest default path:

```text
/Volumes/My Shared Files/<name>
```

Linux guest mount:

```text
sudo mkdir -p /mnt/shared
sudo mount -t virtiofs com.apple.virtio-fs.automount /mnt/shared
```

Linux fstab entry:

```text
com.apple.virtio-fs.automount /mnt/shared virtiofs rw,relatime 0 0
```

Custom tag:

```text
tart run "$VM" --dir=build:"$PWD/build":tag=build
```

macOS guest:

```text
mkdir -p ~/build
mount_virtiofs build ~/build
```

Linux guest:

```text
sudo mkdir -p /mnt/build
sudo mount -t virtiofs build /mnt/build
```

When using multiple directories under the same tag, each share must have a
unique name:

```text
tart run "$VM" \
  --dir=seeds:"$PWD/seeds":ro \
  --dir=out:"$PWD/out"
```

Do not use the same share name twice. Tart will use the last share with that
name, which can silently point a repro at the wrong input.

For evidence integrity:

- Mount payloads, fixtures, and seed corpora read-only.
- Write evidence to a fresh, case-specific host directory.
- Record the host path and mount name in the case notes.
- Do not mount the whole workspace writeable unless the test specifically needs
  it.

## Additional Disks and Root Disk Options

Attach ISO or disk images with `--disk`:

```text
tart run "$VM" --disk=ubuntu-24.04.2-live-server-arm64.iso:ro
tart run "$VM" --disk=./sample-disk.img:ro
tart run "$VM" --disk=./scratch.img
```

The `--disk` grammar is:

```text
--disk=path[:options]
```

Common options:

```text
ro
sync=none
caching=automatic
caching=cached
caching=uncached
```

Use read-only attachments for untrusted samples, repro fixtures, golden images,
and third-party evidence.

```text
tart run "$VM" --disk=./evidence-image.raw:ro
```

Tart can also attach block devices, remote VM disks, and NBD URLs on supported
hosts:

```text
tart run "$VM" --disk=/dev/disk4:ro
tart run "$VM" --disk=ghcr.io/cirruslabs/xcode:16.0:ro
tart run "$VM" --disk=nbd://localhost:10809/myDisk:sync=none
```

Block device warning:

```text
sudo chown $USER /dev/diskX
tart run "$VM" --disk=/dev/diskX
```

Changing `/dev/diskX` ownership gives every process running as that user access
to the block device. Avoid this in hostile-sample work, shared accounts, or
threat models where the host user is not fully trusted.

If a disk is busy:

```text
diskutil unmountDisk /dev/diskX
diskutil umount /dev/diskXsY
```

Root disk options are useful for immutable or performance-sensitive runs:

```text
tart run "$VM" --root-disk-opts=ro
tart run "$VM" --root-disk-opts=sync=none
tart run "$VM" --root-disk-opts=caching=cached,sync=none
```

Do not use `sync=none` for evidence you need to preserve inside the guest. It
trades durability for performance.

## Networking Modes

Tart network modes are mutually exclusive:

- Default shared/NAT networking.
- `--net-bridged=<interface>`.
- `--net-softnet` plus its allow/block/expose options.
- `--net-host`.

Default shared networking is usually enough for outbound web testing and SSH
from the host:

```text
tart run "$VM"
tart ip "$VM"
```

Choose network mode by test requirement:

```text
# Real LAN presence, target can connect to guest directly.
tart run "$VM" --net-bridged=en0

# Outbound internet with private-network restrictions and packet filtering.
tart run "$VM" --net-softnet

# No outside network, host-only testing.
tart run "$VM" --net-host
```

When testing an app's behavior around LAN discovery, captive portals, mDNS,
proxy autodiscovery, or inbound callbacks, the network mode is part of the test
case. Record it.

## Softnet Patterns

Softnet is Tart's user-space packet-filter mode. It is useful for ephemeral
research VMs because it restricts traffic and shortens DHCP leases for high-churn
clone workloads.

Default Softnet allows the guest to:

- Send traffic from its assigned MAC address.
- Send traffic from its DHCP-assigned IP address.
- Reach globally routable IPv4 addresses.
- Reach the vmnet bridge gateway.
- Receive incoming traffic.

Basic use:

```text
tart run "$VM" --net-softnet
```

Allow local lab ranges:

```text
tart run "$VM" --net-softnet --net-softnet-allow=192.168.0.0/16,10.0.0.0/8
```

Default-deny egress, then allow only a target:

```text
tart run "$VM" \
  --net-softnet-block=0.0.0.0/0 \
  --net-softnet-allow=203.0.113.10/32
```

Block a sensitive range while keeping normal Softnet behavior:

```text
tart run "$VM" --net-softnet-block=169.254.169.254/32
```

Allow all destinations but keep Softnet mechanics:

```text
tart run "$VM" --net-softnet-allow=0.0.0.0/0
```

Expose guest ports to the host's egress interface:

```text
tart run "$VM" \
  --net-softnet-expose=2222:22,8080:8080 \
  --net-softnet-allow=192.168.0.0/16
```

Port-forward caveats:

- The guest service must listen on `0.0.0.0` or the guest IP.
- The forwarded external port is reached from the local network or internet, not
  from the host itself.
- Regular Softnet restrictions still apply. Add an allow CIDR for the client
  network, or use `--net-softnet-allow=0.0.0.0/0` when the exposure itself is
  the isolation boundary.

When allow and block CIDRs overlap, longest prefix match wins; for identical
prefixes, block wins. Use this to create clear deny-by-default policies.

## Bridged and Host-Only Patterns

List interfaces before hardcoding bridge names:

```text
tart run "$VM" --net-bridged=list
```

Run bridged:

```text
tart run "$VM" --net-bridged=en0
tart run "$VM" --net-bridged="Wi-Fi"
```

Use bridged networking when the guest must behave like a LAN peer:

- Testing inbound callbacks to a macOS or Linux service inside the VM.
- Validating mDNS, Bonjour, AirDrop-adjacent discovery assumptions, or LAN scan
  behavior.
- Reproducing target allowlists that key on local subnet behavior.
- Running a browser or proxy VM that other lab devices must reach directly.

Use host-only when the guest should talk only to the host-side lab:

```text
tart run "$VM" --net-host
```

Host-only is a good default for local exploit repros where internet access would
pollute evidence, trigger auto-updates, or contact third-party services.

## Linux Guests

Tart Linux guests are useful for browser matrices, command-line tooling, and
arm64 parity testing on the same Mac host.

Create:

```text
tart create --linux ubuntu --disk-size 80
tart run --disk=ubuntu-24.04.2-live-server-arm64.iso:ro ubuntu
```

After install:

```text
sudo apt update
sudo apt install -y openssh-server spice-vdagent
sudo systemctl enable --now ssh
```

Shared dirs require manual mounting unless you configure fstab:

```text
sudo mkdir -p /mnt/shared
sudo mount -t virtiofs com.apple.virtio-fs.automount /mnt/shared
```

Do not attach `amd64` installer media by accident. Tart source explicitly checks
for `-amd64.iso` and rejects likely x86 media. Use arm64/aarch64 images.

Linux screenshots and browser geometry may differ from macOS because display
unit defaults and HiDPI behavior differ. Set display resolution explicitly:

```text
tart set ubuntu --display 1920x1080px
```

## Rosetta in Linux Guests

Rosetta sharing is for Linux guests on Apple Silicon hosts when x86_64 Linux
binaries must run during a test.

Host setup:

```text
softwareupdate --install-rosetta
```

Run with a Rosetta share tag:

```text
tart run ubuntu --rosetta=rosetta
```

The guest still needs the Linux-side Rosetta configuration from Apple's
Virtualization.Framework documentation. Treat Rosetta-enabled results as a
compatibility signal, not as proof of native x86_64 Linux behavior.

## Nested Virtualization

Enable only when the test requires a VM inside the Tart VM:

```text
tart run "$VM" --nested
```

Constraints:

- Host macOS must support nested virtualization.
- Current Tart source rejects nested mode on hosts older than macOS 15.
- Supported Apple hardware is required; current checks require M3-or-newer
  support.
- Nested mode can change timing, entropy, and hardware enumeration enough to
  affect exploitability.

Use a dedicated base image for nested workflows so normal DAST runs do not
inherit nested-only changes.

## Registry and Image Promotion

Tart uses OCI registries for VM images, but Tart images are not Docker
containers. Do not expect `docker pull` images to boot in Tart.

Login:

```text
tart login ghcr.io
```

Push a local VM under one or more tags:

```text
tart push tahoe-base \
  ghcr.io/acme/dast/tahoe-base:2026-06-16 \
  ghcr.io/acme/dast/tahoe-base:stable
```

Pull:

```text
tart pull ghcr.io/acme/dast/tahoe-base:2026-06-16
```

Clone remote:

```text
tart clone ghcr.io/acme/dast/tahoe-base:2026-06-16 tahoe-base
```

Credential sources:

- `tart login` stores credentials in Keychain.
- Docker credential helpers from `~/.docker/config.json` can be used.
- `TART_REGISTRY_USERNAME` and `TART_REGISTRY_PASSWORD` override authorization.
- `TART_REGISTRY_HOSTNAME` scopes those overrides to a registry host.

Evidence image promotion pattern:

```text
tart clone ghcr.io/acme/dast/tahoe-base:2026-06-16 case-001
# reproduce, collect artifacts, stop the VM
tart push case-001 ghcr.io/acme/dast/cases/case-001:proof
```

Do not push dirty evidence images to a broad `latest` or `stable` tag. Preserve
case images under case-specific names.

## Packer and CI

Use Packer when the base image matters enough to rebuild predictably. Keep
manual GUI setup out of the critical path when possible.

Minimal Tart Packer skeleton:

```hcl
packer {
  required_plugins {
    tart = {
      version = ">= 0.5.3"
      source  = "github.com/cirruslabs/tart"
    }
  }
}

source "tart-cli" "tart" {
  vm_base_name = "ghcr.io/cirruslabs/macos-tahoe-base:latest"
  vm_name      = "my-custom-tahoe"
  cpu_count    = 4
  memory_gb    = 8
  disk_size_gb = 70
  ssh_username = "admin"
  ssh_password = "admin"
  ssh_timeout  = "120s"
}

build {
  sources = ["source.tart-cli.tart"]

  provisioner "shell" {
    inline = [
      "sudo mdutil -a -i off"
    ]
  }
}
```

For CI, keep three layers separate:

- Image building: Packer or a controlled manual build.
- VM execution: Tart clone/run/stop/delete.
- Job orchestration and artifact retrieval: Cirrus CLI, GitLab runner executor,
  or the CI system's wrapper.

Do not make the CI runner mutate the shared base. Clone per job.

## DAST Repro Patterns

Clean browser repro:

```text
BASE=tahoe-browser-primed
CASE="browser-$(date +%Y%m%d-%H%M%S)"

tart clone "$BASE" "$CASE"
tart set "$CASE" --random-mac --random-serial
tart run "$CASE" \
  --net-softnet \
  --dir=evidence:"$PWD/evidence/$CASE"
```

Host-only exploit lab:

```text
tart clone tahoe-base local-only
tart run local-only \
  --net-host \
  --dir=payloads:"$PWD/payloads":ro \
  --dir=evidence:"$PWD/evidence/local-only"
```

Bridged callback lab:

```text
tart clone tahoe-base bridged-callback
tart run bridged-callback --net-bridged=en0
tart ip bridged-callback
```

Read-only malicious disk replay:

```text
tart clone tahoe-base disk-replay
tart run disk-replay \
  --disk="$PWD/sample.raw:ro" \
  --dir=evidence:"$PWD/evidence/disk-replay"
```

Default-deny egress with a single target:

```text
tart clone tahoe-base egress-proof
tart run egress-proof \
  --net-softnet-block=0.0.0.0/0 \
  --net-softnet-allow=203.0.113.10/32 \
  --dir=evidence:"$PWD/evidence/egress-proof"
```

Xcode-bearing macOS app test:

```text
tart clone ghcr.io/cirruslabs/macos-sequoia-xcode:latest xcode-case
tart set xcode-case --cpu 6 --memory 16384 --disk-size 120
tart run xcode-case --dir=project:"$PWD/project":ro --dir=evidence:"$PWD/evidence/xcode-case"
```

Use Tart for iOS-adjacent host tooling, not for physical iOS claims. If a finding
depends on iOS entitlements, keychain accessibility classes, app container
protections, push notification behavior, radio/network state, or hardware-backed
identity, validate with the physical iOS workflow instead.

## Evidence Capture

Create a per-case evidence directory before the run:

```text
CASE="case-$(date +%Y%m%d-%H%M%S)"
mkdir -p "evidence/$CASE"
```

Capture host and Tart facts:

```text
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  sw_vers
  uname -a
  tart --version
  tart list
} > "evidence/$CASE/host.txt"
```

Capture VM IP and launch mode:

```text
tart ip "$CASE" > "evidence/$CASE/ip.txt"
printf '%s\n' \
  "base=$BASE" \
  "vm=$CASE" \
  "network=softnet block 0.0.0.0/0 allow 203.0.113.10/32" \
  "dirs=seeds:ro evidence:rw" \
  > "evidence/$CASE/tart-run.txt"
```

Capture macOS guest facts:

```text
ssh admin@$(tart ip "$CASE") '
  sw_vers
  uname -a
  scutil --get ComputerName || true
  system_profiler SPSoftwareDataType SPHardwareDataType
' > "evidence/$CASE/guest-system.txt"
```

Capture Linux guest facts:

```text
ssh admin@$(tart ip "$CASE") '
  uname -a
  cat /etc/os-release
  ip addr
  ip route
' > "evidence/$CASE/guest-system.txt"
```

Pull files through SSH when shared dirs are not mounted:

```text
scp -r admin@$(tart ip "$CASE"):~/Library/Logs "evidence/$CASE/guest-logs"
```

Screen capture options:

```text
screencapture -x "evidence/$CASE/host-window.png"
ssh admin@$(tart ip "$CASE") screencapture -x /tmp/guest.png
scp admin@$(tart ip "$CASE"):/tmp/guest.png "evidence/$CASE/guest.png"
```

For GUI-heavy repros, record:

- Base image reference and tag.
- Clone name.
- Tart version.
- Host macOS version and hardware class.
- VM CPU, memory, display, disk size.
- Network mode and CIDR exceptions.
- Shared dirs and whether each was read-only.
- Whether clipboard, audio, pointer, keyboard, or trackpad were disabled.
- Whether VNC, recovery, nested, Rosetta, or suspendable mode was used.

## Failure Modes

`tart: command not found`

Use Homebrew install path or the app-bundle binary from the release archive:

```text
brew install cirruslabs/cli/tart
./tart.app/Contents/MacOS/tart --version
```

Manual install works only through `tart.app/Contents/MacOS/tart`

The app bundle carries the provisioning profile. A copied bare binary can fail
with privilege or entitlement problems.

`tart ip` returns nothing

Check that the guest booted, networking is enabled, SSH or guest services are
ready, and the selected network mode gives the host a path to the guest.

```text
tart run "$VM"
tart ip "$VM"
```

SSH refused

Enable Remote Login in macOS guests or install and start `openssh-server` in
Linux guests. Check that a firewall inside the guest is not blocking port 22.

Directory is not visible in macOS

Check host and guest macOS versions. macOS guest auto-mount requires macOS 13 or
newer. Default path is:

```text
/Volumes/My Shared Files
```

Directory is not visible in Linux

Mount virtiofs manually:

```text
sudo mkdir -p /mnt/shared
sudo mount -t virtiofs com.apple.virtio-fs.automount /mnt/shared
```

Multiple shared directories collapse into one

Use unique names for each `--dir` share. Reusing a name leaves only the last one.

Block device attach fails with busy or permission errors

Unmount the disk first or avoid block-device attachment:

```text
diskutil unmountDisk /dev/diskX
diskutil umount /dev/diskXsY
```

Avoid `sudo chown $USER /dev/diskX` unless the host-user trust model allows every
process under that user to access the disk.

Network mode validation fails

Use only one of bridged, Softnet, or host-only:

```text
tart run "$VM" --net-bridged=en0
tart run "$VM" --net-softnet
tart run "$VM" --net-host
```

Softnet port forwarding cannot be reached from the host

That is expected. Connect from another machine on the local network or use
normal host-to-guest access such as SSH to `tart ip`.

Nested virtualization rejected

Check host macOS and hardware. Current Tart checks require macOS 15 or newer and
supported Apple hardware.

Disk resize did not shrink

`tart set --disk-size` only increases disk size. Rebuild from a smaller base if
you need a smaller artifact.

Clone identity collides

Randomize MAC and macOS serial:

```text
tart set "$VM" --random-mac --random-serial
```

Tart may also regenerate a MAC when it detects a running VM with the same MAC.
Do not rely on that implicit behavior for reproducibility; set identity
explicitly in automation.

`latest` image changed

That is normal. Pin tags for cases and record image names. Use private registry
promotion for evidence-bearing bases.

## Evidence Checklist

Before run:

- Base image name and tag recorded.
- Clone name recorded.
- Tart version recorded.
- Host macOS version and architecture recorded.
- VM CPU, memory, display, disk size recorded.
- Network mode chosen and documented.
- Shared dirs named, with read-only/writeable state documented.
- Credentials rotated or explicitly accepted for the lab scope.

During run:

- `tart ip` captured.
- Guest OS version captured.
- Relevant logs written to shared evidence dir or pulled by SSH.
- Screenshots or recordings captured when UI state matters.
- Network exceptions, exposed ports, and bridged interface recorded.

After run:

- VM stopped.
- Evidence directory preserved.
- Dirty repro clone either pushed under a case-specific tag or deleted.
- Base image left unmodified.
- Any private credentials, tokens, or target data removed from shareable images.

## References

- [Tart Quick Start](https://tart.run/quick-start/)
- [Tart Packer Integration](https://tart.run/integrations/packer/)
- [Tart Cirrus CLI Integration](https://tart.run/integrations/cirrus-cli/)
- [Tart GitLab Runner Executor](https://tart.run/integrations/gitlab-runner/)
- [Tart source repository](https://github.com/cirruslabs/tart)
