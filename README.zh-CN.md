<p align="center">
  <img src="lutsmith_app/assets/app/icon-128.png" width="112" height="112" alt="GR4-LUTSmith 图标：一根弯成胶片色调曲线的钢条">
</p>

<h1 align="center">GR4-LUTSmith</h1>

<p align="center">
  <strong>用 <code>.cube</code> LUT 制作你自己的色彩风格，放进你的 RICOH GR IV。</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.ja.md">日本語</a> |
  <strong>简体中文</strong> |
  <a href="README.zh-TW.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.es.md">Español</a>
</p>

GR4-LUTSmith 读取调色 LUT（`.cube`），生成一个 GR IV 固件，把 LUT 的风格作为一个 **影像控制** 风格放进相机。你可以在拍照、视频模式和取景器中使用它，也可以在 **RAW Development** 中使用。相机上的其他一切都保持原样，你可以随时恢复官方固件。

本仓库不包含任何 RICOH 固件。官方固件由你自己从 RICOH 下载，附带的工具会在你自己的电脑上把它转换成带有你的风格的版本。

> [!WARNING]
> **非官方，风险自负。** 并非由 RICOH IMAGING 制作或认可。
> 安装修改过的固件可能导致失去保修。请先阅读[开始之前](#开始之前)和[风险](#风险)。

| 你想要 | 前往 |
| --- | --- |
| 在窗口中一步步制作固件（macOS、Windows；支持相机的 21 种语言） | [桌面应用](#桌面应用) |
| 在终端中制作（macOS、Windows、Linux） | [命令行](#命令行) |
| 用别人共享的风格生成固件 | [使用别人共享的风格](#使用别人共享的风格) |
| 查看固件文件里有什么 | [检查固件文件](#检查固件文件) |
| 恢复 RICOH 的固件 | [恢复官方固件](#恢复官方固件) |

使用相同的 LUT 和相同的选择时，应用和命令行生成的固件完全相同。

**目录：**
[工作原理](#工作原理) |
[安装后的效果](#安装后的效果) |
[开始之前](#开始之前) |
[桌面应用](#桌面应用) |
[命令行](#命令行) |
[安装到相机](#安装到相机) |
[个性化设置](#个性化设置) |
[让拟合更接近](#让拟合更接近) |
[须知](#须知) |
[风险](#风险) |
[测试状态](#测试状态) |
[开发者信息](#开发者信息)

## 工作原理

GR IV 不能直接运行 LUT。它的风格由几项原生控制构成：色彩混合、色调曲线、对比度设置和 **分色相调整**（对 12 个色相范围分别改变颜色）。GR4-LUTSmith 会把你的 LUT **拟合** 到这些控制上，测量相机能达到多接近，然后才写入固件。

- **影调和整体色彩风格** 拟合得很好，包括胶片风格的曲线、对比度、褪色的黑色、偏暖或偏冷的色调，以及整体饱和度的变化。
- **单独移动某些色相的风格**（青橙色调、改变绿色或天空的胶片模拟等）使用 **分色相调整** 来拟合。它们比只用色彩混合时接近得多。强烈依赖颜色饱和程度的变化（例如只针对最鲜艳的红色）仍然只是近似，遇到这种情况时工具会告诉你。
- **Log 和特定相机的转换 LUT**（S-Log、V-Log 等）不受支持。请使用为普通（Rec.709 / sRGB）照片制作的“创意” LUT。

拟合结果用 **CIEDE2000** 来评判，这是衡量两种颜色看起来差异多大的标准指标。作为参考，**低于 1 时并排对比也难以看出**，2 左右是可见的细微差异。

| 结果 | 含义 |
| --- | --- |
| **良好**（good） | 平均差异低于 1，且 95 % 的颜色低于 2：看起来相同 |
| **近似**（approximate） | 平均低于 2：接近，部分颜色有可见差异 |
| **较差**（poor） | 相机无法再现 LUT 的全部色彩范围；只要 **日常色彩** 拟合良好，仍会写入固件（见[LUT 结果“较差”时](#lut-结果较差时)） |

每个 LUT 都会从三个方面测量：LUT 的整个色彩范围、**ColorChecker** 色卡上的 24 种日常颜色（肤色、天空、树叶等），以及 **中性灰**（任何偏色在这里最明显）。如果提供了你自己的照片（`--photo`），还会在这张照片上测量。

## 安装后的效果

安装后，**影像控制** 列表的末尾如下。下表及下文中的菜单名称（影像控制、标准、饱和度、色相除外）均按相机设为英语时的显示给出。

| 显示为 | 风格 | 照片 | 视频 |
| --- | --- | :---: | :---: |
| HDR Tone | （你现有的彩色风格） | ✓ | |
| 标准 | 黑白标准 | ✓ | ✓ |
| Solid | 黑白 Solid | ✓ | ✓ |
| Soft | 黑白 Soft | ✓ | |
| **High Contrast** | **你的 LUT 风格，彩色** | ✓ | ✓ |
| Grainy | 黑白 Grainy | ✓ | |
| HDR Tone | 黑白 HDR *（实验性）* | ✓ | |

- 你的风格使用 **High Contrast** 的名称和图标（第一个“HDR Tone”之后的第四项）。你也可以改选 **Cinema (Yellow)**、**Vivid** 或其他槽位，或者同时使用多个：见[选择槽位](#选择槽位)。它还可以显示[你自己的名称](#为槽位命名)和[你自己的图标](#自定义图标)。
- 打开时 **所有滑块均为 0**，锐度为标准值，**颗粒关闭**。你的 LUT 风格正是在这些设置下内置的；之后滑块照常工作，以你的风格为起点。
- GR IV Monochrome 的五种黑白风格也可以使用，与 GR4-MonoUnlock 相同。
- 你现有的所有风格保持不变。

## 开始之前

- **相机：** RICOH GR IV（标准彩色型号）。不支持其他型号。
- **相机必须已升级到固件 1.11。** 请在相机的设置菜单中查看版本。
  - 较旧版本：先用 RICOH 的官方文件按常规方式更新到 1.11。
  - 较新版本：**不要使用本工具。** 它只支持 1.11。
- **官方固件文件。** 从 RICOH IMAGING 官方的 GR IV 支持页面下载 **固件版本 1.11**。如有需要请解压，直到得到文件 **`fwdc248b.bin`**。
- **充满电的电池。** 固件更新过程中绝不能断电。
- **一张可以格式化的 SD 卡。**
- **你的 LUT**：`.cube` 文件（3D 或 1D），并知道它是为 **sRGB**（大多数 LUT）还是 **Adobe RGB** 制作的。
- **推荐：** 一张用你的 GR IV 拍摄的 DNG 照片。工具会用它在真实画面上检查风格，并生成预览。
- 记下你不想重新设置的自定义设置（C1、C2 等）。

然后用[桌面应用](#桌面应用)或[命令行](#命令行)制作你的固件。

## 桌面应用

### 下载

从[最新发布版本](../../releases/latest)下载适合你电脑的文件：

| 电脑 | 文件 |
| --- | --- |
| 搭载 Apple 芯片的 Mac（M1 或更新） | `GR4-LUTSmith-<version>-macOS-AppleSilicon.zip` |
| 搭载 Intel 处理器的 Mac | `GR4-LUTSmith-<version>-macOS-Intel.zip` |
| Windows 10 或 11（64 位） | `GR4-LUTSmith-<version>-Windows-x64.zip` |

需要 macOS 12（Monterey）或更高版本。不确定你的 Mac 是哪种？苹果菜单 → **关于本机**：显示“芯片 Apple M…”的是 Apple 芯片，显示“处理器 Intel”的是 Intel。

每个 zip 包含应用和一个 `Licences` 文件夹（构成应用的各组件的许可证）。

<details>
<summary><strong>确认文件来自本项目</strong>（可选）</summary>

<br>

每个 zip 都由本仓库自己在 GitHub 上的构建生成，构建会签署一份来源记录：仓库、构建以及代码的确切版本。你可以用 [GitHub CLI](https://cli.github.com)（已通过 `gh auth login` 登录）确认你下载的正是该文件，且未被修改或替换：

```sh
gh attestation verify GR4-LUTSmith-2.1.1-macOS-AppleSilicon.zip --repo lemonadesaltbagel/GR4-LUTSmith
```

（请换成你下载的 zip 的文件名；在 Windows 上，请在 PowerShell 中从“下载”文件夹运行。）最后会显示“Verification succeeded!”，并给出生成该文件的构建。出现任何其他结果都意味着：不要打开它，请从发布页面重新下载。仓库的 **Attestations** 页面列出了每个已签署的文件。

更快地确认下载是否完整：发布页面的 `SHA256SUMS` 列出了每个文件的 SHA-256。

- macOS（终端）：`shasum -a 256 ~/Downloads/GR4-LUTSmith-*.zip`
- Windows（PowerShell）：`Get-FileHash $HOME\Downloads\GR4-LUTSmith-*.zip -Algorithm SHA256`

这只能说明文件完整送达，不能说明是谁制作的：`SHA256SUMS` 和 zip 位于同一页面。

你也可以完全不下载：从源代码运行应用（见[开发者信息](#开发者信息)），或用[命令行](#命令行)制作固件。应用和命令行生成的 `fwdc248b.bin` 完全相同，而 `uv run gr4_lutsmith.py check fwdc248b.bin` 可以显示任何固件文件包含的内容。

</details>

### 首次打开

本应用免费，没有使用付费的 Apple 或 Microsoft 证书签名，因此你的电脑会询问一次是否信任它。

**macOS**

1. 解压文件，把 **GR4-LUTSmith** 移到“应用程序”文件夹。
2. 打开它。macOS 会提示无法检查该应用是否包含恶意软件；选择 **完成**（macOS 15）或 **取消**。
3. 打开 **系统设置 → 隐私与安全性**，向下滚动到关于 GR4-LUTSmith 的提示，选择 **仍要打开**，然后输入密码确认。
   在 macOS 12 至 14 上，也可以按住 Control 键点按应用，选择 **打开**，然后再选择一次 **打开**。

此后即可正常打开。

**Windows**

1. 右键点击 zip → **全部解压缩…**，然后打开解压出来的 **GR4-LUTSmith** 文件夹（不要在 zip 内直接运行）。
2. 打开 **GR4-LUTSmith.exe**。如果 Windows 显示“Windows 已保护你的电脑”，选择 **更多信息 → 仍要运行**。

请保持整个文件夹完整：应用需要旁边的 `_internal` 文件夹。

### 使用

应用会在屏幕上引导你完成各个步骤：相机的固件文件、LUT（以及可选的 DNG）、槽位及其名称和图标、拟合，以及生成。它会把 `fwdc248b.bin` 保存到你选择的位置；然后[安装到相机](#安装到相机)。

- **语言：** 应用跟随电脑的语言，可在窗口顶部更改。它也是检查槽位名称时所依据的相机语言（见[为槽位命名](#为槽位命名)）。
- **外观：** 在窗口顶部选择“跟随系统”“日间”或“夜间”。
- **检查固件文件**（左侧）会告诉你某个 `fwdc248b.bin` 是 RICOH 的官方文件、由 GR4-LUTSmith 制作（以及包含哪些风格），还是其他文件。
- 别人共享的风格（`.json`）也可以在应用中使用：在第一页选择“共享风格（.json）”。
- **同时运行多轮：** 在“拟合”页面，选择“轮数”以及“同时运行”的数量（每轮使用一个处理器核心；见[更多轮次](#更多轮次)）。每轮都会显示进度；运行中可以添加轮次，“全部停止”会保留已完成的轮次。各轮完成后，结果会陆续加入表格。

### 出现问题时

- **macOS 提示应用已损坏**：请重新下载（文件不完整），并按[确认文件来自本项目](#下载)中的方法检查。
- **应用在 Windows 上无法启动**：确认你已解压整个 zip，并从解压出来的文件夹运行 `GR4-LUTSmith.exe`。
- **固件文件被拒绝**：应用只接受 RICOH 未经修改的 GR IV 1.11 `fwdc248b.bin`。已被 GR4-LUTSmith 修改过的文件不能再次修改；请从未经修改的文件开始。

## 命令行

### 1. 准备

安装 **[uv](https://docs.astral.sh/uv/)**（它会安装 Python 以及工具所需的其他一切），在此文件夹中打开终端并运行：

```sh
uv sync --extra photo
```

<details>
<summary>不使用 uv</summary>

<br>

使用 Python 3.9 或更高版本：

```sh
python3 -m pip install numpy rawpy pillow
python3 gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

`rawpy` 和 `pillow` 仅在使用 `--photo` 和 `preview` 时需要。

</details>

### 2. 制作固件

请换成你自己的路径：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG
```

| 选项 | 作用 |
| --- | --- |
| `--space adobe` | LUT 是为 Adobe RGB 制作的 |
| `--photo R0001234.DNG` | 同时在你的照片上检查风格（可选，但推荐） |
| `--slot vivid`、`--slot cinema-yellow`、… | 把你的风格放在其他风格的位置，而不是 High Contrast：[选择槽位](#选择槽位) |
| `--name "My Look"` | 让槽位显示你自己的名称：[为槽位命名](#为槽位命名) |
| `--icon my_icon.png` | 为槽位设置你自己的菜单图标：[自定义图标](#自定义图标) |
| `--turns 3` | 运行三次拟合，并保留最好的结果：[更多轮次](#更多轮次) |
| `--jobs 3` | 最多同时运行其中三轮：[更多轮次](#更多轮次) |
| `--after-curves` | 另外尝试第二个色彩混合：[曲线后色彩调整](#曲线后色彩调整) |

工具会：

1. 确认你提供的是真正的官方 1.11 文件；
2. 拟合 LUT（需要几分钟，分色相调整另需一两分钟），并显示拟合程度；
3. 生成固件并进行检查。

顺利的运行会这样结束：

```
  result: GOOD  (ΔE00 0.6, p95 1.42; without the look 2.09)
  on your photo: ΔE00 1.22 (without the look 2.55)
  ...
wrote output/my_look/fwdc248b.bin  (SHA-256 …)
Copy this file to the root of the SD card and run the camera's firmware update.
Then choose High Contrast in Image Control: your look is there.
```

工具还会在开始时说明你的风格放在哪个槽位，例如 `slot: High Contrast (replaces the hidden monochrome High Contrast look)`。

输出文件夹 `output/my_look/` 中还有 `look.json`（拟合所得的风格），也可以存放预览（第 3 步）。你可以把 `look.json` 分享给其他 GR IV 用户：他们无需重新拟合即可生成同样的风格（见[使用别人共享的风格](#使用别人共享的风格)）。

如果 LUT 无法很好地再现，或者固件文件不是官方 1.11，工具会显示 `refused: …`，并且 **不写入固件**。

### 3. 预览（可选）

```sh
uv run gr4_lutsmith.py preview output/my_look/look.json R0001234.DNG
```

这会生成 `output/my_look/preview.jpg`，包含三个画面：未应用风格的相机效果、LUT 本身，以及 **应用风格后** 的相机效果。LUT 画面需要 `.cube` 文件：工具会在 `look.json` 旁边或当前文件夹中查找，也可以用 `--lut my_look.cube` 指定；没有它时，预览只显示另外两个画面。需要比较的是色彩和影调。锐化和噪点不做模拟。

然后[安装到相机](#安装到相机)。

## 安装到相机

应用和命令行生成的固件，安装方法相同。

### 1. 复制到 SD 卡

1. **在相机中格式化 SD 卡。**
2. 把 **`fwdc248b.bin`**（命令行生成的位于 `output/my_look/fwdc248b.bin`）复制到存储卡的 **根目录**：不要放进文件夹，文件名必须保持为 `fwdc248b.bin`。

### 2. 更新相机

1. 装入充满电的电池和 SD 卡。
2. 按照 RICOH 官方 GR IV 固件更新说明，从相机的设置菜单启动固件更新。
3. **相机会显示从版本 1.11 更新到版本 1.11。** 这是正常的：修改后的固件保留了版本号。请确认更新。

> [!CAUTION]
> **在更新完成且相机重新启动之前，不要关闭相机、不要打开电池仓盖或存储卡盖，也不要取出存储卡。**

### 3. 拍摄

- 打开 **影像控制**，选择 **High Contrast**（在第一个“HDR Tone”之后）。它现在是彩色的。如果你选择了其他槽位，请改选那一项。
- 固件版本仍显示 **1.11**。这是正常的。
- 从存储卡中删除 `fwdc248b.bin`（或格式化存储卡），以免意外再次启动更新。

以后若要换成其他 LUT，请用 **官方** 文件制作新的固件，并以同样的方式安装。

### 恢复官方固件

改用 RICOH 的 **官方** `fwdc248b.bin`，重复第 1–2 步。相机同样会显示 **1.11 → 1.11**；确认后，相机即恢复为原厂状态。

## 个性化设置

你的风格放在哪里、叫什么名字、在菜单中是什么样子。在应用中，这些位于槽位步骤；在命令行中，它们是 `make` 和 `build` 的选项。

### 选择槽位

你的风格会替换相机的某一个风格。用 `--slot`（`make` 和 `build`）选择替换哪一个；`uv run gr4_lutsmith.py slots` 会在终端中显示同样的列表：

| `--slot` | 显示为 | 替换 | 照片 | 视频 | 额外滑块 |
| --- | --- | --- | :---: | :---: | --- |
| `high-contrast`（默认） | High Contrast | 隐藏的黑白风格“High Contrast” | ✓ | ✓ | — |
| `cinema-yellow` | Cinema (Yellow) | RICOH 的“Cinema (Yellow)”风格 | ✓ | ✓ | 饱和度、色相 |
| `cinema-green` | Cinema (Green) | RICOH 的“Cinema (Green)”风格 | ✓ | ✓ | 饱和度、色相 |
| `vivid` | Vivid | RICOH 的“Vivid”风格 | ✓ | ✓ | 饱和度、色相 |
| `positive-film` | Positive Film | RICOH 的“Positive Film”风格 | ✓ | ✓ | 饱和度、色相 |
| `negative-film` | Negative Film | RICOH 的“Negative Film”风格 | ✓ | ✓ | 饱和度、色相 |
| `bleach-bypass` | Bleach Bypass | RICOH 的“Bleach Bypass”风格 | ✓ | ✓ | 饱和度、色相 |
| `retro` | Retro | RICOH 的“Retro”风格 | ✓ | ✓ | 饱和度、色相 |
| `soft-monotone` | Soft Monotone | RICOH 的“Soft Monotone”风格 | ✓ | | — |
| `hard-monotone` | Hard Monotone | RICOH 的“Hard Monotone”风格 | ✓ | ✓ | — |
| `hi-contrast-bw` | Hi-Contrast B&W | RICOH 的“Hi-Contrast B&W”风格 | ✓ | ✓ | — |
| `mono-standard` | 标准（第二个） | 隐藏的黑白风格“标准” | ✓ | ✓ | — |
| `mono-soft` | Soft | 隐藏的黑白风格“Soft” | ✓ | | — |
| `mono-solid` | Solid | 隐藏的黑白风格“Solid” | ✓ | ✓ | — |

- 每个槽位的色彩都一样：相机在这些槽位中以同样的方式处理你的风格，因此拟合及其评分不会随槽位而变化。
- 在每个槽位中，你的风格打开时所有滑块均为 0，颗粒关闭。
- 随槽位变化的只有你失去哪一项，以及得到哪些滑块。在黑白槽位上，你的风格是彩色的；那里不提供饱和度和色相。
- **Cinema：** 其 Color Tone 设置对你的风格不起作用。**Bleach Bypass：** 其色调设置不会改变你的风格。**Retro：** Retro 自带的调色效果和类似暗角的影调效果会被移除，因此你得到的只有你的风格。
- 你未使用的槽位保留 RICOH 的风格。如果 High Contrast 上没有放风格，它仍然是黑白的 High Contrast 风格。
- **不可用：** 标准、Monotone、HDR Tone、Cross Processing，以及隐藏的 Grainy 和 HDR 风格。它们与其他风格共用部分处理，或使用会改变你的色彩的特殊处理。
- `check` 会列出哪些槽位带有个人风格。

### 一个固件中放入多个风格

用 `fit` 分别拟合每个 LUT，然后把它们一起生成，每个风格文件后面紧跟它自己的 `--slot`（如有需要，还有 `--name`、`--icon`）：

```sh
uv run gr4_lutsmith.py fit look_a.cube --photo R0001234.DNG -o output/a
uv run gr4_lutsmith.py fit look_b.cube --photo R0001234.DNG -o output/b
uv run gr4_lutsmith.py build output/a/look.json --slot cinema-yellow output/b/look.json --slot vivid --name "Look B" ~/Downloads/fwdc248b.bin -o output/both
```

**一次能放多少个：** High Contrast 和两个 Cinema 槽位始终能容纳完整的风格。其他槽位共用有限的空间：每个风格都需要空间存放色调曲线，分色相调整和曲线后色彩调整则需要多得多的空间。简单的风格（一条色调曲线）最多可同时放在其中 10 个槽位上；带分色相调整的风格能放的要少得多。如果放不下，工具会告知并且不写入任何内容；请减少槽位或使用更简单的风格，并让 High Contrast 空着，以获得最多的空间。

### 为槽位命名

`--name`（`make` 和 `build`）为槽位设置你自己的名称，显示在影像控制菜单及其相关画面中，适用于相机的所有语言：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra"
```

- 每个槽位接受的名称有长度上限：`uv run gr4_lutsmith.py slots` 会显示（从 Retro 的 9 个字符到 Cinema (Yellow) 的 23 个字符）。第二个黑白标准无法重命名，因为它与彩色“标准”风格共用名称。
- **纯 ASCII**（英文字母、数字、空格和标点）在相机的所有语言中都能显示。这是稳妥的选择。
- **其他字母和字符** 可在使用它们的相机语言中显示：日文名称在相机设为日语时显示，`Müller` 在欧洲语言中显示，`Плёнка` 在俄语中显示，依此类推。相机的任何语言都不使用的字符（表情符号、阿拉伯文、希伯来文等）会被拒绝。
- 工具会按你的 **相机语言** 检查名称；除非你设置了 `--camera-language`（例如 `--camera-language Japanese`；`--help` 会列出全部 21 种），否则相机语言就是你电脑的语言。如果名称使用了该语言不使用的字符，工具会警告这些字符可能无法显示，并询问是否仍要使用该名称。输入 `y` 继续，或添加 `--accept-name` 预先同意（当工具无法询问时需要，例如在脚本中）。如果以后把相机切换到其他语言，非 ASCII 的名称在那里可能无法显示。
- 较长的名称在某些画面上可能会被截断（中文、日文和韩文字符约占英文字母的两倍宽度）。
- 不使用 `--name` 时，槽位保留原来的名称。名称不会保存在 `look.json` 中（该文件只保存风格）：在 `build` 时请再次提供 `--name`。`check` 会显示已生成固件中的名称。

### 自定义图标

`--icon`（`make` 和 `build`）用你自己的图片替换槽位在影像控制菜单中的图标：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- 任何图片都可以（PNG、JPEG 等）。菜单图标为 40×40 像素：更大或更小的图片会被缩放；如果不是正方形，则使用其 **中间部分**。透明部分保持透明，因此透明背景的 PNG 看起来就像相机自带的图标。
- `make` 会把结果保存为固件旁边的 `icon.png`，让你确切看到相机将显示的样子。在这么小的尺寸下，简单、醒目的图形最易辨认。
- 除第二个黑白标准外，每个槽位都可以使用自定义图标（那个槽位与彩色“标准”风格共用图标）。`slots` 会列出这些槽位。
- 需要 Pillow（`uv sync --extra photo`）。不使用 `--icon` 时，槽位保留原来的图标。图标不会保存在 `look.json` 中：在 `build` 时请再次提供 `--icon`。`check` 会显示哪些槽位有自定义图标。

### 使用别人共享的风格

`look.json` 只保存风格本身：它的色彩设置，以及与 LUT 的拟合程度。不包含槽位、名称或图标的任何信息，也不包含你电脑上的文件夹（只有 LUT 的文件名）。拿到该文件的人无需 LUT、无需拟合即可直接生成固件，并且在槽位、名称和图标相同时，得到与制作者逐字节相同的固件。

在应用中，在第一页选择“共享风格（.json）”。在命令行中，文件名可以任意，因此分享前可以随意重命名（`portra-400.json` 等）：

```sh
uv run gr4_lutsmith.py build portra-400.json ~/Downloads/fwdc248b.bin --slot vivid --name "Portra" --icon portra.png
```

- 工具会先显示该风格与其 LUT 的拟合程度（即制作者当时看到的结果；“on your photo”指的是制作者的照片）。
- 槽位、名称和图标由你选择，见[选择槽位](#选择槽位)、[为槽位命名](#为槽位命名)和[自定义图标](#自定义图标)。不使用 `--slot` 时，风格会放在 High Contrast 上。
- 多个风格：在每个文件后面紧跟着写上它自己的 `--slot`、`--name` 和 `--icon`：

  ```sh
  uv run gr4_lutsmith.py build portra-400.json --slot vivid --name "Portra" tri-x.json --slot hard-monotone ~/Downloads/fwdc248b.bin -o output/both
  ```

- 生成之前会先检查文件内容：损坏的文件，或含有相机无法接受的值的文件，会被拒绝，且不写入任何内容。
- 1.7.0 之前的版本制作的文件可能还包含槽位、名称、图标以及 LUT 的完整路径。`build` 会忽略槽位、名称和图标（并说明它们原来是什么）；分享这类文件之前，请用文本编辑器打开并检查 `"file"`。

## 让拟合更接近

每次拟合都会尝试分色相调整。如果想要更接近，先运行更多轮次，再尝试曲线后色彩调整（见[哪种帮助更大](#哪种帮助更大)）。

### 分色相调整

在拟合色彩混合和色调曲线之后，工具会尝试用 **分色相调整** 改进风格：相机可以在 12 个色相范围内分别改变颜色。只有在 **明显有帮助**（整个色彩范围或 ColorChecker 至少改善 10 %）**且没有任何一项变差**（你的照片、灰色、ColorChecker）时才会保留。结果行会显示 `hue sectors: yes` 或 `no`。

- 分色相调整从不改变灰色，相邻的色相区间总是无缝衔接，因此颜色从一个色相到下一个色相保持平滑过渡。
- 使用 `--photo` 时，分色相调整也会针对真实画面进行调校（推荐）。
- `--no-hue` 可将其关闭（`make` 和 `fit`）。

### 更多轮次

拟合从一个起点出发，再从那里逐步改进。相机只有几项色彩控制，因此 **拟合从哪里开始往往决定了它能有多接近**。使用 `--turns`（在应用中：在“拟合”页面）时，工具会运行多次拟合（“轮”），每轮从新的随机起点开始，并保留好的结果：

```sh
uv run gr4_lutsmith.py make my_look.cube ~/Downloads/fwdc248b.bin --photo R0001234.DNG --turns 3
```

- 第 1 轮始终使用常规起点，因此只运行一轮（默认）时，结果与以前相同。之后每一轮都会抽取新的随机起点。
- 每轮所需时间与一次普通拟合相同（几分钟）。
- **并行运行。** `--jobs 3` 最多同时运行三轮，每轮使用一个处理器核心，约需 0.8 GB 内存。请至少留一个核心给电脑的其他工作。结果与逐轮依次运行完全相同，只是更快得到。
- **保留的结果。** 新结果会被保留，除非某个较早的结果在每项指标（整个范围、ColorChecker、灰色和你的照片）上都至少同样好。被新结果在每项指标上都超越的较早结果会移出列表。因此，每个保留的结果都至少在一项指标上优于其他所有结果；工具会把它们并排显示，并推荐总体评分最好的那个（拟合所用全部内容上的平均差异）。
- **最后追加轮次。** 结果出来后，工具会询问 `More turns?`。输入数字即可再运行相应的轮数，方式与本次运行开始时相同（`2`）；加上 `a` 表示带[曲线后色彩调整](#曲线后色彩调整)的轮次（`2a`），加上 `b` 表示不带的轮次（`2b`），无论本次运行以哪种方式开始。新轮次会与所有保留的结果比较。按 Enter 键则保留现有结果。
- **重复某一轮。** 每轮的种子都会显示并保存在 `turns.json` 中；`--seed 1234` 会再次运行同一轮（配合 `--turns 3`：种子为 1234、1235、1236）。

有多个保留的结果时，输出文件夹如下：

```
output/my_look/look.json, fwdc248b.bin      the recommended result
output/my_look/turns/turn-1/                 every kept result, each with its
output/my_look/turns/turn-3-after-curves/    own look.json (and, with make, fwdc248b.bin)
output/my_look/turns.json                    every turn, its seed and its scores
```

要使用另一个保留的结果，请改为把它的 `fwdc248b.bin` 复制到 SD 卡。

### 曲线后色彩调整

使用 `--after-curves`（`make` 和 `fit`）时，工具还会尝试第二个色彩混合，由相机在色调曲线 **之后** 应用。许多胶片风格在暗部和亮部对颜色的改变各不相同。常规的色彩混合作用于曲线之前，无法做到这一点，而曲线之后的混合往往可以。

LUT 的整个色彩范围与真实照片并不总是一致：某个版本可能在饱和色上接近得多，而在日常照片上稍差一些。因此两个版本都会进入[更多轮次](#更多轮次)中所述的保留结果列表：只要曲线后色彩调整版本在任何一项（整个范围、ColorChecker、灰色或你的照片）上更好，就会与常规版本一起保留，由你来选择。选择之前，请在你自己的照片上预览两者。

**为什么是可选的。** 常规拟合多运行几轮，效果提升更大（见[哪种帮助更大](#哪种帮助更大)）。曲线后的混合平均而言有帮助，但会让每轮多花几分钟。

- 灰色保持为灰色：该混合绝不会给中性灰添加偏色。
- 拟合需要多花几分钟（额外四次拟合）。

<details>
<summary>24 个 LUT 的结果</summary>

<br>

在我们对 24 个 LUT 的测试中（每个一轮），常规版本与之前完全相同，其中 23 个 LUT 得到了第二个版本：

- **8 个在所有变化项上都更好**：与 LUT 的平均差异从 3.7 降至 2.4（ColorChecker 1.9 → 1.1，照片 0.91 → 0.75）；
- **15 个有取舍**。彩色胶片风格通常在整个范围和 ColorChecker 上接近得多（例如 3.6 → 2.5），照片则略差（最多差 0.17）；黑白风格通常在灰色和照片上接近得多，但在整个范围上差得更多；
- 两个之前被拒绝的 LUT 现在可以生成了。

</details>

### 哪种帮助更大

在拟合时间相同的测试中，常规拟合四轮中最好的一轮继续拟合后，在每一步都胜过带[曲线后色彩调整](#曲线后色彩调整)的拟合。在两者各十轮随机轮次中，曲线后色彩调整版本平均而言更好。所以两者都有帮助，但 **常规拟合多运行几轮的提升更大**：如果有时间，先多运行几轮；想同时比较那个版本时，再加上 `--after-curves`。

### LUT 结果“较差”时

许多胶片模拟 LUT 对高饱和颜色的改变方式是相机的控制无法跟上的，因此尽管日常照片看起来没问题，它们在整个色彩范围上仍是“较差”。在以下情况下仍会写入固件：

- **ColorChecker** 颜色的平均差异小于 2，**灰色** 的平均差异小于 2，且没有灰色出现可见的偏色；并且使用 `--photo` 时，风格在你的照片上不是“较差”；或者
- 使用 `--photo` 时，风格 **在你的照片上为“良好”**（并且至少把那里的差异减半），且满足同样的灰色和偏色限制。

工具会说明适用的是哪条规则。否则不会写入固件；添加 `--force` 可强制生成，但请先检查预览。

## 须知

- **滑块**（Key、Contrast、Highlight、Shadow、Sharpness、Shading、Clarity、Toning、Grain）在你的风格基础上起作用；全部为 0 时得到的就是 LUT 的效果。High Contrast 不提供饱和度和色相；Cinema 槽位提供（见[选择槽位](#选择槽位)）。
- **两个“标准”和两个“HDR Tone”项目。** 黑白标准和黑白 HDR 风格使用与彩色风格相同的名称和图标。
- **RICOH 官方更新会移除你的风格。** 它会替换整个固件。
- **仅适用于标准版 GR IV。** 切勿在其他型号上安装该文件。
- **送修相机之前，** 请恢复官方固件。
- **先多试几个 LUT：** `uv run gr4_lutsmith.py fit my_look.cube --photo R0001234.DNG` 会拟合并报告结果，无需固件文件。

### 检查固件文件

将任何固件文件复制到存储卡之前（在应用中：左侧的 **检查固件文件**）：

```sh
uv run gr4_lutsmith.py check path/to/fwdc248b.bin
```

它会告诉你该文件是官方 1.11、GR4-LUTSmith 固件，还是其他文件。对于 GR4-LUTSmith 固件，它还会列出哪些槽位带有风格、它们的名称和图标，以及这些风格是否使用了分色相调整和曲线后的色彩混合。

要用你的官方文件检查工具本身：

```sh
uv run gr4_lutsmith.py selftest ~/Downloads/fwdc248b.bin
```

这会用附带的示例（`examples/film-1d.cube`）生成固件，并将结果与经过测试的版本比较。它会显示 `selftest: PASSED`。

## 风险

- 相机无法区分完好的固件文件和损坏的文件。只把工具写出的（或经 `check` 确认的）文件复制到存储卡。
- 如果更新被中断，或固件文件无法启动，相机可能无法再进入更新功能，届时就需要 RICOH 维修。测试中没有发生过这种情况，但不能排除。
- 相机自身的校准数据不会被改动。

## 测试状态

| 项目 | 状态 |
| --- | --- |
| 带有自己色调曲线的个人 LUT 风格，在此槽位上，用于拍照、视频、取景器和 RAW Development | 已在 GR IV 1.11 上测试 |
| 更新被接受；恢复官方 1.11 可使相机完全复原 | 已在 GR IV 1.11 上测试 |
| 五种黑白风格 | 已在 GR IV 1.11 上测试（见 GR4-MonoUnlock） |
| 保留槽位自身的“High Contrast”名称和图标 | 名称和图标是 RICOH 原有的，未作改动；这一确切组合尚未安装过 |
| 滑块打开时为 0（颗粒关闭） | 由与已测试版本相同的更改构成（是其中的一部分）；尚未单独安装过 |
| 需要两条或三条色调曲线的风格（偏色、调色风格） | 三条曲线已在 GR IV 1.11 上测试 |
| 分色相调整 | 已在 GR IV 1.11 的 RAW Development 中用一个胶片模拟 LUT 测试（ISO 200，以绿色和黄色为主的日光场景）：相机与工具的预测一致，有色区域与 LUT 的差异降低约 30 %，颜色之间没有可见的断层。红色、蓝色、紫色和更高 ISO 尚未在相机上检查 |
| 曲线后色彩调整（`--after-curves`，可选） | 
| Cinema (Yellow) / Cinema (Green) 槽位上的风格 | 已在 GR IV 1.11 上测试：可用 |
| 其他槽位上的风格（Vivid、Positive Film、Negative Film、Bleach Bypass、Retro、黑白槽位） | 已在 GR IV 1.11 上测试：可用 |
| 槽位的自定义名称（`--name`） | 已在 GR IV 1.11 上测试：可用 |
| 槽位的自定义图标（`--icon`） | 已在 GR IV 1.11 上测试：可用 |
| 用共享的 `look.json` 生成 | 已离线检查：固件与使用相同 LUT 结果、槽位、名称和图标的 `make` 逐字节相同；没有新的内容进入相机 |
| 应用（`GR4-LUTSmith`）生成与命令行相同的固件 | 已离线检查：相同的 LUT、照片和选择下逐字节相同 |
| 并行运行轮次（`--jobs`，应用中的“同时运行”） | 已离线检查：结果与依次运行相同轮次时逐字节相同 |
| 工具能精确再现经过测试的示例 | 已测试（`selftest`） |

## 开发者信息

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

- 从源代码运行应用：`uv sync --extra app`，然后 `uv run python -m lutsmith_app`。
- 构建应用：`uv run python packaging/build.py`（在搭载 Apple 芯片的 Mac 上，添加 `--arch x86_64` 可构建 Intel 版本）；zip 会生成在 `dist/` 中。

| 文件 | SHA-256 |
| --- | --- |
| RICOH GR IV 官方 1.11 `fwdc248b.bin` | `a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f` |
| 示例固件（`selftest`，来自 `examples/film-1d.look.json`） | `d201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052` |
