# 结果 — 真实石墨探索性 run 记录（v1，2026-09-13 → 09-15）

英文版：[`RESULTS.md`](RESULTS.md)。方法背景见
[`ALGORITHM_zh.md`](ALGORITHM_zh.md)。本记录为**探索级，非验证级**——复用任何
数字前先读 §6。

## 1. 总览

| | |
|---|---|
| 几何 | BIL graphite scan119，200³ 子窗 offset (136,136,136)，0.128 µm/voxel → 25.6 µm 立方体，φ=0.4475（Otsu 上限）；加 buffer 后 228×200×200（§2） |
| 基线 | CapA=0.06（σ=0.0606），ψ_solid=−0.68（θ≈30°），ν_r=ν_b=0.1，quasi-steady 容差 5e-7 / 15k 窗，150k 步/档帽 |
| Run | X1 稳定性探针 + sanity · X2 排水（9 档）· X3 吸渗回填 |
| 原始数据 | `results/data/`（逐 run `report.json`、控制台日志）；逐帧快照与 figset 未入 git |

## 2. X1 — NaN 诊断与 buffer 修复（本臂最大方法学产出）

原始 200³ 几何在 20 000 步**纯平衡阶段**内 NaN（无驱动、无界面运动）。五变体
探针链（`probe_gx1_nan.py`）定位触发器：

| 模式 | 配置 | 结果 | 排除/锁定 |
|---|---|---|---|
| A | 复刻 driver（界面在膜，ψ_solid=−0.68） | 50 步内 ρ→0，150 步 NaN；热点处 EDT=1.0 单像素孔 | 基线复现 |
| B | 全润湿起点，无任何界面 | **更快爆**（50 步内 ψ→+25） | 排除"界面触发" |
| D | B + ψ_solid=−1.0（壁色=流色） | 仍爆（ψ→+1300） | 排除"润湿性/壁色通量" |
| E | **去 membrane 去 reservoir**，普通 bounce-back 墙 | **稳定 3000 步**（umax ~0.04 平稳） | 锁定触发器 = **reservoir/膜强制条件 × 亚体素粗糙孔** |

机理：reservoir 掩膜与 ψ 条件膜平面直接压在真实粗糙表面上，1 lu 喉道同时承受
"规定 ρ/ψ"与"两壁 bounce-back"的不相容约束，ρ 塌 0 后发散。同布局在光滑球堆
表面稳定——这是**表面粗糙度 × 边界机制**的耦合，不是 solver 通用缺陷。

**修复（solver 零改动）**：两端各垫 14 lu 开放孔隙，使 reservoir(8)+膜(1)+净
通道(2+) 全落 padding（`make_geo_buffer.py`）。探针 A + buffer-14 稳定
（umax 0.019 且衰减）。buffer=4 **仍 NaN**——padding 必须完整覆盖
reservoir+膜再余量。

Sanity run（`gx1b`，228×200×200）：20 000 步 equilibration + 三档 δ，无 NaN，
泄漏 1.4e-8 pore volume/步。入流标定：δ 0.020→S_nw 0.030（入流前）·
0.040→0.069 · 0.080→0.217（主侵入带）。

## 3. X2 — 主排水阶梯（gx2b_drain，完整 9 档）

累计 ~525k 步，桌面 RTX 5080 约 11 小时；泄漏 1.8e-8/步。前 4 档与被中断的
首跑**逐位复现**。

| δ | Pc | S_nw | 退出 | 步数 |
|---|---|---|---|---|
| 0.030 | 0.0100 | 0.039 | 准稳态 | 25k |
| 0.040 | 0.0133 | 0.098 | 准稳态 | 84k |
| 0.055 | 0.0183 | 0.298 | 步数帽 | 150k |
| 0.074 | 0.0247 | 0.572 | 步数帽 | 150k |
| 0.100 | 0.0333 | 0.628 | 准稳态 | 47k |
| 0.135 | 0.0450 | 0.654 | 准稳态 | 31k |
| 0.182 | 0.0607 | 0.671 | 准稳态 | 18k |
| 0.245 | 0.0817 | 0.680 | 准稳态 | 15k |
| 0.281 | 0.0937 | **0.684** | 准稳态 | 15k |

Driver 口径的 saturation 含 buffer 体积；按石墨区掩膜（x∈[14,214)）重算，
终态 S_nw=0.678 → **残余 wetting saturation Sw=0.322**。

读法：入流带 δ≈0.04–0.075（Pc 0.013–0.025），与几何审计的 EDT 入流估计
（Pc 0.0098–0.0264）吻合。主侵入跨两档完成（两档都打满步数帽、S_nw 仍缓升
——侵入带宽而缓，与球堆的极窄 Pc 带形成对比）。δ≥0.10 后各档快速准稳态，
平台稳定在 S_nw≈0.68。无稳定性事件；umax 峰值 0.097。

## 4. X3 — 吸渗回填困气（gx3_ir）

排水 3 档至膝后，再降 δ 到 0（单实现连续）。排水臂：δ 0.030→0.0393（与 X2
d00 逐位复现）· 0.055→0.2723 · 0.074→0.5579 → **S_i=0.558**。

| δ（吸渗） | S_nw | 退出 | 步数 |
|---|---|---|---|
| 0.055 | 0.567 | 准稳态 | 15k |
| 0.040 | 0.565 | 准稳态 | 15k |
| 0.025 | 0.543 | 准稳态 | 37k |
| 0.012 | 0.405 | 步数帽 | 150k |
| 0.000 | 0.177 | 步数帽 | 150k |

**困气终态：S_nr = 0.171**（尾窗均值；末档到帽时仍极缓下降，读作上界附近，
带宽 ~0.005–0.01）。32 个困气簇；尺寸前八：430 341 / 57 161 / 53 435 /
28 251 / 26 450 / 16 393 / 11 606 / 7 773 体素。**最大簇 = 困气总量 66.7 %
= 石墨孔隙体积 12.0 %**——落在 Finney RCP 验证带内（S_nr 0.16–0.20，单一
mega-ganglion ~12 % 孔隙），即在此探索级口径下，圈闭的**量级与形态**对
"球堆 vs 真实电极"稳健。

物理注记：吸渗前两档 S_nw 几乎不动——非润湿相在孔喉中的 retract 需要更低
驱动；大规模回填发生在 δ≤0.012。

## 5. 图索引

| 文件 | 内容 |
|---|---|
| `results/figures/fig_gx_pcs.png` | 完整 Pc–S 排水曲线（9 档） |
| `results/figures/fig_gx_slices_v2.png` | 恒压侵入切片序列（石墨灰 / 电解液蓝 / 气体红） |
| `results/figures/fig_gx_solid_only.png` | 纯结构切片 + 按比例边界图（墙 / 入口 reservoir / 膜 / buffer / 石墨面 / 出口 reservoir） |
| `results/figures/fig_gx_ir.png` | I–R 点 + 困气簇尺寸 CCDF |
| `results/figures/fig_gx_imb_pair.png` | 吸渗前后对比：S_i 处连通气相 vs S_nr 处困气簇 |
| `results/figures/anim_gx_drain_d03_iso.gif` | 主侵入动画（7 帧，恒 δ=0.074，iso 视角，带 inlet/outlet 箭头） |

## 6. 诚实边界

1. φ=0.4457 为 Otsu 上限（carbon-binder domain 计入孔隙），阈值敏感 ±几 %。
2. 喉道 p50=1.73 lu < 界面宽 2.2 lu：细孔为水力死区，参与流动的孔隙子集由
   p95+ 喉道决定；无 NMC811 对照臂，曲线异常无法区分石墨结构物理与欠分辨
   伪影（本臂的已知、用户知情选择）。
3. y/z periodic wrap 真实立方：跨面人为连通伪影（如实标注，未做镜像 tiling）。
4. 单实现单窗（offset (136,136,136)），无统计展宽。
5. 14 lu buffer 改变入口段流动（入口效应被 buffer 吸收）；石墨区内部不受
   影响，定量 saturation 一律按石墨区掩膜。
6. ρ=0 的孤立孔洞细胞（完全被固相包围的空腔）在所有模式（含稳定模式）中
   存在——体素化伪影，对流动无贡献。
7. 单相渗透率未做（探路臂未含；升级为正式线的第一道门）。

## 7. 复现

```bash
cp data/geo_graphite_200.npz .
python make_geo_buffer.py                       # 生成 geo_graphite_228b14.npz
python probe_gx1_nan.py --mode A|B|C|D|E [--buffer 14]   # NaN 探针链
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds 0.030 0.040 0.055 0.074 0.100 0.135 0.182 0.245 0.281 \
  --max-steps 150000 --dump-every 20000 --tag gx2b_drain
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds-drain 0.030 0.055 0.074 \
  --ds-imbibe 0.055 0.040 0.025 0.012 0.0 --max-steps 150000 --tag gx3_ir
python graphite_figs.py --tag-drain gx2b_drain --tag-ir gx3_ir --picks 6
python viz3d.py figset --run results_pcs_cg3d/gx3_ir --cutaway 0.5 --out gx3_figset
python viz3d.py animate --series results_pcs_cg3d/gx2b_drain/frames \
  --out anim_gx_drain --duration 800 --gif-width 900 --opaque both --view iso
```

桌面 RTX 5080 墙钟时间：排水约 11 小时、I–R 约 17 小时，各为单进程（每进程
一次 ~5.5 min 的 JIT 编译税）。打满步数帽的档属阶梯设计预期，不是 bug。
