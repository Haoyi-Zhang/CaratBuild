# Fact, window, retention, and projection schema

## 1. Canonical fact set

Replica state is a finite set of canonical UTF-8 JSON texts. Parsing rejects duplicate object fields, unknown fields, malformed numbers, invalid enums, repeated references, and noncanonical structures. Canonical text is the set key. Merge is set union; two different facts at one event coordinate remain distinct and cause refusal rather than last-writer selection.

Every fact has:

- `kind` — `mint`, `presentation`, `transform`, `effect`, or `seal`;
- `event_id` — an origin-owned coordinate `origin:counter`;
- `batch` — the accounting-window name;
- a kind-specific globally scoped identifier.

The network service bounds a fact at 32 KiB, a frame at 1 MiB, a page at 32 facts, and an endpoint store at 2,048 facts or 32 MiB. Larger direct in-memory experiments bypass the service limits and are reported separately.

## 2. Fact kinds

### Mint

A mint defines one work-unit identity and positive integer mass:

```text
unit_id, mass, batch, origin, event_id
```

Gross mass is the sum of masses over uniquely defined `unit_id` values. No other fact kind creates mass.

### Presentation

A presentation names a branch label and a finite duplicate-free signed set of unit identities. Signs are `+1` or `-1`. Presentation facts expose representations without minting the units again.

### Transform

A transform names duplicate-free, disjoint input and output presentation IDs and one declared law:

- `rebase` — one input and one output with the same signed unit set;
- `cherry-pick` — one input and one output with the same signed unit set;
- `fork` — one input and one or more outputs, each preserving the signed set;
- `squash` — two or more inputs and one output containing their sign-consistent union;
- `revert` — one input and one output with every sign reversed.

The language checks only these relations. It does not infer semantic source equivalence and does not require an acyclic relation graph.

### Effect

An effect names one unit, one presentation, an outcome (`pass`, `fail`, or `skip`), and an opaque dependency label. The named unit must belong to the named presentation. Effects do not affect gross mass. The core checker does not prove that the dependency label is a real executable edge.

### Seal

A seal is zero-mass completion evidence for one origin and batch. It contains:

- `seal_id`;
- `origin` and `batch`;
- `previous_seal_event` or genesis;
- `frontier`, the last data coordinate allocated to the batch;
- its own event coordinate immediately after the frontier.

For origin `o`, the seal declares the interval `(previous, frontier]`. The interval may be empty. The positive theorem assumes that each origin truthfully reports its complete allocation to the batch.

## 3. Ordinary integrity

A determined accepted state has:

- one definition per semantic identifier;
- one canonical fact per event coordinate;
- all named units and presentations resolved;
- every transform satisfying its declared law;
- every effect unit belonging to its presentation.

The decoder emits refusal witnesses. The separately structured checker reevaluates their public predicates and verifies inclusion minimality under the fixed support convention. It shares the canonical normalizer and is therefore differential validation, not a fully independent formal implementation.

## 4. Fixed-roster finality

For a nonempty fixed origin roster, a batch is final only when:

1. every roster origin has exactly one batch seal and no outside origin contributes batch data or a seal;
2. each covered coordinate contains exactly one non-seal batch fact;
3. no same-batch fact lies outside the declared intervals;
4. every predecessor chain is present, origin-consistent, strictly decreasing, and reaches genesis;
5. event coordinates and mint, presentation, transform, effect, and seal IDs are globally unambiguous;
6. the batch is self-contained: its relations do not require definitions from another window;
7. the ordinary decoder and separate checker both accept and agree on unit count, mass, and normalized violations.

A final result is stable only under admissible extensions: later batches must use new coordinates and globally fresh identifiers. A same-window out-of-range fact or later identifier reuse produces refusal rather than a silent revised final value.

## 5. Retention receipts and certificates

A raw endpoint may issue a receipt only after it stores the complete batch and both finality paths accept. A receipt names:

- batch;
- holder endpoint;
- crash fault bound `f`;
- the full set of origin seal IDs.

Receipt persistence is synchronized before acknowledgment. Receipt records are bounded and newline terminated. Recovery replays complete records, truncates only an incomplete final fragment, and rejects any malformed newline-terminated record. The endpoint reloads each receipt as a permanent raw-data pin before serving requests; a pinned holder refuses projection even under another otherwise valid certificate.

A retention certificate combines receipts and is valid only when:

- the origin and endpoint rosters equal the configured fixed rosters;
- the fault bound is in range;
- receipts agree on batch, fault bound, and seal set;
- holder names are distinct and belong to the endpoint roster;
- at least `f+1` holders are named.

The certificate is structurally trusted and unsigned. It is not a Byzantine attestation.

## 6. Projection summary

A nonholder may project a final self-contained batch after validating a retention certificate. The summary stores:

- exact `(unit_id, mass)` pairs;
- total unique units and gross mass;
- presentation count;
- total, passing, and failing effect counts;
- every presentation ID;
- every transformation ID;
- every effect ID;
- effect counts grouped by unit and outcome;
- the certificate.

The endpoint retains zero-mass seals as predecessor-chain anchors. On load, it revalidates the certificate, checks that the endpoint is not a named raw holder, recomputes the projected result, and requires the retained anchors to match the certificate exactly. Summary and certificate persistence precede atomic raw-log replacement. Recovery completes replacement if the process stopped between those steps.

The four identifier sets reject reuse or replay after projection. The summary does not preserve branch names, transformation edges, dependency labels, or enough detail to reconstruct an arbitrary discarded witness. Imported summaries are structurally trusted rather than cryptographically authenticated.

## 7. Services and transport

The original bounded service uses five loopback listeners and five logs in one event-loop process. The retention experiment uses five independent OS processes and five logs. Its controller schedules bounded sender-to-receiver page relays, preserves a two-group partition for two rounds, restarts one endpoint before healing, and never constructs or broadcasts the global union. Frames are four-byte big-endian length-prefixed JSON.

The correctness transport repeatedly requests pages of complete canonical facts. End-of-file resets the cursor so later sweeps revisit earlier sort positions. Under a finite quiescent union, fair successful sweeps, surviving copies, and sufficient capacity, every connected survivor eventually holds the same set. This is not a communication-optimal protocol.

A separate coordinate-gap transport is retained as a negative comparator. Permanent low holes can hide later facts, and alternative facts at one coordinate can remain mutually undiscovered.

## 8. Durable-log semantics

A whole admission is validated before append. Complete canonical records are newline terminated, flushed, synchronized, and acknowledged only afterward. Recovery:

- replays duplicate complete records idempotently;
- truncates only an incomplete final fragment;
- rejects a malformed complete record;
- reloads and revalidates summaries, certificates, seal anchors, and holder pins before serving requests.

A complete unacknowledged record may survive an ambiguous failure. The claim covers tested process termination under the stated synchronization assumptions, not power loss or disk corruption.
