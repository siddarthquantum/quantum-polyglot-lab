"""Render the CI evidence (results.json from collect.py) as a static report page.

    python3 tools/report/build_report.py report-data/results.json --out site/

Writes site/index.html (self-contained: inline CSS, no scripts, no external
requests) plus a copy of results.json so every number on the page can be
checked against the raw data. Standard library only.
"""

import argparse
import html
import json
import shutil
from pathlib import Path

WORKLOADS = [
    ("build_back", "build_back", "200,000 × push_back"),
    ("traverse", "traverse", "10 passes, alternating direction"),
    ("remove_held", "remove_held", "100,000 removals by handle"),
    ("pop_back", "pop_back", "100,000 × pop_back"),
    ("index_access", "index_access", "200 × get(i) on 20,000 nodes"),
]
ORDER = ["c", "rust", "java", "python"]

GUIDES = [
    (
        "Array basics",
        "shared/array_basics/README.md",
        "contiguous memory, O(1) access, O(n) insert",
    ),
    (
        "Singly linked list",
        "shared/linked_list/README.md",
        "the opposite trade-off, Floyd's cycle detection",
    ),
    (
        "Doubly linked list",
        "shared/doubly_linked_list/README.md",
        "O(1) at both ends, safe unlinking, four containers",
    ),
]

CSS = """
:root {
  --bg: #fbfbfa; --surface: #ffffff; --ink: #1d1f23; --ink-2: #4a4f57; --ink-3: #737983;
  --rule: #e4e5e7; --bar: #3b6fd8; --bar-track: #eef1f6; --good: #1f7a4d; --bad: #b42318;
  --code-bg: #f3f4f6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111317; --surface: #181b20; --ink: #e8e9eb; --ink-2: #b6bac1; --ink-3: #8b9099;
    --rule: #2a2e35; --bar: #7da2f0; --bar-track: #232830; --good: #5cc28f; --bad: #f2877c;
    --code-bg: #1f232a;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 980px; margin: 0 auto; padding: 40px 16px 64px; }
a { color: var(--bar); }
h1 { font-size: 30px; line-height: 1.2; margin: 0 0 8px; letter-spacing: -0.01em; }
h2 { font-size: 20px; margin: 48px 0 6px; }
.lede { color: var(--ink-2); margin: 0 0 4px; max-width: 70ch; }
.meta { color: var(--ink-3); font-size: 14px; margin: 0; }
.meta code { font-size: 13px; }
code { font: 13px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--code-bg); padding: 1px 5px; border-radius: 4px; }
pre { background: var(--code-bg); padding: 14px 16px; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
.sub { color: var(--ink-2); margin: 0 0 18px; max-width: 72ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 28px; }
.tile { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; }
.tile .v { font-size: 26px; font-weight: 650; line-height: 1.15; }
.tile .k { color: var(--ink-2); font-size: 14px; margin-top: 4px; }
.status { display: inline-flex; align-items: center; gap: 6px; font-weight: 600; }
.status.ok { color: var(--good); } .status.fail { color: var(--bad); }
.status svg { width: 16px; height: 16px; flex: none; }
.panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 14px; }
.panel { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px 10px; }
.panel h3 { font-size: 15px; margin: 0; }
.panel p { color: var(--ink-3); font-size: 13px; margin: 2px 0 12px; }
.row { display: grid; grid-template-columns: 58px 1fr 78px; align-items: center; gap: 10px; padding: 4px 0; }
.row .lang { font-size: 14px; color: var(--ink-2); }
.row .ms { font: 13px ui-monospace, SFMono-Regular, Menlo, monospace; text-align: right; color: var(--ink); }
.track { height: 12px; background: var(--bar-track); border-radius: 0 4px 4px 0; }
.fill { height: 12px; background: var(--bar); border-radius: 0 4px 4px 0; min-width: 2px; }
.row:hover .fill { filter: brightness(1.12); }
.tablewrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
th { color: var(--ink-2); font-weight: 600; background: var(--surface); }
tr:last-child td { border-bottom: 0; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.skills { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; padding: 0; list-style: none; }
.skills li { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; }
.skills b { display: block; margin-bottom: 4px; }
.skills span { color: var(--ink-2); font-size: 14px; }
footer { margin-top: 56px; color: var(--ink-3); font-size: 14px; border-top: 1px solid var(--rule); padding-top: 16px; }
"""

CHECK_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" '
    'stroke="currentColor" stroke-width="1.6"/><path d="M4.8 8.2l2.1 2.1 4.3-4.4" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)
CROSS_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" '
    'stroke="currentColor" stroke-width="1.6"/><path d="M5.5 5.5l5 5m0-5l-5 5" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
)


def e(x) -> str:
    return html.escape(str(x))


def status(ok: bool, yes: str = "pass", no: str = "fail") -> str:
    cls, icon, text = ("ok", CHECK_SVG, yes) if ok else ("fail", CROSS_SVG, no)
    return f'<span class="status {cls}">{icon}{e(text)}</span>'


def fmt_ms(ms: float) -> str:
    return f"{ms:,.1f} ms" if ms >= 10 else f"{ms:.2f} ms"


def bench_panels(langs: dict) -> str:
    out = []
    for key, title, desc in WORKLOADS:
        vals = {k: langs[k]["bench"][key]["ms"] for k in ORDER if key in langs[k]["bench"]}
        top = max(vals.values()) or 1.0
        fastest = min(vals.values()) or 1.0
        rows = []
        for k in ORDER:
            if k not in vals:
                continue
            v = vals[k]
            pct = max(v / top * 100, 0.6)
            ratio = v / fastest
            tip = f"{langs[k]['name']}: {v:.3f} ms ({ratio:.1f}× the fastest)"
            rows.append(
                f'<div class="row" title="{e(tip)}"><span class="lang">{e(langs[k]["name"])}</span>'
                f'<div class="track"><div class="fill" style="width:{pct:.1f}%"></div></div>'
                f'<span class="ms">{e(fmt_ms(v))}</span></div>'
            )
        out.append(f'<div class="panel"><h3>{e(title)}</h3><p>{e(desc)}</p>{"".join(rows)}</div>')
    return f'<div class="panels">{"".join(out)}</div>'


def bench_table(langs: dict) -> str:
    head = "".join(f'<th class="num">{e(langs[k]["name"])}</th>' for k in ORDER)
    body = []
    for key, title, _ in WORKLOADS:
        cells = "".join(f'<td class="num">{langs[k]["bench"][key]["ms"]:.3f}</td>' for k in ORDER)
        checksum = langs["c"]["bench"][key]["checksum"]
        body.append(
            f"<tr><td><code>{e(title)}</code></td>{cells}<td class='num'><code>{checksum}</code></td></tr>"
        )
    return (
        '<div class="tablewrap"><table><thead><tr><th>Workload (ms, best of 3)</th>'
        f'{head}<th class="num">Checksum (all four)</th></tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    )


def container_table(langs: dict) -> str:
    rows = []
    for k in ["c", "java", "python", "rust"]:
        L = langs[k]
        iso = L["isolation"]
        caps = (
            "all dropped"
            if "ALL" in iso["cap_drop"] and not iso["cap_add"]
            else ", ".join(iso["cap_add"])
        )
        rows.append(
            "<tr>"
            f"<td>{e(L['name'])}</td>"
            f"<td><code>{e(L['runtime_base'])}</code></td>"
            f"<td class='num'>{L['image_mb']:.1f} MB</td>"
            f"<td><code>{e(iso['user'])}</code></td>"
            f"<td><code>{e(iso['network'])}</code></td>"
            f"<td>{status(iso['read_only_rootfs'], 'read-only', 'writable')}</td>"
            f"<td>{e(caps)}</td>"
            f"<td>{status(iso['no_new_privileges'], 'set', 'missing')}</td>"
            f"<td class='num'>{iso['pids_limit']}</td>"
            f"<td class='num'>{iso['memory_mb']} MB</td>"
            f"<td>{status(L['demo_matches'], 'identical', 'differs')}</td>"
            "</tr>"
        )
    return (
        '<div class="tablewrap"><table><thead><tr><th>Language</th><th>Runtime image</th>'
        '<th class="num">Size</th><th>User</th><th>Network</th><th>Root FS</th><th>Capabilities</th>'
        '<th>no-new-privileges</th><th class="num">PIDs</th><th class="num">Memory</th><th>Demo output</th>'
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def render(r: dict) -> str:
    langs = r["languages"]
    repo_url = f"{r['server']}/{r['repository']}"
    sha = r["commit"]
    blob = f"{repo_url}/blob/{sha}"
    run_link = (
        f'<a href="{e(repo_url)}/actions/runs/{e(r["run_id"])}">CI run {e(r["run_id"])}</a>'
        if r.get("run_id")
        else "a local run"
    )
    all_ok = not r["failures"]
    parity = all(L["demo_matches"] for L in langs.values())
    hardened = sum(
        1
        for L in langs.values()
        if L["isolation"]["network"] == "none" and L["isolation"]["read_only_rootfs"]
    )
    sizes = {k: langs[k]["image_mb"] for k in langs}
    smallest = min(sizes, key=sizes.get)
    largest = max(sizes, key=sizes.get)
    m = r["machine"]

    py_ratio = langs["python"]["bench"]["build_back"]["ms"] / min(
        langs[k]["bench"]["build_back"]["ms"] for k in ("c", "rust", "java")
    )

    guides = "".join(
        f'<li><b><a href="{e(blob)}/{e(path)}">{e(title)}</a></b><span>{e(desc)}</span></li>'
        for title, path, desc in GUIDES
    )

    failures = ""
    if r["failures"]:
        items = "".join(f"<li>{e(f)}</li>" for f in r["failures"])
        failures = f'<h2>Failures</h2><ul class="sub">{items}</ul>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Polyglot Lab Report</title>
<meta name="description" content="CI-generated evidence for one doubly linked list implemented in C, Java, Python and Rust, each running in its own hardened container.">
<style>{CSS}</style>
</head>
<body>
<main>
<h1>Quantum Polyglot Lab — build report</h1>
<p class="lede">One doubly linked list, written four times (C, Java, Python, Rust), each running in its own
locked-down container. Every number below was produced by {run_link} on commit
<a href="{e(repo_url)}/commit/{e(sha)}"><code>{e(sha[:7])}</code></a>. Nothing is typed in by hand.</p>
<p class="meta">Generated {e(r["generated_utc"])} · {e(m["cpu"])}, {e(m["cores"])} cores · Docker {e(m["docker"])} ·
<a href="results.json">raw data (JSON)</a></p>

<div class="tiles">
  <div class="tile"><div class="v">{status(all_ok, "All gates pass", "Gates failing")}</div><div class="k">build fails on any mismatch below</div></div>
  <div class="tile"><div class="v">{status(parity, "4 / 4 identical", "output differs")}</div><div class="k">demo output, byte for byte</div></div>
  <div class="tile"><div class="v">{status(r["checksums_agree"], "5 / 5 agree", "disagree")}</div><div class="k">benchmark checksums — proof of equal work</div></div>
  <div class="tile"><div class="v">{hardened} / 4</div><div class="k">containers with no network and a read-only root</div></div>
  <div class="tile"><div class="v">{sizes[smallest]:.1f} → {sizes[largest]:.0f} MB</div><div class="k">smallest ({e(langs[smallest]["name"])}) to largest ({e(langs[largest]["name"])}) image</div></div>
</div>

<h2>Speed, inside the containers</h2>
<p class="sub">Same algorithm, same data, same checksums. Each bar is scaled to the slowest language for that workload,
so the gap you see is the real gap. On build_back, Python is about {py_ratio:.0f}× slower than the fastest compiled
language. The other three are within a small factor of each other, because the workload is limited by memory
latency and allocation, not by how good the compiler is. Hover a bar for the exact ratio.</p>
{bench_panels(langs)}
<p class="sub" style="margin-top:14px">The same numbers as a table:</p>
{bench_table(langs)}

<h2>Isolation, as Docker applied it</h2>
<p class="sub">Read back with <code>docker inspect</code> from the container that ran the demo, not copied from the
compose file. The job fails if any container runs as root, has a network, has a writable root filesystem, or keeps
any Linux capability. Compiled languages ship on distroless images with no shell. Python has to ship an interpreter,
which is why its image is larger.</p>
{container_table(langs)}

{failures}

<h2>What this repository demonstrates</h2>
<ul class="skills">
  <li><b>Data structures, four ways</b><span>The same operations in C, Java, Python and Rust, with a written guide explaining the trade-offs between them.</span></li>
  <li><b>Memory models</b><span>Manual <code>free</code> in C, garbage collection in Java, reference counting in Python, and a generational arena in safe Rust.</span></li>
  <li><b>Tests that prove something</b><span>Byte-identical output, cross-language checksums, ASan + UBSan leak checks, Rust unit tests.</span></li>
  <li><b>Containers and least privilege</b><span>Multi-stage builds, distroless runtimes, non-root, no network, read-only, no capabilities, resource limits.</span></li>
  <li><b>CI/CD</b><span>GitHub Actions builds, verifies, measures and publishes this page. A red build blocks the merge.</span></li>
  <li><b>Security</b><span>glibc-style safe unlinking, CWE-416/415/401/835, CodeQL and a secret scan on every push.</span></li>
</ul>

<h2>The guides</h2>
<ul class="skills">{guides}</ul>

<h2>Reproduce it</h2>
<pre><code>git clone {e(repo_url)}.git
cd {e(r["repository"].split("/")[-1])}
docker compose -f docker/doubly_linked_list/compose.yaml build
docker compose -f docker/doubly_linked_list/compose.yaml run --rm rust        # demo
docker compose -f docker/doubly_linked_list/compose.yaml run --rm java bench  # benchmark
python3 tools/report/collect.py --out report-data/results.json             # everything on this page</code></pre>

<footer>
<a href="{e(repo_url)}">{e(r["repository"])}</a> · Timings come from a shared CI runner, so they vary from run to run;
compare the ratios, not the absolute values.
</footer>
</main>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("results", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    data = json.loads(args.results.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.html").write_text(render(data))
    shutil.copyfile(args.results, args.out / "results.json")
    print(f"wrote {args.out / 'index.html'}")


if __name__ == "__main__":
    main()
