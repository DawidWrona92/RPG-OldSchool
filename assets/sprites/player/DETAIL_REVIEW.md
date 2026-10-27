# Bohater — statyczny pass detali po nowych referencjach

**Wersja robocza do oceny wyglądu.** Autor poprosił, aby najpierw dopracować
pojedynczy render, a dopiero potem wracać do ruchu. Model nadal pochodzi
z tego samego prototypu; nie zmieniono koncepcji podróżnika ani skali postaci.

[Przegląd w przeglądarce](reviews/detale-01/index.html) ·
[osiem kierunków 1:1](reviews/detale-01/osiem-kierunkow-1x.png) ·
[przed/po 1:1](reviews/detale-01/porownanie-1x.png) ·
[duże rendery przed/po](reviews/detale-01/model-przed-po.png) ·
[włosy i zarost](reviews/detale-01/glowa-przed-po.png).

Edytowalne źródło tej pracy: [bohater_detale.blend](source/bohater_detale.blend),
[manifest](source/bohater_detale.source.json).
Zachowany model poprzedniego pełnego eksportu: [bohater.blend](source/bohater.blend)
(rewizja 08). [Raport pełnego eksportu 08](REPORT.md) ma własne wyniki i ograniczenia.
Nowych detali nie przypisujemy do jego atlasów ani testów animacji.

## Zmiany względem ostatniego renderu

- **Płaszcz:** dłuższe dolne połacie, nieregularny brzeg, kilka głębszych wyrwań,
  trzy miejscowe otwory, luźne włókna i wąskie strzępki. Uszkodzenia mają geometrię;
  nie są samym szumem w shaderze. Zachowano otwarty przód i praktyczną sylwetkę.
- **Naprawy:** naszyta łata na dolnej połaci płaszcza i miękka łata lewego kolana,
  z osobno rozmieszczonymi ściegami. Kolory pozostają brunatne i zgaszone.
- **Kaftan:** dolne połacie zachodzą teraz na biodra i górę spodni, z wąskim
  rozcięciem z przodu i nierównym obszyciem. Pas przeniesiono na zewnętrzną
  powierzchnię stroju, aby nie znikał w wydłużonych połaciach.
- **Koszula:** widoczny jest kontrolowany, poszarpany brzeg pod kaftanem.
  Wcześniej lniany dół tworzył nienaturalny jasny fragment przy kroczu;
  samo schowanie go pod pas dawało następnie zbyt równe odcięcie. Nowy układ
  warstw odtwarza rozwiązanie z referencji, bez pojedynczego długiego płata.
- **Włosy:** sztywne bryły i płaty zastąpiono 14 000 drobnych włókien Curves.
  Układ jest ciągły od czubka do boków, asymetryczny przy grzywce, z różną
  długością i odstającymi końcami. Krótki podkład wypełnia nasadę przy skroniach.
- **Zarost i głowa:** 4260 krótkich włókien na policzkach, żuchwie i podbródku,
  zachowany wąs oraz odsłonięte usta i nos. Delikatnie wzmocniono istniejącą
  żuchwę, nos i łuki brwiowe; nie podmieniano modelu głowy.

Wilgoć, brud i przetarcia nadal korzystają z dostarczonych materiałów i masek,
z ograniczeniem do odpowiednich partii. Nowe łaty, ściegi i postrzępienia są
osobnymi elementami tego samego źródła. Użyto dostępnej biblioteki autora;
nie pobierano nowych zewnętrznych assetów.

## Odniesienie do artów

Zachowano podstawowe cechy: zwykły dorosły podróżnik, len i skóra, ciemne spodnie,
płaszcz, plecak, zwinięte posłanie, pasy i miecz. Nowe obrazy stojącej postaci,
gotowości do walki i biegu były referencją wizualną w rozmowie. Nie są użyte
jako tekstura postaci ani rzekomy zrzut z gry.

Największe skorygowane różnice dotyczyły krótkiego płaszcza, urwanego przy pasie
kaftana i sztywnych włosów. Twarz i fałdy nadal są bardziej stylizowane niż na
ilustracjach. Nie deklarujemy identycznego portretu ani fotograficznej jakości.
Pozy walki i biegu pozostają materiałem do późniejszej pracy nad ruchem;
nie wyprodukowano nowych animacji walki ani biegu.

## Skala, ujęcia i kontrola

Kamera gry, klatka i skala pozostają bez zmian: **192×192 RGBA, 60 px/m,
ortografia 30°, kotwica (96, 158.353829)**. Osiem kierunków to oddzielne obroty
modelu, bez lustrzanych odbić. Anatomia nadal ma 1,8 m; zmiana długości stroju
nie jest powiększeniem całej postaci.

Rendery statyczne mają 384 px / 64 próbki; duże ujęcia całej postaci są prawdziwymi
renderami 1152 px przy tej samej kamerze i ekspozycji. Portrety diagnostyczne
mają 768 px i 128 próbek po obu stronach porównania. Mają bliższą kamerę i nie
zastępują oceny w rzeczywistej skali gry. Nie zastosowano poświaty ani globalnego
przyciemnienia, aby maskować wady.

[Osobne próby światła](reviews/detale-01/swiatlo-1x.png) pokazują wariant bazowy,
chłodny i ciepły. Pochodni nie wypieczono w podstawowych kierunkach.
[Kompozyt na planszy 17](reviews/detale-01/koncept17-1x.png) to **ilustracja
koncepcyjna, nie działająca scena gry**. Tła nie skalowano; przyjęto lokalnie
60 px/m przy kotwicy (590,810), ponieważ ilustracja nie ma kalibrowanej skali.
Postać i cień nadal istnieją jako osobne pliki z przezroczystością.

Wyniki rzeczywiście wykonanych kontroli: [źródło](reviews/detale-01/source-validation.json),
[obrazy i pochodzenie](reviews/detale-01/validation.json),
[sumy plików](reviews/detale-01/checksums.json).
Kontrola obejmuje 12 par obrazu/cienia, format i przezroczyste granice postaci,
zgodność SHA z zapisanym modelem, zapakowane obrazy, geometrię rozdarć oraz
przyłączenie włosów do kości głowy. Nie jest to pełny test przenikania nowego
płaszcza i łat przez ciało w animacji. Takiej akceptacji nie deklarujemy.

## Źródła i następny etap

`source/bohater_detale.blend` jest edytowalnym źródłem tego passu, a nie cache.
Renderer jedynie je odczytuje. Jednorazowe skrypty `detail_*.py` dokumentują
kolejne korekty; nie są wywoływane przez eksport i nie przywracają starych shaderów.
Manifest zapisuje rodzica i aktualny SHA źródła. Wszystkie obrazy materiałów
są zapakowane, a oryginalne pliki i ich pochodzenie pozostają w bibliotece.

Przeliczenie statycznego zestawu, bez regeneracji modelu:

```bash
blender -b assets/sprites/player/source/bohater_detale.blend -t 4 \
  --python-exit-code 1 --python assets/sprites/player/source/render_player.py -- \
  --pilot --output assets/sprites/player/reviews/detale-01/renders
```

Pełne animacje z rewizji 08 można już obejrzeć **bez Blendera**:
[odtwarzacz](previews/review.html), [chód GIF](previews/bohater_chod.gif),
[spoczynek GIF](previews/bohater_spoczynek.gif). Pokazują wcześniejszy wygląd,
nie nowy pass detali. Zachowano ich checkpoint i kompatybilny eksport.

Po ocenie wyglądu nowy, dłuższy płaszcz, łaty i włosy wymagają ponownego przeliczenia
spoczynku/chodu oraz kontroli przenikania w całym cyklu. Nierozstrzygnięta pozostaje
poza z mieczem: wcześniejsza propozycja miała regresję W4–7, a drugi kandydat
poprawiał W kosztem NW. Nie uznano żadnej z tych prób za zatwierdzone rozwiązanie
ani nie przesądzono stałego noszenia dobytej broni podczas eksploracji.
