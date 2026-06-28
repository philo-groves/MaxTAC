# Docker Virtualization

Use Docker for reproducible app and service DAST when the target can run as one
or more containers. Docker is excellent for network topology, dependency
pinning, fast reset, and evidence collection. It is not a full desktop or kernel
virtualization boundary. Linux containers share a Linux kernel with their Docker
host; on macOS and Windows, Linux containers run inside Docker Desktop's Linux
VM, which changes networking, filesystem, and host-boundary behavior.

For security research, treat the Docker daemon, Docker socket, bind mounts,
published ports, and privileged containers as the real trust boundary. A
container escape or Docker socket write is host-impacting.

## Contents

- [Quick Commands](#quick-commands)
- [Host, Context, and Daemon Probes](#host-context-and-daemon-probes)
- [Boundary Model](#boundary-model)
- [Image Pinning and Build Provenance](#image-pinning-and-build-provenance)
- [Build Hygiene](#build-hygiene)
- [Runtime Hardening](#runtime-hardening)
- [Rootless and User Namespaces](#rootless-and-user-namespaces)
- [Docker Socket and Daemon Access](#docker-socket-and-daemon-access)
- [Networking Model](#networking-model)
- [Port Publishing](#port-publishing)
- [Compose Lab Topology](#compose-lab-topology)
- [Volumes, Bind Mounts, and Tmpfs](#volumes-bind-mounts-and-tmpfs)
- [Lifecycle, Reset, and Case State](#lifecycle-reset-and-case-state)
- [Logs, Events, and Runtime State](#logs-events-and-runtime-state)
- [Debugging Containers](#debugging-containers)
- [Multi-Platform and Emulation](#multi-platform-and-emulation)
- [Docker Desktop Differences](#docker-desktop-differences)
- [DAST Repro Patterns](#dast-repro-patterns)
- [Evidence Capture](#evidence-capture)
- [Failure Modes](#failure-modes)
- [Evidence Checklist](#evidence-checklist)
- [References](#references)

## Quick Commands

Host and daemon sanity:

```bash
docker version
docker info
docker context ls
docker context show
docker compose version
docker buildx version
docker system df
```

Record security-relevant daemon settings:

```bash
docker info --format '{{json .SecurityOptions}}'
docker info --format 'security={{json .SecurityOptions}} cgroup={{.CgroupDriver}} driver={{.Driver}}'
docker info --format 'ostype={{.OSType}} os={{.OperatingSystem}} arch={{.Architecture}}'
```

Create a deterministic user-defined bridge network:

```bash
docker network create \
  --driver bridge \
  --subnet 172.30.10.0/24 \
  --gateway 172.30.10.1 \
  --label maxtac.case=case-001 \
  case-001-net
```

Run a hardened one-off target:

```bash
docker run --rm \
  --name case-001-target \
  --network case-001-net \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=128m \
  --cap-drop ALL \
  --security-opt no-new-privileges=true \
  --pids-limit 256 \
  --memory 512m \
  --cpus 1.0 \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/acme/target@sha256:...
```

Compose with an explicit project name:

```bash
COMPOSE_PROJECT_NAME=case001 docker compose up -d --build
COMPOSE_PROJECT_NAME=case001 docker compose ps
COMPOSE_PROJECT_NAME=case001 docker compose logs --timestamps --no-color > evidence/case001/compose.log
COMPOSE_PROJECT_NAME=case001 docker compose down --remove-orphans
```

Capture evidence:

```bash
mkdir -p evidence/case001
docker inspect case-001-target > evidence/case001/container-inspect.json
docker image inspect ghcr.io/acme/target@sha256:... > evidence/case001/image-inspect.json
docker network inspect case-001-net > evidence/case001/network-inspect.json
docker logs --timestamps case-001-target > evidence/case001/container.log 2>&1
docker container diff case-001-target > evidence/case001/container-diff.txt
docker cp case-001-target:/app/artifacts evidence/case001/artifacts
```

Targeted cleanup:

```bash
docker rm -f case-001-target
docker network rm case-001-net
docker volume ls --filter label=maxtac.case=case-001
```

Avoid broad cleanup on a shared host:

```bash
docker system prune
docker volume prune
```

Use broad prune only on disposable lab hosts after confirming ownership.

## Host, Context, and Daemon Probes

The Docker client may point at a local Engine, Docker Desktop, a remote SSH
context, a CI service, or a rootless daemon. Always record the context before a
case.

```bash
docker context ls
docker context show
docker context inspect "$(docker context show)"
docker version
docker info
```

Useful `docker info` fields:

```bash
docker info --format 'ServerVersion={{.ServerVersion}}'
docker info --format 'OperatingSystem={{.OperatingSystem}} OSType={{.OSType}} Architecture={{.Architecture}}'
docker info --format 'Driver={{.Driver}} CgroupDriver={{.CgroupDriver}} CgroupVersion={{.CgroupVersion}}'
docker info --format 'SecurityOptions={{json .SecurityOptions}}'
docker info --format 'DefaultRuntime={{.DefaultRuntime}} Runtimes={{json .Runtimes}}'
```

Probe Desktop state when available:

```bash
docker desktop version
docker desktop status
docker desktop logs
```

On Linux, inspect host kernel and namespace support:

```bash
uname -a
cat /proc/self/uid_map
cat /proc/filesystems | grep overlay || true
sysctl kernel.unprivileged_userns_clone 2>/dev/null || true
```

Do not assume `docker` commands hit the user's local workstation. A remote
context changes data residency, network reachability, and evidence custody.

## Boundary Model

Docker containers are isolated processes, not separate operating systems.

Assume containers can affect findings when the target depends on:

- Kernel version, kernel config, cgroups, seccomp, AppArmor, SELinux, or LSMs.
- Host filesystem semantics, case sensitivity, inotify behavior, or bind mount
  consistency.
- Network namespace behavior, NAT, DNS, loopback, or host routing.
- Capabilities, UID/GID mapping, `setuid`, `ptrace`, raw sockets, or mount
  namespaces.
- Clock, entropy, CPU quota, memory pressure, `/dev/shm`, or process limits.

Do not use Docker as proof for:

- Kernel exploitability unless the kernel and container runtime boundary are
  explicitly in scope.
- Desktop OS behavior, GUI workflows, USB/Bluetooth/Wi-Fi behavior, or hardware
  identity.
- Mobile app behavior. Use the physical iOS/Android workflows instead.
- Host compromise unless the container has a host-impacting bridge such as the
  Docker socket, privileged mode, host namespaces, writeable host bind mounts, or
  device passthrough.

On Docker Desktop for macOS/Windows, a Linux container is inside a Linux VM. A
"host" path bind mount is projected into that VM, and network routes pass through
Desktop's networking layer. Evidence should record Desktop version and settings
when Desktop is in the path.

## Image Pinning and Build Provenance

Tags drift. `latest` is not evidence. Pin by digest for reproducible cases:

```bash
docker pull ubuntu:24.04
docker image inspect ubuntu:24.04 --format '{{json .RepoDigests}}'
docker run --rm ubuntu@sha256:... cat /etc/os-release
```

Record image identity:

```bash
docker image inspect "$IMAGE" > evidence/image-inspect.json
docker history --no-trunc "$IMAGE" > evidence/image-history.txt
docker buildx imagetools inspect "$IMAGE" > evidence/image-manifest.txt
```

Save an exact image used in a proof:

```bash
docker image save "$IMAGE" -o evidence/image.tar
sha256sum evidence/image.tar > evidence/image.tar.sha256
```

Use `docker image save` for image layers and metadata. Use `docker export` only
when you intentionally want a flattened container filesystem without image
history, config, volumes, or metadata.

Compose pull policy matters:

```yaml
services:
  target:
    image: ghcr.io/acme/target@sha256:...
    pull_policy: never
```

Use `pull_policy: never` when the local image is part of the evidence bundle and
network pulls would pollute the run. Use `pull_policy: always` or a pinned digest
when registry state is intentionally part of the test.

## Build Hygiene

Build context is an evidence surface. If the context includes secrets, test data,
or unrelated files, they may be sent to the builder and can end up in image
layers.

Start every case with:

```bash
docker buildx version
docker buildx ls
docker buildx inspect --bootstrap
docker buildx build --progress=plain --no-cache -t case-target:build .
```

Use `.dockerignore` aggressively:

```text
.git
.env
*.pem
*.key
node_modules
evidence
cases
```

Use BuildKit secrets instead of `ARG` or `ENV` for credentials:

```bash
docker buildx build \
  --secret id=npmrc,src="$HOME/.npmrc" \
  -t case-target:build .
```

Dockerfile:

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

Never put tokens in:

- `ARG`
- `ENV`
- `RUN echo token`
- image labels
- committed containers
- Compose files checked into evidence

Use named build stages to separate toolchain from runtime:

```dockerfile
FROM node:24 AS build
WORKDIR /src
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-slim AS runtime
WORKDIR /app
COPY --from=build /src/dist ./dist
USER 1000:1000
CMD ["node", "dist/server.js"]
```

For evidence, capture:

```bash
docker buildx build --progress=plain --metadata-file evidence/build-metadata.json -t case-target:build .
docker image inspect case-target:build > evidence/build-image-inspect.json
```

If a build uses remote cache, registry cache, Git contexts, or multi-platform
builders, record the builder and cache inputs. Build cache can hide dependency
fetches and make "clean repro" claims false.

## Runtime Hardening

Start from least privilege. Add back only what the target requires.

Hardened `docker run` baseline:

```bash
docker run --rm \
  --name target \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=128m \
  --tmpfs /run:rw,noexec,nosuid,nodev,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges=true \
  --pids-limit 256 \
  --memory 512m \
  --cpus 1.0 \
  --network target-net \
  target:build
```

Add Linux capabilities only when needed:

```bash
--cap-add NET_BIND_SERVICE
--cap-add CHOWN
```

Avoid:

```bash
--privileged
--pid host
--ipc host
--network host
--cap-add ALL
--security-opt seccomp=unconfined
--security-opt apparmor=unconfined
-v /:/host
-v /var/run/docker.sock:/var/run/docker.sock
```

Use `--read-only` plus explicit write locations. Many apps need `/tmp`, `/run`,
or an app data directory:

```bash
--read-only \
--tmpfs /tmp:rw,noexec,nosuid,nodev,size=128m \
--mount type=volume,source=case001-data,target=/app/data
```

Constrain shared memory if the target does not need browser-scale `/dev/shm`:

```bash
--shm-size 128m
```

Increase `/dev/shm` for Chromium/browser tests instead of disabling sandboxing:

```bash
--shm-size 1g
```

Seccomp defaults block some kernel attack primitives while preserving broad app
compatibility. If a target needs a syscall blocked by the default profile,
document the reason and use a custom profile rather than `seccomp=unconfined`
when possible.

Compose equivalent:

```yaml
services:
  target:
    image: case-target:build
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=128m
      - /run:rw,noexec,nosuid,nodev,size=64m
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    pids_limit: 256
    mem_limit: 512m
    cpus: 1.0
```

Do not claim a vuln is exploitable by a network attacker if your proof relies on
`docker exec`, host bind mounts, extra caps, privileged mode, or host namespaces.

## Rootless and User Namespaces

Rootless mode runs the Docker daemon and containers as a non-root user. It
reduces daemon and runtime impact but changes behavior.

Probe:

```bash
docker info --format '{{json .SecurityOptions}}'
docker context show
id
```

Expect differences in:

- Low-port binding.
- Cgroup/resource enforcement.
- Overlay and storage behavior.
- Network performance and host reachability.
- Bind mount ownership and UID/GID mapping.

User namespace remapping maps container root to an unprivileged host UID range.
It is useful when a process must be root inside the container but should not be
host root.

Daemon-level `userns-remap` affects storage paths and bind mount ownership. Do
not toggle it casually on a shared Docker host. Record it in evidence:

```bash
docker info --format '{{json .SecurityOptions}}'
```

Per-container user namespace mode may be available depending on daemon config:

```bash
docker run --userns=host ...
```

Use `--userns=host` only when deliberately disabling user namespace isolation for
a compatibility test. Call it out as a boundary change.

Inside a container, inspect UID mapping:

```bash
cat /proc/self/uid_map
cat /proc/self/gid_map
id
```

## Docker Socket and Daemon Access

The Docker daemon is a high-privilege control plane. Access to the Docker socket
can create containers, mount host paths, change networks, and read secrets from
other containers.

Treat this as host-impacting:

```bash
-v /var/run/docker.sock:/var/run/docker.sock
```

Avoid it in target containers. If a tool requires Docker API access, prefer:

- A disposable host or VM.
- A purpose-built socket proxy with an allowlist.
- A rootless daemon dedicated to the case.
- A separate Docker context with scoped credentials.

Check socket exposure:

```bash
docker inspect "$CID" --format '{{json .Mounts}}' | jq .
docker inspect "$CID" --format '{{json .HostConfig.Binds}}' | jq .
```

Do not expose the daemon over TCP without TLS and authorization. If `DOCKER_HOST`
is set, record it:

```bash
env | grep '^DOCKER_'
docker context inspect "$(docker context show)"
```

Docker Desktop security changes over time. Keep Desktop current and record the
version when Desktop is the runtime. Desktop-specific isolation features such as
Enhanced Container Isolation can change UID mappings and Docker socket behavior.

## Networking Model

Use user-defined bridge networks for most DAST stacks. They provide scoped
container-to-container DNS and isolation by project.

Create:

```bash
docker network create --driver bridge case001-net
```

Run:

```bash
docker run --name api --network case001-net api:case
docker run --name scanner --network case001-net scanner:case curl -i http://api:8080/
```

Do not hardcode container IPs unless the test requires IP pinning. Containers can
change IPs on recreate. Use service names, aliases, or Compose DNS.

Set explicit subnet when target behavior depends on CIDR:

```bash
docker network create \
  --driver bridge \
  --subnet 172.31.50.0/24 \
  --gateway 172.31.50.1 \
  case001-net
```

Use `--internal` for networks that should not have external connectivity:

```bash
docker network create --internal --driver bridge case001-internal
```

Attach multiple networks for segmented topology:

```bash
docker network create case001-front
docker network create --internal case001-back
docker run --name proxy --network case001-front proxy:case
docker network connect case001-back proxy
docker run --name db --network case001-back db:case
```

Network driver choice:

- `bridge`: default for single-host DAST labs.
- `host`: no container network namespace isolation. Use only for host-network
  parity tests.
- `none`: no network. Good for offline parser or exploit replay.
- `macvlan` / `ipvlan`: make containers appear on a physical network. Use only
  when LAN peer behavior is required and the lab owns that network segment.
- `overlay`: multi-host Swarm networking. Avoid unless the target architecture
  specifically requires it.

Docker manages host firewall/NAT rules for bridge networks. On Linux, capture
host nftables/iptables state if packet path is evidence.

```bash
iptables-save > evidence/iptables-save.txt 2>/dev/null || true
nft list ruleset > evidence/nft-ruleset.txt 2>/dev/null || true
```

## Port Publishing

Publishing a port exposes a container port through the Docker host. Bind to
loopback for local DAST unless LAN exposure is intentional.

Good default:

```bash
docker run -p 127.0.0.1:8080:8080 target:case
```

Riskier:

```bash
docker run -p 8080:8080 target:case
```

The second form commonly binds on all host interfaces. On Docker Desktop, the
path still traverses Desktop's VM and networking layer, but it can still expose a
service beyond the local process that launched it.

Compose:

```yaml
services:
  target:
    ports:
      - "127.0.0.1:8080:8080"
```

Publish to a random host port when parallel cases may collide:

```bash
docker run -p 127.0.0.1::8080 target:case
docker port "$CID" 8080
```

Restrict default host binding for a user-defined bridge:

```bash
docker network create mybridge \
  -o "com.docker.network.bridge.host_binding_ipv4=127.0.0.1"
```

Publishing is not needed for container-to-container traffic on the same
user-defined network. Expose ports only to the host or outside clients that must
participate in the proof.

## Compose Lab Topology

Use Compose for multi-container targets and scanners. Always set a project name
so names, networks, labels, and cleanup are deterministic.

```bash
export COMPOSE_PROJECT_NAME=case001
docker compose config > evidence/case001/compose.rendered.yaml
docker compose up -d --build
docker compose ps
```

Minimal DAST Compose pattern:

```yaml
services:
  proxy:
    image: nginx:1.29
    ports:
      - "127.0.0.1:8080:80"
    networks:
      - front
      - back
    depends_on:
      api:
        condition: service_healthy

  api:
    build:
      context: ./api
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=128m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    networks:
      - back
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8080/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 20s

  scanner:
    image: ghcr.io/acme/scanner@sha256:...
    profiles:
      - scan
    networks:
      - front
    volumes:
      - type: bind
        source: ./evidence/case001
        target: /evidence

networks:
  front: {}
  back:
    internal: true
```

Compose dependency semantics matter. `depends_on` orders startup, but readiness
requires healthchecks and `condition: service_healthy`.

Run target only:

```bash
docker compose up -d proxy api
```

Run scanner profile:

```bash
docker compose --profile scan run --rm scanner
```

Capture current Compose state:

```bash
docker compose ps --all
docker compose images
docker compose top
docker compose logs --timestamps --no-color
docker compose events --json
```

Cleanup by project:

```bash
docker compose down --remove-orphans
docker compose down --remove-orphans --volumes
```

Use `--volumes` only when the volume contents are not evidence.

## Volumes, Bind Mounts, and Tmpfs

Bind mounts expose host paths directly to a container. Prefer read-only bind
mounts for seeds, payloads, and source trees:

```bash
docker run \
  --mount type=bind,source="$PWD/seeds",target=/seeds,readonly \
  target:case
```

Avoid broad writeable mounts:

```bash
-v "$PWD:/workspace"
-v /:/host
```

If the target path already has files in the image, a bind mount or volume can
obscure them. This often explains "works in image, missing at runtime" behavior.

Named volumes persist after containers are removed:

```bash
docker volume create --label maxtac.case=case001 case001-db
docker run --mount type=volume,source=case001-db,target=/var/lib/postgresql/data ...
```

Inspect and label volumes:

```bash
docker volume inspect case001-db
docker volume ls --filter label=maxtac.case=case001
```

Copy out volume data with a helper container:

```bash
docker run --rm \
  --mount type=volume,source=case001-db,target=/data,readonly \
  --mount type=bind,source="$PWD/evidence/case001",target=/evidence \
  alpine sh -c 'cd /data && tar -czf /evidence/case001-db.tgz .'
```

Use tmpfs for secrets, caches, and ephemeral write paths:

```bash
docker run --tmpfs /run/secrets:rw,noexec,nosuid,nodev,size=16m ...
```

Compose:

```yaml
services:
  target:
    volumes:
      - type: bind
        source: ./seeds
        target: /seeds
        read_only: true
      - type: volume
        source: target-data
        target: /app/data
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=128m

volumes:
  target-data:
    labels:
      maxtac.case: case001
```

On Docker Desktop, bind mount performance and filesystem semantics can differ
from native Linux. If a finding depends on file watching, permissions, symlinks,
case sensitivity, or path traversal behavior, rerun on a native Linux Engine or
record Desktop as part of the environment.

## Lifecycle, Reset, and Case State

Separate image state, container state, and volume state.

Image state:

```bash
docker image inspect target:case
docker image save target:case -o evidence/target-image.tar
```

Container writable layer:

```bash
docker container diff target
docker container export target -o evidence/target-container-rootfs.tar
```

Volume state:

```bash
docker volume inspect case001-db
```

`docker rm` deletes the container writable layer. It does not delete named
volumes unless requested through Compose `down --volumes` or explicit volume
removal.

Avoid `--rm` while developing a proof because it deletes the container on exit.
Use `--rm` for disposable scanner containers after evidence paths are bind
mounted out.

Use labels for case-owned objects:

```bash
docker run --label maxtac.case=case001 ...
docker network create --label maxtac.case=case001 case001-net
docker volume create --label maxtac.case=case001 case001-data
```

List case-owned objects:

```bash
docker ps -a --filter label=maxtac.case=case001
docker network ls --filter label=maxtac.case=case001
docker volume ls --filter label=maxtac.case=case001
docker image ls --filter label=maxtac.case=case001
```

Do not use `docker commit` as a build process. It is acceptable as a triage
artifact when you need to preserve an unexpected container state:

```bash
docker commit target evidence/target:dirty-case001
docker image save evidence/target:dirty-case001 -o evidence/dirty-image.tar
```

Record that committed images are dirty evidence, not a clean reproducible base.

## Logs, Events, and Runtime State

Container logs:

```bash
docker logs --timestamps target > evidence/target.log 2>&1
docker compose logs --timestamps --no-color > evidence/compose.log 2>&1
```

Follow events during a run:

```bash
docker events \
  --filter label=maxtac.case=case001 \
  --format '{{json .}}' \
  > evidence/docker-events.jsonl
```

Container process state:

```bash
docker top target auxww > evidence/target-top.txt
docker stats --no-stream --format '{{json .}}' target > evidence/target-stats.json
docker inspect target > evidence/target-inspect.json
```

Network state:

```bash
docker network inspect case001-net > evidence/network.json
docker exec target ip addr > evidence/target-ip-addr.txt
docker exec target ip route > evidence/target-ip-route.txt
docker exec target cat /etc/resolv.conf > evidence/target-resolv.conf
```

Filesystem changes:

```bash
docker container diff target > evidence/target-diff.txt
docker cp target:/app/logs evidence/target-app-logs
```

Log driver matters. `docker logs` may be unavailable or incomplete with some
remote logging drivers. Record:

```bash
docker inspect target --format '{{json .HostConfig.LogConfig}}'
docker info --format '{{.LoggingDriver}}'
```

## Debugging Containers

`docker exec` is a host-operator action. It does not prove attacker capability.

```bash
docker exec -it target sh
docker exec -u 0 -it target sh
docker exec target env
```

Use `docker exec -u 0` only when host-side triage requires it. Record that root
inside the container was provided by the harness.

Attach a debugger with explicit capability changes only in a debug run:

```bash
docker run --cap-add SYS_PTRACE --security-opt seccomp=unconfined ...
```

That changes exploitability. Keep debug and proof runs separate.

Use a sidecar for network debugging instead of installing tools into the target:

```bash
docker run --rm -it --network container:target nicolaka/netshoot
```

`--network container:target` joins the target's network namespace. It is useful
for observation but changes namespace occupancy and can affect timing or ports.

Host namespace debugging is even stronger:

```bash
docker run --rm -it --pid container:target --cap-add SYS_PTRACE ...
```

Use only for triage, not final proof.

## Multi-Platform and Emulation

`--platform` controls image selection and, when needed, emulation.

```bash
docker run --platform linux/amd64 ...
docker buildx build --platform linux/amd64,linux/arm64 ...
```

If the host architecture differs from the container architecture, Docker may use
emulation through binfmt/QEMU. That can change timing, CPU features, signal
behavior, filesystem race windows, and native dependency behavior.

Record platform:

```bash
docker image inspect "$IMAGE" --format '{{.Architecture}}/{{.Os}}'
docker buildx imagetools inspect "$IMAGE"
docker exec target uname -m
```

For performance-sensitive, memory-corruption, native extension, JIT, or sandbox
findings, rerun on native architecture before making exploitability claims.

## Docker Desktop Differences

On macOS and Windows, Docker Desktop runs Linux containers inside a Linux VM.
This affects:

- Host networking and `--network host`.
- Bind mount consistency and performance.
- File ownership, UID/GID mapping, symlink behavior, and case sensitivity.
- Reachability of host services.
- Availability of Linux kernel features, cgroups, eBPF, AppArmor, and seccomp.
- VPN and proxy routing.

Use `host.docker.internal` for host services when supported:

```bash
curl http://host.docker.internal:8080/
```

On native Linux Engine, add it explicitly when needed:

```bash
docker run --add-host=host.docker.internal:host-gateway ...
```

Do not use Docker Desktop results as proof of native Linux host network behavior
unless Desktop is the target deployment. For SSRF, bind-mount, filesystem, or
local-network findings, record whether Desktop was involved.

Desktop Enhanced Container Isolation can remap container UIDs inside the Desktop
VM and restrict Docker socket behavior. If enabled, capture Desktop settings and
container UID maps:

```bash
docker desktop version
docker run --rm alpine cat /proc/self/uid_map
```

## DAST Repro Patterns

Local-only web target:

```bash
docker network create --label maxtac.case=case001 case001-net
docker run -d \
  --name case001-target \
  --label maxtac.case=case001 \
  --network case001-net \
  -p 127.0.0.1:8080:8080 \
  target@sha256:...
```

Scanner sidecar that does not expose target to LAN:

```bash
docker run --rm \
  --label maxtac.case=case001 \
  --network case001-net \
  --mount type=bind,source="$PWD/evidence/case001",target=/evidence \
  scanner@sha256:... http://case001-target:8080/
```

Backend network hidden from host:

```yaml
services:
  proxy:
    image: nginx:1.29
    ports:
      - "127.0.0.1:8080:80"
    networks:
      - front
      - back

  api:
    image: api@sha256:...
    networks:
      - back

  db:
    image: postgres:18
    networks:
      - back

networks:
  front: {}
  back:
    internal: true
```

Read-only malicious fixture replay:

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=128m \
  --mount type=bind,source="$PWD/fixtures",target=/fixtures,readonly \
  --mount type=bind,source="$PWD/evidence/case001",target=/evidence \
  parser-target@sha256:... /fixtures/input.bin
```

SSRF sink inside the lab:

```yaml
services:
  metadata:
    image: python:3.13-alpine
    command: python -m http.server 80 --directory /srv
    volumes:
      - ./fixtures/metadata:/srv:ro
    networks:
      back:
        aliases:
          - metadata.internal

  target:
    image: target@sha256:...
    networks:
      - back

networks:
  back:
    internal: true
```

Host callback proof:

```bash
docker run -d --name callback -p 127.0.0.1:9000:9000 callback-listener:case
docker run --rm --add-host=host.docker.internal:host-gateway target:case \
  curl http://host.docker.internal:9000/probe
```

Use a VM instead of Docker when the proof requires:

- A different kernel than the host.
- Real systemd boot, kernel modules, or init-level behavior.
- Full network stack parity with a LAN peer.
- Desktop UI, USB, GPU, Wi-Fi, Bluetooth, or hardware identity.
- Strong isolation from hostile code on a shared workstation.

## Evidence Capture

Create a case directory:

```bash
CASE=case001
mkdir -p "evidence/$CASE"
```

Capture host and Docker facts:

```bash
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  uname -a 2>/dev/null || true
  docker version
  docker info
  docker context ls
  docker context inspect "$(docker context show)"
  docker compose version
  docker buildx version
} > "evidence/$CASE/docker-host.txt" 2>&1
```

Capture Compose config:

```bash
COMPOSE_PROJECT_NAME="$CASE" docker compose config > "evidence/$CASE/compose.config.yaml"
COMPOSE_PROJECT_NAME="$CASE" docker compose ps --all > "evidence/$CASE/compose.ps.txt"
COMPOSE_PROJECT_NAME="$CASE" docker compose images > "evidence/$CASE/compose.images.txt"
```

Capture Docker object inventory:

```bash
docker ps -a --filter label=maxtac.case="$CASE" --no-trunc > "evidence/$CASE/containers.txt"
docker network ls --filter label=maxtac.case="$CASE" > "evidence/$CASE/networks.txt"
docker volume ls --filter label=maxtac.case="$CASE" > "evidence/$CASE/volumes.txt"
```

Inspect containers, networks, volumes, and images:

```bash
for cid in $(docker ps -aq --filter label=maxtac.case="$CASE"); do
  docker inspect "$cid" > "evidence/$CASE/container-$cid.json"
  docker logs --timestamps "$cid" > "evidence/$CASE/container-$cid.log" 2>&1 || true
  docker container diff "$cid" > "evidence/$CASE/container-$cid.diff" 2>&1 || true
done

for net in $(docker network ls -q --filter label=maxtac.case="$CASE"); do
  docker network inspect "$net" > "evidence/$CASE/network-$net.json"
done

for vol in $(docker volume ls -q --filter label=maxtac.case="$CASE"); do
  docker volume inspect "$vol" > "evidence/$CASE/volume-$vol.json"
done
```

Capture image digests:

```bash
docker image ls --digests --no-trunc > "evidence/$CASE/images-digests.txt"
```

Save exact images for offline replay:

```bash
docker image save target@sha256:... -o "evidence/$CASE/target-image.tar"
sha256sum "evidence/$CASE/target-image.tar" > "evidence/$CASE/target-image.tar.sha256"
```

Capture network/firewall state on Linux:

```bash
ip addr > "evidence/$CASE/ip-addr.txt" 2>/dev/null || true
ip route > "evidence/$CASE/ip-route.txt" 2>/dev/null || true
iptables-save > "evidence/$CASE/iptables-save.txt" 2>/dev/null || true
nft list ruleset > "evidence/$CASE/nft-ruleset.txt" 2>/dev/null || true
```

Capture volume contents intentionally:

```bash
docker run --rm \
  --mount type=volume,source=case001-db,target=/data,readonly \
  --mount type=bind,source="$PWD/evidence/$CASE",target=/evidence \
  alpine sh -c 'cd /data && tar -czf /evidence/case001-db.tgz .'
```

## Failure Modes

Cannot connect to Docker daemon

Check context and daemon state:

```bash
docker context ls
docker context show
docker version
docker desktop status 2>/dev/null || true
```

Permission denied on `/var/run/docker.sock`

The user is not allowed to access the daemon socket, or rootless context is not
configured. Adding a user to the `docker` group grants high-impact daemon access.
Do it only when that user should control the host's containers.

Wrong Docker context

Remote contexts can run tests on the wrong host:

```bash
docker context inspect "$(docker context show)"
```

Port already allocated

Find owner:

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'
ss -ltnp | grep ':8080' 2>/dev/null || true
```

Use a random host port or case-specific port:

```bash
docker run -p 127.0.0.1::8080 target:case
docker port "$CID" 8080
```

Service is running but not ready

Compose does not wait for readiness unless healthchecks are part of the
dependency condition. Add healthchecks and use `condition: service_healthy`.

Container cannot reach host service

Inside the container, `localhost` is the container itself. Use service DNS for
other containers or `host.docker.internal` for host services when supported. On
Linux, add:

```bash
--add-host=host.docker.internal:host-gateway
```

Published port exposed too broadly

Bind explicitly:

```bash
-p 127.0.0.1:8080:8080
```

Bind mount hides files from the image

Mounting over a populated image path obscures the original contents. Inspect the
image without the mount or mount into an empty purpose-built directory.

Volume data persists after cleanup

`docker compose down` keeps named volumes by default. Use:

```bash
docker compose down --volumes
```

only after preserving evidence.

Container exits and evidence disappears

Avoid `--rm` for target containers until evidence is copied. Use `docker cp`,
volume exports, and logs before removal.

Seccomp or capabilities break a test

Do not jump straight to `--privileged`. Add the minimum capability or custom
seccomp profile required, and record the delta:

```bash
--cap-add SYS_PTRACE
--security-opt seccomp=./seccomp-debug.json
```

Rootless or userns causes permission errors

Inspect mappings:

```bash
docker run --rm alpine cat /proc/self/uid_map
stat -c '%u:%g %n' ./mounted-path
```

Fix ownership for the mapped host UID range or use named volumes.

DNS lookup fails between containers

Use a user-defined network or Compose network. Default bridge behavior is not a
good DAST topology primitive.

Desktop result does not reproduce on Linux Engine

Check whether Desktop's VM, bind mount projection, proxy/VPN integration,
Enhanced Container Isolation, or host networking behavior was part of the result.

## Evidence Checklist

Before run:

- Docker context, Engine/Desktop version, daemon info, storage driver, cgroup
  mode, rootless/userns/security options recorded.
- Image references pinned by digest or image tar preserved.
- Compose rendered config captured.
- Project name and object labels set.
- Published ports bound to loopback unless LAN exposure is intentional.
- Networks, subnets, `internal` flags, aliases, and host mappings recorded.
- Bind mounts reviewed for writeability and host data exposure.
- Docker socket not mounted into target containers unless explicitly in scope.

During run:

- Container logs, Compose logs, events, stats, and inspect output captured.
- Scanner commands and target URLs recorded.
- Healthcheck state and startup ordering recorded.
- Filesystem diffs and app artifacts copied out before removal.
- Host firewall/NAT state captured if packet path matters.

After run:

- Target images saved or digests recorded.
- Volumes exported or intentionally destroyed.
- Dirty containers committed only as triage artifacts and labeled as dirty.
- Containers, networks, and volumes cleaned up by case label/project name.
- Broad prune commands avoided on shared hosts.

## References

- [Running containers](https://docs.docker.com/engine/containers/run/)
- [docker container run reference](https://docs.docker.com/reference/cli/docker/container/run/)
- [Docker networking overview](https://docs.docker.com/engine/network/)
- [Bridge network driver](https://docs.docker.com/engine/network/drivers/bridge/)
- [Port publishing and mapping](https://docs.docker.com/engine/network/port-publishing/)
- [Volumes](https://docs.docker.com/engine/storage/volumes/)
- [Bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Docker Engine security](https://docs.docker.com/engine/security/)
- [Rootless mode](https://docs.docker.com/engine/security/rootless/)
- [User namespace remapping](https://docs.docker.com/engine/security/userns-remap/)
- [Seccomp security profiles](https://docs.docker.com/engine/security/seccomp/)
- [Protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/)
- [Compose services reference](https://docs.docker.com/reference/compose-file/services/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/networking-how-tos/)
- [Enhanced Container Isolation](https://docs.docker.com/enterprise/security/hardened-desktop/enhanced-container-isolation/)
