<p align="center">
  <img src="lutsmith_app/assets/app/icon-128.png" width="112" height="112" alt="Icône de GR4-LUTSmith : une barre d'acier courbée en courbe tonale de film">
</p>

<h1 align="center">GR4-LUTSmith</h1>

<p align="center">
  <strong>Votre propre look couleur, à partir d'une LUT <code>.cube</code>, dans votre RICOH GR IV.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <a href="README.zh-TW.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <strong>Français</strong> |
  <a href="README.es.md">Español</a>
</p>

GR4-LUTSmith prend une LUT d'étalonnage (`.cube`) et crée un firmware GR IV
qui intègre son look comme look du menu **Contrôle de l'image**. Vous pouvez
l'utiliser en photo, en mode vidéo et dans le viseur, ainsi que dans
**RAW Development**. Tout le reste de votre appareil reste exactement comme
avant, et vous pouvez revenir au firmware officiel à tout moment.

Ce dépôt ne contient aucun firmware RICOH. Vous téléchargez vous-même le
firmware officiel chez RICOH, et l'outil fourni le transforme en version avec
votre look, sur votre propre ordinateur.

> [!WARNING]
> **Non officiel, à vos risques et périls.** Ni conçu ni approuvé par RICOH IMAGING.
> L'installation d'un firmware modifié peut annuler votre garantie. Lisez d'abord
> [Avant de commencer](#avant-de-commencer) et [Risques](#risques).

| Vous voulez | Allez à |
| --- | --- |
| Créer votre firmware dans une fenêtre, étape par étape (macOS, Windows ; dans les 21 langues de l'appareil) | [L'app](#lapp) |
| Le créer dans le terminal (macOS, Windows, Linux) | [La ligne de commande](#la-ligne-de-commande) |
| Créer un look que quelqu'un vous a partagé | [Utiliser un look partagé](#utiliser-un-look-partagé) |
| Savoir ce que contient un fichier de firmware | [Vérifier un fichier de firmware](#vérifier-un-fichier-de-firmware) |
| Revenir au firmware de RICOH | [Revenir au firmware officiel](#revenir-au-firmware-officiel) |

L'app et la ligne de commande créent exactement le même firmware à partir de la même LUT et des mêmes choix.

**Sommaire :**
[Comment ça marche](#comment-ça-marche) |
[Ce que vous obtenez](#ce-que-vous-obtenez) |
[Avant de commencer](#avant-de-commencer) |
[L'app](#lapp) |
[La ligne de commande](#la-ligne-de-commande) |
[Installer sur l'appareil](#installer-sur-lappareil) |
[Personnaliser](#personnaliser) |
[Un ajustement plus fidèle](#un-ajustement-plus-fidèle) |
[Bon à savoir](#bon-à-savoir) |
[Risques](#risques) |
[État des tests](#état-des-tests) |
[Pour les développeurs](#pour-les-développeurs)

## Comment ça marche

Le GR IV n'applique pas directement les LUT. Ses looks reposent sur quelques
réglages natifs : un mélange de couleurs, des courbes tonales, des réglages de
contraste et des **secteurs de teinte** (des modifications de couleur
distinctes pour 12 plages de teinte). GR4-LUTSmith **ajuste** votre LUT à ces
réglages, mesure à quel point l'appareil peut s'en approcher, et seulement
ensuite écrit le firmware.

- **Les looks qui agissent sur les tons et la couleur d'ensemble** s'ajustent
  très bien. Cela couvre les courbes de style film, le contraste, les noirs
  délavés, les dominantes chaudes ou froides et les changements de saturation
  globale.
- **Les looks qui déplacent certaines teintes séparément** (teal-orange,
  simulations de film qui modifient les verts ou les ciels, …) sont ajustés avec
  les **secteurs de teinte**. Ils s'en approchent bien plus qu'avec le seul
  mélange de couleurs. Les changements qui dépendent fortement de la saturation
  d'une couleur (par exemple seulement les rouges les plus vifs) restent
  approximatifs, et l'outil vous le signale le cas échéant.
- **Les LUT Log et les LUT de conversion propres à une caméra** (S-Log, V-Log, …)
  ne sont pas prises en charge. Utilisez une LUT « créative » conçue pour des
  images normales (Rec.709 / sRGB).

L'ajustement est évalué avec **CIEDE2000**, la mesure standard de l'écart
perçu entre deux couleurs. À titre indicatif, **en dessous de 1, l'écart est
difficile à voir côte à côte**, et vers 2, c'est une petite différence visible.

| Résultat | Signification |
| --- | --- |
| **bon** | différence moyenne inférieure à 1, et 95 % des couleurs en dessous de 2 : aspect identique |
| **approximatif** | moyenne inférieure à 2 : proche, avec des différences visibles sur certaines couleurs |
| **médiocre** | l'appareil ne peut pas reproduire toute la gamme de couleurs de la LUT ; le firmware est quand même écrit si les **couleurs courantes** correspondent (voir [Quand une LUT est jugée médiocre](#quand-une-lut-est-jugée-médiocre)) |

Chaque LUT est mesurée de trois façons : sur toute sa gamme de couleurs, sur
les 24 couleurs courantes d'une charte **ColorChecker** (peau, ciel, feuillage, …)
et sur des **gris neutres** (où une dominante de couleur se voit le plus). Avec
une photo à vous (`--photo`), également sur cette photo.

## Ce que vous obtenez

Après l'installation, la liste Contrôle de l'image se termine comme ci-dessous.
En dehors de Contrôle de l'image, Standard, Saturation et Teinte, les noms de menu
sont donnés tels qu'ils s'affichent sur un appareil réglé en anglais.

| Affiché comme | Look | Photo | Vidéo |
| --- | --- | :---: | :---: |
| HDR Tone | (votre look couleur existant) | ✓ | |
| Standard | Monochrome Standard | ✓ | ✓ |
| Solid | Monochrome Solid | ✓ | ✓ |
| Soft | Monochrome Soft | ✓ | |
| **High Contrast** | **le look de votre LUT, en couleur** | ✓ | ✓ |
| Grainy | Monochrome Grainy | ✓ | |
| HDR Tone | Monochrome HDR *(expérimental)* | ✓ | |

- Votre look utilise le nom et l'icône de **High Contrast** (la quatrième entrée
  après le premier « HDR Tone »). Vous pouvez choisir à la place **Cinema (Yellow)**,
  **Vivid** ou un autre emplacement, ou en utiliser plusieurs : voir
  [Choisir l'emplacement](#choisir-lemplacement).
  Il peut aussi afficher [votre propre nom](#nommer-lemplacement) et
  [votre propre icône](#votre-propre-icône).
- Il démarre avec **tous les curseurs à 0**, la netteté à sa valeur standard et
  le **grain désactivé**. Le look de votre LUT est intégré pour ces réglages ;
  les curseurs fonctionnent ensuite comme d'habitude, à partir de votre look.
- Les cinq looks monochromes du GR IV Monochrome sont aussi disponibles, comme
  dans GR4-MonoUnlock.
- Tous vos looks existants restent inchangés.

## Avant de commencer

- **Appareil :** RICOH GR IV (le modèle couleur standard). Les autres modèles ne
  sont pas pris en charge.
- **Votre appareil doit déjà être en firmware 1.11.** Vérifiez la version dans
  le menu de configuration de l'appareil.
  - Version plus ancienne : mettez d'abord à jour vers la 1.11 de la manière habituelle, avec le fichier officiel de RICOH.
  - Version plus récente : **n'utilisez pas cet outil.** Il ne prend en charge que la 1.11.
- **Le fichier de firmware officiel.** Sur la page d'assistance officielle du
  GR IV de RICOH IMAGING, téléchargez la **version de firmware 1.11**.
  Décompressez-la si nécessaire jusqu'à obtenir le fichier **`fwdc248b.bin`**.
- **Une batterie complètement chargée.** Une mise à jour du firmware ne doit
  jamais être privée d'alimentation.
- **Une carte SD** que vous pouvez formater.
- **Votre LUT** au format `.cube` (3D ou 1D), en sachant si elle a été conçue
  pour **sRGB** (la plupart des LUT) ou pour **Adobe RGB**.
- **Recommandé :** une photo DNG prise avec votre GR IV. L'outil s'en sert pour
  vérifier le look sur un contenu réel et pour créer un aperçu.
- Notez les réglages personnalisés (C1, C2, …) que vous ne voudriez pas refaire.

Créez ensuite votre firmware avec [l'app](#lapp) ou
[la ligne de commande](#la-ligne-de-commande).

## L'app

### Télécharger

Depuis la [dernière version](../../releases/latest), téléchargez le fichier correspondant à votre ordinateur :

| Ordinateur | Fichier |
| --- | --- |
| Mac avec puce Apple silicon (M1 ou ultérieure) | `GR4-LUTSmith-<version>-macOS-AppleSilicon.zip` |
| Mac avec processeur Intel | `GR4-LUTSmith-<version>-macOS-Intel.zip` |
| Windows 10 ou 11 (64 bits) | `GR4-LUTSmith-<version>-Windows-x64.zip` |

macOS 12 (Monterey) ou ultérieur est nécessaire. Vous ne savez pas quel Mac vous avez ? Menu Pomme → **À propos de ce Mac** :
« Puce Apple M… » signifie Apple silicon, « Processeur Intel » signifie Intel.

Chaque zip contient l'app et un dossier `Licences` (les licences des composants qui la constituent).

<details>
<summary><strong>Vérifier que le fichier vient bien de ce projet</strong> (facultatif)</summary>

<br>

Chaque zip est produit par le propre build de ce dépôt sur GitHub, qui signe un relevé de sa provenance : le
dépôt, le build et la version exacte du code. Avec la [GitHub CLI](https://cli.github.com) (connectée avec
`gh auth login`), vous pouvez vérifier que votre téléchargement est bien ce fichier et qu'il n'a été ni modifié
ni remplacé :

```sh
gh attestation verify GR4-LUTSmith-2.1.0-macOS-AppleSilicon.zip --repo lemonadesaltbagel/GR4-LUTSmith
```

(utilisez le nom du zip que vous avez téléchargé ; sous Windows, lancez la commande dans PowerShell depuis votre
dossier Téléchargements). Elle se termine par « Verification succeeded! » et indique le build qui a produit le
fichier. Tout autre résultat signifie : ne l'ouvrez pas, et téléchargez-le à nouveau depuis la page de la version.
La page **Attestations** du dépôt liste tous les fichiers signés.

Pour vérifier plus rapidement que le téléchargement est complet : la version indique le SHA-256 de chaque
fichier dans `SHA256SUMS`.

- macOS (Terminal) : `shasum -a 256 ~/Downloads/GR4-LUTSmith-*.zip`
- Windows (PowerShell) : `Get-FileHash $HOME\Downloads\GR4-LUTSmith-*.zip -Algorithm SHA256`

Cela montre seulement que le fichier est arrivé intact, pas qui l'a créé : `SHA256SUMS` se trouve sur la même
page que les zips.

Vous pouvez aussi vous passer entièrement du téléchargement : lancez l'app depuis le code source (voir
[Pour les développeurs](#pour-les-développeurs)), ou créez le firmware avec la
[ligne de commande](#la-ligne-de-commande). L'app et la ligne de commande créent exactement le même `fwdc248b.bin`,
et `uv run gr4_lutsmith.py check fwdc248b.bin` montre ce que contient n'importe quel fichier de firmware.

</details>

### Premier lancement

L'app est gratuite et n'est pas signée avec un certificat payant d'Apple ou de Microsoft : votre ordinateur vous
demande donc une fois si vous lui faites confiance.

**macOS**

1. Décompressez le fichier et déplacez **GR4-LUTSmith** dans votre dossier Applications.
2. Ouvrez-la. macOS indique qu'il ne peut pas vérifier l'absence de logiciel malveillant dans l'app ; choisissez **Terminé** (macOS 15) ou **Annuler**.
3. Ouvrez **Réglages Système → Confidentialité et sécurité**, faites défiler jusqu'au message concernant
   GR4-LUTSmith, choisissez **Ouvrir quand même**, puis confirmez avec votre mot de passe.
   Sous macOS 12 à 14, vous pouvez aussi cliquer sur l'app en maintenant la touche Contrôle enfoncée, choisir
   **Ouvrir**, puis à nouveau **Ouvrir**.

Par la suite, elle s'ouvre normalement.

**Windows**

1. Cliquez avec le bouton droit sur le zip → **Extraire tout…**, puis ouvrez le dossier **GR4-LUTSmith** extrait
   (ne la lancez pas depuis l'intérieur du zip).
2. Ouvrez **GR4-LUTSmith.exe**. Si Windows affiche « Windows a protégé votre ordinateur », choisissez
   **Informations complémentaires → Exécuter quand même**.

Gardez le dossier entier tel quel : l'app a besoin du dossier `_internal` placé à côté d'elle.

### Utilisation

L'app vous guide à l'écran à travers les étapes : le fichier de firmware de votre appareil, la LUT (et
éventuellement un DNG), l'emplacement avec son nom et son icône, l'ajustement et la création. Elle enregistre
`fwdc248b.bin` à l'endroit que vous choisissez ; ensuite,
[installez-le sur l'appareil](#installer-sur-lappareil).

- **Langue :** l'app suit la langue de votre ordinateur ; vous pouvez la changer en haut de la fenêtre. C'est
  aussi la langue de l'appareil pour laquelle les noms d'emplacement sont vérifiés (voir
  [Nommer l'emplacement](#nommer-lemplacement)).
- **Apparence :** Système, Jour ou Nuit, en haut de la fenêtre.
- **Vérifier un fichier de firmware** (à gauche) vous indique si un `fwdc248b.bin` est le fichier officiel de
  RICOH, s'il a été créé par GR4-LUTSmith (et avec quels looks), ou s'il s'agit d'autre chose.
- Les looks partagés (`.json`) fonctionnent aussi dans l'app : choisissez « Un look partagé » sur la première page.
- **Plusieurs passes à la fois :** sur la page Ajustement, choisissez combien de passes lancer et combien
  tournent en parallèle (un cœur de processeur chacune ; voir [Plus de passes](#plus-de-passes)). Chaque passe
  indique où elle en est ; vous pouvez ajouter des passes pendant qu'elles tournent, et « Tout arrêter » conserve
  les passes déjà terminées. Les résultats s'ajoutent au tableau à mesure que les passes se terminent.

### En cas de problème

- **macOS indique que l'app est endommagée** : téléchargez-la à nouveau (le fichier était incomplet), puis
  vérifiez-la comme indiqué dans [Vérifier que le fichier vient bien de ce projet](#télécharger).
- **L'app ne démarre pas sous Windows** : assurez-vous d'avoir extrait tout le zip, et lancez `GR4-LUTSmith.exe`
  depuis le dossier extrait.
- **Le fichier de firmware est refusé** : l'app n'accepte que le `fwdc248b.bin` 1.11 du GR IV de RICOH, non
  modifié. Un fichier déjà modifié par GR4-LUTSmith ne peut pas être modifié à nouveau ; repartez du fichier non
  modifié.

## La ligne de commande

### 1. Installation

Installez **[uv](https://docs.astral.sh/uv/)** (il installe Python et tout ce
dont l'outil a besoin), ouvrez un terminal dans ce dossier et lancez :

```sh
uv sync --extra photo
```

<details>
<summary>Sans uv</summary>

<br>

Avec Python 3.9 ou plus récent :

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` et `pillow` ne sont nécessaires que pour `--photo` et `preview`.

</details>

### 2. Créer votre firmware

Utilisez vos propres chemins :

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

| Option | Effet |
| --- | --- |
| `--space adobe` | la LUT a été conçue pour Adobe RGB |
| `--photo R0001234.DNG` | vérifie aussi le look sur votre photo (facultatif, mais recommandé) |
| `--slot vivid`, `--slot cinema-yellow`, … | met votre look à la place d'un autre look plutôt que de High Contrast : [Choisir l'emplacement](#choisir-lemplacement) |
| `--name "My Look"` | affiche l'emplacement sous votre propre nom : [Nommer l'emplacement](#nommer-lemplacement) |
| `--icon my_icon.png` | donne à l'emplacement votre propre icône de menu : [Votre propre icône](#votre-propre-icône) |
| `--turns 3` | lance trois ajustements et garde les meilleurs : [Plus de passes](#plus-de-passes) |
| `--jobs 3` | exécute jusqu'à trois de ces passes côte à côte : [Plus de passes](#plus-de-passes) |
| `--after-curves` | essaie aussi un second mélange de couleurs : [Couleur après les courbes](#couleur-après-les-courbes) |

L'outil :

1. vérifie que vous lui avez donné le véritable fichier officiel 1.11 ;
2. ajuste la LUT (cela prend quelques minutes, plus une ou deux minutes pour les
   secteurs de teinte) et indique la qualité de l'ajustement ;
3. crée le firmware et le vérifie.

Une exécution réussie se termine ainsi :

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
Copy this file to the root of the SD card and run the camera's firmware update.
Then choose High Contrast in Image Control: your look is there.
```

Dès le début, l'outil indique aussi dans quel emplacement va votre look, par exemple
`slot: High Contrast (replaces the hidden monochrome High Contrast look)`.

Le dossier de sortie `output/my_look/` contient aussi `look.json` (le look
ajusté) et peut accueillir un aperçu (étape 3). Vous pouvez partager `look.json`
avec d'autres propriétaires de GR IV : ils créent le même look sans refaire
l'ajustement (voir [Utiliser un look partagé](#utiliser-un-look-partagé)).

Si la LUT ne peut pas être bien reproduite, ou si le fichier de firmware n'est
pas le 1.11 officiel, l'outil affiche `refused: …` et n'écrit **aucun firmware**.

### 3. Aperçu (facultatif)

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

Cette commande crée `output/my_look/preview.jpg` avec trois volets : l'appareil
sans le look, la LUT elle-même, et l'appareil **avec** le look. Le volet de la
LUT a besoin du fichier `.cube` : l'outil le trouve à côté de `look.json` ou
dans le dossier courant, sinon indiquez-le avec `--lut my_look.cube` ; sans
lui, l'aperçu montre les deux autres volets. Ce sont la couleur et les tons
qu'il faut comparer. L'accentuation et le bruit ne sont pas simulés.

Ensuite, [installez-le sur l'appareil](#installer-sur-lappareil).

## Installer sur l'appareil

La marche à suivre est la même pour un firmware créé avec l'app ou avec la ligne de commande.

### 1. Copier sur la carte SD

1. **Formatez la carte SD dans l'appareil.**
2. Copiez **`fwdc248b.bin`** (avec la ligne de commande : `output/my_look/fwdc248b.bin`)
   à la **racine** de la carte : pas dans un dossier, et gardez exactement le nom
   `fwdc248b.bin`.

### 2. Mettre à jour l'appareil

1. Insérez la batterie complètement chargée et la carte SD.
2. Lancez la mise à jour du firmware depuis le menu de configuration de
   l'appareil, comme décrit dans les instructions officielles de RICOH pour la
   mise à jour du firmware du GR IV.
3. **L'appareil affiche une mise à jour de la version 1.11 vers la version 1.11.**
   C'est normal : le firmware modifié conserve le numéro de version. Confirmez la
   mise à jour.

> [!CAUTION]
> **N'éteignez pas l'appareil, n'ouvrez pas la trappe de la batterie ou de la
> carte et ne retirez pas la carte** avant que la mise à jour soit terminée et
> que l'appareil ait redémarré.

### 3. Photographier

- Ouvrez **Contrôle de l'image** et choisissez **High Contrast** (après le premier
  « HDR Tone »). Il est désormais en couleur. Si vous avez choisi un autre
  emplacement, choisissez plutôt cette entrée.
- La version du firmware affiche toujours **1.11**. C'est normal.
- Supprimez `fwdc248b.bin` de la carte (ou formatez la carte) pour que la mise à
  jour ne soit pas relancée par erreur.

Pour passer plus tard à une autre LUT, créez un nouveau firmware à partir du
fichier **officiel** et installez-le de la même façon.

### Revenir au firmware officiel

Répétez les étapes 1–2, cette fois avec le `fwdc248b.bin` **officiel** de RICOH.
L'appareil affiche à nouveau **1.11 → 1.11** ; confirmez, et votre appareil
retrouve son état d'origine.

## Personnaliser

L'emplacement de votre look, son nom et son apparence dans le menu. Dans l'app,
ces choix se font à l'étape Emplacement, nom, icône ; en ligne de commande, ce
sont des options de `make` et `build`.

### Choisir l'emplacement

Votre look remplace l'un des looks de l'appareil. Vous choisissez lequel avec
`--slot` (`make` et `build`) ; `uv run gr4_lutsmith.py slots` affiche la même liste
dans le terminal :

| `--slot` | Affiché comme | Remplace | Photo | Vidéo | Curseurs supplémentaires |
| --- | --- | --- | :---: | :---: | --- |
| `high-contrast` (par défaut) | High Contrast | le look monochrome masqué High Contrast | ✓ | ✓ | — |
| `cinema-yellow` | Cinema (Yellow) | le look Cinema (Yellow) de RICOH | ✓ | ✓ | Saturation, Teinte |
| `cinema-green` | Cinema (Green) | le look Cinema (Green) de RICOH | ✓ | ✓ | Saturation, Teinte |
| `vivid` | Vivid | le look Vivid de RICOH | ✓ | ✓ | Saturation, Teinte |
| `positive-film` | Positive Film | le look Positive Film de RICOH | ✓ | ✓ | Saturation, Teinte |
| `negative-film` | Negative Film | le look Negative Film de RICOH | ✓ | ✓ | Saturation, Teinte |
| `bleach-bypass` | Bleach Bypass | le look Bleach Bypass de RICOH | ✓ | ✓ | Saturation, Teinte |
| `retro` | Retro | le look Retro de RICOH | ✓ | ✓ | Saturation, Teinte |
| `soft-monotone` | Soft Monotone | le look Soft Monotone de RICOH | ✓ | | — |
| `hard-monotone` | Hard Monotone | le look Hard Monotone de RICOH | ✓ | ✓ | — |
| `hi-contrast-bw` | Hi-Contrast B&W | le look Hi-Contrast B&W de RICOH | ✓ | ✓ | — |
| `mono-standard` | Standard (le second) | le look monochrome masqué Standard | ✓ | ✓ | — |
| `mono-soft` | Soft | le look monochrome masqué Soft | ✓ | | — |
| `mono-solid` | Solid | le look monochrome masqué Solid | ✓ | ✓ | — |

- Les couleurs sont les mêmes dans tous les emplacements : l'appareil y traite
  votre look de la même façon, donc l'ajustement et ses scores ne dépendent pas
  de l'emplacement.
- Votre look démarre avec tous les curseurs à 0 et le grain désactivé, dans
  chaque emplacement.
- Selon l'emplacement, seuls changent l'entrée que vous perdez et les curseurs
  dont vous disposez. Sur un emplacement monochrome, votre look est en couleur ;
  Saturation et Teinte n'y sont pas proposés.
- **Cinema :** son réglage Color Tone n'a aucun effet sur votre look.
  **Bleach Bypass :** son réglage de ton ne modifie pas votre look.
  **Retro :** le virage propre à Retro et son effet de ton proche d'un vignettage
  sont supprimés : vous obtenez uniquement votre look.
- Un emplacement que vous n'utilisez pas garde le look de RICOH. Sans look sur
  High Contrast, celui-ci reste le look monochrome High Contrast.
- **Non disponibles :** Standard, Monotone, HDR Tone, Cross Processing ainsi que
  les looks masqués Grainy et HDR. Ils partagent une partie de leur traitement
  avec d'autres looks ou utilisent un traitement spécial qui modifierait vos
  couleurs.
- `check` indique quels emplacements contiennent un look personnel.

### Plusieurs looks dans un firmware

Ajustez chaque LUT avec `fit`, puis créez-les ensemble, chaque fichier de look
suivi de son propre `--slot` (et de `--name`, `--icon` si vous le souhaitez) :

```sh
uv run gr4_lutsmith.py fit look_a.cube --photo R0001234.DNG -o output/a
uv run gr4_lutsmith.py fit look_b.cube --photo R0001234.DNG -o output/b
uv run gr4_lutsmith.py build output/a/look.json --slot cinema-yellow output/b/look.json --slot vivid --name "Look B" ~/Downloads/fwdc248b.bin -o output/both
```

**Combien à la fois :** High Contrast et les deux emplacements Cinema accueillent
toujours un look complet. Les autres emplacements se partagent un espace limité :
chaque look a besoin de place pour ses courbes tonales, et de beaucoup plus pour
les secteurs de teinte et la couleur après les courbes. Un look simple (une seule
courbe tonale) peut occuper jusqu'à 10 de ces emplacements à la fois ; les looks
avec secteurs de teinte, beaucoup moins. S'ils ne tiennent pas, l'outil le signale
et n'écrit rien ; utilisez moins d'emplacements ou des looks plus simples, et
laissez High Contrast inutilisé pour avoir le plus de place.

### Nommer l'emplacement

`--name` (`make` et `build`) donne votre propre nom à l'emplacement, dans le menu
Contrôle de l'image et ses écrans, dans toutes les langues de l'appareil :

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra"
```

- Chaque emplacement accepte des noms jusqu'à une certaine longueur :
  `uv run gr4_lutsmith.py slots` l'indique (de 9 caractères pour Retro à 23 pour
  Cinema (Yellow)). Le second Standard monochrome ne peut pas être renommé, car il
  partage son nom avec le look Standard couleur.
- **L'ASCII simple** (lettres de l'alphabet anglais, chiffres, espaces et
  ponctuation) s'affiche dans toutes les langues de l'appareil. C'est le choix sûr.
- **Les autres lettres et caractères** fonctionnent dans les langues de l'appareil
  qui les utilisent : un nom japonais s'affiche quand l'appareil est réglé en
  japonais, `Müller` dans les langues européennes, `Плёнка` en russe, et ainsi de
  suite. Les caractères qu'aucune langue de l'appareil n'utilise (emoji, arabe,
  hébreu, …) sont refusés.
- L'outil vérifie le nom pour votre **langue de l'appareil**, qui est la langue de
  votre ordinateur, sauf si vous indiquez `--camera-language` (par exemple
  `--camera-language Japanese` ; `--help` liste les 21). Si le nom contient des
  caractères que cette langue n'utilise pas, l'outil prévient qu'ils risquent de
  ne pas s'afficher et demande s'il faut quand même utiliser ce nom. Répondez `y`
  pour continuer, ou ajoutez `--accept-name` pour accepter d'avance (nécessaire
  quand l'outil ne peut pas poser la question, par exemple dans un script). Si
  vous passez ensuite l'appareil dans une autre langue, un nom hors ASCII risque
  de ne pas s'y afficher.
- Les noms longs peuvent être tronqués sur certains écrans (les caractères
  chinois, japonais et coréens occupent environ deux fois la largeur des lettres
  de l'alphabet anglais).
- Sans `--name`, l'emplacement garde son propre nom. Le nom n'est pas enregistré
  dans `look.json` (ce fichier ne contient que le look) : indiquez à nouveau
  `--name` lors du `build`. `check` affiche le nom dans un firmware créé.

### Votre propre icône

`--icon` (`make` et `build`) remplace l'icône de l'emplacement dans le menu
Contrôle de l'image par votre propre image :

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- N'importe quelle image convient (PNG, JPEG, …). L'icône du menu fait 40×40
  pixels : une image plus grande ou plus petite est redimensionnée et, si elle
  n'est pas carrée, c'est son **centre** qui est utilisé. Les parties
  transparentes restent transparentes : un PNG à fond transparent ressemble donc
  aux icônes d'origine de l'appareil.
- `make` enregistre le résultat sous `icon.png` à côté du firmware, pour que vous
  voyiez exactement ce que l'appareil affichera. À cette taille, des formes
  simples et marquées sont les plus lisibles.
- Chaque emplacement, sauf le second Standard monochrome, accepte une icône
  personnalisée (celui-ci partage son icône avec le look Standard couleur).
  `slots` les liste.
- Il faut Pillow (`uv sync --extra photo`). Sans `--icon`, l'emplacement garde
  sa propre icône. L'icône n'est pas enregistrée dans `look.json` : indiquez à
  nouveau `--icon` lors du `build`. `check` indique quels emplacements ont leur
  propre icône.

### Utiliser un look partagé

`look.json` ne contient que le look lui-même : ses réglages de couleur et la
qualité de leur ajustement à la LUT. Rien sur l'emplacement, le nom ou l'icône,
et aucun dossier de votre ordinateur (seulement le nom de fichier de la LUT).
Toute personne qui possède ce fichier peut créer le firmware directement, sans
la LUT et sans ajustement, et obtient exactement le même firmware, octet pour
octet, que son créateur pour le même emplacement, le même nom et la même icône.

Dans l'app, choisissez « Un look partagé » sur la première page. En ligne de
commande, le fichier peut porter n'importe quel nom : renommez-le comme vous le
souhaitez avant de le partager (`portra-400.json`, …) :

```sh
uv run gr4_lutsmith.py build portra-400.json ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- L'outil indique d'abord la qualité de l'ajustement du look à sa LUT (les
  résultats qu'a vus son créateur ; « on your photo » désigne la photo du
  créateur).
- L'emplacement, le nom et l'icône sont à votre choix, comme dans
  [Choisir l'emplacement](#choisir-lemplacement), [Nommer l'emplacement](#nommer-lemplacement)
  et [Votre propre icône](#votre-propre-icône). Sans `--slot`, le look va sur
  High Contrast.
- Plusieurs looks : indiquez juste après chaque fichier ses propres `--slot`,
  `--name` et `--icon` :

  ```sh
  uv run gr4_lutsmith.py build portra-400.json --slot vivid --name "Portra" tri-x.json --slot hard-monotone ~/Downloads/fwdc248b.bin -o output/both
  ```

- Le contenu du fichier est vérifié avant toute création : un fichier
  endommagé, ou contenant des valeurs que l'appareil ne peut pas accepter, est
  refusé et rien n'est écrit.
- Les fichiers créés par les versions antérieures à 1.7.0 peuvent aussi contenir
  un emplacement, un nom, une icône et le chemin complet de la LUT. `build`
  ignore l'emplacement, le nom et l'icône (en indiquant lesquels c'étaient) ;
  ouvrez un tel fichier dans un éditeur de texte et vérifiez `"file"` avant de
  le partager.

## Un ajustement plus fidèle

Les secteurs de teinte sont essayés à chaque ajustement. Pour vous approcher
davantage, lancez d'abord plus de passes, puis essayez la couleur après les
courbes (voir [Ce qui aide le plus](#ce-qui-aide-le-plus)).

### Secteurs de teinte

Après avoir ajusté le mélange de couleurs et les courbes tonales, l'outil essaie
d'améliorer le look avec les **secteurs de teinte** : l'appareil peut modifier
les couleurs séparément dans 12 plages de teinte. Ils ne sont conservés **que
s'ils aident nettement** (la gamme de couleurs entière ou le ColorChecker
s'améliore d'au moins 10 %) **et que rien ne se dégrade** (votre photo, les gris,
le ColorChecker). La ligne de résultat indique `hue sectors: yes` ou `no`.

- Les secteurs de teinte ne modifient jamais les gris, et les secteurs voisins se
  rejoignent toujours sans discontinuité : les couleurs restent fluides d'une
  teinte à l'autre.
- Avec `--photo`, les secteurs de teinte sont aussi réglés pour du contenu réel
  (recommandé).
- `--no-hue` les désactive (`make` et `fit`).

### Plus de passes

L'ajustement part d'un point de départ et s'améliore à partir de là. L'appareil
n'a que peu de réglages de couleur, donc **le point de départ décide souvent de
la précision atteinte**. Avec `--turns` (dans l'app : sur la page Ajustement),
l'outil lance plusieurs ajustements (des « passes »), chacun à partir d'un
nouveau point de départ aléatoire, et retient les bons :

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG --turns 3
```

- La passe 1 utilise toujours le point de départ habituel : une seule passe (par
  défaut) donne donc le même résultat qu'avant. Chaque passe supplémentaire tire
  un nouveau départ aléatoire.
- Chaque passe dure autant qu'un ajustement normal (quelques minutes).
- **Côte à côte.** `--jobs 3` exécute jusqu'à trois passes à la fois, chacune sur
  un cœur de processeur et avec environ 0,8 Go de mémoire. Laissez au moins un
  cœur libre pour le reste de l'ordinateur. Les résultats sont exactement les
  mêmes que si les passes s'exécutaient l'une après l'autre ; ils sont seulement
  prêts plus tôt.
- **Résultats retenus.** Un nouveau résultat est retenu, sauf si un résultat
  précédent est au moins aussi bon sur chaque mesure (la gamme entière, le
  ColorChecker, les gris et votre photo). Un résultat précédent que le nouveau
  bat sur chaque mesure quitte la liste. Chaque résultat retenu est donc meilleur
  que tous les autres sur au moins une mesure ; l'outil les affiche côte à côte
  et recommande celui qui a le meilleur score global (la différence moyenne sur
  tout ce que l'ajustement utilise).
- **Ajouter des passes à la fin.** Quand les résultats s'affichent, l'outil
  demande `More turns?`. Tapez un nombre pour en lancer autant de plus, de la
  même façon que la série a commencé (`2`) ; ajoutez `a` pour des passes avec
  [couleur après les courbes](#couleur-après-les-courbes) (`2a`), ou `b` pour des
  passes sans (`2b`), quelle que soit la façon dont la série a commencé. Les
  nouvelles passes sont comparées à tous les résultats retenus. Appuyez sur
  Entrée pour garder ce que vous avez.
- **Refaire une passe.** La graine de chaque passe est affichée et enregistrée
  dans `turns.json` ; `--seed 1234` relance la même passe (avec `--turns 3` :
  graines 1234, 1235, 1236).

Avec plus d'un résultat retenu, le dossier de sortie se présente ainsi :

```
output/my_look/look.json, fwdc248b.bin      the recommended result
output/my_look/turns/turn-1/                 every kept result, each with its
output/my_look/turns/turn-3-after-curves/    own look.json (and, with make, fwdc248b.bin)
output/my_look/turns.json                    every turn, its seed and its scores
```

Pour utiliser un autre résultat retenu, copiez plutôt son `fwdc248b.bin` sur la carte SD.

### Couleur après les courbes

Avec `--after-curves` (`make` et `fit`), l'outil essaie aussi un second mélange
de couleurs que l'appareil applique **après** les courbes tonales. Beaucoup de
looks film modifient les couleurs différemment dans les ombres et dans les hautes
lumières. Le mélange de couleurs habituel agit avant les courbes et ne peut donc
pas suivre ces différences, alors qu'un mélange après les courbes le peut souvent.

La gamme de couleurs entière de la LUT et les vraies photos ne concordent pas
toujours : une version peut être bien plus proche sur les couleurs saturées et un
peu plus éloignée sur une photo du quotidien. Les deux versions entrent donc dans
la liste des résultats retenus décrite dans [Plus de passes](#plus-de-passes) :
la version avec couleur après les courbes est retenue dès qu'elle est meilleure
sur un point (la gamme entière, le ColorChecker, les gris ou votre photo), à côté
de la version habituelle, et c'est vous qui choisissez. Comparez les deux en
aperçu sur votre propre photo avant de choisir.

**Pourquoi c'est facultatif.** Plus de passes de l'ajustement habituel sont le
levier le plus important (voir [Ce qui aide le plus](#ce-qui-aide-le-plus)). Le
mélange après les courbes aide en moyenne, mais il allonge chaque passe de
plusieurs minutes.

- Les gris restent gris : le mélange n'ajoute jamais de dominante de couleur à un
  gris neutre.
- L'ajustement prend plusieurs minutes de plus (quatre ajustements supplémentaires).

<details>
<summary>Résultats sur 24 LUT</summary>

<br>

Dans nos tests sur 24 LUT (une passe chacune), la version habituelle est restée
exactement la même qu'avant, et 23 LUT ont obtenu une seconde version :

- **8 meilleures sur tout ce qui a changé** : la différence moyenne avec la LUT y
  est passée de 3,7 à 2,4 (ColorChecker 1,9 → 1,1, photo 0,91 → 0,75) ;
- **15 avec un compromis**. Les looks film couleur se rapprochent généralement
  beaucoup sur la gamme entière et le ColorChecker (par exemple 3,6 → 2,5), avec
  une photo légèrement moins bonne (de 0,17 au plus) ; les looks monochromes se
  rapprochent généralement beaucoup sur les gris et la photo, mais s'éloignent
  sur la gamme entière ;
- deux LUT refusées auparavant peuvent désormais être créées.

</details>

### Ce qui aide le plus

Dans un test à temps d'ajustement égal, la meilleure de quatre passes de
l'ajustement habituel, poursuivie, a battu un ajustement avec
[couleur après les courbes](#couleur-après-les-courbes) à chaque étape. Sur dix
passes aléatoires de chaque, la version avec couleur après les courbes était
meilleure en moyenne. Les deux aident donc, mais **plus de passes de
l'ajustement habituel apportent le gain le plus important** : si vous avez le
temps, lancez d'abord plus de passes, et ajoutez `--after-curves` si vous voulez
aussi comparer cette version.

### Quand une LUT est jugée médiocre

Beaucoup de LUT de simulation de film remodèlent les couleurs très saturées
d'une manière que les réglages de l'appareil ne peuvent pas suivre : elles sont
donc « médiocres » sur toute leur gamme de couleurs, même si les images du
quotidien semblent justes. Le firmware est quand même écrit si :

- les couleurs du **ColorChecker** diffèrent de moins de 2 en moyenne, les
  **gris** de moins de 2, et aucun gris ne prend de dominante de couleur
  visible ; et, avec `--photo`, le look n'est pas médiocre sur votre photo ; ou
- avec `--photo`, le look est **bon sur votre photo** (et y réduit la
  différence au moins de moitié), avec les mêmes limites pour les gris et les
  dominantes de couleur.

L'outil indique quelle règle s'est appliquée. Sinon, il n'écrit aucun firmware ;
ajoutez `--force` pour le créer quand même, et vérifiez d'abord l'aperçu.

## Bon à savoir

- **Les curseurs** (Key, Contrast, Highlight, Shadow, Sharpness, Shading,
  Clarity, Toning, Grain) agissent en plus de votre look ; à 0, vous obtenez la
  LUT. Saturation et Teinte ne sont pas proposés sur High Contrast ; sur les
  emplacements Cinema, ils le sont (voir [Choisir l'emplacement](#choisir-lemplacement)).
- **Deux entrées « Standard » et deux entrées « HDR Tone ».** Les looks
  monochromes Standard et HDR utilisent les mêmes noms et icônes que les looks
  couleur.
- **Une mise à jour officielle de RICOH supprime votre look.** Elle remplace
  l'intégralité du firmware.
- **Uniquement pour le GR IV standard.** N'installez jamais ce fichier sur un
  autre modèle.
- **Avant d'envoyer l'appareil en réparation,** revenez au firmware officiel.
- **Essayez d'abord de nombreuses LUT :** `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG`
  ajuste la LUT et affiche le résultat sans avoir besoin du fichier de firmware.

### Vérifier un fichier de firmware

Avant de copier un fichier de firmware sur une carte (dans l'app : **Vérifier un fichier de firmware**, à gauche) :

```sh
uv run gr4_lutsmith.py check path/to/fwdc248b.bin
```

Cette commande vous indique si le fichier est le 1.11 officiel, un firmware
GR4-LUTSmith ou autre chose. Pour un firmware GR4-LUTSmith, elle indique aussi
quels emplacements contiennent un look, leurs noms et icônes, et si les looks
utilisent des secteurs de teinte et le mélange de couleurs après les courbes.

Pour vérifier l'outil lui-même avec votre fichier officiel :

```sh
uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
```

Cette commande crée l'exemple fourni (`examples/film-1d.cube`) et compare le
résultat avec la version testée. Elle affiche `selftest: PASSED`.

## Risques

- Votre appareil ne sait pas distinguer un bon fichier de firmware d'un fichier
  endommagé. Ne copiez sur votre carte qu'un fichier écrit par l'outil (ou
  confirmé avec `check`).
- Si une mise à jour est interrompue, ou si un fichier de firmware ne peut pas
  démarrer, l'appareil risque de ne plus pouvoir accéder à la fonction de mise à
  jour, et devrait alors passer par le service après-vente de RICOH. Cela ne
  s'est pas produit lors des tests, mais on ne peut pas l'exclure.
- Les données d'étalonnage propres à votre appareil ne sont pas modifiées.

## État des tests

| Élément | État |
| --- | --- |
| Un look LUT personnel avec sa propre courbe tonale, dans cet emplacement, en photo, en vidéo, dans le viseur et dans RAW Development | testé sur un GR IV 1.11 |
| Mise à jour acceptée ; revenir au 1.11 officiel restaure entièrement l'appareil | testé sur un GR IV 1.11 |
| Les cinq looks monochromes | testé sur un GR IV 1.11 (voir GR4-MonoUnlock) |
| Conserver le nom « High Contrast » et l'icône d'origine de l'emplacement | le nom et l'icône sont ceux de RICOH, inchangés ; cette combinaison exacte n'a pas encore été installée |
| Curseurs à 0 à l'ouverture (grain désactivé) | composé des mêmes modifications que la version testée (une partie d'entre elles) ; pas encore installé seul |
| Looks qui nécessitent deux ou trois courbes tonales (dominantes de couleur, looks virés) | trois courbes testées sur un GR IV 1.11 |
| Secteurs de teinte | testé sur un GR IV 1.11 dans RAW Development avec une LUT de simulation de film (ISO 200, scène en lumière du jour avec des verts et des jaunes) : l'appareil correspondait à la prédiction de l'outil, la différence avec la LUT a baissé d'environ 30 % sur les zones colorées, et aucune discontinuité entre les couleurs n'était visible. Les rouges, les bleus, les violets et les ISO plus élevées n'ont pas encore été vérifiés sur l'appareil |
| Couleur après les courbes (`--after-curves`, facultatif) | 
| Looks sur les emplacements Cinema (Yellow) / Cinema (Green) | testé sur un GR IV 1.11 : fonctionne |
| Looks sur les autres emplacements (Vivid, Positive Film, Negative Film, Bleach Bypass, Retro, les emplacements monochromes) | testé sur un GR IV 1.11 : fonctionne |
| Votre propre nom pour l'emplacement (`--name`) | testé sur un GR IV 1.11 : fonctionne |
| Votre propre icône pour l'emplacement (`--icon`) | testé sur un GR IV 1.11 : fonctionne |
| Création à partir d'un `look.json` partagé | vérifié hors ligne : le firmware est identique octet pour octet à celui de `make` avec le même résultat de LUT, le même emplacement, le même nom et la même icône ; rien de nouveau n'arrive sur l'appareil |
| L'app (`GR4-LUTSmith`) crée le même firmware que la ligne de commande | vérifié hors ligne : identique octet pour octet pour la même LUT, la même photo et les mêmes choix |
| Passes côte à côte (`--jobs`, « En parallèle » dans l'app) | vérifié hors ligne : les mêmes résultats, octet pour octet, que les mêmes passes l'une après l'autre |
| L'outil reproduit exactement l'exemple testé | testé (`selftest`) |

## Pour les développeurs

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

- Lancer l'app depuis le code source : `uv sync --extra app`, puis `uv run python -m lutsmith_app`.
- La créer : `uv run python packaging/build.py` (sur un Mac avec puce Apple silicon, ajoutez `--arch x86_64`
  pour la version Intel) ; le zip est placé dans `dist/`.

| Fichier | SHA-256 |
| --- | --- |
| `fwdc248b.bin` officiel RICOH GR IV 1.11 | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| firmware d'exemple (`selftest`, à partir de `examples/film-1d.look.json`) | `d201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052` |
