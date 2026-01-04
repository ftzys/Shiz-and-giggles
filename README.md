Shiz & Giggles is a fast-paced, Quake-inspired arena shooter. This guide covers how to host and join matches, the default controls, and best practices for configuring servers and contributing new content while preserving the game's classic feel.

## Quickstart

### Hosting a match
1. Launch a dedicated server:
   ```bash
   ./shiz-server +map q1dm1 +fraglimit 30 +timelimit 10 +sv_public 1
   ```
2. Open the necessary UDP port on your firewall (default: `27960`).
3. Share your IP/hostname and port with players.
4. Keep an eye on server logs for players joining and any configuration warnings.

### Joining a match
- From the main menu, choose **Find Server** and select a listed server.
- Or, connect directly via console:
  ```bash
  connect your.host.name:27960
  ```

### Default keybinds
| Action            | Key  |
| ----------------- | ---- |
| Move forward/back | W / S|
| Strafe left/right | A / D|
| Jump              | Space|
| Crouch            | Ctrl |
| Sprint            | Shift|
| Fire              | Mouse1 |
| Alternate fire    | Mouse2 |
| Use/Interact      | E |
| Weapon next/prev  | Mouse wheel |
| Scoreboard        | Tab |
| Console           | ` (backtick) |

## Server tuning guide

### Frag and time limits
- **Frag limit**: Set higher values (30–50) for duel/FFA maps with strong verticality; lower values (15–25) keep smaller maps brisk.
- **Time limit**: 10 minutes suits duels; 15–20 minutes helps FFA or team modes breathe. Consider enabling sudden death on ties.

### Item timers
- **Weapons**: 5–15 seconds depending on power. Keep staple weapons (SG/NG/GL/RL) on short timers; power weapons (LG/RG/BFG) longer.
- **Armor/Mega**: Common armor at 25 seconds, Mega Health at 35 seconds preserves route planning without over-stacking.
- **Power-ups**: Quad/Haste/Regeneration at 90–120 seconds to make them events rather than constants.
- **Ammo/Health shards**: 15–25 seconds to reward positional control without overfeeding.

### Map rotation
Create a rotation file (example: `config/maprotation.cfg`):
```cfg
set g_mapRotation "q1dm1 q1dm3 q3dm6 pro-q3tourney4"
set g_mapRotationMode "loop"   // loop, random, or vote
set g_intermissionTime 10
```
- Avoid repeating similar layouts back-to-back (e.g., two tight vertical arenas).
- Include at least one beginner-friendly map early to keep new players engaged.
- Refresh the rotation periodically to prevent meta stagnation.

### Additional recommendations
- Enable **warmup** so players can load in and test aim before live play.
- Keep **maxpackets** and **rate** defaults conservative for modem-like connections; allow opt-in higher rates for LAN/modern broadband.
- Publish a short **server rules** MOTD so players know what to expect.

## Contributing new maps and weapons (keeping it Quake-like)

### Maps
- **Scale and movement**: Design for strafe-jumping speed—avoid hallways narrower than double-strafe width and keep ceilings high enough for rocket jumps.
- **Flow**: Aim for 2–3 primary routes per room; include loops that reward control without dead-ends.
- **Item placement**: Separate strong weapons from top-tier armor/mega to prevent single-point domination. Use health/armor breadcrumbs to guide flow.
- **Verticality**: Provide meaningful vertical fights (ledges, jump pads) but ensure escape routes to prevent excessive camping.
- **Visuals**: Stick to readable, high-contrast lighting; avoid excessive particle clutter that obscures player silhouettes.
- **Technical**: Seal leaks, optimize vis/occlusion, add player clips to smooth movement, and confirm bot navigation meshes are baked.

### Weapons
- **Roles over redundancy**: Each weapon should fill a clear niche (e.g., hitscan poke, splash denial, close burst) without duplicating existing strengths.
- **Movement interaction**: Preserve momentum-friendly combat—avoid heavy slows, ironsights, or long ADS; keep recoil minimal and predictable.
- **Resource economy**: Tune ammo so power weapons require deliberate control; avoid infinite-ammo power weapons.
- **TTK expectations**: Duels should reward accuracy and positioning; avoid instant-win mechanics outside timed power-ups.
- **Counterplay**: Introduce weaknesses (range falloff, projectile speed, reload rhythm) so no single weapon dominates all ranges.

### Testing and submission
- Playtest with mixed skill groups; gather feedback on flow, item timing, and spawn safety.
- Validate bot behavior and performance (FPS stability, netcode smoothness).
- Update documentation/configs: add map names to rotations and weapon definitions to loadouts before submitting a PR.
- Follow repository conventions for asset naming and include source files (map sources, textures, scripts) where licensing permits.
