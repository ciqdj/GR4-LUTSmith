<p align="center">
  <img src="lutsmith_app/assets/app/icon-128.png" width="112" height="112" alt="GR4-LUTSmith 圖示：一根鋼條彎成底片色調曲線">
</p>

<h1 align="center">GR4-LUTSmith</h1>

<p align="center">
  <strong>用 <code>.cube</code> LUT 打造您自己的色彩風格，放進您的 RICOH GR IV 或 GR IV HDF。</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.zh-CN.md">简体中文</a> |
  <strong>繁體中文</strong> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.es.md">Español</a>
</p>

GR4-LUTSmith 讀取調色用的 LUT（`.cube`），產生一個 GR IV / GR IV HDF 韌體，將 LUT 的效果做成**影像控制**中的一個風格。拍照、錄影和取景畫面都能使用它，**RAW Development** 中也能使用。相機的其他一切都維持原樣，而且隨時都能還原為官方韌體。

本儲存庫不含任何 RICOH 韌體。官方韌體由您自行從 RICOH 下載，再由隨附的工具在您自己的電腦上，將它轉換成含有您風格的版本。

> [!WARNING]
> **非官方工具，風險自負。** 並非由 RICOH IMAGING 製作或認可。安裝修改過的韌體可能導致保固失效。請先閱讀[開始之前](#開始之前)和[風險](#風險)。

| 您想要 | 前往 |
| --- | --- |
| 在視窗中逐步製作韌體（macOS、Windows；支援相機的 21 種語言） | [應用程式](#應用程式) |
| 在終端機中製作（macOS、Windows、Linux） | [命令列](#命令列) |
| 產生別人分享給您的風格 | [使用別人分享的風格](#使用別人分享的風格) |
| 查看韌體檔案的內容 | [檢查韌體檔案](#檢查韌體檔案) |
| 還原為 RICOH 的韌體 | [還原官方韌體](#還原官方韌體) |

應用程式和命令列以相同的 LUT 和選擇，產生完全相同的韌體。

**目錄：**[運作原理](#運作原理) | [您會得到什麼](#您會得到什麼) | [開始之前](#開始之前) | [應用程式](#應用程式) | [命令列](#命令列) | [安裝到相機](#安裝到相機) | [個人化設定](#個人化設定) | [讓擬合更接近](#讓擬合更接近) | [須知](#須知) | [風險](#風險) | [測試狀態](#測試狀態) | [給開發者](#給開發者)

## 運作原理

GR IV 無法直接使用 LUT。它的風格由幾項原生控制組成：色彩混合、色調曲線、對比設定和**分色相調整**（針對 12 個色相範圍分別調整色彩）。GR4-LUTSmith 會將您的 LUT **擬合**到這些控制上，測量相機能接近到什麼程度，之後才寫入韌體。

- **色調與整體色彩的風格**擬合效果很好，包括底片風格的曲線、對比、褪色的黑色、偏暖或偏冷的色調，以及整體飽和度的變化。
- **個別移動單一色相的風格**（青橙色調、會偏移綠色或天空的底片模擬等）以**分色相調整**擬合，比只用色彩混合接近得多。強烈取決於色彩飽和程度的變化（例如只針對最鮮豔的紅色）仍然只能近似，遇到這種情況時工具會告訴您。
- **Log 和特定相機的轉換 LUT**（S-Log、V-Log 等）不受支援。請使用為一般（Rec.709 / sRGB）照片製作的「創意」LUT。

擬合以 **CIEDE2000** 評判，這是衡量兩種色彩看起來差多少的標準指標。大致而言，**低於 1 時並排比較也難以察覺**，2 左右則是可見的細微差異。

| 結果 | 意義 |
| --- | --- |
| **良好** | 平均差異低於 1，且 95 % 的色彩低於 2：看起來相同 |
| **近似** | 平均低於 2：接近，但部分色彩有可見差異 |
| **不佳** | 相機無法重現 LUT 的完整色彩範圍；只要**日常色彩**擬合良好，仍會寫入韌體（見[LUT 評為不佳時](#lut-評為不佳時)） |

每個 LUT 都以三種方式測量：完整色彩範圍、**ColorChecker** 色卡的 24 種日常色彩（膚色、天空、樹葉等），以及**中性灰**（任何偏色在這裡最明顯）。若提供您自己的照片（`--photo`），也會在該照片上測量。

## 您會得到什麼

安裝後，影像控制清單的最後幾項如下。除了影像控制、標準、飽和度和色相之外，選單名稱均以相機設為英文時的顯示為準。

| 顯示名稱 | 風格 | 照片 | 影片 |
| --- | --- | :---: | :---: |
| HDR Tone | （您現有的彩色風格） | ✓ | |
| 標準 | 黑白標準 | ✓ | ✓ |
| Solid | 黑白 Solid | ✓ | ✓ |
| Soft | 黑白 Soft | ✓ | |
| **High Contrast** | **您的 LUT 風格，彩色** | ✓ | ✓ |
| Grainy | 黑白 Grainy | ✓ | |
| HDR Tone | 黑白 HDR *（實驗性）* | ✓ | |

- 您的風格使用 **High Contrast** 的名稱和圖示（第一個「HDR Tone」之後的第四項）。您也可以改選 **Cinema (Yellow)**、**Vivid** 或其他欄位，或同時使用多個：見[選擇欄位](#選擇欄位)。它也可以顯示[您自己的名稱](#為欄位命名)和[您自己的圖示](#自訂圖示)。
- 開啟時**所有滑桿皆為 0**，銳利度為標準值，**顆粒關閉**。您的 LUT 風格就是以這些設定內建的；之後滑桿照常運作，以您的風格為起點。
- GR IV Monochrome 的五種黑白風格也都可以使用，與 GR4-MonoUnlock 相同。
- 您現有的所有風格都不變。

## 開始之前

- **相機：** RICOH GR IV 或 GR IV HDF。RICOH 的 1.11 更新是兩者共用的同一個檔案，本工具產生的檔案也是如此。不支援其他機型，包括 GR IV Monochrome。
- **您的相機必須已更新至韌體 1.11。** 請在相機的設定選單中確認版本。
  - 較舊版本：先以一般方式，用 RICOH 的官方檔案更新至 1.11。
  - 較新版本：**請勿使用本工具。** 本工具只支援 1.11。
- **官方韌體檔案。** 從 RICOH IMAGING 官方 GR IV（或 GR IV HDF）支援頁面下載**韌體版本 1.11**。如有需要請解壓縮，直到取得 **`fwdc248b.bin`** 檔案。
- **充飽電的電池。** 韌體更新過程中絕不能斷電。
- **一張可以格式化的 SD 卡。**
- **您的 LUT**：`.cube` 檔案（3D 或 1D），並確認它是為 **sRGB**（大多數 LUT）還是 **Adobe RGB** 製作的。
- **建議：** 一張用您的 GR IV 或 GR IV HDF 拍攝的 DNG 照片。工具會用它在真實畫面上檢查風格，並製作預覽。
- 記下您不想重新設定的自訂設定（C1、C2 等）。

接著用[應用程式](#應用程式)或[命令列](#命令列)製作韌體。

## 應用程式

### 下載

從[最新版本](../../releases/latest)下載適合您電腦的檔案：

| 電腦 | 檔案 |
| --- | --- |
| 搭載 Apple 晶片的 Mac（M1 或更新機型） | `GR4-LUTSmith-<version>-macOS-AppleSilicon.zip` |
| 搭載 Intel 處理器的 Mac | `GR4-LUTSmith-<version>-macOS-Intel.zip` |
| Windows 10 或 11（64 位元） | `GR4-LUTSmith-<version>-Windows-x64.zip` |

需要 macOS 12（Monterey）或更新版本。不確定您的 Mac 是哪一種？蘋果選單 → **關於這台 Mac**：「晶片 Apple M…」是 Apple 晶片，「處理器 Intel」是 Intel。

每個 zip 檔都包含應用程式和一個 `Licences` 資料夾（應用程式所用元件的授權條款）。

<details>
<summary><strong>確認檔案來自本專案</strong>（選用）</summary>

<br>

每個 zip 檔都由本儲存庫自己在 GitHub 上的建置流程產生，該流程會簽署一份來源記錄：儲存庫、建置以及程式碼的確切版本。您可以用 [GitHub CLI](https://cli.github.com)（先以 `gh auth login` 登入）確認您下載的正是該檔案，且未經更改或替換：

```sh
gh attestation verify GR4-LUTSmith-2.2.0-macOS-AppleSilicon.zip --repo lemonadesaltbagel/GR4-LUTSmith
```

（請使用您下載的 zip 檔名；在 Windows 上，請在 PowerShell 中從「下載」資料夾執行。）結果最後會顯示「Verification succeeded!」，並列出產生該檔案的建置。出現任何其他結果都表示：請勿開啟，並從版本頁面重新下載。儲存庫的 **Attestations** 頁面列出所有已簽署的檔案。

更快確認下載是否完整的方法：版本頁面在 `SHA256SUMS` 中列出了每個檔案的 SHA-256。

- macOS（終端機）：`shasum -a 256 ~/Downloads/GR4-LUTSmith-*.zip`
- Windows（PowerShell）：`Get-FileHash $HOME\Downloads\GR4-LUTSmith-*.zip -Algorithm SHA256`

這只能證明檔案完整送達，無法證明是誰製作的：`SHA256SUMS` 和 zip 檔放在同一個頁面上。

您也可以完全不下載：從原始碼執行應用程式（見[給開發者](#給開發者)），或用[命令列](#命令列)製作韌體。應用程式和命令列產生的 `fwdc248b.bin` 完全相同，而 `uv run gr4_lutsmith.py check fwdc248b.bin` 可顯示任何韌體檔案的內容。

</details>

### 第一次開啟

本應用程式免費，且未使用付費的 Apple 或 Microsoft 憑證簽署，因此電腦會詢問您一次是否信任它。

**macOS**

1. 解壓縮檔案，將 **GR4-LUTSmith** 移到「應用程式」資料夾。
2. 開啟它。macOS 會表示無法檢查此 App 是否含有惡意軟體；選擇**完成**（macOS 15）或**取消**。
3. 開啟**系統設定 → 隱私權與安全性**，向下捲動到關於 GR4-LUTSmith 的訊息，選擇**強制打開**，然後輸入密碼確認。在 macOS 12 到 14 上，也可以改為按住 Control 鍵並按一下 App，選擇**打開**，再選一次**打開**。

之後即可正常開啟。

**Windows**

1. 在 zip 檔上按右鍵 → **解壓縮全部…**，然後開啟解壓縮後的 **GR4-LUTSmith** 資料夾（請勿直接在 zip 檔內執行）。
2. 開啟 **GR4-LUTSmith.exe**。若 Windows 顯示「Windows 已保護您的電腦」，請選擇**其他資訊 → 仍要執行**。

請將整個資料夾放在一起：應用程式需要旁邊的 `_internal` 資料夾。

### 使用方式

應用程式會在畫面上逐步引導您：相機的韌體檔案、LUT（以及選用的 DNG）、欄位及其名稱和圖示、擬合，最後產生韌體。它會將 `fwdc248b.bin` 儲存到您選擇的位置；接著[安裝到相機](#安裝到相機)。

- **語言：** 應用程式跟隨電腦的語言；可在視窗頂端變更。它也是檢查欄位名稱時所依據的相機語言（見[為欄位命名](#為欄位命名)）。
- **外觀：** 跟隨系統、日間或夜間，位於視窗頂端。
- **檢查韌體檔案**（左側）會告訴您某個 `fwdc248b.bin` 是 RICOH 的官方檔案、由 GR4-LUTSmith 製作（以及包含哪些風格），還是其他檔案。
- 別人分享的風格（`.json`）在應用程式中也能使用：在第一頁選擇「共享風格」。
- **同時執行多輪：** 在「擬合」頁面上，選擇輪數以及「同時執行」的數量（每輪使用一個處理器核心；見[增加輪數](#增加輪數)）。每輪都會顯示進度；執行期間可以新增輪次，「全部停止」會保留已完成的輪次。各輪完成後，結果會陸續加入表格。

### 遇到問題時

- **macOS 表示應用程式已損毀**：請重新下載（檔案不完整），並依[確認檔案來自本專案](#下載)的說明檢查。
- **應用程式在 Windows 上無法啟動**：請確認已解壓縮整個 zip 檔，並從解壓縮後的資料夾執行 `GR4-LUTSmith.exe`。
- **韌體檔案遭拒**：應用程式只接受 RICOH 未經修改的 GR IV / GR IV HDF 1.11 `fwdc248b.bin`。已被 GR4-LUTSmith 修改過的檔案無法再次修改；請從未經修改的檔案開始。

## 命令列

### 1. 安裝

安裝 **[uv](https://docs.astral.sh/uv/)**（它會安裝 Python 和工具所需的其他一切），在此資料夾中開啟終端機並執行：

```sh
uv sync --extra photo
```

<details>
<summary>不使用 uv</summary>

<br>

使用 Python 3.9 或更新版本：

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` 和 `pillow` 只有 `--photo` 和 `preview` 需要。

</details>

### 2. 製作韌體

請換成您自己的路徑：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

| 選項 | 作用 |
| --- | --- |
| `--space adobe` | LUT 是為 Adobe RGB 製作的 |
| `--photo R0001234.DNG` | 也在您的照片上檢查風格（選用，但建議使用） |
| `--slot vivid`、`--slot cinema-yellow`、… | 將您的風格放在其他風格的位置，而非 High Contrast：[選擇欄位](#選擇欄位) |
| `--name "My Look"` | 以您自己的名稱顯示欄位：[為欄位命名](#為欄位命名) |
| `--icon my_icon.png` | 為欄位設定您自己的選單圖示：[自訂圖示](#自訂圖示) |
| `--turns 3` | 執行三次擬合並保留最好的結果：[增加輪數](#增加輪數) |
| `--jobs 3` | 最多同時執行其中三輪：[增加輪數](#增加輪數) |
| `--after-curves` | 另外嘗試第二個色彩混合：[曲線後色彩調整](#曲線後色彩調整) |

工具會：

1. 確認您提供的是真正的官方 1.11 檔案；
2. 擬合 LUT（需要幾分鐘，分色相調整另需一兩分鐘），並顯示擬合程度；
3. 產生韌體並加以檢查。

順利完成時，結尾如下：

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
Copy this file to the root of the SD card and run the camera's firmware update.
Then choose High Contrast in Image Control: your look is there.
```

工具在開始時也會說明您的風格放在哪個欄位，例如 `slot: High Contrast (replaces the hidden monochrome High Contrast look)`。

輸出資料夾 `output/my_look/` 也包含 `look.json`（擬合完成的風格），並可放入預覽（第 3 步）。您可以將 `look.json` 分享給其他 GR IV 和 GR IV HDF 使用者：他們不必重新擬合就能產生相同的風格（見[使用別人分享的風格](#使用別人分享的風格)）。

若 LUT 無法良好重現，或韌體檔案不是官方 1.11，工具會顯示 `refused: …`，且**不寫入任何韌體**。

### 3. 預覽（選用）

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

這會寫入 `output/my_look/preview.jpg`，包含三個畫面：未套用風格的相機、LUT 本身，以及**套用**風格的相機。LUT 畫面需要 `.cube` 檔案：工具會在 `look.json` 旁或目前的資料夾中尋找，您也可以用 `--lut my_look.cube` 指定；沒有的話，預覽只顯示另外兩個畫面。要比較的是色彩和色調。銳利化和雜訊不會模擬。

接著[安裝到相機](#安裝到相機)。

## 安裝到相機

應用程式和命令列產生的韌體，步驟都相同。

### 1. 複製到 SD 卡

1. **在相機中格式化 SD 卡。**
2. 將 **`fwdc248b.bin`**（命令列：`output/my_look/fwdc248b.bin`）複製到記憶卡的**最上層**：不要放進資料夾，檔名必須完全保持 `fwdc248b.bin`。

### 2. 更新相機

1. 裝入充飽電的電池和 SD 卡。
2. 依照 RICOH 官方 GR IV / GR IV HDF 韌體更新說明，從相機的設定選單開始韌體更新。
3. **相機會顯示從版本 1.11 更新到版本 1.11。** 這是正常的：修改過的韌體保留原本的版本號碼。請確認更新。

> [!CAUTION]
> 在更新完成且相機重新啟動之前，**請勿關閉相機、打開電池蓋或記憶卡蓋，也不要取出記憶卡**。

### 3. 拍攝

- 開啟**影像控制**，選擇 **High Contrast**（第一個「HDR Tone」之後）。它現在是彩色的。如果您選了其他欄位，請改選該項。
- 韌體版本仍顯示 **1.11**，這是正常的。
- 從記憶卡刪除 `fwdc248b.bin`（或格式化記憶卡），以免不小心再次開始更新。

之後若要換成其他 LUT，請從**官方**檔案製作新的韌體，並以相同方式安裝。

### 還原官方韌體

改用 RICOH 的**官方** `fwdc248b.bin` 重複步驟 1–2。相機同樣會顯示 **1.11 → 1.11**；確認後，相機就恢復原廠狀態。

## 個人化設定

風格放在哪裡、叫什麼名稱、在選單中長什麼樣子。在應用程式中，這些位於欄位步驟；在命令列中，它們是 `make` 和 `build` 的選項。

### 選擇欄位

您的風格會取代相機的其中一個風格。用 `--slot`（`make` 和 `build`）選擇要取代哪一個；`uv run gr4_lutsmith.py slots` 會在終端機中顯示相同的清單：

| `--slot` | 顯示名稱 | 取代 | 照片 | 影片 | 額外滑桿 |
| --- | --- | --- | :---: | :---: | --- |
| `high-contrast`（預設） | High Contrast | 隱藏的黑白風格「High Contrast」 | ✓ | ✓ | — |
| `cinema-yellow` | Cinema (Yellow) | RICOH 的「Cinema (Yellow)」風格 | ✓ | ✓ | 飽和度、色相 |
| `cinema-green` | Cinema (Green) | RICOH 的「Cinema (Green)」風格 | ✓ | ✓ | 飽和度、色相 |
| `vivid` | Vivid | RICOH 的「Vivid」風格 | ✓ | ✓ | 飽和度、色相 |
| `positive-film` | Positive Film | RICOH 的「Positive Film」風格 | ✓ | ✓ | 飽和度、色相 |
| `negative-film` | Negative Film | RICOH 的「Negative Film」風格 | ✓ | ✓ | 飽和度、色相 |
| `bleach-bypass` | Bleach Bypass | RICOH 的「Bleach Bypass」風格 | ✓ | ✓ | 飽和度、色相 |
| `retro` | Retro | RICOH 的「Retro」風格 | ✓ | ✓ | 飽和度、色相 |
| `soft-monotone` | Soft Monotone | RICOH 的「Soft Monotone」風格 | ✓ | | — |
| `hard-monotone` | Hard Monotone | RICOH 的「Hard Monotone」風格 | ✓ | ✓ | — |
| `hi-contrast-bw` | Hi-Contrast B&W | RICOH 的「Hi-Contrast B&W」風格 | ✓ | ✓ | — |
| `mono-standard` | 標準（第二個） | 隱藏的黑白風格「標準」 | ✓ | ✓ | — |
| `mono-soft` | Soft | 隱藏的黑白風格「Soft」 | ✓ | | — |
| `mono-solid` | Solid | 隱藏的黑白風格「Solid」 | ✓ | ✓ | — |

- 每個欄位的色彩都相同：相機在每個欄位處理您風格的方式都一樣，所以擬合及其分數不會因欄位而改變。
- 在每個欄位中，您的風格開啟時所有滑桿皆為 0，顆粒關閉。
- 欄位改變的只有：您失去哪一項，以及得到哪些滑桿。在黑白欄位上，您的風格是彩色的；那裡不提供飽和度和色相。
- **Cinema：** 它的 Color Tone 設定對您的風格沒有作用。**Bleach Bypass：** 它的色調設定不會改變您的風格。**Retro：** Retro 本身的調色效果和類似暗角的色調效果會被移除，因此您只會得到您的風格。
- 未使用的欄位保留 RICOH 的風格。High Contrast 上沒有放風格時，它仍是黑白的 High Contrast 風格。
- **無法使用：** 標準、Monotone、HDR Tone、Cross Processing，以及隱藏的 Grainy 和 HDR 風格。這些風格與其他風格共用部分處理，或使用會改變您色彩的特殊處理。
- `check` 會列出哪些欄位放有個人風格。

### 一個韌體放入多個風格

用 `fit` 擬合每個 LUT，再將它們一起產生，每個風格檔案後面接著它自己的 `--slot`（如有需要，也可加上 `--name`、`--icon`）：

```sh
uv run gr4_lutsmith.py fit look_a.cube --photo R0001234.DNG -o output/a
uv run gr4_lutsmith.py fit look_b.cube --photo R0001234.DNG -o output/b
uv run gr4_lutsmith.py build output/a/look.json --slot cinema-yellow output/b/look.json --slot vivid --name "Look B" ~/Downloads/fwdc248b.bin -o output/both
```

**一次能放幾個：** High Contrast 和兩個 Cinema 欄位一律各自容納完整的風格。其他欄位共用有限的空間：每個風格都需要空間存放色調曲線，分色相調整和曲線後色彩調整則需要多得多的空間。簡單的風格（一條色調曲線）最多可同時放入其中 10 個欄位；含分色相調整的風格能放的少得多。放不下時，工具會告知並且不寫入任何內容；請減少欄位或使用較簡單的風格，並將 High Contrast 留空以取得最多空間。

### 為欄位命名

`--name`（`make` 和 `build`）讓欄位在影像控制選單及其畫面中，以相機的所有語言顯示您自己的名稱：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra"
```

- 每個欄位可接受的名稱都有長度上限：`uv run gr4_lutsmith.py slots` 會顯示（從 Retro 的 9 個字元到 Cinema (Yellow) 的 23 個字元）。第二個黑白標準無法重新命名，因為它與彩色「標準」風格共用名稱。
- **純 ASCII**（英文字母、數字、空格和標點符號）在每種相機語言中都能顯示。這是安全的選擇。
- **其他字母和字元**只在使用它們的相機語言中有效：日文名稱在相機設為日文時顯示，`Müller` 在歐洲語言中顯示，`Плёнка` 在俄文中顯示，依此類推。相機所有語言都不使用的字元（表情符號、阿拉伯文、希伯來文等）會被拒絕。
- 工具會依您的**相機語言**檢查名稱；除非您設定 `--camera-language`（例如 `--camera-language Japanese`；`--help` 會列出全部 21 種），否則相機語言就是您電腦的語言。若名稱使用了該語言沒有的字元，工具會警告這些字元可能無法顯示，並詢問是否仍要使用此名稱。輸入 `y` 繼續，或加上 `--accept-name` 預先同意（工具無法詢問時需要，例如在腳本中）。若之後將相機切換為其他語言，非 ASCII 的名稱在那裡可能無法顯示。
- 較長的名稱在某些畫面上可能會被截斷（中文、日文和韓文字元的寬度約為英文字母的兩倍）。
- 不使用 `--name` 時，欄位保留原本的名稱。名稱不會儲存在 `look.json` 中（該檔案只包含風格本身）：`build` 時請再次提供 `--name`。`check` 會顯示已產生韌體中的名稱。

### 自訂圖示

`--icon`（`make` 和 `build`）以您自己的圖片取代欄位在影像控制選單中的圖示：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- 任何圖片都可以（PNG、JPEG 等）。選單圖示為 40×40 像素：較大或較小的圖片會調整大小，非正方形的圖片則使用其**中央**部分。透明部分保持透明，因此背景透明的 PNG 看起來會像相機本身的圖示。
- `make` 會將結果儲存為韌體旁的 `icon.png`，讓您確切看到相機將顯示的樣子。在這種尺寸下，簡單、粗大的形狀最容易辨識。
- 除了第二個黑白標準之外，每個欄位都可以使用自訂圖示（那一個與彩色「標準」風格共用圖示）。`slots` 會列出這些欄位。
- 需要 Pillow（`uv sync --extra photo`）。不使用 `--icon` 時，欄位保留原本的圖示。圖示不會儲存在 `look.json` 中：`build` 時請再次提供 `--icon`。`check` 會顯示哪些欄位有自訂圖示。

### 使用別人分享的風格

`look.json` 只包含風格本身：它的色彩設定，以及這些設定與 LUT 的擬合程度。不含欄位、名稱或圖示，也不含您電腦上的任何資料夾（只有 LUT 的檔名）。任何擁有此檔案的人都能直接產生韌體，不需要 LUT，也不需要擬合；在欄位、名稱和圖示相同時，得到的韌體與製作者的逐位元組相同。

在應用程式中，於第一頁選擇「共享風格」。在命令列中，檔案可以使用任何名稱，因此分享前可隨意重新命名（`portra-400.json` 等）：

```sh
uv run gr4_lutsmith.py build portra-400.json ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- 工具會先顯示此風格與其 LUT 的擬合程度（即製作者看到的結果；「on your photo」指的是製作者的照片）。
- 欄位、名稱和圖示由您選擇，方法同[選擇欄位](#選擇欄位)、[為欄位命名](#為欄位命名)和[自訂圖示](#自訂圖示)。不使用 `--slot` 時，風格會放在 High Contrast。
- 多個風格：在每個檔案後面緊接著寫上它自己的 `--slot`、`--name` 和 `--icon`：

  ```sh
  uv run gr4_lutsmith.py build portra-400.json --slot vivid --name "Portra" tri-x.json --slot hard-monotone ~/Downloads/fwdc248b.bin -o output/both
  ```

- 產生任何內容之前，會先檢查檔案內容：損毀的檔案，或含有相機無法接受之數值的檔案，都會被拒絕，且不寫入任何內容。
- 1.7.0 之前版本製作的檔案可能還包含欄位、名稱、圖示以及 LUT 的完整路徑。`build` 會忽略欄位、名稱和圖示（並說明原本是什麼）；分享這類檔案前，請用文字編輯器開啟並檢查 `"file"`。

## 讓擬合更接近

每次擬合都會嘗試分色相調整。想要更接近時，先執行更多輪，再嘗試曲線後色彩調整（見[哪個幫助更大](#哪個幫助更大)）。

### 分色相調整

擬合色彩混合和色調曲線後，工具會嘗試以**分色相調整**改善風格：相機可以在 12 個色相範圍中分別調整色彩。**只有在明顯有幫助時**（完整色彩範圍或 ColorChecker 至少改善 10 %）**且沒有任何一項變差時**（您的照片、灰色、ColorChecker）才會保留。結果行會顯示 `hue sectors: yes` 或 `no`。

- 分色相調整絕不會改變灰色，而且相鄰區段之間一律無縫銜接，因此色彩從一個色相到下一個色相都保持平滑。
- 使用 `--photo` 時，分色相調整也會針對真實畫面調整（建議）。
- `--no-hue` 會關閉此功能（`make` 和 `fit`）。

### 增加輪數

擬合從一個起點開始，再從那裡逐步改善。相機只有少數幾項色彩控制，因此**擬合從哪裡開始，往往決定了能接近到什麼程度**。使用 `--turns`（應用程式中：在「擬合」頁面上），工具會執行多次擬合（「輪」），每輪都從新的隨機起點開始，並保留好的結果：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG --turns 3
```

- 第 1 輪一律使用一般起點，因此執行一輪（預設）會得到與以前相同的結果。之後的每一輪都會抽取新的隨機起點。
- 每輪所需時間與一般擬合相同（幾分鐘）。
- **同時執行。** `--jobs 3` 最多同時執行三輪，每輪使用一個處理器核心和約 0.8 GB 記憶體。請至少保留一個核心給電腦的其他工作。結果與逐輪依序執行完全相同，只是更快完成。
- **保留的結果。** 除非先前某個結果在每項指標上（完整範圍、ColorChecker、灰色和您的照片）都至少一樣好，否則新結果就會保留。若新結果在每項指標上都勝過先前的某個結果，該結果就會離開清單。因此每個保留的結果都至少在一項指標上優於其他所有結果；工具會將它們並列顯示，並建議整體分數最佳的那一個（擬合所用全部內容的平均差異）。
- **最後再加輪。** 結果出現時，工具會詢問 `More turns?`。輸入數字，即可以與本次相同的方式再執行那麼多輪（`2`）；加上 `a` 表示含[曲線後色彩調整](#曲線後色彩調整)的輪次（`2a`），加上 `b` 表示不含的輪次（`2b`），無論本次以哪種方式開始。新的輪次會與所有保留的結果比較。按 Enter 即保留現有結果。
- **重複某一輪。** 每輪的種子都會顯示並儲存在 `turns.json` 中；`--seed 1234` 會再次執行同一輪（搭配 `--turns 3`：種子 1234、1235、1236）。

有多個保留的結果時，輸出資料夾如下：

```
output/my_look/look.json, fwdc248b.bin      the recommended result
output/my_look/turns/turn-1/                 every kept result, each with its
output/my_look/turns/turn-3-after-curves/    own look.json (and, with make, fwdc248b.bin)
output/my_look/turns.json                    every turn, its seed and its scores
```

若要使用其他保留的結果，請改將它的 `fwdc248b.bin` 複製到 SD 卡。

### 曲線後色彩調整

使用 `--after-curves`（`make` 和 `fit`）時，工具還會嘗試第二個色彩混合，由相機在色調曲線**之後**套用。許多底片風格在陰影和亮部改變色彩的方式不同。一般的色彩混合作用在曲線之前，因此無法跟上這種變化，但曲線後的混合通常可以。

LUT 的完整色彩範圍和真實照片不一定一致：某個版本可能在飽和色彩上接近得多，在日常照片上卻稍差一點。因此兩個版本都會進入[增加輪數](#增加輪數)中所述的保留結果清單：只要含曲線後色彩調整的版本在任何一項（完整範圍、ColorChecker、灰色或您的照片）表現更好，就會與一般版本並列保留，由您選擇。選擇前，請在您自己的照片上預覽兩者。

**為什麼是選用的。** 一般擬合多跑幾輪是更大的槓桿（見[哪個幫助更大](#哪個幫助更大)）。曲線後的混合平均而言有幫助，但會讓每輪多花好幾分鐘。

- 灰色保持灰色：此混合絕不會為中性灰加上偏色。
- 擬合時間會多出好幾分鐘（額外四次擬合）。

<details>
<summary>24 個 LUT 的結果</summary>

<br>

在我們對 24 個 LUT 的測試中（各一輪），一般版本與以前完全相同，有 23 個 LUT 得到了第二個版本：

- **8 個在所有有變化的項目上都更好**：在這些 LUT 上，與 LUT 的平均差異從 3.7 降到 2.4（ColorChecker 1.9 → 1.1，照片 0.91 → 0.75）；
- **15 個有取捨**。彩色底片風格通常在完整範圍和 ColorChecker 上接近得多（例如 3.6 → 2.5），照片則稍差一點（最多 0.17）；黑白風格通常在灰色和照片上接近得多，但在完整範圍上差一些；
- 兩個先前遭拒的 LUT 現在可以產生了。

</details>

### 哪個幫助更大

在相同擬合時間的測試中，一般擬合四輪中最好的一輪，繼續擬合下去，每一步都勝過含[曲線後色彩調整](#曲線後色彩調整)的擬合。在各十個隨機輪次中，含曲線後色彩調整的版本平均較好。所以兩者都有幫助，但**一般擬合多跑幾輪帶來的改善更大**：如果有時間，請先多跑幾輪，想同時比較該版本時再加上 `--after-curves`。

### LUT 評為不佳時

許多底片模擬 LUT 會以相機控制無法跟上的方式重塑非常飽和的色彩，因此即使日常照片看起來正確，它們在完整色彩範圍上仍是「不佳」。在下列情況下仍會寫入韌體：

- **ColorChecker** 色彩的平均差異小於 2、**灰色**小於 2，且沒有任何灰色出現可見的偏色；並且使用 `--photo` 時，風格在您的照片上不是「不佳」；或
- 使用 `--photo` 時，風格**在您的照片上為良好**（且至少將那裡的差異減半），灰色和偏色限制相同。

工具會說明套用了哪條規則。否則不會寫入韌體；加上 `--force` 可強制產生，但請先檢查預覽。

## 須知

- **滑桿**（Key、Contrast、Highlight、Shadow、Sharpness、Shading、Clarity、Toning、Grain）作用於您的風格之上；設為 0 時就是 LUT 的效果。High Contrast 上不提供飽和度和色相；Cinema 欄位上則有（見[選擇欄位](#選擇欄位)）。
- **兩個「標準」和兩個「HDR Tone」項目。** 黑白標準和 HDR 風格使用與彩色風格相同的名稱和圖示。
- **RICOH 官方更新會移除您的風格。** 它會取代整個韌體。
- **只適用於 GR IV 和 GR IV HDF。** 絕對不要將此檔案安裝到其他機型，也絕對不要安裝到 GR IV Monochrome。
- **在 GR IV HDF 上使用 2.2.0 之前製作的檔案：** 風格仍在，但滑桿開啟時是 RICOH 為該欄位設定的值，而不是 0。請用 2.2.0 或更新版本重新產生相同的 `look.json`；`check` 會告訴您哪些檔案需要這樣做。在 GR IV 上這些檔案沒有問題。
- **送修相機之前**，請先還原官方韌體。
- **先多試幾個 LUT：** `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG` 不需要韌體檔案即可擬合並回報結果。

### 檢查韌體檔案

將任何韌體檔案複製到記憶卡之前（應用程式中：左側的**檢查韌體檔案**）：

```sh
uv run gr4_lutsmith.py check path/to/fwdc248b.bin
```

它會告訴您該檔案是官方 1.11、GR4-LUTSmith 韌體，還是其他檔案。若是 GR4-LUTSmith 韌體，還會列出哪些欄位放有風格、它們的名稱和圖示，以及這些風格是否使用分色相調整和曲線後色彩調整。

用您的官方檔案檢查工具本身：

```sh
uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
```

這會產生隨附的範例（`examples/film-1d.cube`），並將結果與經過測試的版本比較。它會顯示 `selftest: PASSED`。

## 風險

- 相機無法分辨良好的韌體檔案和損毀的檔案。只將工具寫入的檔案（或經 `check` 確認的檔案）複製到記憶卡。
- 若更新中斷，或韌體檔案無法啟動，相機可能無法再進入更新功能，屆時就需要 RICOH 維修。測試中沒有發生過這種情況，但無法排除。
- 相機本身的校正資料不會被更動。

## 測試狀態

| 項目 | 狀態 |
| --- | --- |
| 具有自己色調曲線的個人 LUT 風格，放在此欄位，用於照片、影片、取景畫面和 RAW Development | 已在 GR IV 1.11 上測試 |
| 更新可被接受；還原為官方 1.11 可讓相機完全恢復 | 已在 GR IV 1.11 上測試 |
| 五種黑白風格 | 已在 GR IV 1.11 上測試（見 GR4-MonoUnlock） |
| 保留欄位原本的「High Contrast」名稱和圖示 | 名稱和圖示是 RICOH 原本的，未經更改；這個確切組合尚未實際安裝過 |
| 滑桿開啟時為 0（顆粒關閉） | 由與已測試版本相同的變更組成（是其中的一部分）；尚未單獨安裝過 |
| 需要兩條或三條色調曲線的風格（偏色、調色風格） | 已在 GR IV 1.11 上測試三條曲線 |
| 分色相調整 | 已在 GR IV 1.11 的 RAW Development 中以底片模擬 LUT 測試（ISO 200，以綠色和黃色為主的日光場景）：相機與工具的預測一致，有色區域與 LUT 的差異減少約 30 %，色彩之間沒有可見的斷層。紅色、藍色、紫色和較高 ISO 尚未在相機上檢查 |
| 曲線後色彩調整（`--after-curves`，選用） | 已在 GR IV 1.11 上測試：正常運作；每輪需要更長時間；與 LUT 的平均差異較小，但在相同時間內，一般擬合多跑幾輪帶來的改善更大（見[哪個幫助更大](#哪個幫助更大)） |
| Cinema (Yellow) / Cinema (Green) 欄位上的風格 | 已在 GR IV 1.11 上測試：正常運作 |
| 其他欄位上的風格（Vivid、Positive Film、Negative Film、Bleach Bypass、Retro、黑白欄位） | 已在 GR IV 1.11 上測試：正常運作 |
| 欄位的自訂名稱（`--name`） | 已在 GR IV 1.11 上測試：正常運作 |
| 欄位的自訂圖示（`--icon`） | 已在 GR IV 1.11 上測試：正常運作 |
| 在 GR IV HDF 上：相同的風格，滑桿同樣開啟時為 0（2.2.0） | 已在 GR IV HDF 1.11 上測試：正常運作 |
| 在 GR IV 上使用 2.2.0 的檔案 | 已離線檢查：唯一新增的是 GR IV HDF 專屬的滑桿設定；GR IV 讀取的內容與 2.1.1 完全相同；尚未實際安裝過 |
| 從分享的 `look.json` 產生 | 已離線檢查：韌體與使用相同 LUT 結果、欄位、名稱和圖示的 `make` 逐位元組相同；沒有任何新內容進入相機 |
| 應用程式（`GR4-LUTSmith`）產生與命令列相同的韌體 | 已離線檢查：相同的 LUT、照片和選擇下逐位元組相同 |
| 同時執行多輪（`--jobs`，應用程式的「同時執行」） | 已離線檢查：結果與依序執行相同輪次逐位元組相同 |
| 工具完全重現經過測試的範例 | 已測試（`selftest`） |

## 給開發者

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

- 從原始碼執行應用程式：`uv sync --extra app`，然後 `uv run python -m lutsmith_app`。
- 建置：`uv run python packaging/build.py`（在搭載 Apple 晶片的 Mac 上，加上 `--arch x86_64` 可建置 Intel 版本）；zip 檔會放在 `dist/`。

| 檔案 | SHA-256 |
| --- | --- |
| RICOH 官方 GR IV / GR IV HDF 1.11 `fwdc248b.bin` | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| 範例韌體（`selftest`，由 `examples/film-1d.look.json` 產生） | `bb838b5426249f27da68b410223f6c24df36c4816abdaf156472a2a3b61d4441` |
