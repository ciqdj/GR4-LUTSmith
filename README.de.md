<p align="center">
  <img src="lutsmith_app/assets/app/icon-128.png" width="112" height="112" alt="GR4-LUTSmith-Symbol: ein Stahlstab, zu einer Film-Tonwertkurve gebogen">
</p>

<h1 align="center">GR4-LUTSmith</h1>

<p align="center">
  <strong>Ihr eigener Farb-Look aus einer <code>.cube</code>-LUT, direkt in Ihrer RICOH GR IV.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.zh-TW.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <strong>Deutsch</strong> |
  <a href="README.fr.md">Français</a> |
  <a href="README.es.md">Español</a>
</p>

GR4-LUTSmith nimmt eine LUT für die Farbkorrektur (`.cube`) und erstellt eine
GR-IV-Firmware, die deren Look als **Bildsteuerung**-Look enthält. Sie können
damit Fotos und Videos aufnehmen, ihn im Sucher sehen und in
**RAW Development** verwenden. Alles andere an Ihrer Kamera bleibt genau so,
wie es war, und Sie können jederzeit zur offiziellen Firmware zurückkehren.

Dieses Repository enthält keine RICOH-Firmware. Sie laden die offizielle
Firmware selbst von RICOH herunter, und das enthaltene Werkzeug macht daraus auf
Ihrem eigenen Computer die Version mit Ihrem Look.

> [!WARNING]
> **Inoffiziell, auf eigenes Risiko.** Nicht von RICOH IMAGING erstellt oder
> unterstützt. Die Installation veränderter Firmware kann Ihre Garantie
> ungültig machen. Bitte lesen Sie zuerst [Bevor Sie beginnen](#bevor-sie-beginnen)
> und [Risiken](#risiken).

| Sie möchten | Weiter zu |
| --- | --- |
| Ihre Firmware Schritt für Schritt in einem Fenster erstellen (macOS, Windows; in den 21 Sprachen der Kamera) | [Die App](#die-app) |
| Sie im Terminal erstellen (macOS, Windows, Linux) | [Die Befehlszeile](#die-befehlszeile) |
| Einen Look erstellen, den jemand mit Ihnen geteilt hat | [Einen geteilten Look verwenden](#einen-geteilten-look-verwenden) |
| Herausfinden, was eine Firmware-Datei enthält | [Firmware-Datei prüfen](#firmware-datei-prüfen) |
| Zur Firmware von RICOH zurückkehren | [Zurück zur offiziellen Firmware](#zurück-zur-offiziellen-firmware) |

Die App und die Befehlszeile erstellen aus derselben LUT und derselben Auswahl genau dieselbe Firmware.

**Inhalt:**
[So funktioniert es](#so-funktioniert-es) |
[Was Sie bekommen](#was-sie-bekommen) |
[Bevor Sie beginnen](#bevor-sie-beginnen) |
[Die App](#die-app) |
[Die Befehlszeile](#die-befehlszeile) |
[Auf die Kamera bringen](#auf-die-kamera-bringen) |
[Ihre persönliche Note](#ihre-persönliche-note) |
[Genauer anpassen](#genauer-anpassen) |
[Gut zu wissen](#gut-zu-wissen) |
[Risiken](#risiken) |
[Teststand](#teststand) |
[Für Entwickler](#für-entwickler)

## So funktioniert es

Die GR IV kann LUTs nicht direkt verwenden. Ihre Looks entstehen aus wenigen
eigenen Reglern: einer Farbmischung, Tonwertkurven, Kontrasteinstellungen und
**Farbtonsektoren** (getrennte Farbänderungen für 12 Farbtonbereiche).
GR4-LUTSmith **passt** Ihre LUT an diese Regler **an**, misst, wie nah die
Kamera ihr kommt, und schreibt erst dann die Firmware.

- **Tonwert-Looks und Looks mit einer Gesamtfarbwirkung** lassen sich sehr gut
  anpassen. Dazu gehören filmartige Kurven, Kontrast, ausgeblichene Schwarztöne,
  warme oder kühle Farbstiche und Änderungen der Gesamtsättigung.
- **Looks, die einzelne Farbtöne getrennt verschieben** (Teal-Orange,
  Filmsimulationen, die Grüntöne oder den Himmel verschieben, …), werden mit den
  **Farbtonsektoren** angepasst. Sie kommen damit viel näher als mit der
  Farbmischung allein. Änderungen, die stark davon abhängen, wie gesättigt eine
  Farbe ist (z. B. nur die kräftigsten Rottöne), bleiben eine Annäherung, und
  das Werkzeug sagt Ihnen, wenn das der Fall ist.
- **Log- und kameraspezifische Umwandlungs-LUTs** (S-Log, V-Log, …) werden nicht
  unterstützt. Verwenden Sie eine „kreative“ LUT für normale Bilder
  (Rec.709 / sRGB).

Die Anpassung wird mit **CIEDE2000** bewertet, dem üblichen Maß dafür, wie
verschieden zwei Farben aussehen. Als Richtwert: **Unter 1 ist im direkten
Vergleich kaum zu sehen**, und um 2 ist ein kleiner sichtbarer Unterschied.

| Ergebnis | Bedeutung |
| --- | --- |
| **gut** | mittlerer Unterschied unter 1 und 95 % der Farben unter 2: sieht gleich aus |
| **ungefähr** | Mittelwert unter 2: nah dran, mit sichtbaren Unterschieden bei einigen Farben |
| **schwach** | die Kamera kann nicht den ganzen Farbbereich der LUT wiedergeben; die Firmware wird trotzdem geschrieben, wenn die **Alltagsfarben** passen (siehe [Wenn eine LUT „schwach“ ist](#wenn-eine-lut-schwach-ist)) |

Jede LUT wird auf drei Arten gemessen: über ihren ganzen Farbbereich, an den
24 Alltagsfarben einer **ColorChecker**-Tafel (Haut, Himmel, Laub, …) und an
**neutralen Grautönen** (wo jeder Farbstich am deutlichsten zu sehen ist). Mit
einem eigenen Foto (`--photo`) auch an diesem Foto.

## Was Sie bekommen

Nach der Installation endet die Liste der Bildsteuerung so. Menünamen außer
Bildsteuerung, Standard, Farbsättigung und Farbton sind so angegeben, wie sie auf
einer auf Englisch eingestellten Kamera erscheinen.

| Angezeigt als | Look | Foto | Video |
| --- | --- | :---: | :---: |
| HDR Tone | (Ihr bisheriger Farb-Look) | ✓ | |
| Standard | Monochrom Standard | ✓ | ✓ |
| Solid | Monochrom Solid | ✓ | ✓ |
| Soft | Monochrom Soft | ✓ | |
| **High Contrast** | **der Look Ihrer LUT, in Farbe** | ✓ | ✓ |
| Grainy | Monochrom Grainy | ✓ | |
| HDR Tone | Monochrom HDR *(experimentell)* | ✓ | |

- Ihr Look verwendet den Namen und das Symbol von **High Contrast** (der vierte
  Eintrag nach dem ersten „HDR Tone“). Sie können stattdessen **Cinema (Yellow)**,
  **Vivid** oder einen anderen Platz wählen oder mehrere verwenden: siehe
  [Den Platz wählen](#den-platz-wählen). Er kann auch
  [Ihren eigenen Namen](#den-platz-benennen) und
  [Ihr eigenes Symbol](#ihr-eigenes-symbol) zeigen.
- Er startet mit **allen Reglern auf 0**, der Schärfe auf ihrem Standardwert und
  **ausgeschalteter Körnung**. Der Look Ihrer LUT ist für diese Einstellungen
  eingebaut; die Regler wirken dann wie gewohnt, ausgehend von Ihrem Look.
- Die fünf Monochrom-Looks der GR IV Monochrome sind ebenfalls verfügbar, wie
  bei GR4-MonoUnlock.
- Alle Ihre bisherigen Looks bleiben unverändert.

## Bevor Sie beginnen

- **Kamera:** RICOH GR IV (das normale Farbmodell). Andere Modelle werden nicht
  unterstützt.
- **Ihre Kamera muss bereits Firmware 1.11 haben.** Prüfen Sie die Version im
  Einstellungsmenü der Kamera.
  - Ältere Version: Aktualisieren Sie zuerst auf dem üblichen Weg mit der
    offiziellen Datei von RICOH auf 1.11.
  - Neuere Version: **Verwenden Sie dieses Werkzeug nicht.** Es unterstützt nur 1.11.
- **Die offizielle Firmware-Datei.** Laden Sie auf der offiziellen
  GR-IV-Supportseite von RICOH IMAGING die **Firmware-Version 1.11** herunter.
  Entpacken Sie sie bei Bedarf, bis Sie die Datei **`fwdc248b.bin`** haben.
- **Ein voll geladener Akku.** Während eines Firmware-Updates darf der Strom
  niemals ausfallen.
- **Eine SD-Karte**, die Sie formatieren können.
- **Ihre LUT** als `.cube`-Datei (3D oder 1D) und die Angabe, ob sie für
  **sRGB** (die meisten LUTs) oder **Adobe RGB** erstellt wurde.
- **Empfohlen:** ein DNG-Foto, aufgenommen mit Ihrer GR IV. Das Werkzeug prüft
  damit den Look an echten Motiven und erstellt eine Vorschau.
- Notieren Sie sich eigene Einstellungen (C1, C2, …), die Sie nicht noch einmal
  einrichten möchten.

Erstellen Sie dann Ihre Firmware mit [der App](#die-app) oder
[der Befehlszeile](#die-befehlszeile).

## Die App

### Herunterladen

Laden Sie aus dem [neuesten Release](../../releases/latest) die Datei für Ihren Computer herunter:

| Computer | Datei |
| --- | --- |
| Mac mit Apple Chip (M1 oder neuer) | `GR4-LUTSmith-<version>-macOS-AppleSilicon.zip` |
| Mac mit Intel-Prozessor | `GR4-LUTSmith-<version>-macOS-Intel.zip` |
| Windows 10 oder 11 (64 Bit) | `GR4-LUTSmith-<version>-Windows-x64.zip` |

Sie brauchen macOS 12 (Monterey) oder neuer. Sie wissen nicht, welchen Mac Sie haben? Apple-Menü →
**Über diesen Mac**: „Chip Apple M…“ bedeutet Apple Chip, „Prozessor Intel“ bedeutet Intel.

Jede Zip-Datei enthält die App und einen Ordner `Licences` (die Lizenzen der Bestandteile, aus denen sie gebaut ist).

<details>
<summary><strong>Prüfen, ob die Datei von diesem Projekt stammt</strong> (optional)</summary>

<br>

Jede Zip-Datei wird vom eigenen Build dieses Repositorys auf GitHub erstellt. Dieser signiert einen Nachweis
ihrer Herkunft: das Repository, den Build und die genaue Version des Codes. Mit der
[GitHub CLI](https://cli.github.com) (angemeldet mit `gh auth login`) können Sie prüfen, dass Ihr Download genau
diese Datei ist und nicht verändert oder ausgetauscht wurde:

```sh
gh attestation verify GR4-LUTSmith-2.1.1-macOS-AppleSilicon.zip --repo lemonadesaltbagel/GR4-LUTSmith
```

(Verwenden Sie den Namen der Zip-Datei, die Sie heruntergeladen haben; unter Windows führen Sie den Befehl in
PowerShell in Ihrem Ordner „Downloads“ aus.) Am Ende steht „Verification succeeded!“ und der Build, der die Datei
erstellt hat. Jedes andere Ergebnis bedeutet: Öffnen Sie die Datei nicht, und laden Sie sie erneut von der
Release-Seite herunter. Die Seite **Attestations** des Repositorys listet jede signierte Datei auf.

Eine schnellere Prüfung, ob der Download vollständig ist: Das Release nennt die SHA-256 jeder Datei in `SHA256SUMS`.

- macOS (Terminal): `shasum -a 256 ~/Downloads/GR4-LUTSmith-*.zip`
- Windows (PowerShell): `Get-FileHash $HOME\Downloads\GR4-LUTSmith-*.zip -Algorithm SHA256`

Das zeigt nur, dass die Datei unversehrt angekommen ist, nicht wer sie erstellt hat: `SHA256SUMS` steht auf
derselben Seite wie die Zip-Dateien.

Sie können den Download auch ganz weglassen: Starten Sie die App aus dem Quellcode (siehe
[Für Entwickler](#für-entwickler)), oder erstellen Sie die Firmware mit der
[Befehlszeile](#die-befehlszeile). Die App und die Befehlszeile erstellen genau dieselbe `fwdc248b.bin`,
und `uv run gr4_lutsmith.py check fwdc248b.bin` zeigt, was eine Firmware-Datei enthält.

</details>

### Beim ersten Öffnen

Die App ist kostenlos und nicht mit einem kostenpflichtigen Zertifikat von Apple oder Microsoft signiert. Daher
fragt Ihr Computer einmal nach, ob Sie ihr vertrauen.

**macOS**

1. Entpacken Sie die Datei und ziehen Sie **GR4-LUTSmith** in Ihren Ordner „Programme“.
2. Öffnen Sie die App. macOS meldet, dass die App nicht auf Schadsoftware geprüft werden kann; wählen Sie
   **Fertig** (macOS 15) oder **Abbrechen**.
3. Öffnen Sie **Systemeinstellungen → Datenschutz & Sicherheit**, scrollen Sie nach unten zur Meldung über
   GR4-LUTSmith, wählen Sie **Dennoch öffnen** und bestätigen Sie mit Ihrem Passwort.
   Unter macOS 12 bis 14 können Sie stattdessen bei gedrückter Ctrl-Taste auf die App klicken, **Öffnen** wählen
   und dann noch einmal **Öffnen**.

Danach öffnet sie sich ganz normal.

**Windows**

1. Klicken Sie mit der rechten Maustaste auf die Zip-Datei → **Alle extrahieren…** und öffnen Sie den
   entpackten Ordner **GR4-LUTSmith** (starten Sie die App nicht aus der Zip-Datei heraus).
2. Öffnen Sie **GR4-LUTSmith.exe**. Wenn Windows „Der Computer wurde durch Windows geschützt“ anzeigt, wählen Sie
   **Weitere Informationen → Trotzdem ausführen**.

Lassen Sie den ganzen Ordner beisammen: Die App braucht den Ordner `_internal` neben sich.

### Verwenden

Die App führt Sie auf dem Bildschirm durch die Schritte: die Firmware-Datei Ihrer Kamera, die LUT (und optional
ein DNG), den Platz mit Name und Symbol, die Anpassung und das Erstellen. Sie speichert `fwdc248b.bin` an einem Ort
Ihrer Wahl; dann [bringen Sie sie auf die Kamera](#auf-die-kamera-bringen).

- **Sprache:** Die App folgt der Sprache Ihres Computers; Sie können sie oben im Fenster ändern. Das ist auch die
  Kamerasprache, für die die Namen Ihrer Plätze geprüft werden (siehe [Den Platz benennen](#den-platz-benennen)).
- **Darstellung:** System, Tag oder Nacht, oben im Fenster.
- **Firmware-Datei prüfen** (links) sagt Ihnen, ob eine `fwdc248b.bin` die offizielle Datei von RICOH ist, mit
  GR4-LUTSmith erstellt wurde (und mit welchen Looks) oder etwas anderes ist.
- Geteilte Looks (`.json`) funktionieren auch in der App: Wählen Sie auf der ersten Seite „Ein geteilter Look“.
- **Mehrere Durchgänge gleichzeitig:** Wählen Sie auf der Seite „Anpassen“, wie viele Durchgänge es sind und wie
  viele gleichzeitig laufen (je ein Prozessorkern; siehe [Mehr Durchgänge](#mehr-durchgänge)). Jeder Durchgang
  zeigt seinen Fortschritt; Sie können Durchgänge hinzufügen, während sie laufen, und „Alle anhalten“ behält die
  bereits abgeschlossenen Durchgänge. Die Ergebnisse kommen in die Tabelle, sobald Durchgänge fertig sind.

### Wenn etwas nicht funktioniert

- **macOS meldet, die App sei beschädigt:** Laden Sie sie erneut herunter (die Datei war unvollständig), und
  prüfen Sie sie wie unter [Prüfen, ob die Datei von diesem Projekt stammt](#herunterladen).
- **Die App startet unter Windows nicht:** Achten Sie darauf, dass Sie die ganze Zip-Datei entpackt haben, und
  starten Sie `GR4-LUTSmith.exe` aus dem entpackten Ordner.
- **Die Firmware-Datei wird abgelehnt:** Die App akzeptiert nur die unveränderte `fwdc248b.bin` 1.11 der GR IV
  von RICOH. Eine Datei, die GR4-LUTSmith bereits verändert hat, kann nicht erneut verändert werden; beginnen Sie
  mit der unveränderten Datei.

## Die Befehlszeile

### 1. Einrichten

Installieren Sie **[uv](https://docs.astral.sh/uv/)** (es installiert Python und
alles andere, was das Werkzeug braucht), öffnen Sie ein Terminal in diesem
Ordner und führen Sie aus:

```sh
uv sync --extra photo
```

<details>
<summary>Ohne uv</summary>

<br>

Mit Python 3.9 oder neuer:

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` und `pillow` werden nur für `--photo` und `preview` benötigt.

</details>

### 2. Ihre Firmware erstellen

Verwenden Sie Ihre eigenen Pfade:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

| Option | Was sie bewirkt |
| --- | --- |
| `--space adobe` | die LUT wurde für Adobe RGB erstellt |
| `--photo R0001234.DNG` | prüft den Look zusätzlich an Ihrem Foto (optional, aber empfohlen) |
| `--slot vivid`, `--slot cinema-yellow`, … | setzt Ihren Look statt auf High Contrast an die Stelle eines anderen Looks: [Den Platz wählen](#den-platz-wählen) |
| `--name "My Look"` | zeigt den Platz unter Ihrem eigenen Namen: [Den Platz benennen](#den-platz-benennen) |
| `--icon my_icon.png` | gibt dem Platz Ihr eigenes Menüsymbol: [Ihr eigenes Symbol](#ihr-eigenes-symbol) |
| `--turns 3` | führt drei Anpassungen aus und behält die besten: [Mehr Durchgänge](#mehr-durchgänge) |
| `--jobs 3` | führt bis zu drei dieser Durchgänge nebeneinander aus: [Mehr Durchgänge](#mehr-durchgänge) |
| `--after-curves` | versucht zusätzlich eine zweite Farbmischung: [Farbe nach den Kurven](#farbe-nach-den-kurven) |

Das Werkzeug:

1. stellt sicher, dass Sie ihm die echte offizielle Datei 1.11 gegeben haben;
2. passt die LUT an (das dauert einige Minuten, plus ein bis zwei Minuten für
   die Farbtonsektoren) und zeigt, wie gut sie passt;
3. erstellt die Firmware und prüft sie.

Ein erfolgreicher Lauf endet so:

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
Copy this file to the root of the SD card and run the camera's firmware update.
Then choose High Contrast in Image Control: your look is there.
```

Das Werkzeug sagt zu Beginn auch, auf welchen Platz Ihr Look kommt, zum Beispiel
`slot: High Contrast (replaces the hidden monochrome High Contrast look)`.

Der Ausgabeordner `output/my_look/` enthält außerdem `look.json` (den
angepassten Look) und kann eine Vorschau aufnehmen (Schritt 3). Sie können
`look.json` mit anderen GR-IV-Besitzern teilen: Sie erstellen damit denselben
Look, ohne ihn erneut anzupassen (siehe
[Einen geteilten Look verwenden](#einen-geteilten-look-verwenden)).

Wenn sich die LUT nicht gut wiedergeben lässt oder die Firmware-Datei nicht die
offizielle 1.11 ist, gibt das Werkzeug `refused: …` aus und schreibt **keine
Firmware**.

### 3. Vorschau (optional)

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

Das schreibt `output/my_look/preview.jpg` mit drei Feldern: die Kamera ohne den
Look, die LUT selbst und die Kamera **mit** dem Look. Das LUT-Feld braucht die
`.cube`-Datei: Das Werkzeug findet sie neben `look.json` oder im aktuellen
Ordner, oder Sie geben sie mit `--lut my_look.cube` an; ohne sie zeigt die
Vorschau die beiden anderen Felder. Vergleichen Sie Farbe und Tonwerte.
Schärfung und Rauschen werden nicht simuliert.

Dann [bringen Sie sie auf die Kamera](#auf-die-kamera-bringen).

## Auf die Kamera bringen

Das gilt gleichermaßen für eine Firmware aus der App und aus der Befehlszeile.

### 1. Auf die SD-Karte kopieren

1. **Formatieren Sie die SD-Karte in der Kamera.**
2. Kopieren Sie **`fwdc248b.bin`** (aus der Befehlszeile: `output/my_look/fwdc248b.bin`)
   in die **oberste Ebene** der Karte: nicht in einen Ordner, und der Name muss
   genau `fwdc248b.bin` bleiben.

### 2. Kamera aktualisieren

1. Setzen Sie den voll geladenen Akku und die SD-Karte ein.
2. Starten Sie das Firmware-Update im Einstellungsmenü der Kamera, wie in der
   offiziellen Anleitung von RICOH zum Firmware-Update der GR IV beschrieben.
3. **Die Kamera zeigt ein Update von Version 1.11 auf Version 1.11.** Das ist
   so gewollt: Die veränderte Firmware behält die Versionsnummer. Bestätigen Sie
   das Update.

> [!CAUTION]
> **Schalten Sie die Kamera nicht aus, öffnen Sie weder Akku- noch
> Kartenfach, und nehmen Sie die Karte nicht heraus**, bis das Update
> abgeschlossen ist und die Kamera neu gestartet hat.

### 3. Fotografieren

- Öffnen Sie **Bildsteuerung** und wählen Sie **High Contrast** (nach dem ersten
  „HDR Tone“). Der Eintrag ist jetzt in Farbe. Wenn Sie einen anderen Platz
  gewählt haben, wählen Sie stattdessen diesen Eintrag.
- Die Firmware-Version zeigt weiterhin **1.11**. Das ist normal.
- Löschen Sie `fwdc248b.bin` von der Karte (oder formatieren Sie die Karte),
  damit das Update nicht versehentlich erneut startet.

Um später zu einer anderen LUT zu wechseln, erstellen Sie aus der **offiziellen**
Datei eine neue Firmware und installieren Sie sie auf dieselbe Weise.

### Zurück zur offiziellen Firmware

Wiederholen Sie die Schritte 1–2 stattdessen mit der **offiziellen** `fwdc248b.bin`
von RICOH. Die Kamera zeigt wieder **1.11 → 1.11**; bestätigen Sie, und Ihre
Kamera ist wieder im Originalzustand.

## Ihre persönliche Note

Wohin Ihr Look kommt, wie er heißt und wie er im Menü aussieht. In der App
finden Sie das im Schritt „Platz, Name, Symbol“; in der Befehlszeile sind es
Optionen von `make` und `build`.

### Den Platz wählen

Ihr Look ersetzt einen der Looks der Kamera. Welchen, wählen Sie mit `--slot`
(`make` und `build`); `uv run gr4_lutsmith.py slots` zeigt dieselbe Liste im
Terminal:

| `--slot` | Angezeigt als | Ersetzt | Foto | Video | Zusätzliche Regler |
| --- | --- | --- | :---: | :---: | --- |
| `high-contrast` (Standardwert) | High Contrast | den verborgenen monochromen Look High Contrast | ✓ | ✓ | — |
| `cinema-yellow` | Cinema (Yellow) | den RICOH-Look Cinema (Yellow) | ✓ | ✓ | Farbsättigung, Farbton |
| `cinema-green` | Cinema (Green) | den RICOH-Look Cinema (Green) | ✓ | ✓ | Farbsättigung, Farbton |
| `vivid` | Vivid | den RICOH-Look Vivid | ✓ | ✓ | Farbsättigung, Farbton |
| `positive-film` | Positive Film | den RICOH-Look Positive Film | ✓ | ✓ | Farbsättigung, Farbton |
| `negative-film` | Negative Film | den RICOH-Look Negative Film | ✓ | ✓ | Farbsättigung, Farbton |
| `bleach-bypass` | Bleach Bypass | den RICOH-Look Bleach Bypass | ✓ | ✓ | Farbsättigung, Farbton |
| `retro` | Retro | den RICOH-Look Retro | ✓ | ✓ | Farbsättigung, Farbton |
| `soft-monotone` | Soft Monotone | den RICOH-Look Soft Monotone | ✓ | | — |
| `hard-monotone` | Hard Monotone | den RICOH-Look Hard Monotone | ✓ | ✓ | — |
| `hi-contrast-bw` | Hi-Contrast B&W | den RICOH-Look Hi-Contrast B&W | ✓ | ✓ | — |
| `mono-standard` | Standard (der zweite) | den verborgenen monochromen Look Standard | ✓ | ✓ | — |
| `mono-soft` | Soft | den verborgenen monochromen Look Soft | ✓ | | — |
| `mono-solid` | Solid | den verborgenen monochromen Look Solid | ✓ | ✓ | — |

- Die Farben sind auf jedem Platz gleich: Die Kamera verarbeitet Ihren Look dort
  auf dieselbe Weise, daher ändern sich die Anpassung und ihre Werte mit dem
  Platz nicht.
- Ihr Look startet auf jedem Platz mit allen Reglern auf 0 und ausgeschalteter
  Körnung.
- Mit dem Platz ändert sich nur, welchen Eintrag Sie verlieren und welche Regler
  Sie bekommen. Auf einem Monochrom-Platz ist Ihr Look in Farbe; Farbsättigung
  und Farbton werden dort nicht angeboten.
- **Cinema:** Die Einstellung Color Tone wirkt sich nicht auf Ihren Look aus.
  **Bleach Bypass:** Die Toneinstellung verändert Ihren Look nicht.
  **Retro:** Die eigene Tonung von Retro und der vignettenartige Toneffekt
  werden entfernt, sodass Sie nur Ihren Look bekommen.
- Ein Platz, den Sie nicht verwenden, behält den Look von RICOH. Ohne einen Look
  auf High Contrast bleibt dort der monochrome Look High Contrast.
- **Nicht verfügbar:** Standard, Monotone, HDR Tone, Cross Processing und die
  verborgenen Looks Grainy und HDR. Diese teilen Teile ihrer Verarbeitung mit
  anderen Looks oder nutzen eine besondere Verarbeitung, die Ihre Farben
  verändern würde.
- `check` listet auf, welche Plätze einen persönlichen Look tragen.

### Mehrere Looks in einer Firmware

Passen Sie jede LUT mit `fit` an und erstellen Sie sie dann zusammen, jede
Look-Datei gefolgt von ihrem eigenen `--slot` (und nach Wunsch `--name`,
`--icon`):

```sh
uv run gr4_lutsmith.py fit look_a.cube --photo R0001234.DNG -o output/a
uv run gr4_lutsmith.py fit look_b.cube --photo R0001234.DNG -o output/b
uv run gr4_lutsmith.py build output/a/look.json --slot cinema-yellow output/b/look.json --slot vivid --name "Look B" ~/Downloads/fwdc248b.bin -o output/both
```

**Wie viele auf einmal:** High Contrast und die beiden Cinema-Plätze nehmen immer
einen vollständigen Look auf. Die anderen Plätze teilen sich einen begrenzten
Speicherplatz: Jeder Look braucht Platz für seine Tonwertkurven und viel mehr für
Farbtonsektoren und Farbe nach den Kurven. Ein einfacher Look (eine Tonwertkurve)
passt auf bis zu 10 davon gleichzeitig; Looks mit Farbtonsektoren auf weit
weniger. Wenn sie nicht passen, sagt das Werkzeug das und schreibt nichts;
verwenden Sie weniger Plätze oder einfachere Looks, und lassen Sie High Contrast
frei, um den meisten Platz zu haben.

### Den Platz benennen

`--name` (`make` und `build`) gibt dem Platz Ihren eigenen Namen, im Menü
Bildsteuerung und seinen Bildschirmen, in allen Sprachen der Kamera:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra"
```

- Jeder Platz erlaubt Namen bis zu einer bestimmten Länge:
  `uv run gr4_lutsmith.py slots` zeigt sie (von 9 Zeichen bei Retro bis 23 bei
  Cinema (Yellow)). Der zweite monochrome Standard kann nicht umbenannt werden,
  weil er seinen Namen mit dem Farb-Look Standard teilt.
- **Einfaches ASCII** (englische Buchstaben, Ziffern, Leerzeichen und
  Satzzeichen) wird in jeder Kamerasprache angezeigt. Das ist die sichere Wahl.
- **Andere Buchstaben und Zeichen** funktionieren in den Kamerasprachen, die sie
  verwenden: Ein japanischer Name wird angezeigt, wenn die Kamera auf Japanisch
  eingestellt ist, `Müller` in den europäischen Sprachen, `Плёнка` auf Russisch
  und so weiter. Zeichen, die keine der Sprachen der Kamera verwendet (Emoji,
  Arabisch, Hebräisch, …), werden abgelehnt.
- Das Werkzeug prüft den Namen für Ihre **Kamerasprache**. Das ist die Sprache
  Ihres Computers, sofern Sie nicht `--camera-language` angeben (zum Beispiel
  `--camera-language Japanese`; `--help` listet alle 21 auf). Wenn der Name
  Zeichen enthält, die diese Sprache nicht verwendet, warnt das Werkzeug, dass
  sie eventuell nicht angezeigt werden, und fragt, ob Sie den Namen trotzdem
  verwenden möchten. Antworten Sie `y`, um fortzufahren, oder fügen Sie
  `--accept-name` hinzu, um im Voraus zuzustimmen (nötig, wenn das Werkzeug
  nicht fragen kann, zum Beispiel in einem Skript). Wenn Sie die Kamera später
  auf eine andere Sprache umstellen, wird ein Name außerhalb von ASCII dort
  eventuell nicht angezeigt.
- Lange Namen werden auf manchen Bildschirmen eventuell abgeschnitten
  (chinesische, japanische und koreanische Zeichen sind etwa doppelt so breit
  wie englische Buchstaben).
- Ohne `--name` behält der Platz seinen eigenen Namen. Der Name wird nicht in
  `look.json` gespeichert (diese Datei enthält nur den Look): Geben Sie `--name`
  erneut an, wenn Sie `build` ausführen. `check` zeigt den Namen in einer
  erstellten Firmware.

### Ihr eigenes Symbol

`--icon` (`make` und `build`) ersetzt das Symbol des Platzes im Menü
Bildsteuerung durch Ihr eigenes Bild:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- Jedes Bild funktioniert (PNG, JPEG, …). Das Menüsymbol ist 40×40 Pixel groß:
  Ein größeres oder kleineres Bild wird skaliert, und wenn es nicht quadratisch
  ist, wird seine **Mitte** verwendet. Transparente Bereiche bleiben transparent,
  sodass ein PNG mit transparentem Hintergrund wie die eigenen Symbole der Kamera
  aussieht.
- `make` speichert das Ergebnis als `icon.png` neben der Firmware, damit Sie
  genau sehen, was die Kamera zeigen wird. Einfache, kräftige Formen sind in
  dieser Größe am besten zu erkennen.
- Jeder Platz außer dem zweiten monochromen Standard nimmt ein eigenes Symbol an
  (dieser teilt sein Symbol mit dem Farb-Look Standard). `slots` listet sie auf.
- Dafür wird Pillow benötigt (`uv sync --extra photo`). Ohne `--icon` behält der
  Platz sein eigenes Symbol. Das Symbol wird nicht in `look.json` gespeichert:
  Geben Sie `--icon` erneut an, wenn Sie `build` ausführen. `check` zeigt, welche
  Plätze ein eigenes Symbol haben.

### Einen geteilten Look verwenden

`look.json` enthält nur den Look selbst: seine Farbeinstellungen und wie gut sie
zur LUT passen. Nichts über den Platz, den Namen oder das Symbol und keine
Ordner Ihres Computers (nur den Dateinamen der LUT). Wer die Datei hat, kann
die Firmware direkt erstellen, ohne die LUT und ohne Anpassung, und erhält bei
gleichem Platz, Namen und Symbol Byte für Byte dieselbe Firmware wie der
Ersteller.

Wählen Sie in der App auf der ersten Seite „Ein geteilter Look“. In der
Befehlszeile kann die Datei einen beliebigen Namen haben; benennen Sie sie also
vor dem Teilen nach Belieben um (`portra-400.json`, …):

```sh
uv run gr4_lutsmith.py build portra-400.json ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- Das Werkzeug zeigt zuerst, wie gut der Look zu seiner LUT passt (die
  Ergebnisse, die der Ersteller gesehen hat; „on your photo“ bedeutet das Foto
  des Erstellers).
- Platz, Name und Symbol wählen Sie selbst, wie unter
  [Den Platz wählen](#den-platz-wählen), [Den Platz benennen](#den-platz-benennen)
  und [Ihr eigenes Symbol](#ihr-eigenes-symbol). Ohne `--slot` kommt der Look auf
  High Contrast.
- Mehrere Looks: Schreiben Sie `--slot`, `--name` und `--icon` jeder Datei
  direkt hinter die Datei:

  ```sh
  uv run gr4_lutsmith.py build portra-400.json --slot vivid --name "Portra" tri-x.json --slot hard-monotone ~/Downloads/fwdc248b.bin -o output/both
  ```

- Der Inhalt der Datei wird geprüft, bevor etwas erstellt wird: Eine beschädigte
  Datei oder eine mit Werten, die die Kamera nicht verarbeiten kann, wird
  abgelehnt, und es wird nichts geschrieben.
- Dateien aus Versionen vor 1.7.0 können auch einen Platz, einen Namen, ein
  Symbol und den vollständigen Pfad zur LUT enthalten. `build` ignoriert Platz,
  Name und Symbol (und sagt, welche es waren); öffnen Sie eine solche Datei in
  einem Texteditor und prüfen Sie `"file"`, bevor Sie sie teilen.

## Genauer anpassen

Farbtonsektoren werden bei jeder Anpassung versucht. Wenn Sie es genauer
möchten, führen Sie zuerst mehr Durchgänge aus und versuchen Sie dann Farbe nach
den Kurven (siehe [Was mehr hilft](#was-mehr-hilft)).

### Farbtonsektoren

Nach der Anpassung von Farbmischung und Tonwertkurven versucht das Werkzeug, den
Look mit **Farbtonsektoren** zu verbessern: Die Kamera kann Farben in 12
Farbtonbereichen getrennt ändern. Sie werden **nur behalten, wenn sie deutlich
helfen** (der ganze Farbbereich oder der ColorChecker verbessert sich um
mindestens 10 %) **und nichts schlechter wird** (Ihr Foto, die Grautöne, der
ColorChecker). Die Ergebniszeile sagt `hue sectors: yes` oder `no`.

- Grautöne werden von den Farbtonsektoren nie verändert, und benachbarte Sektoren
  schließen immer lückenlos aneinander an, sodass die Farben von einem Farbton zum
  nächsten gleichmäßig verlaufen.
- Mit `--photo` werden die Farbtonsektoren auch auf echte Motive abgestimmt
  (empfohlen).
- `--no-hue` schaltet sie aus (`make` und `fit`).

### Mehr Durchgänge

Die Anpassung beginnt an einem Startpunkt und verbessert sich von dort aus. Die
Kamera hat nur wenige Farbregler, daher **entscheidet oft der Startpunkt, wie nah
die Anpassung kommt**. Mit `--turns` (in der App: auf der Seite „Anpassen“) führt
das Werkzeug mehrere Anpassungen („Durchgänge“) aus, jede von einem neuen
zufälligen Startpunkt, und behält die guten:

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG --turns 3
```

- Durchgang 1 verwendet immer den üblichen Startpunkt, daher liefert ein
  Durchgang (der Standardwert) dasselbe Ergebnis wie bisher. Jeder weitere
  Durchgang zieht einen neuen zufälligen Start.
- Jeder Durchgang dauert so lange wie eine normale Anpassung (einige Minuten).
- **Nebeneinander.** `--jobs 3` führt bis zu drei Durchgänge gleichzeitig aus,
  jeden auf einem Prozessorkern und mit etwa 0,8 GB Arbeitsspeicher. Lassen Sie
  mindestens einen Kern für den Rest des Computers frei. Die Ergebnisse sind genau
  dieselben wie bei Durchgängen nacheinander; sie sind nur früher fertig.
- **Behaltene Ergebnisse.** Ein neues Ergebnis wird behalten, außer ein früheres
  ist bei jedem Maß mindestens genauso gut (der ganze Bereich, der ColorChecker,
  die Grautöne und Ihr Foto). Ein früheres Ergebnis, das das neue bei jedem Maß
  übertrifft, fällt aus der Liste. Jedes behaltene Ergebnis ist also bei
  mindestens einem Maß besser als alle anderen; das Werkzeug zeigt sie
  nebeneinander und empfiehlt das mit dem besten Gesamtwert (dem mittleren
  Unterschied über alles, was die Anpassung verwendet).
- **Am Ende Durchgänge hinzufügen.** Wenn die Ergebnisse erscheinen, fragt das
  Werkzeug `More turns?`. Geben Sie eine Zahl ein, um so viele weitere
  Durchgänge auszuführen, auf dieselbe Art, wie der Lauf begonnen hat (`2`);
  hängen Sie `a` an für Durchgänge mit
  [Farbe nach den Kurven](#farbe-nach-den-kurven) (`2a`) oder `b` für
  Durchgänge ohne (`2b`), unabhängig davon, wie der Lauf begonnen hat. Neue
  Durchgänge werden mit allen behaltenen Ergebnissen verglichen. Drücken Sie
  die Eingabetaste, um zu behalten, was Sie haben.
- **Einen Durchgang wiederholen.** Der Seed jedes Durchgangs wird angezeigt und
  in `turns.json` gespeichert; `--seed 1234` führt denselben Durchgang erneut aus
  (mit `--turns 3`: Seeds 1234, 1235, 1236).

Mit mehr als einem behaltenen Ergebnis sieht der Ausgabeordner so aus:

```
output/my_look/look.json, fwdc248b.bin      the recommended result
output/my_look/turns/turn-1/                 every kept result, each with its
output/my_look/turns/turn-3-after-curves/    own look.json (and, with make, fwdc248b.bin)
output/my_look/turns.json                    every turn, its seed and its scores
```

Um ein anderes behaltenes Ergebnis zu verwenden, kopieren Sie stattdessen dessen
`fwdc248b.bin` auf die SD-Karte.

### Farbe nach den Kurven

Mit `--after-curves` (`make` und `fit`) versucht das Werkzeug zusätzlich eine
zweite Farbmischung, die die Kamera **nach** den Tonwertkurven anwendet. Viele
Film-Looks verändern Farben in Schatten und Lichtern unterschiedlich. Die übliche
Farbmischung wirkt vor den Kurven und kann dem daher nicht folgen, eine Mischung
nach den Kurven aber oft schon.

Der ganze Farbbereich der LUT und echte Fotos stimmen nicht immer überein: Eine
Version kann bei gesättigten Farben viel näher sein und bei einem Alltagsfoto
etwas weiter entfernt. Daher kommen beide Versionen in die Liste der behaltenen
Ergebnisse, die unter [Mehr Durchgänge](#mehr-durchgänge) beschrieben ist: Die
Version mit Farbe nach den Kurven wird immer dann behalten, wenn sie in
irgendetwas besser ist (der ganze Bereich, der ColorChecker, die Grautöne oder
Ihr Foto), neben der üblichen, und Sie wählen. Sehen Sie sich vor der Wahl beide
in der Vorschau an Ihrem eigenen Foto an.

**Warum es optional ist.** Mehr Durchgänge der üblichen Anpassung sind der
größere Hebel (siehe [Was mehr hilft](#was-mehr-hilft)). Die Mischung nach den
Kurven hilft im Mittel, macht aber jeden Durchgang um mehrere Minuten länger.

- Grau bleibt grau: Die Mischung fügt einem neutralen Grau nie einen Farbstich
  hinzu.
- Die Anpassung dauert mehrere Minuten länger (vier zusätzliche Anpassungen).

<details>
<summary>Ergebnisse mit 24 LUTs</summary>

<br>

In unseren Tests mit 24 LUTs (je ein Durchgang) blieb die übliche Version genau
wie zuvor, und 23 LUTs bekamen eine zweite Version:

- **8 bei allem besser, was sich geändert hat**: Dort sank der mittlere
  Unterschied zur LUT von 3,7 auf 2,4 (ColorChecker 1,9 → 1,1, Foto 0,91 → 0,75);
- **15 mit einem Kompromiss**. Farbfilm-Looks kommen meist über den ganzen
  Bereich und beim ColorChecker viel näher (z. B. 3,6 → 2,5), bei einem etwas
  schlechteren Foto (um bis zu 0,17); Monochrom-Looks kommen meist bei Grautönen
  und beim Foto viel näher, aber über den ganzen Bereich weniger nah;
- zwei LUTs, die zuvor abgelehnt wurden, lassen sich jetzt erstellen.

</details>

### Was mehr hilft

In einem Test mit derselben Anpassungszeit schlug der beste von vier
Durchgängen der üblichen Anpassung, weitergeführt, eine Anpassung mit
[Farbe nach den Kurven](#farbe-nach-den-kurven) bei jedem Schritt. Über je zehn
zufällige Durchgänge war die Version mit Farbe nach den Kurven im Mittel besser.
Beides hilft also, aber **mehr Durchgänge der üblichen Anpassung bringen den
größeren Gewinn**: Wenn Sie Zeit haben, führen Sie zuerst mehr Durchgänge aus,
und fügen Sie `--after-curves` hinzu, wenn Sie auch diese Version vergleichen
möchten.

### Wenn eine LUT „schwach“ ist

Viele LUTs zur Filmsimulation formen sehr gesättigte Farben auf eine Weise um,
der die Regler der Kamera nicht folgen können. Daher sind sie über ihren ganzen
Farbbereich „schwach“, obwohl Alltagsbilder richtig aussehen. Die Firmware wird
trotzdem geschrieben, wenn:

- die **ColorChecker**-Farben im Mittel um weniger als 2 abweichen, die
  **Grautöne** um weniger als 2, und kein Grau einen sichtbaren Farbstich
  bekommt; und mit `--photo` der Look an Ihrem Foto nicht schwach ist; oder
- mit `--photo` der Look **an Ihrem Foto gut** ist (und den Unterschied dort
  mindestens halbiert), mit denselben Grenzen für Grautöne und Farbstich.

Das Werkzeug sagt, welche Regel gegriffen hat. Andernfalls schreibt es keine
Firmware; fügen Sie `--force` hinzu, um trotzdem zu erstellen, und prüfen Sie
vorher die Vorschau.

## Gut zu wissen

- **Die Regler** (Key, Contrast, Highlight, Shadow, Sharpness, Shading,
  Clarity, Toning, Grain) wirken zusätzlich zu Ihrem Look; bei 0 bekommen Sie
  die LUT. Farbsättigung und Farbton werden auf High Contrast nicht angeboten;
  auf den Cinema-Plätzen schon (siehe [Den Platz wählen](#den-platz-wählen)).
- **Zwei Einträge „Standard“ und zwei „HDR Tone“.** Die monochromen Looks
  Standard und HDR verwenden dieselben Namen und Symbole wie die farbigen.
- **Ein offizielles Update von RICOH entfernt Ihren Look.** Es ersetzt die
  gesamte Firmware.
- **Nur für die normale GR IV.** Installieren Sie die Datei nie auf einem
  anderen Modell.
- **Bevor Sie die Kamera zum Service schicken,** kehren Sie zur offiziellen
  Firmware zurück.
- **Probieren Sie zuerst viele LUTs aus:** `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG`
  passt an und berichtet, ohne dass die Firmware-Datei nötig ist.

### Firmware-Datei prüfen

Bevor Sie eine Firmware-Datei auf eine Karte kopieren (in der App: **Firmware-Datei prüfen**, links):

```sh
uv run gr4_lutsmith.py check path/to/fwdc248b.bin
```

Es sagt Ihnen, ob die Datei die offizielle 1.11, eine GR4-LUTSmith-Firmware oder
etwas anderes ist. Bei einer GR4-LUTSmith-Firmware listet es außerdem auf, welche
Plätze einen Look tragen, ihre Namen und Symbole und ob die Looks
Farbtonsektoren und die Farbmischung nach den Kurven verwenden.

So prüfen Sie das Werkzeug selbst mit Ihrer offiziellen Datei:

```sh
uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
```

Das erstellt das mitgelieferte Beispiel (`examples/film-1d.cube`) und vergleicht
das Ergebnis mit dem getesteten Build. Es gibt `selftest: PASSED` aus.

## Risiken

- Ihre Kamera kann eine gute Firmware-Datei nicht von einer beschädigten
  unterscheiden. Kopieren Sie nur eine Datei auf Ihre Karte, die das Werkzeug
  geschrieben (oder mit `check` bestätigt) hat.
- Wenn ein Update unterbrochen wird oder eine Firmware-Datei nicht starten kann,
  erreicht die Kamera die Update-Funktion eventuell nicht mehr und müsste dann
  zum RICOH-Service. Das ist in den Tests nicht passiert, lässt sich aber nicht
  ausschließen.
- Die eigenen Kalibrierungsdaten Ihrer Kamera werden nicht angetastet.

## Teststand

| Was | Stand |
| --- | --- |
| Ein persönlicher LUT-Look mit eigener Tonwertkurve, auf diesem Platz, bei Fotos, Video, im Sucher und in RAW Development | getestet auf einer GR IV 1.11 |
| Update akzeptiert; die Rückkehr zur offiziellen 1.11 stellt die Kamera vollständig wieder her | getestet auf einer GR IV 1.11 |
| Die fünf Monochrom-Looks | getestet auf einer GR IV 1.11 (siehe GR4-MonoUnlock) |
| Beibehaltung des eigenen Namens „High Contrast“ und des Symbols des Platzes | Name und Symbol sind die von RICOH, unverändert; genau diese Kombination wurde noch nicht installiert |
| Regler starten auf 0 (Körnung aus) | besteht aus denselben Änderungen wie der getestete Build (einer Teilmenge davon); für sich allein noch nicht installiert |
| Looks, die zwei oder drei Tonwertkurven brauchen (Farbstiche, getonte Looks) | drei Kurven getestet auf einer GR IV 1.11 |
| Farbtonsektoren | getestet auf einer GR IV 1.11 in RAW Development mit einer LUT zur Filmsimulation (ISO 200, eine Tageslichtszene mit Grün- und Gelbtönen): Die Kamera entsprach der Vorhersage des Werkzeugs, der Unterschied zur LUT sank in farbigen Bereichen um etwa 30 %, und es waren keine Lücken zwischen den Farben zu sehen. Rot-, Blau- und Violetttöne sowie höhere ISO-Werte wurden noch nicht auf der Kamera geprüft |
| Farbe nach den Kurven (`--after-curves`, optional) | 
| Looks auf den Plätzen Cinema (Yellow) / Cinema (Green) | getestet auf einer GR IV 1.11: funktioniert |
| Looks auf den anderen Plätzen (Vivid, Positive Film, Negative Film, Bleach Bypass, Retro, die Monochrom-Plätze) | getestet auf einer GR IV 1.11: funktioniert |
| Ihr eigener Name für den Platz (`--name`) | getestet auf einer GR IV 1.11: funktioniert |
| Ihr eigenes Symbol für den Platz (`--icon`) | getestet auf einer GR IV 1.11: funktioniert |
| Erstellen aus einer geteilten `look.json` | offline geprüft: Die Firmware ist Byte für Byte identisch mit `make` bei gleichem LUT-Ergebnis, Platz, Namen und Symbol; nichts Neues gelangt auf die Kamera |
| Die App (`GR4-LUTSmith`) erstellt dieselbe Firmware wie die Befehlszeile | offline geprüft: Byte für Byte identisch bei gleicher LUT, gleichem Foto und gleicher Auswahl |
| Durchgänge nebeneinander (`--jobs`, in der App „Gleichzeitig“) | offline geprüft: Byte für Byte dieselben Ergebnisse wie dieselben Durchgänge nacheinander |
| Das Werkzeug reproduziert das getestete Beispiel exakt | getestet (`selftest`) |

## Für Entwickler

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

- Die App aus dem Quellcode starten: `uv sync --extra app`, dann `uv run python -m lutsmith_app`.
- Sie erstellen: `uv run python packaging/build.py` (auf einem Mac mit Apple Chip fügen Sie `--arch x86_64` für
  den Intel-Build hinzu); die Zip-Datei landet in `dist/`.

| Datei | SHA-256 |
| --- | --- |
| offizielle `fwdc248b.bin` 1.11 der RICOH GR IV | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| Beispiel-Firmware (`selftest`, aus `examples/film-1d.look.json`) | `d201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052` |
