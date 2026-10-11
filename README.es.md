<p align="center">
  <img src="lutsmith_app/assets/app/icon-128.png" width="112" height="112" alt="Icono de GR4-LUTSmith: una barra de acero doblada en forma de curva tonal de película">
</p>

<h1 align="center">GR4-LUTSmith</h1>

<p align="center">
  <strong>Tu propio look de color, a partir de una LUT <code>.cube</code>, dentro de tu RICOH GR IV o GR IV HDF.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.zh-TW.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.fr.md">Français</a> |
  <strong>Español</strong>
</p>

GR4-LUTSmith toma una LUT de gradación de color (`.cube`) y crea un firmware para la GR IV / GR IV HDF
que lleva su look como un look de **Control de imagen**. Puedes usarlo al hacer
fotos, en modo vídeo y en el visor, y también en **RAW Development**.
Todo lo demás de tu cámara queda exactamente como estaba, y puedes volver al
firmware oficial en cualquier momento.

Este repositorio no contiene ningún firmware de RICOH. Tú mismo descargas el
firmware oficial de RICOH, y la herramienta incluida lo convierte en la versión
con tu look, en tu propio ordenador.

> [!WARNING]
> **No oficial, bajo tu propia responsabilidad.** No está hecho ni respaldado por RICOH IMAGING.
> Instalar un firmware modificado puede anular la garantía. Lee primero
> [Antes de empezar](#antes-de-empezar) y [Riesgos](#riesgos).

| Quieres | Ve a |
| --- | --- |
| Crear tu firmware en una ventana, paso a paso (macOS, Windows; en los 21 idiomas de la cámara) | [La app](#la-app) |
| Crearlo en el terminal (macOS, Windows, Linux) | [La línea de comandos](#la-línea-de-comandos) |
| Crear un look que alguien ha compartido contigo | [Usar un look compartido](#usar-un-look-compartido) |
| Saber qué contiene un archivo de firmware | [Comprobar un archivo de firmware](#comprobar-un-archivo-de-firmware) |
| Volver al firmware de RICOH | [Volver al firmware oficial](#volver-al-firmware-oficial) |

La app y la línea de comandos crean exactamente el mismo firmware con la misma LUT y las mismas opciones.

**Contenido:**
[Cómo funciona](#cómo-funciona) |
[Qué obtienes](#qué-obtienes) |
[Antes de empezar](#antes-de-empezar) |
[La app](#la-app) |
[La línea de comandos](#la-línea-de-comandos) |
[Instálalo en la cámara](#instálalo-en-la-cámara) |
[Hazlo tuyo](#hazlo-tuyo) |
[Afinar el ajuste](#afinar-el-ajuste) |
[Conviene saber](#conviene-saber) |
[Riesgos](#riesgos) |
[Estado de las pruebas](#estado-de-las-pruebas) |
[Para desarrolladores](#para-desarrolladores)

## Cómo funciona

La GR IV no aplica LUT directamente. Sus looks se construyen con unos pocos
controles propios: una mezcla de color, curvas tonales, ajustes de contraste y
**sectores de matiz** (cambios de color independientes para 12 rangos de matiz).
GR4-LUTSmith **ajusta** tu LUT a esos controles, mide cuánto se puede acercar la
cámara y solo entonces escribe el firmware.

- **Los looks tonales y de color general** se ajustan muy bien. Eso incluye
  curvas de estilo película, contraste, negros lavados, dominantes cálidas o
  frías y cambios de saturación general.
- **Los looks que mueven matices concretos por separado** (teal-orange,
  simulaciones de película que desplazan los verdes o el cielo, …) se ajustan con
  los **sectores de matiz**. Así se acercan mucho más que solo con la mezcla de
  color. Los cambios que dependen mucho de lo saturado que esté un color (por
  ejemplo, solo los rojos más vivos) siguen siendo aproximados, y la herramienta
  te avisa cuando es el caso.
- **Las LUT Log y las de conversión para una cámara concreta** (S-Log, V-Log, …)
  no son compatibles. Usa una LUT "creativa" hecha para imágenes normales
  (Rec.709 / sRGB).

El ajuste se evalúa con **CIEDE2000**, la medida estándar de cuánto se diferencian
dos colores a la vista. Como referencia, **por debajo de 1 es difícil verlo uno
junto al otro**, y en torno a 2 es una diferencia pequeña pero visible.

| Resultado | Significado |
| --- | --- |
| **bueno** (GOOD) | diferencia media por debajo de 1, y el 95 % de los colores por debajo de 2: se ve igual |
| **aproximado** (APPROXIMATE) | media por debajo de 2: cercano, con diferencias visibles en algunos colores |
| **deficiente** (POOR) | la cámara no puede reproducir todo el rango de colores de la LUT; el firmware se escribe igualmente si los **colores cotidianos** encajan (ver [Cuando una LUT es «deficiente»](#cuando-una-lut-es-deficiente)) |

Cada LUT se mide de tres formas: en todo su rango de colores, en los 24 colores
cotidianos de una carta **ColorChecker** (piel, cielo, follaje, …) y en
**grises neutros** (donde cualquier dominante de color se nota más). Con una
foto tuya (`--photo`), también en esa foto.

## Qué obtienes

Después de instalarlo, la lista de Control de imagen termina así. Los nombres de
los menús se dan como en una cámara configurada en inglés (Control de imagen,
Saturación, Matiz y Estándar, en español).

| Se muestra como | Look | Foto | Vídeo |
| --- | --- | :---: | :---: |
| HDR Tone | (tu look de color actual) | ✓ | |
| Estándar | Estándar monocromo | ✓ | ✓ |
| Solid | Solid monocromo | ✓ | ✓ |
| Soft | Soft monocromo | ✓ | |
| **High Contrast** | **el look de tu LUT, en color** | ✓ | ✓ |
| Grainy | Grainy monocromo | ✓ | |
| HDR Tone | HDR monocromo *(experimental)* | ✓ | |

- Tu look usa el nombre y el icono de **High Contrast** (la cuarta entrada después
  del primer "HDR Tone"). En su lugar puedes elegir **Cinema (Yellow)**, **Vivid**
  u otra posición, o usar varias: consulta [Elegir la posición](#elegir-la-posición).
  También puede mostrar [tu propio nombre](#nombrar-la-posición) y
  [tu propio icono](#tu-propio-icono).
- Empieza con **todos los controles a 0**, la nitidez en su valor estándar y
  **el grano desactivado**. El look de tu LUT está integrado con esos ajustes;
  después los controles funcionan como siempre, a partir de tu look.
- También están disponibles los cinco looks monocromos de la GR IV Monochrome,
  como en GR4-MonoUnlock.
- Todos tus looks actuales quedan sin cambios.

## Antes de empezar

- **Cámara:** RICOH GR IV o GR IV HDF. La actualización 1.11 de RICOH es un solo archivo para ambas, y también lo es
  el archivo que crea esta herramienta. Otros modelos, incluida la GR IV Monochrome, no son compatibles.
- **Tu cámara ya debe tener el firmware 1.11.** Comprueba la versión en el menú
  de configuración de la cámara.
  - Versión anterior: actualiza primero a la 1.11 de la forma normal, con el archivo oficial de RICOH.
  - Versión más reciente: **no uses esta herramienta.** Solo es compatible con la 1.11.
- **El archivo de firmware oficial.** En la página oficial de soporte de la GR IV (o de la GR IV HDF)
  de RICOH IMAGING, descarga la **versión de firmware 1.11**. Descomprímela si hace
  falta hasta tener el archivo **`fwdc248b.bin`**.
- **Una batería totalmente cargada.** Una actualización de firmware nunca debe
  quedarse sin alimentación.
- **Una tarjeta SD** que puedas formatear.
- **Tu LUT** como archivo `.cube` (3D o 1D), y saber si se hizo para **sRGB**
  (la mayoría de las LUT) o para **Adobe RGB**.
- **Recomendado:** una foto DNG hecha con tu GR IV o GR IV HDF. La herramienta la usa para
  comprobar el look con contenido real y para crear una vista previa.
- Apunta los ajustes personalizados (C1, C2, …) que no quieras tener que volver a configurar.

Después crea tu firmware con [la app](#la-app) o con
[la línea de comandos](#la-línea-de-comandos).

## La app

### Descarga

En la [versión más reciente](../../releases/latest), descarga el archivo para tu ordenador:

| Ordenador | Archivo |
| --- | --- |
| Mac con Apple silicon (M1 o posterior) | `GR4-LUTSmith-<version>-macOS-AppleSilicon.zip` |
| Mac con procesador Intel | `GR4-LUTSmith-<version>-macOS-Intel.zip` |
| Windows 10 u 11 (64 bits) | `GR4-LUTSmith-<version>-Windows-x64.zip` |

Se necesita macOS 12 (Monterey) o posterior. ¿No sabes qué Mac tienes? Menú Apple → **Acerca de este Mac**: «Chip
Apple M…» es Apple silicon, «Procesador Intel» es Intel.

Cada zip contiene la app y una carpeta `Licences` (las licencias de los componentes con los que está hecha).

<details>
<summary><strong>Comprueba que viene de este proyecto</strong> (opcional)</summary>

<br>

Cada zip lo crea el propio proceso de compilación de este repositorio en GitHub, que firma un registro de su
origen: el repositorio, la compilación y la versión exacta del código. Puedes comprobar que tu descarga es ese
archivo y que no se ha modificado ni sustituido, con la [GitHub CLI](https://cli.github.com) (con la sesión
iniciada mediante `gh auth login`):

```sh
gh attestation verify GR4-LUTSmith-2.2.0-macOS-AppleSilicon.zip --repo lemonadesaltbagel/GR4-LUTSmith
```

(usa el nombre del zip que descargaste; en Windows, ejecútalo en PowerShell desde tu carpeta Descargas). Termina
con "Verification succeeded!" e indica la compilación que creó el archivo. Cualquier otro resultado significa: no
lo abras y vuelve a descargarlo desde la página de la versión. La página **Attestations** del repositorio muestra
todos los archivos firmados.

Una comprobación más rápida de que la descarga está completa: la versión publicada indica el SHA-256 de cada
archivo en `SHA256SUMS`.

- macOS (Terminal): `shasum -a 256 ~/Downloads/GR4-LUTSmith-*.zip`
- Windows (PowerShell): `Get-FileHash $HOME\Downloads\GR4-LUTSmith-*.zip -Algorithm SHA256`

Esto solo demuestra que el archivo llegó intacto, no quién lo hizo: `SHA256SUMS` está en la misma página que los zip.

También puedes no descargar nada: ejecuta la app desde el código fuente (consulta
[Para desarrolladores](#para-desarrolladores)) o crea el firmware con la
[línea de comandos](#la-línea-de-comandos). La app y la línea de comandos crean exactamente el mismo `fwdc248b.bin`,
y `uv run gr4_lutsmith.py check fwdc248b.bin` muestra qué contiene cualquier archivo de firmware.

</details>

### Ábrela por primera vez

La app es gratuita y no está firmada con un certificado de pago de Apple o Microsoft, así que tu ordenador te
pregunta una vez si confías en ella.

**macOS**

1. Descomprime el archivo y mueve **GR4-LUTSmith** a tu carpeta Aplicaciones.
2. Ábrela. macOS dice que no puede comprobar si la app contiene software malicioso; elige **Done** («Hecho»,
   macOS 15) o **Cancelar**.
3. Abre **Ajustes del Sistema → Privacidad y seguridad**, baja hasta el mensaje sobre GR4-LUTSmith y elige
   **Abrir igualmente**; después confirma con tu contraseña.
   En macOS 12 a 14 también puedes hacer clic en la app con la tecla Control pulsada, elegir **Abrir** y luego **Abrir** otra vez.

A partir de entonces se abre con normalidad.

**Windows**

1. Haz clic derecho en el zip → **Extraer todo…** y abre la carpeta **GR4-LUTSmith** extraída (no la ejecutes
   desde dentro del zip).
2. Abre **GR4-LUTSmith.exe**. Si Windows muestra «Windows protegió su PC», elige **Más información → Ejecutar de todas formas**.

Mantén la carpeta completa: la app necesita la carpeta `_internal` que está a su lado.

### Úsala

La app te guía por los pasos en pantalla: el archivo de firmware de tu cámara, la LUT (y, si quieres, un DNG), la
posición con su nombre y su icono, el ajuste y la creación. Guarda `fwdc248b.bin` donde elijas; después
[instálalo en la cámara](#instálalo-en-la-cámara).

- **Idioma:** la app sigue el idioma de tu ordenador; puedes cambiarlo en la parte superior de la ventana. Es también
  el idioma de la cámara con el que se comprueban los nombres de tus posiciones (consulta [Nombrar la posición](#nombrar-la-posición)).
- **Apariencia:** Sistema, Día o Noche, en la parte superior de la ventana.
- **Comprobar un archivo de firmware** (a la izquierda) te dice si un `fwdc248b.bin` es el archivo oficial de RICOH,
  uno creado por GR4-LUTSmith (y con qué looks) u otra cosa.
- Los looks que alguien ha compartido (`.json`) también funcionan en la app: elige «Un look compartido» en la primera página.
- **Varias rondas a la vez:** en la página «Ajuste», elige cuántas rondas hacer y cuántas se ejecutan a la vez (un núcleo
  del procesador cada una; consulta [Más rondas](#más-rondas)). Cada ronda muestra cuánto le falta; puedes añadir rondas
  mientras se ejecutan, y «Detener todo» conserva las rondas que ya han terminado. Los resultados se añaden a la tabla a
  medida que terminan las rondas.

### Si algo falla

- **macOS dice que la app está dañada**: vuelve a descargarla (el archivo quedó incompleto) y compruébala como en
  [Comprueba que viene de este proyecto](#descarga).
- **La app no se inicia en Windows**: asegúrate de haber extraído el zip completo y ejecuta `GR4-LUTSmith.exe` desde
  la carpeta extraída.
- **El archivo de firmware es rechazado**: la app solo acepta el `fwdc248b.bin` 1.11 de la GR IV / GR IV HDF de RICOH sin modificar.
  Un archivo que GR4-LUTSmith ya ha cambiado no se puede volver a cambiar; parte del archivo sin modificar.

## La línea de comandos

### 1. Preparación

Instala **[uv](https://docs.astral.sh/uv/)** (instala Python y todo lo demás que
necesita la herramienta), abre un terminal en esta carpeta y ejecuta:

```sh
uv sync --extra photo
```

<details>
<summary>Sin uv</summary>

<br>

Con Python 3.9 o posterior:

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` y `pillow` solo hacen falta para `--photo` y `preview`.

</details>

### 2. Crea tu firmware

Usa tus propias rutas:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

| Opción | Qué hace |
| --- | --- |
| `--space adobe` | la LUT se hizo para Adobe RGB |
| `--photo R0001234.DNG` | comprueba el look también en tu foto (opcional, pero recomendado) |
| `--slot vivid`, `--slot cinema-yellow`, … | pone tu look en lugar de otro look en vez de High Contrast: [Elegir la posición](#elegir-la-posición) |
| `--name "My Look"` | muestra la posición con tu propio nombre: [Nombrar la posición](#nombrar-la-posición) |
| `--icon my_icon.png` | da a la posición tu propio icono de menú: [Tu propio icono](#tu-propio-icono) |
| `--turns 3` | hace tres ajustes y conserva los mejores: [Más rondas](#más-rondas) |
| `--jobs 3` | ejecuta hasta tres de esas rondas a la vez: [Más rondas](#más-rondas) |
| `--after-curves` | prueba también una segunda mezcla de color: [Color tras las curvas](#color-tras-las-curvas) |

La herramienta:

1. comprueba que le has dado el archivo oficial 1.11 auténtico;
2. ajusta la LUT (tarda unos minutos, más uno o dos minutos para los sectores
   de matiz) y muestra lo bien que se ajusta;
3. crea el firmware y lo comprueba.

Una ejecución correcta termina así:

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
Copy this file to the root of the SD card and run the camera's firmware update.
Then choose High Contrast in Image Control: your look is there.
```

Al principio, la herramienta también indica a qué posición va tu look, por ejemplo
`slot: High Contrast (replaces the hidden monochrome High Contrast look)`.

La carpeta de salida `output/my_look/` contiene además `look.json` (el look
ajustado) y puede guardar una vista previa (paso 3). Puedes compartir `look.json`
con otros propietarios de una GR IV o una GR IV HDF: crean el mismo look sin tener que ajustarlo
de nuevo (consulta [Usar un look compartido](#usar-un-look-compartido)).

Si la LUT no se puede reproducir bien, o el archivo de firmware no es el 1.11
oficial, la herramienta muestra `refused: …` y **no escribe ningún firmware**.

### 3. Vista previa (opcional)

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

Esto escribe `output/my_look/preview.jpg` con tres paneles: la cámara sin el
look, la propia LUT y la cámara **con** el look. El panel de la LUT necesita el
archivo `.cube`: la herramienta lo busca junto a `look.json` o en la carpeta
actual, o puedes indicarlo con `--lut my_look.cube`; sin él, la vista previa
muestra los otros dos paneles. Lo que hay que comparar es el color y el tono.
La nitidez y el ruido no se simulan.

Después [instálalo en la cámara](#instálalo-en-la-cámara).

## Instálalo en la cámara

Es igual para un firmware creado con la app o con la línea de comandos.

### 1. Cópialo a la tarjeta SD

1. **Formatea la tarjeta SD en la cámara.**
2. Copia **`fwdc248b.bin`** (desde la línea de comandos: `output/my_look/fwdc248b.bin`)
   en la **raíz** de la tarjeta: no dentro de una carpeta, y con el nombre
   exactamente `fwdc248b.bin`.

### 2. Actualiza la cámara

1. Inserta la batería totalmente cargada y la tarjeta SD.
2. Inicia la actualización de firmware desde el menú de configuración de la cámara,
   como se describe en las instrucciones oficiales de RICOH para actualizar el firmware de la GR IV / GR IV HDF.
3. **La cámara muestra una actualización de la versión 1.11 a la versión 1.11.** Es
   lo esperado: el firmware modificado mantiene el número de versión. Confirma la actualización.

> [!CAUTION]
> **No apagues la cámara, no abras la tapa de la batería o de la tarjeta y no
> saques la tarjeta** hasta que la actualización haya terminado y la cámara se haya reiniciado.

### 3. A disparar

- Abre **Control de imagen** y elige **High Contrast** (después del primer
  "HDR Tone"). Ahora es en color. Si elegiste otra posición, elige esa
  entrada.
- La versión del firmware sigue mostrando **1.11**. Es normal.
- Borra `fwdc248b.bin` de la tarjeta (o formatéala) para que la actualización no
  se inicie de nuevo por error.

Para cambiar más adelante a otra LUT, crea un firmware nuevo a partir del archivo
**oficial** e instálalo de la misma manera.

### Volver al firmware oficial

Repite los pasos 1–2 con el `fwdc248b.bin` **oficial** de RICOH. La cámara vuelve
a mostrar **1.11 → 1.11**; confírmalo y tu cámara vuelve a su estado original.

## Hazlo tuyo

Dónde va tu look, cómo se llama y qué aspecto tiene en el menú. En la app, esto
está en el paso de la posición; en la línea de comandos, son opciones de
`make` y `build`.

### Elegir la posición

Tu look reemplaza uno de los looks de la cámara. Eliges cuál con
`--slot` (`make` y `build`); `uv run gr4_lutsmith.py slots` muestra la misma lista
en el terminal:

| `--slot` | Se muestra como | Reemplaza | Foto | Vídeo | Controles adicionales |
| --- | --- | --- | :---: | :---: | --- |
| `high-contrast` (predeterminado) | High Contrast | el look monocromo oculto High Contrast | ✓ | ✓ | — |
| `cinema-yellow` | Cinema (Yellow) | el look Cinema (Yellow) de RICOH | ✓ | ✓ | Saturación, Matiz |
| `cinema-green` | Cinema (Green) | el look Cinema (Green) de RICOH | ✓ | ✓ | Saturación, Matiz |
| `vivid` | Vivid | el look Vivid de RICOH | ✓ | ✓ | Saturación, Matiz |
| `positive-film` | Positive Film | el look Positive Film de RICOH | ✓ | ✓ | Saturación, Matiz |
| `negative-film` | Negative Film | el look Negative Film de RICOH | ✓ | ✓ | Saturación, Matiz |
| `bleach-bypass` | Bleach Bypass | el look Bleach Bypass de RICOH | ✓ | ✓ | Saturación, Matiz |
| `retro` | Retro | el look Retro de RICOH | ✓ | ✓ | Saturación, Matiz |
| `soft-monotone` | Soft Monotone | el look Soft Monotone de RICOH | ✓ | | — |
| `hard-monotone` | Hard Monotone | el look Hard Monotone de RICOH | ✓ | ✓ | — |
| `hi-contrast-bw` | Hi-Contrast B&W | el look Hi-Contrast B&W de RICOH | ✓ | ✓ | — |
| `mono-standard` | Estándar (la segunda entrada) | el look monocromo oculto Estándar | ✓ | ✓ | — |
| `mono-soft` | Soft | el look monocromo oculto Soft | ✓ | | — |
| `mono-solid` | Solid | el look monocromo oculto Solid | ✓ | ✓ | — |

- Los colores son los mismos en todas las posiciones: la cámara procesa tu look
  igual en cada una, así que el ajuste y sus puntuaciones no cambian con la posición.
- Tu look empieza con todos los controles a 0 y el grano desactivado, en todas las posiciones.
- Lo único que cambia con la posición es qué entrada pierdes y qué controles
  obtienes. En una posición monocroma tu look es en color; ahí no se ofrecen
  Saturación ni Matiz.
- **Cinema:** su ajuste Color Tone no afecta a tu look.
  **Bleach Bypass:** su ajuste de tono no cambia tu look.
  **Retro:** se eliminan el virado propio de Retro y su efecto tonal parecido a
  una viñeta, así que obtienes solo tu look.
- Una posición que no uses conserva el look de RICOH. Sin un look en High Contrast,
  sigue siendo el look monocromo High Contrast.
- **No disponibles:** Estándar, Monotone, HDR Tone, Cross Processing y los looks
  ocultos Grainy y HDR. Comparten partes de su procesado con otros looks o usan un
  procesado especial que cambiaría tus colores.
- `check` indica qué posiciones llevan un look personal.

### Varios looks en un firmware

Ajusta cada LUT con `fit` y después créalas juntas, cada archivo de look seguido
de su propio `--slot` (y `--name`, `--icon` si quieres):

```sh
uv run gr4_lutsmith.py fit look_a.cube --photo R0001234.DNG -o output/a
uv run gr4_lutsmith.py fit look_b.cube --photo R0001234.DNG -o output/b
uv run gr4_lutsmith.py build output/a/look.json --slot cinema-yellow output/b/look.json --slot vivid --name "Look B" ~/Downloads/fwdc248b.bin -o output/both
```

**Cuántos a la vez:** High Contrast y las dos posiciones Cinema siempre admiten un
look completo. Las demás posiciones comparten un espacio limitado: cada look
necesita espacio para sus curvas tonales, y mucho más para los sectores de matiz y
el color tras las curvas. Un look sencillo (una curva tonal) cabe en hasta 10 de
ellas a la vez; los looks con sectores de matiz caben en muchas menos. Si no caben,
la herramienta lo indica y no escribe nada; usa menos posiciones o looks más
sencillos, y deja High Contrast sin usar para tener el máximo espacio.

### Nombrar la posición

`--name` (`make` y `build`) da a la posición tu propio nombre, en el menú de Control
de imagen y sus pantallas, en todos los idiomas de la cámara:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra"
```

- Cada posición admite nombres hasta una longitud determinada: `uv run gr4_lutsmith.py slots`
  la muestra (de 9 caracteres en Retro a 23 en Cinema (Yellow)). La segunda
  entrada Estándar (monocroma) no se puede renombrar, porque comparte su nombre con el look
  en color Estándar.
- **ASCII simple** (letras inglesas, dígitos, espacios y signos de puntuación) se ve en
  todos los idiomas de la cámara. Es la opción segura.
- **Otras letras y caracteres** funcionan en los idiomas de la cámara que los usan:
  un nombre en japonés se ve cuando la cámara está en japonés, `Müller` en los
  idiomas europeos, `Плёнка` en ruso, etc. Los caracteres que no usa ninguno de
  los idiomas de la cámara (emoji, árabe, hebreo, …) se rechazan.
- La herramienta comprueba el nombre para el **idioma de tu cámara**, que es el
  idioma de tu ordenador salvo que indiques `--camera-language` (por ejemplo
  `--camera-language Japanese`; `--help` muestra los 21). Si el nombre usa
  caracteres que ese idioma no usa, la herramienta avisa de que puede que no se
  vean y pregunta si quieres usar el nombre de todos modos. Responde `y` para
  continuar, o añade `--accept-name` para aceptarlo de antemano (necesario cuando la
  herramienta no puede preguntar, por ejemplo en un script). Si después cambias la
  cámara a otro idioma, un nombre fuera de ASCII puede no verse allí.
- Los nombres largos pueden cortarse en algunas pantallas (los caracteres chinos,
  japoneses y coreanos ocupan aproximadamente el doble de ancho que las letras inglesas).
- Sin `--name`, la posición conserva su propio nombre. El nombre no se guarda en
  `look.json` (ese archivo solo contiene el look): vuelve a indicar `--name` cuando
  uses `build`. `check` muestra el nombre en un firmware creado.

### Tu propio icono

`--icon` (`make` y `build`) reemplaza el icono de la posición en el menú de Control
de imagen por tu propia imagen:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- Sirve cualquier imagen (PNG, JPEG, …). El icono del menú mide 40×40 píxeles: una
  imagen más grande o más pequeña se redimensiona y, si no es cuadrada, se usa su
  **centro**. Las partes transparentes siguen siendo transparentes, así que un PNG
  con fondo transparente se parece a los iconos propios de la cámara.
- `make` guarda el resultado como `icon.png` junto al firmware, para que veas
  exactamente lo que mostrará la cámara. A este tamaño se leen mejor las formas
  simples y marcadas.
- Todas las posiciones admiten un icono propio excepto la segunda entrada Estándar (monocroma)
  (esa comparte su icono con el look en color Estándar). `slots` las muestra.
- Necesita Pillow (`uv sync --extra photo`). Sin `--icon`, la posición conserva
  su propio icono. El icono no se guarda en `look.json`: vuelve a indicar `--icon`
  cuando uses `build`. `check` muestra qué posiciones tienen su propio icono.

### Usar un look compartido

`look.json` solo contiene el look en sí: sus ajustes de color y lo bien que se
ajustan a la LUT. Nada sobre la posición, el nombre o el icono, y ninguna carpeta
de tu ordenador (solo el nombre de archivo de la LUT). Quien tenga el archivo puede
crear el firmware directamente, sin la LUT y sin ajuste, y obtiene el mismo
firmware, byte a byte, que su autor con la misma posición, nombre e icono.

En la app, elige «Un look compartido» en la primera página. En la línea de comandos,
el archivo puede tener cualquier nombre, así que cámbiaselo como quieras antes de
compartirlo (`portra-400.json`, …):

```sh
uv run gr4_lutsmith.py build portra-400.json ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- La herramienta muestra primero lo bien que el look se ajusta a su LUT (los
  resultados que vio su autor; "on your photo" se refiere a la foto del autor).
- La posición, el nombre y el icono los eliges tú, como en
  [Elegir la posición](#elegir-la-posición), [Nombrar la posición](#nombrar-la-posición)
  y [Tu propio icono](#tu-propio-icono). Sin `--slot`, el look va en
  High Contrast.
- Varios looks: escribe el `--slot`, `--name` e `--icon` de cada archivo justo
  después de él:

  ```sh
  uv run gr4_lutsmith.py build portra-400.json --slot vivid --name "Portra" tri-x.json --slot hard-monotone ~/Downloads/fwdc248b.bin -o output/both
  ```

- El contenido del archivo se comprueba antes de crear nada: un archivo dañado, o
  uno con valores que la cámara no admite, se rechaza y no se escribe
  nada.
- Los archivos creados con versiones anteriores a la 1.7.0 también pueden contener
  una posición, un nombre, un icono y la ruta completa a la LUT. `build` ignora la
  posición, el nombre y el icono (indica cuáles eran); abre ese archivo en un editor
  de texto y revisa `"file"` antes de compartirlo.

## Afinar el ajuste

Los sectores de matiz se prueban en cada ajuste. Si quieres acercarte más, haz primero
más rondas y después prueba el color tras las curvas (consulta [Qué ayuda más](#qué-ayuda-más)).

### Sectores de matiz

Después de ajustar la mezcla de color y las curvas tonales, la herramienta intenta
mejorar el look con **sectores de matiz**: la cámara puede cambiar los colores por
separado en 12 rangos de matiz. Se conservan **solo cuando ayudan claramente** (todo
el rango de colores o la ColorChecker mejora al menos un 10 %) **y nada empeora**
(tu foto, los grises, la ColorChecker). La línea de resultado dice `hue sectors: yes` o `no`.

- Los sectores de matiz nunca cambian los grises, y los sectores vecinos siempre se
  unen sin huecos, así que los colores pasan con suavidad de un matiz al siguiente.
- Con `--photo`, los sectores de matiz se afinan también para contenido real (recomendado).
- `--no-hue` los desactiva (`make` y `fit`).

### Más rondas

El ajuste empieza en un punto de partida y mejora a partir de ahí. La cámara solo
tiene unos pocos controles de color, así que **el punto de partida del ajuste suele
decidir cuánto se acerca**. Con `--turns` (en la app: en la página «Ajuste»), la
herramienta hace varios ajustes ("rondas"), cada uno desde un nuevo punto de partida
aleatorio, y conserva los buenos:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG --turns 3
```

- La ronda 1 siempre usa el punto de partida habitual, así que una sola ronda (lo
  predeterminado) da el mismo resultado que antes. Cada ronda adicional elige un nuevo
  inicio aleatorio.
- Cada ronda tarda lo mismo que un ajuste normal (unos minutos).
- **A la vez.** `--jobs 3` ejecuta hasta tres rondas a la vez, cada una en un núcleo
  del procesador y con unos 0,8 GB de memoria. Deja al menos un núcleo libre para el
  resto del ordenador. Los resultados son exactamente los mismos que al hacer las
  rondas una tras otra; solo están listos antes.
- **Resultados conservados.** Un resultado nuevo se conserva salvo que uno anterior sea
  al menos igual de bueno en todas las medidas (todo el rango, la ColorChecker, los
  grises y tu foto). Un resultado anterior al que el nuevo supera en todas las medidas
  sale de la lista. Así, cada resultado conservado es mejor que todos los demás en al
  menos una medida; la herramienta los muestra uno junto a otro y recomienda el que
  tiene la mejor puntuación global (la diferencia media en todo lo que usa el ajuste).
- **Añadir rondas al final.** Cuando aparecen los resultados, la herramienta pregunta
  `More turns?`. Escribe un número para hacer esa cantidad de rondas más, del mismo
  modo en que empezó la ejecución (`2`); añade `a` para rondas con
  [color tras las curvas](#color-tras-las-curvas) (`2a`), o `b` para rondas
  sin él (`2b`), sea cual sea el modo en que empezó la ejecución. Las rondas nuevas se
  comparan con todos los resultados conservados. Pulsa Intro para quedarte con lo que tienes.
- **Repetir una ronda.** La semilla de cada ronda se muestra y se guarda en `turns.json`;
  `--seed 1234` vuelve a hacer la misma ronda (con `--turns 3`: semillas 1234, 1235,
  1236).

Con más de un resultado conservado, la carpeta de salida queda así:

```
output/my_look/look.json, fwdc248b.bin      the recommended result
output/my_look/turns/turn-1/                 every kept result, each with its
output/my_look/turns/turn-3-after-curves/    own look.json (and, with make, fwdc248b.bin)
output/my_look/turns.json                    every turn, its seed and its scores
```

Para usar otro resultado conservado, copia su `fwdc248b.bin` a la tarjeta SD.

### Color tras las curvas

Con `--after-curves` (`make` y `fit`), la herramienta prueba también una segunda mezcla
de color que la cámara aplica **después** de las curvas tonales. Muchos looks de
película cambian los colores de forma distinta en las sombras y en las luces. La mezcla
de color habitual actúa antes de las curvas, así que no puede seguir eso, pero una
mezcla después de las curvas a menudo sí puede.

Todo el rango de colores de la LUT y las fotos reales no siempre coinciden: una versión
puede acercarse mucho más en los colores saturados y alejarse un poco en una foto
cotidiana. Por eso las dos versiones entran en la lista de resultados conservados
descrita en [Más rondas](#más-rondas): la versión con color tras las curvas se conserva
siempre que sea mejor en algo (todo el rango, la ColorChecker, los grises o tu foto),
junto a la habitual, y tú eliges. Mira la vista previa de ambas en tu propia foto
antes de elegir.

**Por qué es opcional.** Hacer más rondas del ajuste habitual es la palanca más grande
(consulta [Qué ayuda más](#qué-ayuda-más)). La mezcla tras las curvas ayuda de media,
pero alarga cada ronda varios minutos.

- Los grises siguen siendo grises: la mezcla nunca añade una dominante de color a un gris neutro.
- El ajuste tarda varios minutos más (cuatro ajustes adicionales).

<details>
<summary>Resultados con 24 LUT</summary>

<br>

En nuestras pruebas con 24 LUT (una ronda cada una), la versión habitual quedó
exactamente igual que antes, y 23 LUT obtuvieron una segunda versión:

- **8 mejores en todo lo que cambió**: en ellas la diferencia media con la LUT
  bajó de 3,7 a 2,4 (ColorChecker 1,9 → 1,1, foto 0,91 → 0,75);
- **15 con compromiso**. Los looks de película en color suelen acercarse mucho
  más en todo el rango y en la ColorChecker (p. ej., 3,6 → 2,5) con una foto
  algo peor (hasta 0,17); los looks monocromos suelen acercarse mucho más en los
  grises y en la foto, pero se alejan en todo el rango;
- dos LUT que antes se rechazaban ahora se pueden crear.

</details>

### Qué ayuda más

En una prueba con el mismo tiempo de ajuste, la mejor de cuatro rondas del ajuste
habitual, continuada, superó a un ajuste con [color tras las curvas](#color-tras-las-curvas)
en cada paso. Con diez rondas aleatorias de cada uno, la versión con color tras las
curvas fue mejor de media. Así que ambas cosas ayudan, pero **más rondas del ajuste
habitual dan la mayor mejora**: si tienes tiempo, haz primero más rondas, y añade
`--after-curves` cuando también quieras comparar esa versión.

### Cuando una LUT es «deficiente»

Muchas LUT de simulación de película transforman los colores muy saturados de formas
que los controles de la cámara no pueden seguir, así que son «deficientes» en todo su
rango de colores aunque las imágenes cotidianas se vean bien. El firmware se escribe
igualmente cuando:

- los colores de la **ColorChecker** se diferencian menos de 2 de media, los **grises**
  menos de 2, y ningún gris tiene una dominante de color visible; y, con `--photo`,
  el look no es deficiente en tu foto; o
- con `--photo`, el look es **bueno en tu foto** (y al menos reduce a la mitad la
  diferencia ahí), con los mismos límites para los grises y las dominantes de color.

La herramienta indica qué regla se aplicó. Si no, no escribe ningún firmware; añade
`--force` para crearlo de todos modos, y revisa antes la vista previa.

## Conviene saber

- **Los controles** (Key, Contrast, Highlight, Shadow, Sharpness, Shading,
  Clarity, Toning, Grain) actúan sobre tu look; a 0 obtienes la LUT.
  Saturación y Matiz no se ofrecen en High Contrast; en las posiciones Cinema sí
  (consulta [Elegir la posición](#elegir-la-posición)).
- **Dos entradas "Estándar" y dos "HDR Tone".** Los looks monocromos Estándar y HDR
  usan los mismos nombres e iconos que los de color.
- **Una actualización oficial de RICOH elimina tu look.** Reemplaza todo el
  firmware.
- **Solo para la GR IV y la GR IV HDF.** Nunca instales el archivo en otro modelo, ni en una GR IV
  Monochrome.
- **Archivos creados antes de la 2.2.0, en una GR IV HDF:** el look está ahí, pero los controles se abren con los
  ajustes de RICOH para esa posición en lugar de a 0. Vuelve a crear el mismo `look.json` con la 2.2.0 o posterior;
  `check` te indica qué archivos lo necesitan. En una GR IV están bien.
- **Antes de enviar la cámara al servicio técnico,** vuelve al firmware oficial.
- **Prueba primero muchas LUT:** `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG`
  ajusta e informa sin necesitar el archivo de firmware.

### Comprobar un archivo de firmware

Antes de copiar cualquier archivo de firmware a una tarjeta (en la app: **Comprobar un archivo de firmware**, a la izquierda):

```sh
uv run gr4_lutsmith.py check path/to/fwdc248b.bin
```

Te dice si el archivo es el 1.11 oficial, un firmware de GR4-LUTSmith u otra cosa.
Para un firmware de GR4-LUTSmith, indica también qué posiciones llevan un look, sus
nombres e iconos, y si los looks usan sectores de matiz y la mezcla de color tras las
curvas.

Para comprobar la propia herramienta con tu archivo oficial:

```sh
uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
```

Esto crea el ejemplo incluido (`examples/film-1d.cube`) y compara el resultado con la
compilación probada. Muestra `selftest: PASSED`.

## Riesgos

- Tu cámara no puede distinguir un archivo de firmware bueno de uno dañado. Copia a
  tu tarjeta solo un archivo que haya escrito la herramienta (o que hayas confirmado con `check`).
- Si una actualización se interrumpe, o un archivo de firmware no puede arrancar, puede
  que la cámara ya no llegue a la función de actualización, y entonces necesitaría el
  servicio técnico de RICOH. No ocurrió en las pruebas, pero no se puede descartar.
- Los datos de calibración propios de tu cámara no se tocan.

## Estado de las pruebas

| Qué | Estado |
| --- | --- |
| Un look personal a partir de una LUT con su propia curva tonal, en esta posición, en fotos, vídeo, visor y RAW Development | probado en una GR IV 1.11 |
| Actualización aceptada; volver al 1.11 oficial restablece la cámara por completo | probado en una GR IV 1.11 |
| Los cinco looks monocromos | probado en una GR IV 1.11 (ver GR4-MonoUnlock) |
| Conservar el nombre "High Contrast" y el icono originales de la posición | el nombre y el icono son los de RICOH, sin cambios; esta combinación exacta aún no se ha instalado |
| Controles que empiezan en 0 (grano desactivado) | formado por los mismos cambios que la compilación probada (una parte de ellos); todavía no se ha instalado por separado |
| Looks que necesitan dos o tres curvas tonales (dominantes de color, looks virados) | tres curvas probadas en una GR IV 1.11 |
| Sectores de matiz | probado en una GR IV 1.11 en RAW Development con una LUT de simulación de película (ISO 200, una escena a la luz del día con verdes y amarillos): la cámara coincidió con la predicción de la herramienta, la diferencia con la LUT bajó alrededor de un 30 % en las zonas de color y no se vieron huecos entre colores. Los rojos, azules, morados y las ISO más altas aún no se han comprobado en la cámara |
| Color tras las curvas (`--after-curves`, opcional) | probado en una GR IV 1.11: funciona; cada ronda tarda más; la diferencia media con la LUT es menor, pero en el mismo tiempo más rondas del ajuste habitual dan más mejora (ver [Qué ayuda más](#qué-ayuda-más)) |
| Looks en las posiciones Cinema (Yellow) / Cinema (Green) | probado en una GR IV 1.11: funciona |
| Looks en las demás posiciones (Vivid, Positive Film, Negative Film, Bleach Bypass, Retro, las posiciones monocromas) | probado en una GR IV 1.11: funciona |
| Tu propio nombre para la posición (`--name`) | probado en una GR IV 1.11: funciona |
| Tu propio icono para la posición (`--icon`) | probado en una GR IV 1.11: funciona |
| En una GR IV HDF: los mismos looks, también allí con los controles a 0 (2.2.0) | probado en una GR IV HDF 1.11: funciona |
| Un archivo de la 2.2.0 en una GR IV | comprobado sin la cámara: lo único que se añade son los ajustes de los controles propios de la GR IV HDF; una GR IV lee exactamente lo mismo que con la 2.1.1; todavía no se ha instalado |
| Crear a partir de un `look.json` compartido | comprobado sin la cámara: el firmware es idéntico byte a byte al de `make` con el mismo resultado de la LUT, posición, nombre e icono; no llega nada nuevo a la cámara |
| La app (`GR4-LUTSmith`) crea el mismo firmware que la línea de comandos | comprobado sin la cámara: idéntico byte a byte con la misma LUT, foto y opciones |
| Rondas a la vez (`--jobs`, «A la vez» en la app) | comprobado sin la cámara: los mismos resultados, byte a byte, que las mismas rondas una tras otra |
| La herramienta reproduce exactamente el ejemplo probado | probado (`selftest`) |

## Para desarrolladores

```
GR4-LUTSmith/
├── README.md            this guide
├── gr4_lutsmith.py      the tool (the command line, and the engine the app uses)
├── lutsmith_app/        the app: window, translations (assets/i18n), icons and fonts
├── packaging/           building the app (packaging/build.py), its icons and licence texts
├── tests/test_app.py    checks run before every app build
├── tools/               translation check, app icon
├── pyproject.toml       dependencies (for uv)
├── uv.lock
└── examples/
    ├── film-1d.cube      a 1D film-style LUT (used by selftest)
    └── film-1d.look.json its fitted look
```

- Ejecutar la app desde el código fuente: `uv sync --extra app` y después `uv run python -m lutsmith_app`.
- Crearla: `uv run python packaging/build.py` (en un Mac con Apple silicon, añade `--arch x86_64` para la versión
  para Intel); el zip queda en `dist/`.

| Archivo | SHA-256 |
| --- | --- |
| `fwdc248b.bin` oficial de RICOH GR IV / GR IV HDF 1.11 | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| firmware de ejemplo (`selftest`, a partir de `examples/film-1d.look.json`) | `bb838b5426249f27da68b410223f6c24df36c4816abdaf156472a2a3b61d4441` |
