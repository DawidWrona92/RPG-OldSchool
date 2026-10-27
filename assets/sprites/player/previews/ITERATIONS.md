# Przegląd iteracji

- Iteracja 01: rzeczywisty próbny render. `iteration01-diagnostic.png` jest
  powiększonym wycinkiem diagnostycznym, nie widokiem 1:1 ani finalnym wynikiem.
  Wykryto rozłączone stawy wskutek użycia nieprzeliczonych macierzy rodziców,
  nienaturalnie opinający kaftan, sztywną linię zarostu i zdublowane dłonie
  objęte selekcją spodni.
- Iteracja 02: jawne macierze spoczynkowe i macierze rodziców przy wyznaczaniu
  pozy; stawy są połączone. Kaftan zastąpiono osobnymi wykrojami, koszulę
  ciągłą tuniką z rękawami, wyłączono dłonie z selekcji spodni. Zarost jest
  jaśniejszy i mniejszy; dodano pasma włosów, obszycia i rzemienie plecaka.

W obu próbach faktycznie uruchomiono Cycles CPU w Blenderze 4.3.2.
Build systemowy nie zawiera OpenImageDenoise; pipeline używa większej liczby
próbek i supersamplingu zamiast żądać niedostępnego odszumiania.

Próby nie dorównują malarskiemu detalowi referencji. Kolejna kontrola obejmuje
światło, czytelność w świecie oraz ruch całego szkieletu, nie tylko statyczną pozę.

- Iteracja 03–04: kompletny spoczynek i chód (160 klatek), fizyczny cień jako
  osobny render, 192 px eksport z renderów 384 px. Sprawdzono 242 pozy szkieletu
  oraz zgodność 22 póz kluczowych z zapisanymi akcjami. Przegląd 1:1 pokazuje
  nadal zbyt gładkie tkaniny i uproszczoną sylwetkę względem konceptów.
- Iteracja 05: po dostarczeniu przez autora trzech widoków podróżnika zmieniono
  płaszcz na dłuższy i brązowy, odsłonięto przedramiona, dodano podwinięte rękawy,
  luźniejsze spodnie, większe pasma włosów i pustą pochwę. Osobny test Object Index
  ujawnił zasłanianie miecza i oglądanie płaszczyzny ostrza z krawędzi w NW.
  Poprawki obejmują pozycję noszenia, stabilizację nadgarstka i obrót płaszczyzny
  głowni; wyniki końcowe zapisuje `render-validation.json`.
