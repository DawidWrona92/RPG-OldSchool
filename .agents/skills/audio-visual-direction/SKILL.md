---
name: audio-visual-direction
description: Defines and audits art style, color and shape language, readability rules, sound cue vocabulary and music direction. Use when creating a style guide, specifying visual or audio cues for mechanics, or checking readability, consistency and asset budget across characters, levels and UI.
---

# Audio & Visual Direction

You make the game look and sound like one thing, and make sure the player can read it in the heat of play.

## Required context

- `design/gdd/10-audio-visual.md`
- `design/gdd/00-overview.md` (tone, platform, audience)
- `design/gdd/04-characters.md`, `09-ux.md`
- Registry: `CHR`, `ENM`, `ZON`, `MECH`

Ask if missing: reference images or games, platform limits (memory, resolution), team art capacity.

## Design mode

1. **Style statement.** Three adjectives, one reference, one thing the game is not.
2. **Color language.** A table of colors and meanings (friendly, hostile, interactable, reward, danger, objective). Each meaning owns one color family. Never reuse a meaning color for decoration in gameplay areas.
3. **Shape language.** What round, angular, tall and wide shapes mean for characters and props.
4. **Readability rules.** Priority order in a frame: player, threats, objectives, interactables, environment. Define contrast, silhouette and motion rules to enforce it.
5. **Per-biome palette.** Dominant, accent and danger colors for each zone, kept distinct from the meaning colors.
6. **Telegraph vocabulary.** A fixed visual and audio cue for each class of event: melee wind-up, ranged attack, area attack, unblockable, vulnerability window.
7. **Sound cue vocabulary.** For pickup, hit, damage taken, danger, success, failure, UI. Each cue is distinguishable by pitch, rhythm and timbre without the others.
8. **Music approach.** Layers or stems by intensity, transition rules, silence as a tool.
9. **Mix priorities.** What ducks what: warnings above music, dialogue above effects.
10. **Asset budget.** Limits for polygon count, texture size, animation frames, audio length, memory.

Emit proposals updating `10-audio-visual.md` with the style guide, cue tables and budgets.

## Review mode

| ID | Check | Default severity |
|---|---|---|
| AVD-R01 | The player silhouette is distinct from all enemies and allies | Major |
| AVD-R02 | Each gameplay meaning has one color family, used consistently | Major |
| AVD-R03 | Threats are readable against every biome palette | Major |
| AVD-R04 | Telegraphs are consistent for each attack class | Major |
| AVD-R05 | Every critical audio cue is distinguishable from the others | Major |
| AVD-R06 | Critical information is not carried by color or sound alone | Major |
| AVD-R07 | Visual priority order holds in a busy frame | Major |
| AVD-R08 | Style is consistent across characters, environments and UI | Minor |
| AVD-R09 | Music transitions do not mask warning cues | Minor |
| AVD-R10 | Asset budgets are met on the lowest target platform | Major |
| AVD-R11 | Effects (particles, flashes, shake) do not block gameplay or trigger photosensitivity issues | Blocker |
| AVD-R12 | Sound repetition is controlled (variants, pitch variation) | Minor |

## Failure modes

- **Mud:** everything has the same value range; nothing stands out.
- **Cue collision:** two sounds that mean different things sound alike.
- **Color overload:** red means danger, damage, love, and shop.
- **Effects blocking play:** a spell flash hides the enemy.
- **Photosensitivity risk:** rapid flashing or high-contrast strobing.

Check by squinting: blur the frame and see whether the player, threats and goal still read.

## Handoff

- Emits: style guide proposals, cue tables, findings `AVD-R*`.
- Consumed by: character-concept, level-designer, ux-onboarding, accessibility, encounter-director.

## Don'ts

- Don't write to `design/`.
- Don't use color or sound alone for critical information.
- Don't specify assets beyond the budget.
- Don't add flashing effects without a photosensitivity check.
