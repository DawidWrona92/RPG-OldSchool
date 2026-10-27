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
