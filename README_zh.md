# cg3d-graphite（中文版）

在**真实锂离子电池 graphite anode 微结构**（实验室 X-ray nano-CT）上做 drainage
与 imbibition 两相 Lattice-Boltzmann 仿真的代码与结果，应用背景是**电池注液 /
trapped gas（困气）**问题。英文主文档见 [README.md](README.md)。

求解器为 3D **D3Q19 MRT color-gradient（Rothman–Keller）** 两相模型，用
[Taichi](https://github.com/taichi-dev/taichi) 编写；通过 ψ-Dirichlet reservoir
与 semi-permeable membrane 实现两端压力边界的**开放系统**，以逐档 capillary
pressure 阶梯驱动。可视化走脚本化 offscreen
[PyVista](https://docs.pyvista.org) 管线（切片、6 面板 figset、逐簇渲染、GIF
动画），所有 3D 图必带 inlet/outlet 流向箭头。

## 这套代码跑出了什么

对 BIL graphite scan119 的 200³ 子窗（0.128 µm/voxel，即 25.6 µm 真实石墨立方体）
跑了三个核心算例：

| 算例 | 内容 | 主要结果 |
|---|---|---|
| X1 sanity + NaN 探针 | reservoir/membrane 布局在亚体素粗糙真实表面上的稳定性 | **强制边界条件不能压在粗糙面上**：原始布局纯平衡阶段 ~200 步内 NaN；两端各垫 14 lu 开放孔隙 buffer 修复，**solver 零改动** |
| X2 排水（`run_pcs_cg3d.py`） | 9 档 capillary pressure 阶梯 | 入流带 Pc 0.013–0.025（与 EDT 估计吻合）；平台 S_nw→0.684；石墨区残余 wetting saturation **Sw=0.322** |
| X3 吸渗回填（`run_ir_cg3d.py`） | 排水至 S_i=0.558 后逐档降 δ 到 0 | 困气 **S_nr=0.171**，32 个 gas cluster，最大 ganglion 占困气 66.7%、占孔隙 12%——落在 Finney RCP 验证带（0.16–0.20）内 |

精选图在 [`results/figures/`](results/figures/)；完整数据与诚实边界见
[`docs/RESULTS_zh.md`](docs/RESULTS_zh.md)。

**探索级口径**：该石墨喉道中位数 p50=1.73 lu，低于 CG 界面宽 2.2 lu——参与流动
的孔隙子集由 p95+ 喉道决定，全部结论按 exploration-grade（非 validation-grade）
读。复用任何数字前先看 `docs/RESULTS_zh.md §6` 的七条诚实边界。

## 目录结构

| 路径 | 内容 |
|---|---|
| `lbm_solver_cg3d.py` | 求解器：D3Q19 MRT color-gradient 两相、race-free 双色 membrane、ρ-Dirichlet ψ 边界 reservoir、逐节点 wettability 场。Taichi，默认 GPU（`LBM_ARCH=cpu` 强制 CPU） |
| `run_pcs_cg3d.py` | 排水驱动：δ 阶梯 → Pc–S 曲线，quasi-steady 退出判据，逐档快照 + 增量 `report_partial.json` |
| `run_ir_cg3d.py` | 吸渗驱动：排水至目标 S_i 再逐档降 δ（单实现状态跨档延续） |
| `make_geo_buffer.py` | 在原始 200³ 几何两端垫 14 lu 开放 buffer（NaN 修复） |
| `probe_gx1_nan.py` | NaN 诊断探针链 A/B/C/D/E（定位发散触发器） |
| `audit_graphite_geo.py` | 几何审计：渗流占比、喉道 EDT 统计、选窗、入流压力估计 |
| `process_electrode_BIL.py` | BIL 原始 nano-CT 切片栈 → 分割 npz 立方体（几何构建管线） |
| `viz3d.py`（+ `viz3d.cmd`） | offscreen PyVista 渲染：`figset`、`animate`（GIF）、切片、逐簇配色、inlet/outlet 箭头 |
| `graphite_figs.py`、`graphite_slices_v2.py`、`graphite_imb_pair.py` | 2D 结果图（Pc–S 曲线、恒压侵入切片序列、吸渗前后对比） |
| `data/geo_graphite_200.npz` | 仿真几何：scan119 200³ 子窗，offset (136,136,136)，φ=0.4475（int8 solid mask） |
| `results/figures/` | 精选图 + 排水侵入 GIF |
| `results/data/` | run 的 `report.json` 与控制台日志（小文件；逐帧快照与 figset 不进 git） |
| `docs/` | 方法、结果、操作文档（双语） |

## 快速开始

环境：Python 3.10+，建议 CUDA GPU（200³ 算例约需 4.6 GB 显存；CPU 可跑但慢
~14 倍），`pip install -r requirements.txt`。

```bash
# 1. 重建缓冲几何（228x200x200 = 200³ 立方体 + 两端各 14 lu 开放 buffer）
cp data/geo_graphite_200.npz .
python make_geo_buffer.py            # 生成 geo_graphite_228b14.npz

# 2. 排水，9 档阶梯（桌面 RTX 5080 约 11 小时）
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds 0.030 0.040 0.055 0.074 0.100 0.135 0.182 0.245 0.281 \
  --max-steps 150000 --dump-every 20000 --tag gx2b_drain

# 3. 吸渗回填（3 档排水到 S_i≈0.56，再降 δ 到 0；约 17 小时）
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds-drain 0.030 0.055 0.074 \
  --ds-imbibe 0.055 0.040 0.025 0.012 0.0 --max-steps 150000 --tag gx3_ir

# 4. 出图
python graphite_figs.py --tag-drain gx2b_drain --tag-ir gx3_ir --picks 6
python viz3d.py figset --run results_pcs_cg3d/gx3_ir --cutaway 0.5 --out gx3_figset
python viz3d.py animate --series results_pcs_cg3d/gx2b_drain/frames \
  --out anim_gx_drain --duration 800 --gif-width 900 --opaque both --view iso
```

改任何参数前先读 [`docs/BC_IC_OUTPUT.md`](docs/BC_IC_OUTPUT.md)——开新仿真的
操作参考：x 方向布局语义、ψ_solid→contact angle registry、为什么粗糙几何上
buffer 规则不可省。

## 文档

| 文档 | 内容 |
|---|---|
| [`docs/ALGORITHM.md`](docs/ALGORITHM.md) / [`_zh`](docs/ALGORITHM_zh.md) | 算法说明：lattice、MRT moment、recoloring、wettability、reservoir/membrane 压力边界、含 ρ 的平衡态 |
| [`docs/RESULTS.md`](docs/RESULTS.md) / [`_zh`](docs/RESULTS_zh.md) | 完整 run 记录：NaN 诊断链、排水阶梯表、吸渗困气统计、诚实边界、复现命令 |
| [`docs/BC_IC_OUTPUT.md`](docs/BC_IC_OUTPUT.md) | 边界/初始条件/输出选择操作参考 |
| [`docs/VIZ_3D_STYLE.md`](docs/VIZ_3D_STYLE.md) | 3D 可视化规范：相机配方、配色（含灰阶安全实测）、流向箭头放置规则 |

## 运行注意（踩坑换来的）

- **JIT 编译税**：每进程首个 solver 实例化约 5.5 min（展开的 MRT kernel）。
  批量运行应单实例 re-init 复用，不要每档起一个进程。
- **批运行期间禁止编辑任何被 import 的 `.py`**——Taichi 会在运行中热加载并毁掉整批。
- 输出默认遵守"不要只输出头尾"：每 20000 步落一帧（文件名含档位 δ），每档结束
  写增量 `report_partial.json`，中断不丢已算档位。
- PyVista 渲染不要与 GPU 仿真在同一张卡上并行。

## 数据来源与许可

`data/` 中的几何衍生自 **Battery Imaging Library (BIL)** graphite anode
nano-CT scan 119（pristine，0.128 µm/voxel），许可 **CC-BY-4.0**：

- BIL：<https://www.batteryimaginglibrary.com>
- 论文：R. Docherty et al., *Battery Imaging Library*, 2025,
  DOI [10.26434/chemrxiv-2025-sbp73](https://doi.org/10.26434/chemrxiv-2025-sbp73)
- Scan 记录：[10.5281/zenodo.18601879](https://doi.org/10.5281/zenodo.18601879)
  （文件 `A-A015A-Anode-Fresh`）

使用该几何请引用 BIL 网站与上述论文。`process_electrode_BIL.py`
展示了原始切片栈的分割与裁剪过程。

## 代码许可

MIT——见 [LICENSE](LICENSE)。本项目是
[yjhp1016/taichi_LBM3D](https://github.com/yjhp1016/taichi_LBM3D)
（MIT，© 2021 Jianhui Yang, Liang Yang）的衍生：本 repo 的 3D solver 为
class-based 重写，数值表（moment matrix、recoloring 对、relaxation 布局）取自
上游，并修复了上游四个已知缺陷（见 solver docstring 与
`docs/ALGORITHM_zh.md §7`）。
