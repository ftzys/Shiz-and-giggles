# Arena Specifications and Implementation Guide

This document proposes two compact arena layouts built for fast combat with strong verticality. Each layout includes jump pads, teleporters, and clear item placement for armor, health, and ammo. Lighting and navigation guidelines are provided for efficient implementation in engines such as Unreal Engine 5 or Unity.

## Arena 1: Foundry Stack (small/medium)
- **Theme:** Industrial foundry with stacked mezzanines.
- **Footprint:** ~38m x 32m with three primary vertical layers (ground, mid catwalks, upper cranes).
- **Flow:** Short sightlines with frequent elevation changes; two mirrored jump pads to the upper cranes; teleporters link low spawn to opposite high ground.
- **Key spaces:**
  - Ground floor: furnaces, low cover blocks, and a central hazard pit with grating.
  - Mid level: dual catwalk rings with grated floors overlooking center.
  - Upper level: crane platforms connected by short bridges.
- **Traversal aids:**
  - **Jump Pads (x2):** Corners of ground floor lift to each crane platform (align launch velocity to land near railings).
  - **Teleporters (x2 pads, linked):** Behind furnaces on ground floor; exit behind opposite crane, giving flank potential.
  - **Ladders/ramps:** Short ramps from ground to mid catwalks on both long sides.
- **Item placement:**

| Item               | Location                                                            |
| ------------------ | ------------------------------------------------------------------- |
| 50 Armor           | Mid catwalk east, near railing overlooking pit                      |
| 25 Armor           | Ground floor west, beside furnace block                             |
| Mega Health (1x)   | Upper crane east, exposed; jump pad or teleporter reaches it        |
| Small Health (2x)  | Base of each jump pad landing zone                                  |
| Rockets (1x)       | Mid catwalk west, near ramp entry                                   |
| Bullets (1x)       | Ground floor north alcove                                           |
| Shells (1x)        | Upper crane west bridge                                             |
| Cells (1x)         | Ground floor south behind cover                                     |

## Arena 2: Skyline Atrium (small/medium)
- **Theme:** Rooftop atrium with open central void and glass skywalks.
- **Footprint:** ~34m x 34m plus two corner balconies; three layers (ground plaza, mid balconies, top glass ring).
- **Flow:** Circular loop with vertical combat across the atrium; jump pads feed the top ring; teleporters provide cross-atrium surprise routes.
- **Key spaces:**
  - Ground plaza: low planter cover and a shallow reflecting pool (non-lethal) breaking sightlines.
  - Mid balconies: two opposite balconies with short stairs to ground; small overhang for ambushes.
  - Top ring: glass skywalk loop with clear views; partial roof supports block long shots.
- **Traversal aids:**
  - **Jump Pads (x2):** Ground near each balcony lifts to adjacent top ring segment.
  - **Teleporters (x2 pads, linked):** Under the skywalk on each balcony; exits appear on the opposite balcony behind a support column.
  - **Drop shafts:** Safe drop holes from top ring back to ground plaza corners.
- **Item placement:**

| Item               | Location                                                            |
| ------------------ | ------------------------------------------------------------------- |
| 50 Armor           | Top ring north, slightly exposed                                    |
| 25 Armor           | Mid balcony west near stairs                                        |
| Mega Health (1x)   | Center of ground plaza fountain (forces exposure)                   |
| Small Health (2x)  | Under each teleporter exit alcove                                   |
| Rockets (1x)       | Balcony east tucked behind pillar                                   |
| Bullets (1x)       | Top ring south near drop shaft                                      |
| Shells (1x)        | Ground plaza southwest planter                                      |
| Cells (1x)         | Balcony west, interior corner                                       |

## Lighting setups
Choose one of the following based on performance targets. Bake static meshes wherever possible and keep dynamic/shadow-casting actors minimal.

### Option A: Baked lightmaps (performance-focused)
- Lightmap resolution targets: 64–128 for walls, 256 for hero floors/ceilings, 32 for small props.
- Enable ambient occlusion in the bake; use a high-quality but compressed format.
- Keep dynamic lights to 2–3 small radius fill lights near jump pad landings and teleporter exits to highlight interaction points.
- In UE5: Use **GPU Lightmass** or **Lumen with Surface Cache baked mode**, disable dynamic GI for static meshes, and keep **Max Shadow Rays** modest for faster bakes.
- In Unity (HDRP/URP): Use **Progressive GPU lightmapper**, **Auto Generate** off, bake manually after layout changes; set **Directional Mode** to **Directional** for soft shadows.

### Option B: Real-time lighting (flexibility-focused)
- Limit shadow-casting dynamic lights to <6; favor stationary/mixed lights for upper layers and non-shadowed fill on ground.
- Use cascaded shadow maps with 2–3 cascades; set distance to ~40–60m to cover full arena while limiting cost.
- Enable screen-space ambient occlusion at a medium setting; add light probes/reflection captures around jump pads and teleporters.
- In UE5 Lumen: Use **Software Ray Tracing** for scalability; clamp **Max Trace Distance** to ~30m and **Lumen Scene Detail** to Medium.
- In Unity: Set **Realtime GI** off unless needed; prefer **Mixed** lights with shadow distance at ~60m and **LOD Bias** tuned for targets.

### Occlusion and culling
- Place **occlusion volumes/portals** at corridor entrances to the catwalk rings (Foundry) and balcony archways (Skyline) to reduce overdraw.
- Use **HLOD/LOD Groups** for repeating props (crates, planters, supports); swap to billboard/imp posters past 25–30m.
- Enable **frustum culling** and **distance culling** for small pickups and decals (>45m off-screen).
- For transparent glass (Skyline), keep material overdraw low: single layer, disable SSR on distant panels.

## Navigation meshes and bot support
- Define a nav mesh/volume per arena layer; ensure **vertical links** between layers are flagged:
  - **Jump pads:** Add **nav jump links** with takeoff/landing markers; set arc/impulse to match pad velocity so bots understand the path cost.
  - **Teleporters:** Use **off-mesh links** with bidirectional cost; place entrances slightly inset to avoid stuck collisions.
  - **Drop shafts:** Mark as **one-way off-mesh links** to prevent bots from attempting upward traversal.
- Add **blocking volumes** around hazard pits (Foundry) and fountains (Skyline) to keep nav agents from skimming edges.
- Generate **cover points** along mid-level railings and balcony supports for smarter peeking behavior.
- Bake nav meshes after placing jump pads/teleporters so links are generated correctly; re-bake whenever collision changes.

## Implementation checklist
1. Block out each arena with simple geometry; confirm jump pad arcs and teleporter connections.
2. Place pickups per tables above; ensure line-of-sight balance (no dominant sniper lane across entire arena).
3. Select lighting option (A or B) and bake/adjust shadows; verify 90+ FPS on target hardware with occlusion enabled.
4. Configure nav meshes with off-mesh links for jump pads, teleporters, and drop shafts; test with bots to confirm pathing and item navigation.
5. Add trim/props, set final LODs and culling distances, and lock lighting.
