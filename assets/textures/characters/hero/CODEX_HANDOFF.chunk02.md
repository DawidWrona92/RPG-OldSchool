# Brief integracyjny dla Codexa — bohater, Chunk 02

Przeanalizuj źródła z `main` i istniejące modele `vibe/sprite-bohater-codex`. Pobierz z `main` (dawniej gałąź `vibe/hero-materials-chunk02-gpt6`, scalona 27.10.2026) wyłącznie 16 tekstur PNG w `assets/textures/characters/hero/` i manifest `manifest.chunk02.json`. Nie zmieniaj zatwierdzonej koncepcji podróżnika ani fabuły.

**Cel:** uporządkować UV i shadery spodni, butów, skórzanego plecaka i płóciennego posłania; zachować istniejące 3 prototypy tkanin i skóry na `main`. Model Codexa pozostaje źródłem animacji; nie nadpisuj poprawek z innych gałęzi.

**Kryterium akceptacji:** pokaż side-by-side stare vs nowe renderowane sprite'y **192×192** w ośmiu kierunkach, krótki ruch, zimny las i cieplejsze światło, identyczne ustawienia kamery i ekspozycji. Dołącz listę mapowań materiał↔obiekt, sposób uzyskania UV, wynik kontroli seam/moire i problemy, których same tekstury nie rozwiązują. Nie włączaj do renderów tekstury całego tła. W razie złego efektu wróć do starej wersji shaderów na kopii porównawczej, nie akceptuj automatycznie.

Po integracji poproś o decyzję artystyczną; nie deklaruj assetu finalnego bez przeglądu. Nie zmieniaj na siłę geometrii, włosów i animacji w ramach zadania materiałowego.
