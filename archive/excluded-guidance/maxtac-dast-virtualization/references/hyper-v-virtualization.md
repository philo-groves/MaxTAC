# Hyper-V Virtualization

Use Hyper-V for reproducible Windows and Linux virtual machines on Windows
hosts. For DAST work, treat it as a controllable desktop/server OS lab with
strong host-side automation and practical network isolation. Do not treat a VM
as equivalent to physical Windows hardware, physical TPM-backed identity, USB
device behavior, corporate endpoint management, or mobile-device testing.

Run most commands from an elevated PowerShell session on the Hyper-V host unless
the command explicitly targets the guest through PowerShell Direct, SSH, or
another guest channel.

## Contents

- [Quick Commands](#quick-commands)
- [Host and Feature Probes](#host-and-feature-probes)
- [Host Boundaries](#host-boundaries)
- [VM Creation](#vm-creation)
- [Generation, Firmware, Secure Boot, and TPM](#generation-firmware-secure-boot-and-tpm)
- [CPU and Memory](#cpu-and-memory)
- [VHD and Differencing Disk Strategy](#vhd-and-differencing-disk-strategy)
- [Checkpoints](#checkpoints)
- [Export, Import, and Case Images](#export-import-and-case-images)
- [Guest Execution](#guest-execution)
- [File Transfer](#file-transfer)
- [Virtual Switches](#virtual-switches)
- [Custom NAT Networks](#custom-nat-networks)
- [Port Exposure](#port-exposure)
- [Network ACLs, Guards, VLANs, and Mirroring](#network-acls-guards-vlans-and-mirroring)
- [Nested Virtualization](#nested-virtualization)
- [Linux Guests](#linux-guests)
- [Console, Enhanced Session, and Serial Debug](#console-enhanced-session-and-serial-debug)
- [Integration Services](#integration-services)
- [DAST Repro Patterns](#dast-repro-patterns)
- [Evidence Capture](#evidence-capture)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Host sanity:

```powershell
Get-ComputerInfo -Property OsName,OsVersion,WindowsProductName,HyperVisorPresent,CsHypervisorPresent
systeminfo
Get-Command -Module Hyper-V | Select-Object -First 20 Name
Get-VMHost | Format-List *
Get-VMHostSupportedVersion
Get-VMSwitch
Get-NetNat
```

Enable Hyper-V on Windows client:

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
Restart-Computer
```

Enable Hyper-V on Windows Server:

```powershell
Install-WindowsFeature -Name Hyper-V -IncludeManagementTools -Restart
```

Create a deterministic internal NAT lab:

```powershell
New-VMSwitch -Name DAST-NAT -SwitchType Internal
New-NetIPAddress -InterfaceAlias "vEthernet (DAST-NAT)" -IPAddress 192.168.250.1 -PrefixLength 24
New-NetNat -Name DAST-NAT -InternalIPInterfaceAddressPrefix 192.168.250.0/24
```

Create a Windows VM from ISO:

```powershell
$VM = "win-dast-base"
$Root = "D:\HyperV\$VM"

New-Item -ItemType Directory -Force -Path $Root | Out-Null
New-VM -Name $VM -Generation 2 -MemoryStartupBytes 4GB `
  -NewVHDPath "$Root\$VM.vhdx" -NewVHDSizeBytes 80GB `
  -Path $Root -SwitchName DAST-NAT
Set-VMProcessor -VMName $VM -Count 4
Set-VMMemory -VMName $VM -DynamicMemoryEnabled $false
Set-VM -Name $VM -AutomaticCheckpointsEnabled $false
Add-VMDvdDrive -VMName $VM -Path "D:\ISO\Windows.iso"
Set-VMFirmware -VMName $VM -FirstBootDevice (Get-VMDvdDrive -VMName $VM)
Start-VM -Name $VM
vmconnect.exe localhost $VM
```

Create a disposable case VM from a read-only parent disk:

```powershell
$Base = "D:\HyperV\Base\windows-clean.vhdx"
$Case = "case-$(Get-Date -Format yyyyMMdd-HHmmss)"
$CaseRoot = "D:\HyperV\$Case"

New-Item -ItemType Directory -Force -Path $CaseRoot | Out-Null
New-VHD -Path "$CaseRoot\$Case.vhdx" -ParentPath $Base -Differencing
New-VM -Name $Case -Generation 2 -MemoryStartupBytes 4GB `
  -VHDPath "$CaseRoot\$Case.vhdx" -Path $CaseRoot -SwitchName DAST-NAT
Set-VMProcessor -VMName $Case -Count 4
Set-VM -Name $Case -AutomaticCheckpointsEnabled $false -CheckpointType Standard
Start-VM -Name $Case
```

Checkpoint and revert:

```powershell
Set-VM -Name $VM -CheckpointType Standard
Checkpoint-VM -Name $VM -SnapshotName clean-before-repro
Restore-VMCheckpoint -VMName $VM -Name clean-before-repro -Confirm:$false
Remove-VMCheckpoint -VMName $VM -Name clean-before-repro
```

Run commands inside a Windows guest without network:

```powershell
$Cred = Get-Credential
Invoke-Command -VMName $VM -Credential $Cred -ScriptBlock {
  hostname
  Get-ComputerInfo -Property OsName,OsVersion,WindowsProductName
}
```

Copy files through PowerShell Direct:

```powershell
$S = New-PSSession -VMName $VM -Credential $Cred
Copy-Item -ToSession $S -Path ".\seed.zip" -Destination "C:\repro\seed.zip"
Copy-Item -FromSession $S -Path "C:\repro\evidence" -Destination ".\evidence" -Recurse
Remove-PSSession $S
```

Expose a NAT guest service:

```powershell
Add-NetNatStaticMapping -NatName DAST-NAT -Protocol TCP `
  -ExternalIPAddress 0.0.0.0 -ExternalPort 8443 `
  -InternalIPAddress 192.168.250.10 -InternalPort 443
```

## Host and Feature Probes

Record host capability before trusting a repro. Hyper-V behavior is host-version
and hardware dependent.

```powershell
Get-ComputerInfo -Property OsName,OsVersion,WindowsProductName,HyperVisorPresent,CsHypervisorPresent
systeminfo
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V*
Get-Command -Module Hyper-V | Sort-Object Name
Get-VMHost | Format-List *
Get-VMHostSupportedVersion
```

Requirements that matter in practice:

- Windows 10/11 Pro or Enterprise for client Hyper-V. Home editions cannot
  install the Hyper-V role.
- 64-bit CPU, SLAT, VM Monitor Mode Extensions, and enough memory for the host
  and guests.
- Firmware virtualization must be enabled.
- Hyper-V conflicts with some older third-party virtualization assumptions. If
  another hypervisor stack is involved, record it.
- Nested virtualization has additional host CPU, OS, and VM configuration
  version requirements.

Check the module shape on the actual host:

```powershell
Get-Command Checkpoint-VM,Get-VMCheckpoint,Restore-VMCheckpoint,Restore-VMSnapshot
Get-Command Set-VMFirmware,Enable-VMTPM,Set-VMKeyProtector
Get-Command Add-NetNatStaticMapping,Add-VMNetworkAdapterExtendedAcl
```

The Hyper-V module still exposes older `Snapshot` cmdlets, and current docs also
use checkpoint aliases such as `Get-VMCheckpoint`. In scripts, prefer the command
names present on the host and avoid mixing both names in one pipeline.

## Host Boundaries

Hyper-V is a security boundary between a normal guest workload and the host, but
Hyper-V administrators are extremely powerful from the guest's perspective.

Assume a Hyper-V administrator can:

- Start, stop, checkpoint, export, and restore the VM.
- Attach or mount virtual disks.
- Access the VM console.
- Use PowerShell Direct against supported Windows guests with guest credentials.
- Change network attachment, ACLs, memory, CPU, and integration services.

Do not use VM behavior as proof that:

- A physical TPM, Secure Enclave-like hardware, USB controller, GPU, Wi-Fi radio,
  or Bluetooth stack behaves the same way.
- Corporate EDR, MDM, BitLocker, credential guard, Windows Hello, or device
  identity behaves the same way as a managed physical endpoint.
- Host firewall logs capture NATed guest traffic the same way they capture host
  process traffic.

For hostile samples, separate the Hyper-V host from normal workstations. Enhanced
Session, clipboard, shared drives, PowerShell Direct, and guest services are all
convenience bridges that can contaminate evidence or leak host data.

## VM Creation

Use Generation 2 for modern Windows and Linux guests unless you need BIOS
compatibility for an old OS or bootloader.

New VM with a new VHDX:

```powershell
$VM = "win-lab"
$Root = "D:\HyperV\$VM"

New-Item -ItemType Directory -Force -Path $Root | Out-Null
New-VM -Name $VM -Generation 2 -MemoryStartupBytes 4GB `
  -NewVHDPath "$Root\$VM.vhdx" -NewVHDSizeBytes 80GB `
  -Path $Root -SwitchName DAST-NAT
```

New VM with an existing VHDX:

```powershell
New-VM -Name "win-from-vhd" -Generation 2 -MemoryStartupBytes 4GB `
  -VHDPath "D:\Images\win-base.vhdx" -Path "D:\HyperV\win-from-vhd" `
  -SwitchName DAST-NAT
```

Install from ISO:

```powershell
Add-VMDvdDrive -VMName $VM -Path "D:\ISO\installer.iso"
Set-VMFirmware -VMName $VM -FirstBootDevice (Get-VMDvdDrive -VMName $VM)
Start-VM -Name $VM
vmconnect.exe localhost $VM
```

Disable automatic checkpoints in lab automation. They are useful for casual
desktop Hyper-V, but they create unexpected `.avhdx` state and can hide the
actual mutation boundary of a repro.

```powershell
Set-VM -Name $VM -AutomaticCheckpointsEnabled $false
```

Use explicit paths. Hyper-V defaults often land under
`C:\ProgramData\Microsoft\Windows\Hyper-V` and
`C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks`, which is awkward for
case retention and disk space accounting.

## Generation, Firmware, Secure Boot, and TPM

Generation choice affects boot, firmware, and device model:

- Generation 2: UEFI, Secure Boot, virtual TPM support, modern Windows/Linux.
- Generation 1: legacy BIOS compatibility and old OS installers.

Inspect firmware:

```powershell
Get-VMFirmware -VMName $VM | Format-List *
```

Secure Boot for Windows:

```powershell
Set-VMFirmware -VMName $VM -EnableSecureBoot On -SecureBootTemplate MicrosoftWindows
```

Secure Boot for many Linux guests:

```powershell
Set-VMFirmware -VMName $VM -EnableSecureBoot On `
  -SecureBootTemplate MicrosoftUEFICertificateAuthority
```

Disable Secure Boot for unsigned kernels, custom bootloaders, or forensics media:

```powershell
Set-VMFirmware -VMName $VM -EnableSecureBoot Off
```

List host Secure Boot templates:

```powershell
Get-VMHost | Select-Object -ExpandProperty SecureBootTemplates
```

Enable a virtual TPM for Windows 11-style guests or tests that depend on TPM
presence:

```powershell
Set-VMKeyProtector -VMName $VM -NewLocalKeyProtector
Enable-VMTPM -VMName $VM
Get-VMKeyProtector -VMName $VM
```

Virtual TPM and local key protectors are host-bound enough to affect export,
import, and evidence portability. Record vTPM state. If a finding depends on TPM
attestation, Windows Hello, BitLocker recovery, device identity, or measured
boot, retest on the target class of physical hardware.

## CPU and Memory

Set CPU and memory explicitly. Defaults vary by creation path and are often too
small for browser-heavy DAST.

```powershell
Set-VMProcessor -VMName $VM -Count 4
Set-VMMemory -VMName $VM -DynamicMemoryEnabled $false -StartupBytes 8GB
```

Dynamic memory is convenient for dense labs but can change timing,
out-of-memory behavior, browser process pressure, and performance-sensitive
vulnerabilities.

For deterministic reproduction:

```powershell
Set-VMMemory -VMName $VM -DynamicMemoryEnabled $false -StartupBytes 8GB
```

For high-density non-timing-sensitive scans:

```powershell
Set-VMMemory -VMName $VM -DynamicMemoryEnabled $true `
  -MinimumBytes 2GB -StartupBytes 4GB -MaximumBytes 8GB
```

Inspect runtime state:

```powershell
Get-VM -Name $VM | Select-Object Name,State,CPUUsage,MemoryAssigned,Uptime,Status,Version
Measure-VM -VMName $VM
```

## VHD and Differencing Disk Strategy

Use VHDX, not VHD, unless an old toolchain requires VHD.

Create a base disk, patch it, shut it down cleanly, then treat it as immutable.
Create per-case differencing disks from that parent:

```powershell
$Parent = "D:\HyperV\Base\windows-clean.vhdx"
$Child = "D:\HyperV\case-001\case-001.vhdx"

New-VHD -Path $Child -ParentPath $Parent -Differencing
New-VM -Name case-001 -Generation 2 -MemoryStartupBytes 4GB `
  -VHDPath $Child -Path "D:\HyperV\case-001" -SwitchName DAST-NAT
```

The parent disk must not be modified after children exist. Changing the parent
can invalidate the evidence chain for every child. Make the parent read-only at
the filesystem level if multiple operators use the lab.

```powershell
Set-ItemProperty -Path $Parent -Name IsReadOnly -Value $true
```

Mount disks read-only for offline evidence inspection:

```powershell
Mount-VHD -Path "D:\HyperV\case-001\case-001.vhdx" -ReadOnly
Get-Disk | Where-Object IsOffline -eq $false
Dismount-VHD -Path "D:\HyperV\case-001\case-001.vhdx"
```

Resize a VHDX when the guest needs more space:

```powershell
Resize-VHD -Path "D:\HyperV\case-001\case-001.vhdx" -SizeBytes 120GB
```

Compaction is evidence-affecting disk maintenance. Do it on base images before
case use, not after exploitation unless you record it:

```powershell
Optimize-VHD -Path "D:\HyperV\Base\windows-clean.vhdx" -Mode Full
```

Avoid expanding or editing VHDX files that have checkpoints. Checkpoint chains
use `.avhdx` differencing disks. Modify and merge through Hyper-V cmdlets, not
manual file operations.

## Checkpoints

Use checkpoints for short-lived DAST state boundaries, not for backup.

Set checkpoint type:

```powershell
Set-VM -Name $VM -CheckpointType Standard
Set-VM -Name $VM -CheckpointType Production
Set-VM -Name $VM -CheckpointType ProductionOnly
Set-VM -Name $VM -CheckpointType Disabled
```

Practical choice:

- `Standard`: captures disk plus VM memory/device state. Best for exploit
  repros where an open process, browser tab, debugger, or crash state matters.
- `Production`: uses guest-supported quiescing. Better for data consistency but
  does not capture VM memory state.
- `ProductionOnly`: fail instead of silently falling back to Standard.
- `Disabled`: use for bases or workloads where checkpoint state would pollute
  evidence.

Create and list:

```powershell
Checkpoint-VM -Name $VM -SnapshotName "clean-before-repro"
Get-VMCheckpoint -VMName $VM
Get-VMSnapshot -VMName $VM
```

Restore:

```powershell
Restore-VMCheckpoint -VMName $VM -Name "clean-before-repro" -Confirm:$false
```

Remove:

```powershell
Remove-VMCheckpoint -VMName $VM -Name "clean-before-repro"
```

Export a checkpoint as a case image:

```powershell
Export-VMCheckpoint -VMName $VM -Name "proof-state" -Path "D:\Exports\case-001"
```

Checkpoint cautions:

- Do not delete `.avhdx` files manually. Use `Remove-VMCheckpoint`.
- Deleting a checkpoint triggers merge work. Wait for merges before copying or
  archiving the VM.
- Standard checkpoints can preserve secrets in memory.
- Production checkpoint restore may leave the VM off. Start it intentionally and
  record the restore/start boundary.
- Checkpoints can hurt disk performance and consume host storage quickly.

For clean repeatability, prefer this loop:

```powershell
Stop-VM -Name $VM -TurnOff
Restore-VMCheckpoint -VMName $VM -Name clean -Confirm:$false
Start-VM -Name $VM
```

Use `-TurnOff` only for disposable lab state where guest shutdown consistency is
not needed.

## Export, Import, and Case Images

Export a VM for evidence or migration:

```powershell
Export-VM -Name $VM -Path "D:\Exports\$VM"
```

For running VMs, choose live-state capture intentionally:

```powershell
Export-VM -Name $VM -Path "D:\Exports\$VM" -CaptureLiveState CaptureSavedState
Export-VM -Name $VM -Path "D:\Exports\$VM" -CaptureLiveState CaptureDataConsistentState
Export-VM -Name $VM -Path "D:\Exports\$VM" -CaptureLiveState CaptureCrashConsistentState
```

Import as a new copy:

```powershell
$Config = Get-ChildItem "D:\Exports\case-001" -Recurse -Filter *.vmcx | Select-Object -First 1
Import-VM -Path $Config.FullName -Copy -GenerateNewId
```

Check import compatibility before assuming a case image will run on another host:

```powershell
$Report = Compare-VM -Path $Config.FullName
$Report.Incompatibilities
```

Use `-GenerateNewId` when importing multiple copies of the same exported VM. Keep
the original ID only when identity continuity is part of the evidence.

Record exported folder contents. VM exports normally include configuration,
snapshots/checkpoints, and virtual hard disks under separate folders.

## Guest Execution

PowerShell Direct is the best host-to-Windows-guest primitive when the guest is
local and supported. It works regardless of guest network configuration and
remote-management settings.

Requirements:

- Host runs Windows 10 / Windows Server 2016 or newer with Hyper-V.
- Guest runs Windows 10 / Windows Server 2016 or newer.
- VM is local to the host, turned on, and has at least one configured user.
- Host user is a Hyper-V administrator.
- Caller supplies valid guest credentials.

Interactive:

```powershell
Enter-PSSession -VMName $VM -Credential (Get-Credential)
hostname
Exit-PSSession
```

Single command:

```powershell
Invoke-Command -VMName $VM -Credential $Cred -ScriptBlock {
  Get-Date -Format o
  hostname
  ipconfig /all
}
```

Run a host script inside the guest:

```powershell
Invoke-Command -VMName $VM -Credential $Cred -FilePath ".\guest-setup.ps1"
```

Persistent session:

```powershell
$S = New-PSSession -VMName $VM -Credential $Cred
Invoke-Command -Session $S -ScriptBlock { New-Item -ItemType Directory -Force C:\repro }
Remove-PSSession $S
```

Security note: Hyper-V administrator access does not imply guest administrator
access. You still need guest credentials. Do not cite PowerShell Direct output as
something a remote attacker could do unless the attack path has equivalent guest
privileges.

For Linux guests, use SSH or console automation. PowerShell Direct is not the
Linux path.

## File Transfer

Use PowerShell Direct sessions for bidirectional file movement with supported
Windows guests:

```powershell
$S = New-PSSession -VMName $VM -Credential $Cred
Copy-Item -ToSession $S -Path ".\payloads\seed.zip" -Destination "C:\repro\seed.zip"
Copy-Item -FromSession $S -Path "C:\repro\evidence" -Destination ".\evidence\$VM" -Recurse
Remove-PSSession $S
```

Use `Copy-VMFile` for host-to-guest file injection when the Guest Service
Interface is enabled:

```powershell
Enable-VMIntegrationService -VMName $VM -Name "Guest Service Interface"
Copy-VMFile -Name $VM -FileSource Host `
  -SourcePath ".\seed.zip" `
  -DestinationPath "C:\repro\seed.zip" `
  -CreateFullPath
```

Check integration services:

```powershell
Get-VMIntegrationService -VMName $VM | Format-Table Name,Enabled,PrimaryStatusDescription
```

Do not enable host-to-guest file bridges by default for hostile-sample VMs. Use
read-only ISOs, disposable VHDs, or a one-way staging pattern when sample escape
or evidence contamination matters.

Create a read-only ISO for sample ingress:

```powershell
# Use oscdimg or another controlled ISO builder, then attach read-only media.
Add-VMDvdDrive -VMName $VM -Path "D:\Cases\case-001\payloads.iso"
```

## Virtual Switches

Switch types:

- `External`: attaches to a physical adapter; guests can appear on the LAN.
- `Internal`: host and guests can communicate; no external connectivity unless
  NAT/routing is added.
- `Private`: guests on the switch can communicate with each other; host is not
  connected.

List:

```powershell
Get-VMSwitch | Format-Table Name,SwitchType,NetAdapterInterfaceDescription
Get-VMNetworkAdapter -VMName $VM | Format-List *
```

Create external:

```powershell
New-VMSwitch -Name DAST-External -NetAdapterName "Ethernet" -AllowManagementOS $true
```

Create internal:

```powershell
New-VMSwitch -Name DAST-Internal -SwitchType Internal
```

Create private:

```powershell
New-VMSwitch -Name DAST-Private -SwitchType Private
```

Attach a VM:

```powershell
Connect-VMNetworkAdapter -VMName $VM -SwitchName DAST-NAT
```

Add a second NIC for separate management and target traffic:

```powershell
Add-VMNetworkAdapter -VMName $VM -Name mgmt -SwitchName DAST-NAT
Add-VMNetworkAdapter -VMName $VM -Name target -SwitchName DAST-Private
```

Avoid the `Default Switch` for evidence. It is useful for quick internet access,
but its subnet, NAT behavior, and Windows-managed lifecycle are not ideal for
reproducible test cases.

## Custom NAT Networks

Use a custom internal switch plus WinNAT for reproducible outbound internet and
host-to-guest access.

Create:

```powershell
New-VMSwitch -Name DAST-NAT -SwitchType Internal
New-NetIPAddress -InterfaceAlias "vEthernet (DAST-NAT)" `
  -IPAddress 192.168.250.1 -PrefixLength 24
New-NetNat -Name DAST-NAT -InternalIPInterfaceAddressPrefix 192.168.250.0/24
```

Attach:

```powershell
Connect-VMNetworkAdapter -VMName $VM -SwitchName DAST-NAT
```

Set guest networking manually unless you provide DHCP on the internal network.
For a Windows guest, first identify the guest interface alias, then assign an
address:

```powershell
Invoke-Command -VMName $VM -Credential $Cred -ScriptBlock {
  Get-NetAdapter | Format-Table Name,Status,MacAddress
  New-NetIPAddress -InterfaceAlias "Ethernet" `
    -IPAddress 192.168.250.10 -PrefixLength 24 -DefaultGateway 192.168.250.1
  Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 1.1.1.1,8.8.8.8
}
```

Inspect NAT:

```powershell
Get-NetNat
Get-NetNatSession | Sort-Object CreationTime -Descending | Select-Object -First 20
Get-NetIPAddress -InterfaceAlias "vEthernet (DAST-NAT)"
```

WinNAT limitation: design around one internal NAT subnet prefix per host. Docker,
Windows containers, WSL, and other tools can create NATs and HNS networks. Before
creating a DAST NAT, inspect the host:

```powershell
Get-NetNat
Get-VMSwitch
```

Do not casually run broad cleanup on a shared host. If you must remove a lab NAT,
target the specific NAT and switch:

```powershell
Remove-NetNat -Name DAST-NAT -Confirm:$false
Remove-VMSwitch -Name DAST-NAT -Force
```

If Docker/containers share the host, avoid stealing their NAT prefix. Pick a lab
prefix that does not overlap container networks, VPN routes, or corporate LANs.

## Port Exposure

With an external switch, expose services by binding inside the guest and opening
guest firewall rules. The guest is a LAN peer.

With WinNAT, use static mappings:

```powershell
Add-NetNatStaticMapping -NatName DAST-NAT -Protocol TCP `
  -ExternalIPAddress 0.0.0.0 -ExternalPort 8443 `
  -InternalIPAddress 192.168.250.10 -InternalPort 443
```

List mappings:

```powershell
Get-NetNatStaticMapping -NatName DAST-NAT
```

Remove a mapping:

```powershell
Get-NetNatStaticMapping -NatName DAST-NAT |
  Where-Object ExternalPort -eq 8443 |
  Remove-NetNatStaticMapping -Confirm:$false
```

When a forwarded port is unreachable:

- Confirm the guest static IP is correct.
- Confirm the guest service listens on the internal IP or `0.0.0.0`.
- Confirm the guest firewall allows the internal port.
- Confirm the host firewall allows the external port.
- Confirm no other service already owns the host external port.
- Check `Get-NetNatSession`.

For DAST evidence, record whether the target accessed the guest through external
switch addressing, WinNAT static mapping, or a host-side reverse proxy.

## Network ACLs, Guards, VLANs, and Mirroring

Use vSwitch-level controls to reduce accidental network reachability. Do not
confuse them with guest firewall policy or target-side authorization.

DHCP and router guard:

```powershell
Set-VMNetworkAdapter -VMName $VM -DhcpGuard On -RouterGuard On
```

MAC spoofing:

```powershell
Set-VMNetworkAdapter -VMName $VM -MacAddressSpoofing On
```

Enable MAC spoofing only when the guest must bridge, route, run nested VMs, or
perform tests that require non-default source MAC behavior. Otherwise leave it
off to reduce lateral-noise risk.

Basic ACLs:

```powershell
Add-VMNetworkAdapterAcl -VMName $VM -Direction Outbound -Action Deny `
  -RemoteIPAddress 169.254.169.254
Get-VMNetworkAdapterAcl -VMName $VM
Remove-VMNetworkAdapterAcl -VMName $VM -Direction Outbound -Action Deny `
  -RemoteIPAddress 169.254.169.254
```

Extended ACLs can express ports and protocols:

```powershell
Add-VMNetworkAdapterExtendedAcl -VMName $VM -Direction Outbound `
  -Action Deny -RemoteIPAddress 10.0.0.0/8 -Protocol TCP `
  -RemotePort 445 -Weight 100
Get-VMNetworkAdapterExtendedAcl -VMName $VM
```

VLAN access mode:

```powershell
Set-VMNetworkAdapterVlan -VMName $VM -Access -VlanId 121
```

VLAN trunk mode:

```powershell
Set-VMNetworkAdapterVlan -VMName $VM -Trunk -AllowedVlanIdList 1-100 -NativeVlanId 10
```

Port mirroring for packet capture:

```powershell
Set-VMNetworkAdapter -VMName target-vm -PortMirroring Source
Set-VMNetworkAdapter -VMName capture-vm -PortMirroring Destination
```

Capture inside `capture-vm` with Wireshark, pktmon, tcpdump, or the guest tool
of choice. The capture VM must be on the same virtual switch as the source.

## Nested Virtualization

Enable nested virtualization only for test cases that require Hyper-V, Android
emulators, WSL2, Docker with Hyper-V isolation, or another hypervisor inside the
guest.

Prerequisite-sensitive command:

```powershell
Stop-VM -Name $VM
Set-VMProcessor -VMName $VM -ExposeVirtualizationExtensions $true
Start-VM -Name $VM
```

Disable:

```powershell
Stop-VM -Name $VM
Set-VMProcessor -VMName $VM -ExposeVirtualizationExtensions $false
```

Nested networking choices:

```powershell
Get-VMNetworkAdapter -VMName $VM | Set-VMNetworkAdapter -MacAddressSpoofing On
```

or create NAT inside the level-1 guest:

```powershell
New-VMSwitch -Name VmNAT -SwitchType Internal
New-NetNat -Name LocalNAT -InternalIPInterfaceAddressPrefix 192.168.100.0/24
New-NetIPAddress -InterfaceAlias "vEthernet (VmNAT)" `
  -IPAddress 192.168.100.1 -AddressFamily IPv4 -PrefixLength 24
```

Current Microsoft requirements include:

- Intel VT-x/EPT hosts: Windows Server 2016 or later, or Windows 10 or later,
  with VM configuration version 8.0 or higher.
- AMD EPYC/Ryzen or later hosts: Windows Server 2022 or later, or Windows 11 or
  later, with VM configuration version 9.3 or higher.

Check versions:

```powershell
Get-VM -Name $VM | Select-Object Name,Version,Generation
Get-VMHostSupportedVersion
```

Do not enable nested virtualization on a base image used for ordinary DAST.
Nested mode changes performance, CPU feature exposure, networking, and guest
security posture.

## Linux Guests

Use Generation 2 unless the distro installer requires legacy BIOS.

Common Linux firmware pattern:

```powershell
Set-VMFirmware -VMName $VM -EnableSecureBoot On `
  -SecureBootTemplate MicrosoftUEFICertificateAuthority
```

If the Linux installer or custom kernel fails early, test Secure Boot off:

```powershell
Set-VMFirmware -VMName $VM -EnableSecureBoot Off
```

Install/update Linux Integration Services through the distro kernel packages.
Check Hyper-V drivers inside Linux:

```bash
lsmod | grep '^hv_'
dmesg | grep -i hyper-v
ip addr
```

Use SSH for guest automation:

```powershell
ssh user@192.168.250.20 uname -a
scp .\seed.tgz user@192.168.250.20:/tmp/seed.tgz
scp -r user@192.168.250.20:/tmp/evidence .\evidence\linux-case
```

Production checkpoints for Linux rely on filesystem freeze support. If they
fail, use `ProductionOnly` to detect the failure instead of silently collecting a
Standard checkpoint when consistency matters.

## Console, Enhanced Session, and Serial Debug

Open the VM console:

```powershell
vmconnect.exe localhost $VM
```

Enhanced Session can redirect clipboard, drives, printers, audio, and other host
resources. That is useful for manual UI work and risky for evidence isolation.
Disable or avoid it for hostile samples and secret-bearing tests.

Configure a named-pipe COM port for serial output:

```powershell
Set-VMComPort -VMName $VM -Number 1 -Path "\\.\pipe\$VM-com1"
```

Use serial for bootloader, kernel, or early crash evidence. Configure the guest
OS to emit console output to the serial port.

Inject NMI for hang/crash triage when you intentionally need a dump:

```powershell
Debug-VM -Name $VM -InjectNonMaskableInterrupt -Force
```

Only use `Debug-VM` in controlled debugging workflows. It changes the guest
state and can crash the VM by design.

## Integration Services

List services:

```powershell
Get-VMIntegrationService -VMName $VM |
  Format-Table Name,Enabled,PrimaryStatusDescription
```

Enable file-copy service:

```powershell
Enable-VMIntegrationService -VMName $VM -Name "Guest Service Interface"
```

Disable bridges that pollute isolation:

```powershell
Disable-VMIntegrationService -VMName $VM -Name "Guest Service Interface"
Disable-VMIntegrationService -VMName $VM -Name "Time Synchronization"
```

Time synchronization can ruin time-skew tests, token expiry tests, cache TTL
tests, replay windows, and forensic timeline work. If you disable it, record how
guest time is controlled:

```powershell
Invoke-Command -VMName $VM -Credential $Cred -ScriptBlock {
  Get-Date -Format o
  w32tm /query /status
}
```

Heartbeat, shutdown, VSS, and key-value-pair exchange can be useful for health
checks and orchestration. They are also host/guest signals. Record integration
service state in evidence.

## DAST Repro Patterns

Clean Windows browser repro:

```powershell
$Parent = "D:\HyperV\Base\win-browser-clean.vhdx"
$Case = "browser-$(Get-Date -Format yyyyMMdd-HHmmss)"
$Root = "D:\HyperV\$Case"

New-Item -ItemType Directory -Force -Path $Root | Out-Null
New-VHD -Path "$Root\$Case.vhdx" -ParentPath $Parent -Differencing
New-VM -Name $Case -Generation 2 -MemoryStartupBytes 8GB `
  -VHDPath "$Root\$Case.vhdx" -Path $Root -SwitchName DAST-NAT
Set-VMProcessor -VMName $Case -Count 4
Set-VM -Name $Case -AutomaticCheckpointsEnabled $false -CheckpointType Standard
Start-VM -Name $Case
```

Host-only exploit lab:

```powershell
New-VMSwitch -Name DAST-Private -SwitchType Private
Connect-VMNetworkAdapter -VMName $VM -SwitchName DAST-Private
```

Outbound-only NAT scan lab:

```powershell
Connect-VMNetworkAdapter -VMName $VM -SwitchName DAST-NAT
Set-VMNetworkAdapter -VMName $VM -DhcpGuard On -RouterGuard On
```

LAN peer callback lab:

```powershell
New-VMSwitch -Name DAST-External -NetAdapterName "Ethernet" -AllowManagementOS $true
Connect-VMNetworkAdapter -VMName $VM -SwitchName DAST-External
```

Packet-capture lab:

```powershell
Set-VMNetworkAdapter -VMName target-vm -PortMirroring Source
Set-VMNetworkAdapter -VMName capture-vm -PortMirroring Destination
```

Windows service proof with revert:

```powershell
Set-VM -Name $VM -CheckpointType Standard
Checkpoint-VM -Name $VM -SnapshotName before-service-test
Invoke-Command -VMName $VM -Credential $Cred -FilePath .\run-service-proof.ps1
$S = New-PSSession -VMName $VM -Credential $Cred
Copy-Item -FromSession $S -Path C:\repro\evidence -Destination .\evidence\$VM -Recurse
Remove-PSSession $S
Restore-VMCheckpoint -VMName $VM -Name before-service-test -Confirm:$false
```

For malware-adjacent or exploit-chain replay:

- Use a non-personal host or disposable host.
- Avoid Enhanced Session drive sharing and clipboard.
- Disable Guest Service Interface unless actively transferring a file.
- Use private or NAT-only networks.
- Prefer read-only payload media.
- Record every bridge opened between host and guest.

## Evidence Capture

Create a case directory:

```powershell
$Case = "case-$(Get-Date -Format yyyyMMdd-HHmmss)"
$Evidence = "D:\Evidence\$Case"
New-Item -ItemType Directory -Force -Path $Evidence | Out-Null
```

Capture host state:

```powershell
Get-Date -Format o | Out-File "$Evidence\host.txt"
Get-ComputerInfo -Property OsName,OsVersion,WindowsProductName,HyperVisorPresent,CsHypervisorPresent |
  Format-List | Out-File "$Evidence\host-computerinfo.txt"
Get-VMHost | Format-List * | Out-File "$Evidence\vmhost.txt"
Get-VMHostSupportedVersion | Out-File "$Evidence\vmhost-supported-version.txt"
```

Capture VM state:

```powershell
Get-VM -Name $VM | Format-List * | Out-File "$Evidence\vm.txt"
Get-VMProcessor -VMName $VM | Format-List * | Out-File "$Evidence\vm-processor.txt"
Get-VMMemory -VMName $VM | Format-List * | Out-File "$Evidence\vm-memory.txt"
Get-VMFirmware -VMName $VM | Format-List * | Out-File "$Evidence\vm-firmware.txt"
Get-VMHardDiskDrive -VMName $VM | Format-List * | Out-File "$Evidence\vm-disks.txt"
Get-VMNetworkAdapter -VMName $VM | Format-List * | Out-File "$Evidence\vm-nics.txt"
Get-VMNetworkAdapterVlan -VMName $VM | Format-List * | Out-File "$Evidence\vm-vlan.txt"
Get-VMIntegrationService -VMName $VM | Format-Table Name,Enabled,PrimaryStatusDescription |
  Out-File "$Evidence\vm-integration-services.txt"
Get-VMCheckpoint -VMName $VM | Format-List * | Out-File "$Evidence\vm-checkpoints.txt"
```

Capture networking:

```powershell
Get-VMSwitch | Format-List * | Out-File "$Evidence\vmswitches.txt"
Get-NetNat | Format-List * | Out-File "$Evidence\netnat.txt"
Get-NetNatStaticMapping | Format-List * | Out-File "$Evidence\netnat-static-mapping.txt"
Get-NetIPAddress | Out-File "$Evidence\host-ipaddresses.txt"
```

Capture guest state through PowerShell Direct:

```powershell
Invoke-Command -VMName $VM -Credential $Cred -ScriptBlock {
  Get-Date -Format o
  hostname
  Get-ComputerInfo -Property OsName,OsVersion,WindowsProductName,WindowsBuildLabEx
  ipconfig /all
  Get-NetIPConfiguration
  Get-LocalUser | Select-Object Name,Enabled,LastLogon
} | Out-File "$Evidence\guest-state.txt"
```

Copy guest artifacts:

```powershell
$S = New-PSSession -VMName $VM -Credential $Cred
Copy-Item -FromSession $S -Path "C:\repro\evidence" -Destination "$Evidence\guest-evidence" -Recurse
Remove-PSSession $S
```

Export a proof VM or checkpoint only after deciding whether memory state matters:

```powershell
Export-VM -Name $VM -Path "$Evidence\vm-export" -CaptureLiveState CaptureSavedState
Export-VMCheckpoint -VMName $VM -Name proof-state -Path "$Evidence\checkpoint-export"
```

## Failure Modes

Hyper-V role is missing

Check edition and feature state:

```powershell
Get-ComputerInfo -Property WindowsProductName
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V*
```

Windows Home editions cannot install the Hyper-V role.

PowerShell says access denied or commands fail

Run an elevated PowerShell session and ensure the user is in the Hyper-V
Administrators group or local Administrators group.

VM will not start

Check hypervisor presence, firmware virtualization, memory pressure, saved state,
and event logs:

```powershell
Get-ComputerInfo -Property HyperVisorPresent,CsHypervisorPresent
Get-VM -Name $VM | Format-List State,Status,OperationalStatus
Get-WinEvent -LogName Microsoft-Windows-Hyper-V-VMMS-Admin -MaxEvents 50
Get-WinEvent -LogName Microsoft-Windows-Hyper-V-Worker-Admin -MaxEvents 50
```

Custom NAT creation fails

WinNAT supports one internal NAT subnet prefix per host. Inspect existing NATs:

```powershell
Get-NetNat
Get-VMSwitch
```

Do not remove Docker, WSL, or container NATs on a shared host unless the lab owns
that host.

Guest has no IP on custom NAT

Custom WinNAT does not automatically mean the guest has DHCP. Set static guest IP
or provide DHCP inside the lab network.

NAT port forward unreachable

Check guest service bind address, guest firewall, host firewall, static mapping,
and host port conflicts:

```powershell
Get-NetNatStaticMapping -NatName DAST-NAT
Get-NetTCPConnection -LocalPort 8443 -ErrorAction SilentlyContinue
```

PowerShell Direct has no `-VMName` parameter

The host OS or PowerShell version does not support PowerShell Direct. Check:

```powershell
[System.Environment]::OSVersion.Version
$PSVersionTable.PSVersion
Get-Command Enter-PSSession -Syntax
```

PowerShell Direct says remote session ended

Common causes: VM is off, guest is too old, guest has not completed boot,
PowerShell is unavailable in the guest, or guest services are unhealthy.

```powershell
Get-VM -Name $VM
vmconnect.exe localhost $VM
```

`Copy-VMFile` fails

Enable Guest Service Interface or use PowerShell Direct `Copy-Item`:

```powershell
Get-VMIntegrationService -VMName $VM
Enable-VMIntegrationService -VMName $VM -Name "Guest Service Interface"
```

Linux installer will not boot

Try the Microsoft UEFI CA template or disable Secure Boot:

```powershell
Set-VMFirmware -VMName $VM -SecureBootTemplate MicrosoftUEFICertificateAuthority
Set-VMFirmware -VMName $VM -EnableSecureBoot Off
```

Checkpoint merge or paused-critical state

Free host disk space and remove checkpoints through Hyper-V:

```powershell
Get-VMCheckpoint -VMName $VM
Remove-VMCheckpoint -VMName $VM -Name old-checkpoint
```

Do not delete `.avhdx` files directly.

Imported VM identity collides

Use:

```powershell
Import-VM -Path $Config.FullName -Copy -GenerateNewId
```

Nested VM networking fails

Enable MAC spoofing on the level-1 VM NIC or use NAT inside the level-1 VM:

```powershell
Get-VMNetworkAdapter -VMName $VM | Set-VMNetworkAdapter -MacAddressSpoofing On
```

Default Switch changed subnet

Move evidence workflows to a custom internal switch and explicit WinNAT subnet.

## Evidence Checklist

Before run:

- Host OS edition, version, Hyper-V module availability, and hypervisor presence
  recorded.
- VM generation, configuration version, firmware, Secure Boot template, and TPM
  state recorded.
- CPU, memory, dynamic memory, automatic checkpoints, and integration services
  recorded.
- VHD parent/child relationship recorded if using differencing disks.
- Network mode recorded: external, internal NAT, private, Default Switch, VLAN,
  ACLs, static mappings.
- Guest credentials and host-to-guest bridges scoped to the lab.

During run:

- Checkpoint name or differencing child name recorded before mutation.
- Guest OS version, IP configuration, time, and relevant logs captured.
- NAT sessions, packet captures, or mirrored traffic captured when network proof
  matters.
- Screenshots or console recordings captured when UI state matters.

After run:

- Guest evidence copied out through a recorded channel.
- VM exported or checkpoint exported if state preservation is required.
- Dirty case VM deleted, reverted, or retained under a case-specific name.
- Base VHDX remains unchanged.
- `.avhdx` files were not manually edited or deleted.
- Any broad NAT, switch, or ACL cleanup was limited to lab-owned objects.

## References

- [Install Hyper-V](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/install-hyper-v)
- [System requirements for Hyper-V](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/system-requirements-for-hyper-v-on-windows)
- [Hyper-V PowerShell module](https://learn.microsoft.com/en-us/powershell/module/hyper-v/)
- [Using Hyper-V checkpoints](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints)
- [PowerShell Direct](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/powershell-direct)
- [Set up a NAT network](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/setup-nat-network)
- [Nested virtualization](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/enable-nested-virtualization)
