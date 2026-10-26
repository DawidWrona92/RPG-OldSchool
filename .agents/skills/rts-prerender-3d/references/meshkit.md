# Meshkit — poprawne konturowe pryzmy OBJ

Silnik `rtcore.js` ma `Model.addObj(material, text, options)`, który **nie przetwarza** instrukcji `usemtl`/`g`. Dlatego różne materiały muszą być dodawane oddzielnymi wywołaniami.

```js
const rt = require('../scripts/rtcore.js');
const meshkit = require('../scripts/meshkit.js');
const prism = meshkit.polyPrismObj(meshkit.heaterOutline(1),0.08,{
  front:'team',back:'iron',sides:'metal'
});
const groups=meshkit.splitObjByGroup(prism);
const model=rt.standardModel(rt.standardTextures(['metal']));
for(const [name,g] of Object.entries(groups)) model.addObj(g.materialHint,g.obj,{offset:[0,0,1]});
```

**Orientacja:** kontur CCW patrząc od +Z. Pokrywa na zMax normalna +Z, na zMin normalna -Z; boki skierowane na zewnątrz. Dla konturu wklęsłego pokrywy są triangulowane przez ear clipping. Generator odrzuca NaN, kontury z samoprzecięciami, zdegenerowane, współliniowe i powtarzające się krawędzie. Przy `taperPrismObj` liczby punktów i zwrot konturów muszą być zgodne; duże skręcenie przekroju może mimo to tworzyć samoprzecięcia w 3D. Wynik ma grupy front/back/sides oraz różne nazwy materiałów, ale dopiero `splitObjByGroup` przekłada je na sposób pracy importera.

Do sprawdzania: `node tests/test_tools.js` oraz `node tests/test_integrated.js` w katalogu głównym pakietu. Wycięcie z konturu tarczy nie oznacza automatycznego poprawnego nałożenia emblematu — emblemat wymaga oddzielnej geometrii/materialu.
