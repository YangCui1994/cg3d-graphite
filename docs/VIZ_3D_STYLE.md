# 3D 可视化规范（viz3d.py）

适用：`LBM/source_code/taichi_LBM3D/2phase/` 下所有 3D 算例（P 线 granular、R 线 Berea/BIL）的
出图。建立于 2026-09-13。渲染层是 `2phase/viz3d.py`。

## 1. 决策与理由

**渲染引擎 = PyVista（Python 脚本，无头渲染）。不用 pvpython 驱动 ParaView，也不用回 matplotlib。**

- 走 ParaView 的代价是第二套 Python 解释器 + 一套完全不同的 API（`2phase/post3d.py` 会被 4 个
  validation 脚本 import，重写它风险高），本机 ParaView 也未安装。PyVista 就是在 `lbm` 环境里
  `import pyvista`，直接吃现有 numpy 数组，可批处理、可复现。
- 回 matplotlib 不行：`Poly3DCollection` 用画家算法排序，多个半透明面必然 z 序错乱，也没有环境光遮蔽。
  这是旧渲染器 `vis3d_report.py` 看着"平"的原因。
- ParaView 仍然保留为**人的眼睛**：`pyevtk.hl.gridToVTK` 写出的 `.vtr` 用 ParaView 双击就能看，
  但它不参与出图流水线。

**后处理不碰 Taichi**：viz3d 只读 `.npz`，是普通 numpy/PyVista 进程，因此**没有 JIT 编译税**，
也不占 16 GB 显存。但必须等 GPU batch 退出后再跑，不要在长跑中渲染。

## 2. 用法

```
cd LBM/source_code/taichi_LBM3D/2phase
python viz3d.py figset   --run results_pcs_cg3d/p3b_finney          # 标准 5 图
python viz3d.py figset   --run results_pcs_cg3d/p4_siA --style slide
python viz3d.py selfcheck --run results_pcs_cg3d/p3b_finney         # 断言，非 0 退出即有问题
python viz3d.py geometry --run <run> [--full] [--cutaway 0.5]
python viz3d.py cutaway  --run <run> --focus nw|wet [--level L]
python viz3d.py clusters --run <run> --top 12
python viz3d.py slices   --run <run>
python viz3d.py animate  --series <frames-dir> --out <dir> --style slide   # GIF
python viz3d.py explore  --series <frames-dir>                              # 交互窗口
```

默认输出目录 `results_p5_figs_pv3d/<tag>/`；`--out` 只接受**目录**（文件名固定）。
`--full` 显示 wall + reservoir 薄片（默认裁掉）；`--cutaway f` 保留 x 方向前 f 段。

## 3. 硬规则

1. **同一视图最多一个半透明相。** 200³ 随机球堆积即使 alpha=0.18 也会把内部糊死。默认只有固相
   幽灵（alpha 0.16/0.20）是半透明的，焦点相不透明；固相与流体**裁掉同一个切面**（"看进一个打开的盒子"）。
2. **一律正交投影**（`enable_parallel_projection`）。透视会让远处 cluster 显得小，跨算例比较 cluster
   尺寸/CCDF 时会系统性失真。
3. **相机由域框（BBox）导出，不由数据导出**：先加 wireframe 域框再 `reset_camera()`。同一几何的所有
   run 因此得到完全相同的视角（p3b_finney 与 p4_siA 的 p0_geo 输出逐像素统计完全一致，见 §6）。
   方向固定 `CAM_ELEV=18°, CAM_AZIM=-55°`（沿用旧 matplotlib 视角）。
4. **轴序**：npz 存 `(nx,ny,nz)`，VTK `ImageData` 点序 x 最快 → 必须 `dimensions=a.shape` +
   `a.ravel(order='F')`。搞错就是几何转置/镜像且不报错。`selfcheck` 第 1 项专门断言这个。
5. **>256³ 先降采样再 contour**（`--cutaway` / stride），**永不 upsample**。200³ 直接 contour 没问题
   （见 §6 耗时）。
6. **界面处理**：CG 是弥散界面，用"掩膜连续场"技巧——把固相体素设成 ±1 再对 psi 取 0 等值面，
   得到亚体素光滑、且精确贴着颗粒壁的面；直接对二值指示场取 0.5 等值面会得到台阶状表面。
   - 非润湿相：`mask_value=-1`（面停在颗粒壁外）
   - 润湿相：`mask_value=+1`（面顺着颗粒壁走，因为润湿相确实接触固相）
7. **曲线图（Pc–S、k、CCDF、I–R）继续用 matplotlib 2D**，不要交给 3D 引擎。
8. 不在 GPU 长跑中渲染；帧与体数据不进对话上下文（沿用 `PLAN_3d` §10.2 的有界输出纪律）。

## 4. 配色

气相/非润湿相**不要用纯白**：白是纸面底色，会被读成"空缺/域外"；而这个项目的主角恰恰是困气
（H 线主结果），把主角画成白色方向反了。白气只在深色底下成立，所以做成 `slide` 风格。

单位：L 为灰度亮度（PIL `convert('L')`，即黑白打印看到的值）。

| 元素 | `report`（白页 PDF，默认） | `slide`（深底幻灯片） |
|---|---|---|
| 背景 | white (L=1.00) | `#1b1b1b` (L=0.11) |
| 固相（几何图，不透明） | `#b0b0b0` (L=0.69) | `#8a8a8f` (L=0.55) |
| 固相幽灵（半透明） | `#8a8a8f` @ 0.16 → 合成 L=0.93 | `#8a8a8f` @ 0.20 → 合成 L=0.19 |
| 液相/润湿相 | `#2166ac` (L=0.35) | `#2f7fd0` (L=0.44) |
| 气相/非润湿相 | `#e08214` 琥珀 (L=0.57) | `#f5f5f5` 白 (L=0.96) |
| 小簇 overflow | `#7f7f7f` @ 0.9 → L=0.55 | `#9a9a9a` @ 0.9 → L=0.55 |
| psi 切片色带 | `#2166ac → #f2f2f2 → #e08214` | `#2f7fd0 → #2b2b2b → #f5f5f5` |

**为什么非润湿相是琥珀而不是 2D 报告的暗红**：`#2166ac` 与 `#b2182b` 的灰度差只有 **ΔL=0.067**，
而 3D 旧 demo 用的 `#d62728` 与蓝色差 **ΔL=0.008** —— 黑白打印下液相和气相是同一个灰。琥珀保持
暖色家族，ΔL=0.224。这是"气相该亮一点"这个直觉的硬证据。

**簇配色的保留色规则**：报告风格保留蓝（液相）与琥珀（气相），所以调度色板把绿/品红/棕排前面，
蓝/橙排到第 7 位之后——4 个簇的图不能一上来就是一个"像液体"的蓝团。色板内**不含灰色**
（灰是固相/幽灵/overflow 的专用色）。

**镜面高光与"太亮"**：材质取哑光（`specular=0.08, specular_power=30`）。但要如实说明——实测这个
旋钮从 0 到 0.6 只改变全图平均亮度 2.2 个灰阶，所以它**不是**"图像发白"的原因，别把它当修复。
白页风格下画面偏亮的主因是固相幽灵（alpha 0.16 合成后 L=0.93）铺满画面。要压这个用
`--ghost-alpha 0.5`（乘数），不要动流体颜色。

## 5. 图版布局（`figset` 的 6 张）

| 面板 | 内容 | 引擎 |
|---|---|---|
| `p0_geo` | 球堆积几何，不透明，域框 + 标尺 | PyVista |
| `p1_slices` | 三正交 mid-slice（psi）+ 颗粒轮廓线 | matplotlib（见 §7 的色彩口径） |
| `p2_twophase` | **两相同框**：多数相玻璃、少数相不透明 + 固相幽灵 | PyVista |
| `p3_nonwetting` | 裁剪视图，只看非润湿相（psi>0），不透明 | PyVista |
| `p4_wetting` | 裁剪视图，只看润湿残余（psi<0），不透明 | PyVista |
| `p5_clusters` | 困气簇逐簇配色 + 按体积排序图例，过小的簇用中性灰 | PyVista |

`p2_twophase` 排在单相面板前面是刻意的：它回答"气相相对液相在哪儿"，单相图只有在读者已经看过两相之后才有意义。

### 5.1 两相同框的规则（`focus='both'`）

**多数相做玻璃（alpha 0.30），少数相不透明。** 依据是体积占比自动判定，逐算例翻转：

- 注液终态（p4_siA，非润湿占孔隙 8.2%）→ 气相不透明、液相玻璃
- 排驱终态（p3b_finney，非润湿占孔隙 73.3%）→ 润湿残余不透明、气相玻璃

这条规则的来由是一个**设计错误**，记在这里防止重犯：第一版让两相都不透明同框，结果占 84% 孔隙的润湿相把困气团**整个包在里面挡住**——色相统计只有 3% 暖色，而气相的体积占比是 8.2%，即被遮挡了一半以上。改成"多数相玻璃"后变为 11% ≥ 体积占比，少数相不再被挡。当两相都在场时，固相幽灵的 alpha 再乘 0.6，保证"眼睛能解析的那层玻璃"是流体。

两相在 `psi=0` 处严格相接（面重合）。VTK 默认的 coincident-topology 处理能应付；若共享界面出现斑点，用 `--level-gap 0.3` 给两相各让出一点。

### 5.2 单相面板的固有缺陷（为什么必须有 p2_twophase）

单相面板里**另一相完全没有被渲染，那片白色背景"就是"另一相**。这正是 §4 里批评"气相用白色会被读成空缺"的同一个毛病。所以 p3/p4 只用于"单独讲一相"的论证场合，不能用来回答"气液分布"。

## 6. 实测（200³，RTX 5080 机器，`lbm` 环境）

- 5 图全跑 **21.8 s**；几何单图 3.7 s；固相等值面 **796k 点 / 1.58M 三角面**。
- `selfcheck` 4 项全 PASS（results_pcs_cg3d/p3b_finney 与 p4_siA 均通过）：
  - 轴序：等值面精确落在 x=8.00，x 展布 0.000
  - 壁面：x 两端固相分数 1.00/1.00，y/z 四端 0.65–0.69
  - 流向：inlet reservoir ψ=+1.000、outlet ψ=-1.000（仅统计孔隙体素）
  - 灰度：report 最差一对 液↔气 ΔL=0.22；slide 最差一对 幽灵↔液 ΔL=0.25（阈值 0.06）
- 无头渲染、depth peeling、SSAO、正交投影、透明背景在本机 Windows 全部可用。
- 像素统计（非空/非剪影的代理证据）：p0_geo ink=0.495、5624 色；p2 色相带 100% 暖色、
  p3 100% 蓝色（`qa_stats` 按色相带分类，见函数 `HUE_BANDS`）。
- slide 白气相：表面约占画面 30%，最亮 202/255（Lambert 着色下为反照率的 79%），背景 27 —— 对比充分。

## 7. 动画（`animate`，2026-09-13 新增）

目标形态对标 `taichi_LBM3D/img/ket_drain.gif`（960×520、43 帧、500 ms/帧、21.5 s、8.4 MB）。

```
python viz3d.py animate --series results_pcs_cg3d/<tag>/frames \
    --out results_p5_figs_pv3d/anim --style slide --opaque both \
    --view top --cut-axis z --cut-keep lo --cutaway 0.65 \
    --level-gap 0.1 --ghost-alpha 0.12 --window 900x1020 \
    --duration 450 --colors 128 --tag <tag>
```

**视角是量出来的，不是选的。** 同一帧（S_nw≈0.13）在 1400×1400 窗口下逐配置测量"气相像素占比"
（亮度 >110，即明显亮于蓝色液相 L≈90）：

| 视角 / 剖切 | 内容投影 | 气相>110 | 结论 |
|---|---|---|---|
| iso（up=z）/ 剖 y | 1132×1356（竖） | 1.5–2.1% | 基线 |
| front（up=y）/ 剖 z | 1082×1224 | 3.5–4.5% | 提亮但构图仍竖 |
| front / 剖 y 成条带 | 1224×800（横） | 1.2% | 横构图但更差 |
| **top（仰角 58°）/ 剖 z** | 968×1094 | **2.9%** | **采用**：正对剖切面看 |

原因：俯视时视线基本垂直于水平剖切面，孔隙内部的流体是**正对**看到的，而不是被斜向遮挡；
`iso` 的斜视把剖切面上的内容压在掠射角里。横构图的 `front` 虽像参考 GIF，但要以一半的气相
可见度为代价，放弃。

**`--opaque both`（两相都不透明）是对标 `ket_drain.gif` 的做法**：量过参考 GIF 的调色板——背景是
深板岩灰 [72,72,85]、侵入相是高饱和亮色、两相基本不透明。两相占据互不重叠的体素，只要**都不是
半透明**就不存在遮挡问题，唯一的半透明物体是固相幽灵。早先"多数相做玻璃"是给静态单图用的
（要同时看见被包住的少数相），动画改用 both 更接近参考观感。

**数据来源**：运行器 `run_pcs_cg3d.py --dump-every N` 每 N 步往 `<out>/frames/` 写一个
int8 量化的 psi（0.01 分辨率，裁到孔域；固相只写一次 `f_solid.npz`）。默认协议仍不存体数据帧，
只有给了 `--dump-every` 才付这个代价。`animate` 也吃 Shan-Chen 的 `phase` / `rho1-rho2` 命名，
所以两族求解器的序列都能用同一路径出动画。

**四条与静态面板不同的默认值，都有原因**：

1. **沿 z 剖并俯视，不沿 x 剖。** 静态面板切 x（丢掉下游一半）是为了看内部；但动画追踪的是推进的
   侵入前沿，切 x 会把后半程的侵入一起切掉。采用 `--view top --cut-axis z --cut-keep lo`（见上表）：
   入口 x 投影在画面左侧（相机 azim=−55 时 +x 投影到右，已核算），前沿从左向右推进，剖切面朝上
   正对相机。
2. **固相取绝对不透明度 0.12–0.15**（不是静态面板那套"幽灵×0.6"的极淡值）——这是用户明确要求的：
   透过骨架能同时看清液相和气相，固相要"看得见但透明"，不能淡到消失。
   `--ghost-alpha` 是**绝对不透明度覆盖**，不是乘数：乘数会和两相面板的 0.6 系数叠乘成 0.04，
   固相直接看不见（这个坑已踩过，语义已改）。
3. **玻璃/不透明判定在整段动画里冻结**（按最后一帧的 S_nw 定），否则颜色会在播放中途互换，
   看起来像渲染 bug。
4. **固相网格只构建一次**：岩石不变，40 帧重复 contour 纯属浪费。

**实测（anim_drain_n200，200³ Finney，单次恒压 d=0.0464，80k 步，40 帧）**：GIF 900×1020 / 450 ms /
40 帧 / 128 色 → **5.77 MB**（参考 ket_drain.gif 为 8.4 MB），渲染 43 s。逐帧量到气相像素单调增长
**10.5×**（0.0057→0.0601）、液相像素单调收缩（0.2988→0.2292），与 S_nw 0.030→0.441 一致 —— 即
"气相推进、液相退却"确实被画出来了，不是静态帧。

注意该算例是**冷启动的单次恒压排驱**（ΔP=0.0464 恰为 Pc–S 曲线的突破压力/膝点），**不是**准静态
阶梯；出图和标签不能写成 ladder 结果。

尺寸与体积：每帧自适应量化（`--colors` 可降到 128 缩小文件）+ `optimize=True`，`--gif-width` 可再降采样。实测 13 帧 / 900×700 / 400 ms
→ 3.4 MB，13 帧渲染 8 s。

**别和 GPU 算例并行渲染。** VTK 无头渲染在 Windows 上走 GPU（WGL），会和 Taichi CUDA 抢设备：
实测一个 200³ 算例被并行的 viz3d 渲染从 33.8 步/秒拖到 13.9 步/秒。出图一律等算例退出后再跑。

## 8. 交互查看器（`explore`，2026-09-13 新增）

给"我自己想转着看、想刷帧"用的。`animate` 出的是给别人看的成品 GIF；`explore` 是给你自己在屏幕上
手动翻的工具。

```
cd LBM/source_code/taichi_LBM3D/2phase
viz3d.cmd explore --series results_pcs_cg3d/anim_drain_n200/frames
```

**先 `conda activate lbm`，否则用同目录的 `viz3d.cmd`。** 这台机器的裸 `python` 是 base 环境
(``C:\Users\yangc\anaconda3\python.exe``)，**没有 pyvista**；pyvista 0.49 / vtk 9.7 装在 `lbm`
环境（``C:\Users\yangc\anaconda3\envs\lbm\python.exe``）。`viz3d.cmd` 会自动挑一个真的能
`import pyvista` 的解释器并转发参数。用错解释器时 `check_env()` 直接打印上面这些修复方式，而不再
抛裸的 `ModuleNotFoundError`（2026-09-13 加）。

单看某个终态用 `--run results_pcs_cg3d/<tag>`（不需要 frames 目录）。

**鼠标是 VTK 自带的，不用写代码**：左键拖=旋转，滚轮=缩放，中键拖=平移。

**加在上面的操作**：

| 键 | 作用 |
|---|---|
| 滑块 | 刷帧（松手才更新，因为每帧要重算等值面） |
| `space` | 播放/暂停（每帧一次等值面，所以首轮慢、第二轮起是瞬时的） |
| `n` / `p` | 下一帧 / 上一帧 |
| `g` | 循环固相幽灵不透明度 0 → 0.06 → 0.12 → 0.20 → 0.35 → 1.0 |
| `c` | 循环剖切比例 1.0 → 0.85 → 0.75 → 0.65 → 0.5 → 0.35 |
| `x` | 循环剖切轴 (z,lo) → (y,hi) → (x,lo) |
| `o` | 循环不透明相 both → nw → wet |
| `b` | 显示/隐藏域框 |
| `r` | 相机复位到预设视角 |
| `q` | 关闭 |

**这是本模块唯一不开无头渲染的东西**，需要桌面会话。窗口创建失败会给出明确报错并提示改用
`figset` / `animate`。

**验证方式**：`--selftest` 分两段跑——第一段离屏建场景、把每个按键处理函数都调一遍并截图（验证逻辑），
第二段真的创建一个屏幕窗口，用 `show(interactive=False)` 渲染一帧就返回（**不进交互循环、不留窗口**），
打印 `selftest on-screen OK` 即证明这台机器上 GUI 路径可用。实测 200³ 6 帧 11 秒跑完两段。

**代价要说清楚**：一帧 = 两个相场在 200³ 上做 marching cubes，约 1–2 s。所以**首次**刷到某一帧会
卡顿一下、之后瞬间（有缓存）；`space` 连播的第一次循环约 1–2 fps，之后才是流畅的。想更跟手就
`--decimate 0.5` 或 `--max-frames N` 只载入一段。

**另一条路（没做，但记下来）**：napari 是通用的体数据浏览器，可以在**原始体素数据**上逐层翻切片、
做体渲染，适合"钻进原始数据里看有没有异常"。它出不了本文档这套等值面观感，而且要额外装一个 Qt
依赖。若将来需要，`psi` 数组直接喂给 `napari.view_image(psi, ndisplay=3)` 即可。

## 9. 已知不一致（不要当成 bug）

- **`run_pcs_cg3d.mid_slice_png` 用 `cmap='RdBu'`**，即 psi>0（非润湿）渲染成**蓝**，与报告口径
  （暖色 = 非润湿）相反。这是 in-loop 诊断图，按"不改动在跑脚本"原则**保持原样**；若要把某张
  in-loop 帧放进报告，用 `viz3d.py slices` 重新出。
- **已交付的 2D 报告**（`make_report_figures.py` 等）用 `LIQ='#2166ac'` / `GAS='#b2182b'`，
  灰度差 0.067，黑白打印下不可分。3D 一律不复用这套；2D 是否追溯调整由用户定。

## 10. 环境

`lbm` 环境（Python 3.10.21）：`pyvista==0.49.0`、`vtk==9.7.0`（已写进
`taichi_LBM3D/requirements.txt`）。pin 死：VTK 渲染 API 在小版本间有变动，图面风格依赖它。

**解释器别搞错**：base 环境（裸 `python`）没有 pyvista。用 `conda activate lbm`、同目录的
`viz3d.cmd`，或 ``"C:/Users/yangc/anaconda3/envs/lbm/python.exe" viz3d.py``。

## 11. 未做 / 待办

- 速度场 streamline / glyph（二期，`pv.streamlines_from_source` 可用）
- 体渲染（volume rendering）看弥散界面内部
- 逐帧动画（mp4）——目前只有静态图
- R 线 336³ / BIL 的默认 `--cutaway` 与 `min_voxels` 需要重新标定
- **视觉验收未完成**：本会话视觉通道（zai-vision）额度耗尽，图像只经过了程序化检查
  （ink/色相带/亮度分布）和人工代码审查，没有人眼看过。验收请直接看
  `results_p5_figs_pv3d/*_qa_montage.png`。

## 12. 修改记录

- 2026-09-13 初版：PyVista 路线、两套 style、5 面板、selfcheck。
- 2026-09-13 修订：新增 `viz3d.cmd` 启动器 + `check_env()` 依赖守卫——裸 `python` 是 base
  环境、没有 pyvista，之前只会抛 `ModuleNotFoundError`；现在直接打印三种正确调用方式。
- 2026-09-13 修订：新增 `explore` 交互查看器（鼠标旋转/缩放 + 滑块刷帧 + 9 个按键开关；
  `--selftest` 两段验证，其中第二段真的开窗渲染一帧）。
- 2026-09-13 修订：**修掉相机 `zoom=1.12` 的裁剪缺陷**——VTK 的 `camera.zoom` 大于 1 是**放大**，
  原默认值把几何边缘裁出画面（俯视配置下四边全部触边可证），改为 0.92 留白。此前所有静态面板
  都带这个缺陷。
- 2026-09-13 修订：新增 `animate`（逐帧 GIF）；裁剪推广到任意轴（`_crop3`/`_bounds`），
  顺带**修掉一个静默 bug**：旧 `_domain_bounds` 给 wireframe 域框的 origin 加了 `dom.start`，
  而被 contour 的网格没有加，域框相对数据错位 12 lu（200³ 下约画面的 14%）——图一直在，只是没人眼看过。
- 2026-09-13 修订：**加 `p2_twophase` 并定为默认首图**（用户反馈"没办法在一张图里同时观察到气相和
  液相"——诊断确认是设计缺陷而非配色问题：单相面板让另一相变成白背景，两相同框时多数相又会遮挡
  少数相 → 引入"多数相玻璃"规则）；镜面收紧；增 `--ghost-alpha`、`--level-gap`。
- 2026-09-13 修订（石墨探路臂，用户要求"可视化表明入口出口"）：新增 **flow markers**——
  `add_flow_markers(pl, style)` 画两根 `pv.Arrow`（皆指 +x，长 8%dx）：左=inlet（红/非润湿相入口，−x 面）、
  右=outlet（+x 面）；文字标签 font 15、`style['text']` 色、无框无光照。接线：panel_geometry/
  panel_cutaway/panel_clusters + panel_slices（xz/xy 两切片底部 "inlet →"/"→ outlet"）+
  animate（经 cutaway 自动继承）；CLI `--no-flow` 关闭。selfcheck 第 5 断言校验
  tail/tip 单调与盒心位置。标签用英文（vtk 离屏字体无 CJK 字形）。
  **放置迭代三版（教训全录）**：①盒内前下缘——被不透明相网格深度遮挡，右侧箭头完全消失（p3b 验出）；
  ②盒外正下、mid-y——满框场景（石墨 228³）下 outlet 箭头被右缘裁掉大半、标签投影落进盒内结构上
  （gx3 像素扫描：右半暗像素 157 vs 左 4133）；**③终版：盒外前下方（y0−4.5%dy、z0−4.5%dz），
  尾端内收 1.5%dx，outlet 标签锚尾端**——像素（左 1141/右 4013）与视觉双验通过。核对手段：
  底条带暗像素左右半计数 + CDN 视觉核验。
- 2026-09-20 新增（IC/BC 图，`graphite_ic_bc_figs.py`）：drainage t=0（psi0 纯 numpy
  复刻 protocol.py:41-43）与 imbibition 起始态（= gx3c drain 终态帧）的全域 cutaway——
  y 切半 keep='hi'（iso 相机在 −y 侧，hi 半的切面朝向相机；x 全程保留以示 inlet→outlet）、
  气 opaque nw / 液 glass / ghost 0.12；新元素：绿色半透明 membrane 平面（#009E73，30%）+
  reservoir ρ/ψ 标签 + wall/periodic 注记（英文，vtk 无 CJK）。组合图右侧配 x-z mid-y 切片
  分带标注条（matplotlib，CJK 可用；宽带竖排、窄带括线横排，标签画在 axes 内 y>200 区，
  勿再放轴外——首版贴标题）。产物 results/figures/fig_gx_ic_bc*.png，副本在父工作区
  output_docs/figures_graphite/。zai-vision 超时回退用 4_5v analyze_image（CDN URL）。
