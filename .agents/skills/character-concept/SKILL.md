---
name: character-concept
description: Designs and audits player characters, NPCs and enemies as concepts: role, silhouette, personality, abilities, backstory and tactical function. Use when creating a new character or enemy, checking a roster for overlap, or verifying a character fits lore and mechanics.
---

# Character Concept

You turn an idea into a character the player can read at a glance and the team can build.

## Required context

- `design/gdd/00-overview.md` (pillars, tone, audience)
- `design/gdd/04-characters.md`, `02-world.md`, `03-narrative.md`
- Registry entries with prefix `CHR`, `ENM`, `FAC`, `SKL`

## Design mode

Produce one concept card per character. Every card has:

1. **Name, ID proposal, role.** Role is a gameplay role (tank, ranged, support, flanker, brute, swarm, elite, boss, ally, vendor, guide) plus a narrative role (mentor, rival, victim, villain).
2. **One-line hook.** Who they are in a sentence a stranger would remember.
3. **Silhouette and shape language.** Three visual anchors (overall shape, signature prop, color accent). Must read in black on white at thumbnail size.
4. **Personality.** Three traits, one contradiction, one want, one fear.
5. **Abilities** (for combatants): each with a name, telegraph, effect, counter-play. Reference existing `SKL-` IDs where possible.
6. **Tactical question** (enemies): the one problem this enemy asks the player to solve.
7. **Weakness and tell** (enemies): what the player exploits and how they learn it.
8. **Faction and backstory.** Two or three sentences, tied to an `FAC-` ID and consistent with lore.
9. **Voice notes** for dialogue-voice: speech pattern, vocabulary, taboos.
10. **Visual and audio cues** for audio-visual-direction.

Enemy rosters: aim for archetype coverage (tank, ranged, support, flanker) and for distinct tactical questions. Two enemies may share an archetype only if they ask different questions.

Emit proposals for `CHR-`, `ENM-` entries.

## Review mode

| ID | Check | Default severity |
|---|---|---|
| CHA-R01 | Silhouette is distinct from every other character in the registry | Major |
| CHA-R02 | Role is clear within three seconds of seeing the character | Major |
| CHA-R03 | Enemy has a unique tactical question | Major |
| CHA-R04 | Every ability has a telegraph and a counter | Major |
| CHA-R05 | Backstory is consistent with canon lore and faction goals | Major |
| CHA-R06 | Personality traits show up in behavior, not only in text | Minor |
| CHA-R07 | Roster covers the archetypes the encounters need | Minor |
| CHA-R08 | Character fits the tone bible and audience rating | Major |
| CHA-R09 | Design avoids harmful stereotypes or lazy tropes | Major |
| CHA-R10 | Abilities exist in the mechanics (no invented verbs) | Blocker |
| CHA-R11 | Asset cost is within the scope budget | Minor |
| CHA-R12 | Character is memorable: removing the name, a player could still describe them | Note |

## Failure modes

- **Silhouette collision:** two enemies read the same in a fast fight.
- **Lore-only characters** with no gameplay presence or gameplay-only enemies with no world presence.
- **Unfair tells:** the ability has no telegraph, or the telegraph is the same as another enemy's.
- **Tropes by default:** the grizzled mentor, the evil cult, with nothing added.

## Handoff

- Emits: `CHR-*`, `ENM-*` proposals; findings `CHA-R*`.
- Consumed by: combat-balancer (stats), encounter-director (placement), dialogue-voice, audio-visual-direction.

## Don'ts

- Don't write to `design/`.
- Don't assign numeric stats. That is combat-balancer's job.
- Don't invent factions or locations. Propose them through narrative-director.
- Don't give an enemy an ability the mechanics do not support.
