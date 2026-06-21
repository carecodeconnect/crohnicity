"""Per-case referral-pathway graphs from the model predictions in data/out/.

Reads each `data/out/P###.json`, takes its `referral_pathway` (a list of canonical `PathwayStep`
tokens — already consolidated, so no phase-mapping needed), and writes an interactive pyvis graph
per patient to `data/out/referral_pathway_<pid>.html`. Also prints phase/transition frequencies.

Capturing cycles / repetition — why & how:
- WHY: a referral journey is often *cyclic* — relapse, loss_of_response, repeated
  biologic_switch. The prompt asks for `referral_pathway` as an event log (repeat a step each
  time it recurs), so a recurring phase appears more than once. A Sankey / straight chain hides
  those loops, so we draw a directed graph that can show them.
- HOW: a repeated phase collapses to one node the journey revisits (node size grows with the
  visit count), and every edge's tooltip carries its traversal count `(xN)`. Layout is chosen
  per journey: a *cyclic* one (a phase recurs) uses a force layout so loops render as loops; a
  *linear* one uses a left-to-right hierarchy for a clean start -> outcome read. Recurrence is
  also recoverable from `treatment_records`; the cyclical deep-dive is in README "Next Steps".

Run: `uv run python src/referral_pathway_analysis.py`  (offline — reads artefacts, no Gemini calls)
"""

import json
from collections import Counter
from pathlib import Path

import pandas as pd
from loguru import logger
from pyvis.network import Network

OUT = Path(__file__).resolve().parents[1] / "data" / "out"
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
# loguru file sink: persist the run summary + catch per-graph errors during regeneration
logger.add(LOG_DIR / "referral_pathway.log", level="INFO", rotation="1 MB")


def load_pathways() -> dict[str, list[str]]:
    """patient_id -> ordered referral_pathway tokens, from the persisted predictions."""
    return {
        p.stem: json.loads(p.read_text())["referral_pathway"]
        for p in sorted(OUT.glob("P[0-9][0-9][0-9].json"))
    }


def render(pid: str, seq: list[str], path: Path) -> Path:
    """Write an interactive directed graph for one patient's pathway. Recurrence shows as the loop
    it is: a revisited phase is a single node the journey cycles back to (bigger the more it
    recurs), with the traversal count in each edge's tooltip. Cyclic journeys use a force layout
    (loops render as loops); linear journeys use a left-to-right hierarchy (clean start -> outcome)."""
    net = Network(
        directed=True,
        height="750px",
        width="100%",
        cdn_resources="remote",  # tiny files (load vis.js from CDN); 50 in_line copies = ~50 MB
        heading=f"Referral pathway: {pid}",
    )
    nodes = Counter(seq)
    edges = Counter(zip(seq, seq[1:]))
    for phase, count in nodes.items():
        net.add_node(
            phase, label=phase, value=count
        )  # a revisited phase -> bigger node
    for (s, d), count in edges.items():
        net.add_edge(
            s, d, title=f"{s} -> {d} (x{count})"
        )  # count in tooltip; uniform width
    if len(seq) != len(nodes):
        # a phase recurs -> the journey LOOPS; a force layout draws loops as loops (hierarchical
        # left->right can't lay out a cycle and flattens it into a confusing line).
        net.set_options('{"physics": {"enabled": true, "solver": "forceAtlas2Based"}}')
    else:
        # linear journey -> hierarchical left-to-right, clean and readable start -> outcome.
        net.set_options(
            '{"layout": {"hierarchical": {"enabled": true, "direction": "LR", '
            '"sortMethod": "directed", "levelSeparation": 250, "nodeSpacing": 130}}, '
            '"physics": {"enabled": false}}'
        )
    net.write_html(str(path), notebook=False, open_browser=False)
    # pyvis renders `heading` twice (known quirk) — keep a single page-level <h1>.
    html = path.read_text()
    dup = f"<h1>Referral pathway: {pid}</h1>"
    if html.count(dup) > 1:
        path.write_text("".join(html.rsplit(dup, 1)))
    return path


@logger.catch(reraise=True)
def main() -> None:
    """Write a per-case journey graph for every patient + log phase/transition frequencies.
    Per-graph errors are logged and skipped so one bad pathway can't abort the whole regeneration."""
    pathways = load_pathways()
    nodes: Counter[str] = Counter()
    edges: Counter[tuple[str, str]] = Counter()
    for seq in pathways.values():
        nodes.update(seq)
        edges.update(zip(seq, seq[1:]))

    phase_freq = pd.DataFrame(nodes.most_common(), columns=["phase", "count"])
    transitions = pd.DataFrame(
        [(a, b, c) for (a, b), c in edges.most_common()],
        columns=["from_phase", "to_phase", "count"],
    )
    logger.info(
        "{} pathways - {} distinct phases - {} transitions",
        len(pathways),
        len(nodes),
        sum(edges.values()),
    )
    logger.info("PHASE FREQUENCY\n{}", phase_freq.to_string(index=False))
    logger.info("TRANSITIONS (top 20)\n{}", transitions.head(20).to_string(index=False))

    written = 0
    for pid, seq in pathways.items():
        try:
            render(pid, seq, OUT / f"referral_pathway_{pid}.html")
            written += 1
        except Exception:
            logger.exception("failed to render graph for {}", pid)
    logger.info(
        "wrote {}/{} per-case graphs -> {}/referral_pathway_*.html",
        written,
        len(pathways),
        OUT,
    )


if __name__ == "__main__":
    main()
