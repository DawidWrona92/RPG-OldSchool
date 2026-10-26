# Analiza pliku referencyjnego bez fałszywych wniosków

Silnik `pixelcraft.analyze_reference(filename)` zwraca: rozmiar, liczbę kolorów, dominujące barwy, histogram odcieni i diagnostykę krawędzi. **Nie odgaduje** anatomii, epoki artystycznej ani rozkładu oświetlenia. To zadanie dla wizualnej interpretacji człowieka / modelu z dostępem do obrazu.

Po pomiarach utwórz *kartę stylu* w `references/learned/<nazwa>.md`, ze świadomymi regułami: docelowa wielkość sprite'a w px, długość głowy względem sylwetki, proporcje broni, kierunek światła, stopnie ramp, kontrast sylwetki, dopuszczalny dithering, reguła konturu, kotwica.

Nie kopiuj cudzych gotowych assetów do własnej gry; z referencji wykorzystuj abstrakcyjne zasady stylu. Nie używaj przetwarzania jako sztuczki do obejścia praw autorskich. Przy analizie materiału 3D/soft alpha nie traktuj pojedynczego wygładzonego piksela jako „błąd szumu”.

Pełna procedura: render → obejrzyj w 1× i 8× → oceń w kontekście gry → popraw konkretny element generatora → render ponownie. Zapisz źródło generatora i raport QA.
