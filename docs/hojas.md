# Hojas de familia para corregir glifos en Affinity

Las hojas agrupan los glifos que comparten estructura, para corregirlos juntos y comparar peso, sobresaltos y ritmo mientras dibujas (Cheng, *Designing Type*). El maestro sigue siendo `sources/<slug>.sfd`: lo que corrijas en Affinity vuelve a él por script.

| Hoja | Glifos | Referencia (gris) |
| --- | --- | --- |
| 01-redondas | o c e s | n |
| 02-arcos | n m h u r | o |
| 03-panzas | a b d p q g | n o |
| 04-astas | i j l f t ı | n |
| 05-diagonales | v w x y k z | n o |
| 06-mayusculas-rectas | H I L E F T | O |
| 07-mayusculas-redondas | O C G Q D S | H |
| 08-mayusculas-panzas | B P R U J | H O |
| 09-mayusculas-diagonales | A V W X Y K M N Z | H |
| 10-cifras | 0–9 | H |
| 11-signos | . , : ; ! ? ¡ ¿ ‘ ’ “ ” - – — ( ) « » ‹ › ‚ „ … | n H |
| 12-especiales | & @ € $ % # * / ß ð þ ƒ æ œ Æ Œ | n H |
| 13-acentos | ´ ` ˆ ˜ ¨ ˇ ˚ ¸ ȷ | n o |
| 14-otros | lo que tenga contorno y no esté en otra hoja (flechas, variantes…), si hay | n H |

Cada hoja muestra solo los glifos que existen en la fuente. Las acentuadas no tienen hoja: se rehacen con su letra base y su acento (si son componentes, se actualizan solas).

Cada celda tiene las guías de línea base, altura de x, sobresaltos de las redondas (punteadas), mayúsculas y descendentes. El recuadro punteado de la celda marca el ancho de avance del glifo.

## Flujo

1. **Exportar las hojas** desde el maestro actual:
   ```
   git switch -c hojas/correcciones
   mise run hojas
   ```
2. **Abrir en Affinity** la hoja que vas a trabajar: **File › Open** → `hojas/02-arcos.svg`.
3. **Corregir** los glifos dentro de su celda. Cada glifo es un grupo con su nombre en el panel **Layers**.
   - Dibuja en negro y relleno; las guías son solo trazo y se ignoran.
   - No muevas ni borres los dos **cuadros negros de las esquinas**: son las marcas de registro que calibran la escala al volver.
   - No cambies el tamaño de la mesa de trabajo. Si Affinity escala la hoja al abrirla, no pasa nada: las marcas lo corrigen.
   - Los glifos en gris son referencia; puedes moverlos de lugar o borrarlos, no se importan.
   - Guarda tu trabajo también como `.afdesign` si quieres conservar capas propias (fuera de `hojas/` o con otro nombre).
4. **Exportar desde Affinity**: **File › Export** → formato **SVG**, preset **SVG (for export)**, con **Rasterise: Nothing**. Guarda encima de `hojas/02-arcos.svg` (mismo nombre).
5. **Importar al maestro**:
   ```
   mise run importar-hojas
   ```
   - Solo se reemplazan los glifos que cambiaron; el resto del maestro no se toca.
   - Las acentuadas (á à â ä ã å, ñ, é…) se regeneran con el cuerpo nuevo de su letra base. Para no hacerlo: `python pipeline/scripts/ff.py 11_hojas.py importar --sin-acentos`.
   - Se conservan los márgenes laterales de cada glifo y el ancho de avance se ajusta. Para mantener el ancho: `python pipeline/scripts/ff.py 11_hojas.py importar --conservar-ancho`.
   - Puedes guardar iteraciones con sufijo (`01-redondas-iteracion-2.svg`): se reconocen como su familia.
   - En GitHub: sube la hoja a una rama `importar/…` y Actions la importa, compila y devuelve el maestro a la rama.
6. **Revisar y subir**:
   ```
   mise run build
   mise run pruebas
   git add hojas sources/<slug>.sfd
   git commit -m "Correcciones manuales: arcos"
   git push -u origin HEAD
   gh pr create --fill
   ```

## Cuándo usar FontForge directamente

Para ajustes de puntos sueltos, espaciado (**Window › New Metrics Window**) y kerning, es más rápido trabajar sobre el maestro en FontForge. Si después vuelves a las hojas, expórtalas de nuevo (`mise run hojas`) para que muestren el estado actual.
