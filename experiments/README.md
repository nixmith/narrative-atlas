# Narrative Atlas — Experiments

This directory holds experimental work that supports — but is not part of — the production codebase under `src/`. Validation harnesses, exploratory simulations, identifiability stress-tests, and any code whose purpose is to defend or refute a design-document commitment lives here. Production code that downstream consumers depend on does not.

The separation is strict. Experiments may freely import standard scientific Python libraries and may carry their own dependency lists; they do not import from `src/`, and `src/` does not import from them. When an experimental result graduates to a production capability, the relevant code is rewritten to `src/` conventions, given a proper module boundary, and the experiment that produced it is left in place as the historical record of how the decision was reached.

## Layout

Every experiment lives at `experiments/<layer>/<short_descriptor>_<version>/`. Layers correspond to the five-layer Narrative Atlas model documented in `docs/`; the descriptor is a short slug that names what the experiment does; the version is a serial integer prefixed by `v`, not semver. Versions advance when the experiment is meaningfully revised — a v1 of a harness is not a bugfix on v0, it is a new harness whose scope, model, or methodology has changed enough that comparison to v0 is informative. Bugfixes within a version are committed in place.

A canonical experiment directory contains:

```
experiments/<layer>/<descriptor>_<version>/
├── README.md          # what this is, how to run it, how to read its outputs
├── requirements.txt   # experiment-local dependencies
├── run.py             # the entry point; reproducible from a single command
├── outputs/           # gitignored; created at runtime
└── notes.md           # observations, deviations from spec, gaps for future work
```

Additional files (audit documents, status reports, alternative entry points, fixture data) may be added as the experiment requires; the four files above are the minimum.

## What is committed and what is not

Code, README, requirements, notes, and any audit or status documents are committed. Anything written to an `outputs/` directory is not — the project root `.gitignore` excludes `experiments/*/*/outputs/` recursively. Experimental outputs are reproducible by re-running the harness; they are not the historical record. The harness, the notes, and the documentation around them are.

## Naming conventions

Layer directories use the same names as the design documents under `docs/layers/` (e.g., `layer_2/`, `layer_4/`). Descriptors are lowercase snake_case and name the *artifact*, not the *question* — `hmm_validation` rather than `does_the_hmm_work`. Versions are `v0`, `v1`, `v2`. A v0 is initial; a v1 is a deliberate successor whose existence is documented in the predecessor's `notes.md` or in the relevant design document.

## Adding a new experiment

Create the directory and the four required files. Write `README.md` first — naming the question the experiment is answering, the single-command invocation, and the interpretation of outputs — before writing `run.py`. The README is the contract; the code is the implementation. If a contributor cannot tell from the README alone what the experiment is for and how to run it, the README is not yet adequate and the experiment is not ready to commit.

Do not share code between experiments. If two experiments would benefit from a common utility, that utility belongs in `src/` (after promotion review) or it belongs duplicated. Cross-experiment dependencies create coupling that makes the historical record unreliable.

## Relationship to the design documents

Experiments validate or stress-test commitments made in the design documents under `docs/layers/`. A design document references the experiments that support its claims by relative path; an experiment references the design document section whose commitment it is testing. The relationship is bidirectional and explicit. When a design document is updated, the experiments it cites are reviewed for whether they still apply to the new commitment.
