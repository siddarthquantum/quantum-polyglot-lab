"""Build the four doubly-linked-list containers, verify them, and record the evidence.

For each language this script:
  1. builds the image (timed),
  2. runs the demo in its hardened container and diffs it against
     shared/doubly_linked_list/expected_demo.txt,
  3. reads the container's real isolation settings back with `docker inspect`
     (so the report shows what Docker applied, not what we hoped it applied),
  4. runs the benchmark inside the container and parses checksums and timings.

It exits non-zero if any demo differs, any checksum disagrees across languages,
or any container is missing a hardening setting. Results go to a JSON file that
tools/report/build_report.py turns into the published page.

    python3 tools/report/collect.py --out report-data/results.json

Needs Docker with the compose plugin. Standard library only.
"""

import argparse
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker" / "doubly_linked_list" / "compose.yaml"
EXPECTED = ROOT / "shared" / "doubly_linked_list" / "expected_demo.txt"
LANGS = ["c", "java", "python", "rust"]
NAMES = {"c": "C", "java": "Java", "python": "Python", "rust": "Rust"}
BENCH_LINE = re.compile(r"^(\w+)\s+checksum=(-?\d+)\s+time_ms=([\d.]+)$")


def sh(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    # Always a fixed argv list (docker, git) -- never a shell, never user input.
    return subprocess.run(  # noqa: S603
        args, cwd=ROOT, check=True, text=True, capture_output=capture
    )


def compose(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return sh("docker", "compose", "-f", str(COMPOSE), *args, capture=capture)


def runtime_base(lang: str) -> str:
    """The last FROM line is the image the program actually runs on."""
    dockerfile = COMPOSE.parent / f"{lang}.Dockerfile"
    froms = [ln.split()[1] for ln in dockerfile.read_text().splitlines() if ln.startswith("FROM ")]
    return froms[-1]


def cpu_model() -> str:
    try:
        for ln in Path("/proc/cpuinfo").read_text().splitlines():
            if ln.startswith("model name"):
                return ln.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def isolation(container: str) -> dict:
    info = json.loads(sh("docker", "inspect", container).stdout)[0]
    hc, cfg = info["HostConfig"], info["Config"]
    return {
        "user": cfg.get("User") or "root",
        "network": hc.get("NetworkMode"),
        "read_only_rootfs": bool(hc.get("ReadonlyRootfs")),
        "cap_drop": hc.get("CapDrop") or [],
        "cap_add": hc.get("CapAdd") or [],
        "no_new_privileges": any("no-new-privileges" in o for o in (hc.get("SecurityOpt") or [])),
        "pids_limit": hc.get("PidsLimit"),
        "memory_mb": (hc.get("Memory") or 0) // (1024 * 1024),
        "cpus": (hc.get("NanoCpus") or 0) / 1e9,
        "privileged": bool(hc.get("Privileged")),
        "exit_code": info["State"]["ExitCode"],
    }


def isolation_problems(iso: dict) -> list[str]:
    problems = []
    if iso["user"] in ("", "root", "0", "0:0"):
        problems.append("runs as root")
    if iso["network"] != "none":
        problems.append(f"network is {iso['network']!r}, expected 'none'")
    if not iso["read_only_rootfs"]:
        problems.append("root filesystem is writable")
    if "ALL" not in iso["cap_drop"] or iso["cap_add"]:
        problems.append("capabilities not fully dropped")
    if not iso["no_new_privileges"]:
        problems.append("no-new-privileges not set")
    if iso["privileged"]:
        problems.append("privileged container")
    if not iso["pids_limit"] or iso["pids_limit"] <= 0:
        problems.append("no pids limit")
    if not iso["memory_mb"]:
        problems.append("no memory limit")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    expected = EXPECTED.read_text()
    results: dict = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": os.environ.get("GITHUB_SHA", sh("git", "rev-parse", "HEAD").stdout.strip()),
        "repository": os.environ.get("GITHUB_REPOSITORY", "siddarthquantum/quantum-polyglot-lab"),
        "server": os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "event": os.environ.get("GITHUB_EVENT_NAME", "local"),
        "machine": {
            "cpu": cpu_model(),
            "cores": os.cpu_count(),
            "os": f"{platform.system()} {platform.release()}",
            "docker": sh("docker", "version", "--format", "{{.Server.Version}}").stdout.strip(),
        },
        "languages": {},
        "failures": [],
    }

    for lang in LANGS:
        name = NAMES[lang]
        entry: dict = {"name": name, "runtime_base": runtime_base(lang)}
        print(f"== {name}: build", flush=True)

        t0 = time.perf_counter()
        compose("build", lang, capture=False)
        entry["build_seconds"] = round(time.perf_counter() - t0, 1)
        size = sh(
            "docker", "image", "inspect", f"polyglot-dll-{lang}", "--format", "{{.Size}}"
        ).stdout
        entry["image_mb"] = round(int(size.strip()) / 1e6, 1)

        print(f"== {name}: demo in hardened container", flush=True)
        probe = f"polyglot-dll-probe-{lang}"
        sh("docker", "rm", "-f", probe)
        t0 = time.perf_counter()
        demo = compose("run", "-T", "--name", probe, lang).stdout
        entry["demo_wall_ms"] = round((time.perf_counter() - t0) * 1e3)
        entry["isolation"] = isolation(probe)
        sh("docker", "rm", "-f", probe)

        entry["demo_matches"] = demo == expected
        if not entry["demo_matches"]:
            results["failures"].append(f"{name}: demo output differs from expected_demo.txt")
        for p in isolation_problems(entry["isolation"]):
            results["failures"].append(f"{name}: {p}")

        print(f"== {name}: benchmark", flush=True)
        bench = {}
        for ln in compose("run", "--rm", "-T", lang, "bench").stdout.splitlines():
            m = BENCH_LINE.match(ln.strip())
            if m:
                bench[m.group(1)] = {"checksum": int(m.group(2)), "ms": float(m.group(3))}
        entry["bench"] = bench
        results["languages"][lang] = entry

    sums = {
        lang: {k: v["checksum"] for k, v in e["bench"].items()}
        for lang, e in results["languages"].items()
    }
    reference = sums["c"]
    results["checksums_agree"] = bool(reference) and all(s == reference for s in sums.values())
    if not results["checksums_agree"]:
        results["failures"].append(f"benchmark checksums disagree: {sums}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.out}")

    if results["failures"]:
        print("FAILURES:", *results["failures"], sep="\n  ", file=sys.stderr)
        return 1
    print("PASS  all four containers: identical output, identical checksums, fully hardened")
    return 0


if __name__ == "__main__":
    sys.exit(main())
