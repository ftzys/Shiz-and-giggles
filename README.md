# Performance Tuning Plan

This document outlines the actionable steps to optimize frame timing, rendering, and networking for the target hardware, with special attention to worst-case 16-player chaos scenarios.

## Profiling and Instrumentation
- Profile on target hardware early and continuously; collect captures for GPU, CPU, and memory during both solo play and 16-player stress scenes.
- Record frame time budgets separately for simulation (tick) and rendering, and log spikes with markers (e.g., weapon fire, VFX bursts, teleport events).
- Track perf regressions via automated captures on repeatable scenes (e.g., “16-player plaza chaos”), saving baseline CSVs for frame time, bandwidth, and CPU utilization.

## Frame Timing: Tick vs. Frame
- Decouple game tick from render frame when possible; clamp simulation rate (e.g., 60–120 Hz) and interpolate/extrapolate for display refresh variability.
- Tune tick rate to stay within CPU budget under peak load; use instrumentation to flag when the simulation overruns its budget.
- Enable frame pacing to smooth frame delivery; verify even frame spacing under VSync on/off and during large VFX bursts.
- Add a user-facing VSync toggle (with fallback to driver-controlled adaptive vsync) and persist the setting; default to VSync on for stability, but expose an unlocked option for latency-sensitive users.

## Rendering Optimizations
- Level of Detail (LOD): ensure meshes have at least 2–3 LODs; use screen-size thresholds validated on target displays. Audit hero assets visible in the 16-player chaos scene first.
- Lighting: bake static and stationary lighting where possible; minimize dynamic shadow casters. Use lightmaps/light probes for crowds and set conservative shadow draw distances.
- GPU instancing: instance repeatable props (cover objects, debris, foliage) and ensure material compatibility (no per-instance material variants where avoidable).
- VFX pooling: pool particle systems and decals; avoid per-spawn allocations. Pre-warm expensive effects used in chaotic encounters (e.g., explosions, ultimates).

## Networking and Bandwidth
- Monitor bandwidth and CPU usage during 16-player chaos scenes; log per-client and server CPU plus bandwidth (avg/peak).
- Tune net update rates per actor class (players > projectiles > ambient) and cap packet sizes to stay within MTU. Bundle small updates and avoid redundant component replication.
- Apply relevancy culling and priority-based throttling; lower update frequency for distant/occluded actors and cosmetic-only effects.
- Validate packet serialization costs on CPU; cache frequently sent payloads where safe and avoid per-frame heap allocations in replication paths.

## Checklist for Implementation
- [ ] Add automated perf capture on target hardware for the 16-player chaos scenario.
- [ ] Implement frame pacing verification and expose a VSync toggle with persisted user settings.
- [ ] Audit tick vs. frame timings; decouple and clamp simulation rate as needed.
- [ ] LOD audit and fixes for hero assets; enforce baked lighting on static geometry.
- [ ] Enable GPU instancing for repeatable props; ensure material compatibility.
- [ ] Introduce pooled VFX and pre-warm heavy effects.
- [ ] Instrument and tune network update rates, packet sizes, and relevancy rules during 16-player chaos tests.
