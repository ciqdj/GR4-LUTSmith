# GR4-LUTSmith

**Your own colour look, from a `.cube` LUT, inside your RICOH GR IV.**

GR4-LUTSmith takes a colour-grading LUT (`.cube`) and builds a GR IV firmware
that carries its look as an **Image Control** look. You can shoot with it in
stills, in movie mode and in the viewfinder, and use it in **RAW Development**.
Everything else on your camera stays exactly as it was, and you can go back to
the official firmware at any time.

This repository contains no RICOH firmware. You download the official firmware
from RICOH yourself, and the included tool turns it into the version with your
look, on your own computer.

> **Unofficial, at your own risk.** Not made or endorsed by RICOH IMAGING.
> Installing modified firmware may void your warranty. Please read
> [Before you start](#before-you-start) and [Risks](#risks) first.

## How it works

The GR IV does not run LUTs directly. Its looks are built from a few native
controls: a colour mix, tone curves and contrast settings. GR4-LUTSmith
**fits** your LUT to those controls, measures how close the camera can get, and
only then writes the firmware.

- **Tonal and overall colour looks** fit very well. That covers film-style
  curves, contrast, faded blacks, warm or cool casts, and overall saturation
  changes.
- **Looks that move single hues separately** can only be approximated. That
  covers teal-orange, skin-tone protection, and "this green only". The tool
  tells you when that is the case.
- **Log and camera-specific conversion LUTs** (S-Log, V-Log, …) are not
  supported. Use a "creative" LUT made for normal (Rec.709 / sRGB) pictures.

The fit is judged with **CIEDE2000**, the standard measure of how different
two colours look. As a guide, **below 1 is hard to see side by side** and
around 2 is a small visible difference.

| Result | Meaning |
| --- | --- |
| **good** | average difference below 1, and 95 % of colours below 2: looks the same |
| **approximate** | average below 2: close, with visible differences in some colours |
| **poor** | the camera cannot reproduce the LUT's whole colour range; firmware is still written when **everyday colours** fit (see [When a LUT is "poor"](#when-a-lut-is-poor)) |

Every LUT is measured three ways: across its whole colour range, on the
24 everyday colours of a **ColorChecker** chart (skin, sky, foliage, …), and on
**neutral greys** (where any colour cast is most visible). With `--photo`, also
on your own photo.

## What you get

After installing, the Image Control list ends like this:

| Shown as | Look | Still | Movie |
| --- | --- | :---: | :---: |
| HDR Tone | (your existing colour look) | ✓ | |
| Standard | Monochrome Standard | ✓ | ✓ |
| Solid | Monochrome Solid | ✓ | ✓ |
| Soft | Monochrome Soft | ✓ | |
| **High Contrast** | **your LUT's look, in colour** | ✓ | ✓ |
| Grainy | Monochrome Grainy | ✓ | |
| HDR Tone | Monochrome HDR *(experimental)* | ✓ | |

- Your look uses the name and icon of **High Contrast** (the fourth entry after
  the first "HDR Tone").
- It opens with **every slider at 0**, sharpness at its standard value and
  **grain off**. Your LUT's look is built in at those settings; the sliders then
  work as usual, starting from your look.
- The five monochrome looks of the GR IV Monochrome are available too, as in
  GR4-MonoUnlock.
- All your existing looks are unchanged.

## Before you start

- **Camera:** RICOH GR IV (the standard colour model). Other models are not
  supported.
- **Your camera must already be on firmware 1.11.** Check the version in the
  camera's setup menu.
  - Older version: first update to 1.11 the normal way, with RICOH's official file.
  - Newer version: **do not use this tool.** It only supports 1.11.
- **A fully charged battery.** A firmware update must never lose power.
- **An SD card** you can format.
- **A computer with [uv](https://docs.astral.sh/uv/)** (it installs Python
  and everything else the tool needs). If you prefer plain Python instead, see
  [Without uv](#without-uv).
- **Your LUT** as a `.cube` file (3D or 1D), and whether it was made for
  **sRGB** (most LUTs) or **Adobe RGB**.
- **Recommended:** a DNG photo taken with your GR IV. The tool uses it to check
  the look on real content and to make a preview.
- Note down any custom settings (C1, C2, …) you would not want to set up again.

## Install

### 1. Download the official firmware

From RICOH IMAGING's official GR IV support page, download **firmware version
1.11**. Unpack it if needed until you have the file **`fwdc248b.bin`**.

### 2. Make your firmware

Open a terminal in this folder and run (use your own paths):

```sh
uv sync --extra photo
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

- Add `--space adobe` if the LUT was made for Adobe RGB.
- `--photo` is optional, but recommended.

The tool:

1. makes sure you gave it the genuine official 1.11 file;
2. fits the LUT (this takes one to three minutes) and shows how well it fits;
3. builds the firmware and checks it.

A good run ends like this:

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
```

The output folder `output/my_look/` also contains `look.json` (the fitted
look) and can take a preview (step 3).

If the LUT cannot be reproduced well, or the firmware file is not the official
1.11, the tool prints `refused: …` and writes **no firmware**.

### 3. (Optional) Preview it

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

This writes `output/my_look/preview.jpg` with three panels: the camera
without the look, the LUT itself, and the camera **with** the look. Colour and
tone are what to compare. Sharpening and noise are not simulated.

### 4. Copy it to the SD card

1. **Format the SD card in the camera.**
2. Copy **`output/my_look/fwdc248b.bin`** to the **top level** of the card:
   not into a folder, and keep the name exactly `fwdc248b.bin`.

### 5. Update the camera

1. Insert the fully charged battery and the SD card.
2. Start the firmware update from the camera's setup menu, as described in
   RICOH's official GR IV firmware update instructions.
3. **The camera shows an update from version 1.11 to version 1.11.** This is
   expected: the modified firmware keeps the version number. Confirm the update.
4. **Do not turn the camera off, open the battery or card door, or remove the
   card** until the update has finished and the camera has restarted.

### 6. Shoot

- Open **Image Control** and choose **High Contrast** (after the first
  "HDR Tone"). It is in colour now.
- The firmware version still shows **1.11**. That is normal.
- Delete `fwdc248b.bin` from the card (or format the card) so the update is not
  started again by accident.

To change to another LUT later, make a new firmware from the **official**
file and install it the same way.

## Going back to the official firmware

Repeat steps 4–5 with the **official** `fwdc248b.bin` from RICOH instead. The
camera again shows **1.11 → 1.11**; confirm it, and your camera is back to stock.

## When a LUT is "poor"

Many film-simulation LUTs reshape very saturated colours in ways the camera's
controls cannot follow, so they are "poor" across their whole colour range even
though everyday pictures look right. The firmware is still written when:

- the **ColorChecker** colours differ by less than 2 on average, the **greys**
  by less than 2, and no grey gets a visible colour cast; and, with `--photo`,
  the look is not poor on your photo; or
- with `--photo`, the look is **good on your photo** (and at least halves the
  difference there), with the same grey and colour-cast limits.

The tool says which rule applied. Otherwise it writes no firmware; add
`--force` to build anyway, and check the preview first.

## Good to know

- **The sliders** (Key, Contrast, Highlight, Shadow, Sharpness, Shading,
  Clarity, Toning, Grain) work on top of your look; at 0 you get the LUT.
  Saturation and Hue are not offered for this slot.
- **Two "Standard" and two "HDR Tone" entries.** The monochrome Standard and HDR
  looks use the same names and icons as the colour ones.
- **An official RICOH update removes your look.** It replaces the whole
  firmware.
- **Only for the standard GR IV.** Never install the file on another model.
- **Before sending the camera for service,** go back to the official firmware.
- To check any firmware file before copying it to a card:

  ```sh
  uv run gr4_lutsmith.py check path/to/fwdc248b.bin
  ```

  It tells you whether the file is the official 1.11, a GR4-LUTSmith firmware,
  or something else.
- To check the tool itself against your official file:

  ```sh
  uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
  ```

  This builds the bundled example (`examples/film-1d.cube`) and compares the
  result with the tested build. It prints `selftest: PASSED`.
- `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG` fits and
  reports without needing the firmware file, so you can try many LUTs first.

## Without uv

With Python 3.9 or newer:

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` and `pillow` are only needed for `--photo` and `preview`.

## Risks

- Your camera cannot tell a good firmware file from a damaged one. Only copy a
  file the tool has written (or confirmed with `check`) to your card.
- If an update is interrupted, or a firmware file cannot start, the camera may
  not reach the update function again, and it would then need RICOH service.
  This did not happen in testing, but it cannot be ruled out.
- Your camera's own calibration data is not touched.

## Testing status

| What | Status |
| --- | --- |
| A personal LUT look with its own tone curve, in this slot, on stills, movie, viewfinder and RAW Development | tested on a GR IV 1.11 |
| Update accepted; going back to the official 1.11 restores the camera completely | tested on a GR IV 1.11 |
| The five monochrome looks | tested on a GR IV 1.11 (see GR4-MonoUnlock) |
| Keeping the slot's own "High Contrast" name and icon | the name and icon are RICOH's own, unchanged; this exact combination has not been installed yet |
| Sliders opening at 0 (grain off) | made of the same changes as the tested build (a subset of them); not installed on its own yet |
| Looks that need two tone curves | built and checked on the computer; not yet installed |
| The tool reproduces the tested example exactly | tested (`selftest`) |

## Files

```
GR4-LUTSmith/
├── README.md            this guide
├── gr4_lutsmith.py      the tool
├── pyproject.toml       dependencies (for uv)
├── uv.lock
└── examples/
    ├── film-1d.cube      a 1D film-style LUT (used by selftest)
    └── film-1d.look.json its fitted look
```

| File | SHA-256 |
| --- | --- |
| official RICOH GR IV 1.11 `fwdc248b.bin` | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| example firmware (`selftest`, from `examples/film-1d.look.json`) | `d201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052` |
