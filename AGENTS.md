# Instrukcje dla agentów (LLM)

Projekt: **Welesza** — demo ARPG dark fantasy w duchu Diablo 2. Faza projektowa, silnik niewybrany. Zacznij od [README](README.md); kolejność czytania dokumentów jest tam w tabeli.

## Zasady ogólne

- Dokumenty w `docs/` odróżniają decyzje autora od propozycji. Nie przedstawiaj propozycji jako zatwierdzonych i nie dopisuj kanonu za autora; wątpliwości konsultuj z nim.
- Pisz po polsku, jak reszta repozytorium.

## Grafika postaci i potworów

**Jedyna obowiązująca metoda: [`.agents/skills/welesza-sprites/SKILL.md`](.agents/skills/welesza-sprites/SKILL.md)** — prerender brył SDF w NumPy, kod w `assets/sprites/prerender/`, wzorzec `drwal.py`. Przeczytaj skill w całości przed rysowaniem.

- Nie twórz pixel-artu składanego z figur i nie przywracaj usuniętych skilli graficznych (router RTS, retro/painted/prerender-3d, godot-pipeline, pixel-art). Dawały wyniki nie do przyjęcia.
- Specyfikacją postaci jest karta w [bestiariuszu](docs/bestiariusz-demo.md).
- Wiele agentów może rysować równolegle: jedna postać = jeden plik i jeden katalog wyjściowy; wspólnego `sdfkit.py` i kontraktu kadru nie zmieniaj bez zgody autora. Szczegóły w skillu.
