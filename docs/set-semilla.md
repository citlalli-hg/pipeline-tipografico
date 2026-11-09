# Set semilla: qué dibujar para que el pipeline genere la fuente completa

Lo aprendido con Sterna: las letras de partida se pueden limpiar y armonizar, y con sus piezas se construye casi todo lo demás. Pero lo que se construye sin un dibujo propio queda como boceto (el 2, el 7, el &, la coma). El **set semilla** son los 68 glifos que conviene dibujar desde el principio, en este orden, para que el resto (≈ 250 glifos de Latin-1 y Windows-1252) salga de ellos con buena calidad.

En `proyecto.py`: `DRAWN = "semilla"` → `mise run plantilla` genera las hojas de dibujo con este set y en este orden.

## 1. Controles (4): n o H O

Se dibujan primero y se revisan juntos antes de seguir (Tracy, *Letters of Credit*; Cheng, *Designing Type*). Fijan:

| Glifo | Fija |
| --- | --- |
| **n** | asta de caja baja, arco, remates, altura de x, espaciado de lados rectos |
| **o** | panza, contraste, eje, sobresalto, espaciado de lados redondos |
| **H** | asta y remates de caja alta, barra (filete), altura de mayúsculas |
| **O** | redonda de caja alta, contraste y sobresalto de mayúsculas |

## 2. Minúsculas (24), por familia

Cada una aporta una pieza que el pipeline reutiliza. Dibujarlas en familia mantiene la coherencia (las hojas de Affinity usan las mismas familias).

| Orden | Glifos | Pieza que aporta | Qué se genera con ella |
| --- | --- | --- | --- |
| arcos | h m u r | arco, hombro, terminal de la r | ñ (base), ı |
| panzas | b d p q | unión panza-asta | þ, ð (base), @ (con a) |
| redondas abiertas | c e | terminal de gota, ojo y barra de la e | ç (con cedilla), œ, æ, € (con barras) |
| | a | panza de la a, terminal | @, æ, ª |
| | s | lomo | $ (con filete), §, ẞ/ß (con f) |
| | g | oreja, lazo inferior | — |
| astas | i l j | punto, asta con remate, gancho | ı ȷ . : … ¨ (del punto) |
| | f t | barra, gancho de ascendente | fi fl (ligaduras), ß, ƒ |
| diagonales | v w x y k z | trazo grueso y fino en diagonal | acentos agudo y grave (asta de la v), ˆ ‹ › « » |

## 3. Mayúsculas (24), por familia

| Orden | Glifos | Qué se genera |
| --- | --- | --- |
| rectas | I L E F T | 1 (asta y remate de la I), 4 (asta), 5 (brazo de la T), † ‡ |
| redondas | D C G Q | 0 (de O), 6 y 9 (C sobre o), €, © ® |
| panzas | B P R | 3 (panzas de la B sin asta), 8 |
| | S | 2 y ? (parte alta en espejo), $, § |
| | U J | — |
| diagonales | A V W X Y K M N Z | 7 (Z sin base), Æ (A + E), & (diagonal), % (barra) |

## 4. No letras que hay que dibujar (16)

Son las que en Sterna quedaron más débiles al construirlas, o de las que salen muchas otras:

| Glifo | Por qué dibujarlo | Qué se genera |
| --- | --- | --- |
| **. ,** | la coma define la puntuación | ; : … ’ ‘ ” “ ‚ „ (6 comillas) |
| **? !** | forma propia, no se arma bien con partes | ¿ ¡ (girados) |
| **(** | contraste y curva propios | ) (espejo), [ ] { } |
| **-** | fija altura y grosor de las rayas | – — · |
| **´ ˜ ¸** | acentos con forma propia | \` (espejo del agudo), ˆ ˇ, todas las acentuadas (á é í ó ú ñ ç…) como componentes |
| **1 2 3 4 6 7** | las cifras con estructura propia | 0 (de O u o), 5 (brazo + panza del 3), 8, 9 (6 girado), ½ ¼ ¹ ² ³, % |
| **&** | no tiene piezas comunes con nada | — |

## 5. Lo que se genera solo

Con el set semilla dibujado, `mise run completar` (y `proyecto/completar.py`) arma:

- **Acentuadas** (≈ 120 en Latin extendido): letra + acento como componentes (`mise run limpiar`). Si se corrige un acento, todas cambian.
- **Derivadas por espejo o giro**: ) ] } ¿ ¡ \` 9 ‹ «.
- **Derivadas por partes**: 0 5 8 ; : … comillas, ı ȷ, ¨, «», @, $, %, #, *, /, ligaduras fi fl.
- **Limpieza**: nodos en extremos, asas H/V, quiebres alisados, G2 (`LIMPIAR_CURVAS`, `LIMPIAR_QUIEBRES`), alturas y sobresaltos estabilizados (`ESTABILIZAR_MAYUSCULAS`), espaciado por lados y kerning por perfiles.

## Repertorio de partes (antes de dibujar)

Siguiendo a Smeijers (*Counterpunch*) y a Noordzij (*The Stroke*), conviene fijar en una hoja las piezas que se repiten antes de dibujar el set: **asta**, **filete**, **remate** (con y sin apoyo), **terminal de gota**, **arco**, **panza**, **lomo**, **diagonal gruesa y fina** y **punto**. Cada pieza se anota con su medida (en Sterna: asta ≈ 100, filete ≈ 14, punto ≈ 119). Las letras del set semilla son la forma de comprobar que esas piezas funcionan juntas.

## Cómo encaja con el pipeline

1. Brief y métricas en `proyecto.py`; `DRAWN = "semilla"`.
2. `mise run plantilla` → hojas de dibujo en el orden de arriba. Primero solo la hoja de controles; revisarla impresa antes de seguir.
3. Escaneo → `mise run digitalizar` → `mise run importar` (o vectores de Affinity en `glyphs-svg/`).
4. `mise run completar` → genera el resto; `mise run curvas` y `mise run control` → revisión.
5. Corrección en las hojas de familia (`mise run hojas`, rama `importar/…`).
