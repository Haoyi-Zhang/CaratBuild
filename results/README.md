# Reproduction evidence

`raw/` contains per-case outcomes and negative evidence. `summary/` contains aggregate collectors and descriptive resource measurements. Semantic reproduction checks compare counts, sets, masses, decisions, witness acceptance, finality, crash survival, and projection preservation. Timings and operating-system memory high-water marks are descriptive and may differ across runs.

## Stage inventory

### Six original campaigns

1. `manipulation` — 720 generated valid histories;
2. `faults` — 160 five-replica coordinate-emulator runs;
3. `ambiguity` — 400 injected-invalid histories and witnesses;
4. `scale` — 18 direct in-memory rows;
5. `compaction` — six bulk projection sizes;
6. `exhaustive` — 960 tiny delivery schedules, 39 composed operation sequences, and the permanent-hole counterexample.

### Twelve boundary campaigns

1. `identity` — strongest scalar baseline over all 1,120 histories;
2. `transport` — coordinate-gap counterexamples plus 324 complete-page cases;
3. `service-pilot` — bounded endpoint pilot;
4. `service` — twelve framed five-endpoint campaigns;
5. `recovery` — whole-process termination and acknowledged-set reconstruction;
6. `compaction-boundaries` — projection, overlap, forged-summary, and replay decisions;
7. `public-pair` — six adapter decisions and one service run;
8. `semantic-boundaries` — four deliberately accepted non-claims;
9. `sealed-windows` — two completion worlds, 32 arrival vectors, 32 future vectors, identifier reuse, five service phases, and sealed projection;
10. `multiprocess-retention` — five independent processes, two partitioned exchange rounds, a pre-heal restart, pagewise convergence, `f+1` certificates, crashes, raw export, and projection recovery;
11. `completion-boundaries` — identity worlds, ten support removals, six ablations, and Byzantine omission worlds;
12. `executable-build` — three local task-graph scenarios.

The final collector combines all eighteen campaigns with the 51-test outcome; the artifact audit then checks the claim ledger, 78-row reference audit, provenance surface, and package hygiene.

## Principal recorded results

- 720 valid and 400 invalid histories; unique-mint mass exact in all 1,120;
- 400 integrity refusals and 400 verified witnesses;
- occurrence-based amplification reaches 17× while unique-mint mass remains 1×;
- identity observation identical with oracle masses 5 and 10;
- completion observation identical with complete mass 10 or delayed mass 5;
- exactly one final arrival vector among 32; all 32 admissible future subsets preserve mass 15;
- ten support removals refused and six ablation counterexamples admitted by their weakened predicates;
- five processes and logs converge by pagewise relay in three rounds after two partitioned rounds and a pre-heal restart; the controller does not compute the union;
- three holders at `f=2`, all 16 crash sets, two holder kills, and a 205-fact survivor export;
- projected restart preserves mass 600; interrupted deletion proceeds only after exact reconstruction from surviving raw facts; tampered pending summaries, cross-summary overlap, malformed complete receipt/projected records, and closed replay fail closed; holder pin survives restart and certificate rotation;
- bulk projection reduces 503,178 to 74,079 bytes (85.2778%);
- two projected process logs reduce 43,480 to 10,382 bytes (76.1224%);
- all 324 full-page cases converge; retained coordinate-gap cases do not;
- twelve service campaigns reach exact union, with six common acceptances and six common refusals;
- one process kill preserves 46 acknowledged fact occurrences and reaches the 46-fact union;
- executable build records twelve outcomes from nine subprocesses: seven pass, two fail, three skip;
- largest direct row: 20,000 units, 20,013 facts, 2,972,060 bytes, 774.196 ms median decode, and 754.883 ms median checker time.

## Resource scope

`summary/complete_overview.json` records the retained run's post-import stage CPU total and largest single-worker resident-memory high-water mark. The CPU value excludes imports, manuscript work, historical engineering, and unmeasured parent/child activity outside stage instrumentation; the memory value is not concurrent aggregate RSS. Clean reproduction is required to preserve semantic decisions and counts, not environment-specific timing. `summary/artifact_audit.json` records the final artifact-local consistency audit.
