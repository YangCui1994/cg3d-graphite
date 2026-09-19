# CG3D 两相驱动的边界/初始条件/输出设置参考(v1,2026-09-15)

适用:`2phase/run_pcs_cg3d.py`(排水阶梯)、`2phase/run_ir_cg3d.py`(排水+吸渗 I–R),求解器 `lbm_solver_cg3d.py`。
用途:**开新仿真前照此文件调整参数**,不必翻驱动源码。所有行号指向 2026-09-15 版本。
规则来源:2026-09-15 用户指令"输出选择,不要只输出头尾"已落成驱动默认行为(见 §3)。

## 1. 域布局与边界条件(x = 流动方向)

```
x:  0        3            11 12  14                    214  217 218        225   228
    | wall   | res_in     | M |buf|   GRAPHITE (真实结构)  |buf| M  | res_out  | wall |
    | 3 lu   | 8 lu       | 1 |2lu|        200 lu        |3lu| 1  | 8 lu     | 3 lu |
      BB       ρ=1+δ/2      膜   开放垫层                   垫层  膜    ρ=1−δ/2
               ψ=+1(气源)  只过气  (NaN修复垫)               只过液 ψ=−1(液汇)
```

| 边界 | 实现 | 关键参数 | 语义 |
|---|---|---|---|
| 固壁(x 两端各 3) | bounce-back(solid=1) | — | 无滑移 |
| 入口 reservoir `[3,11)` | `set_reservoirs(res_in, +1, 1+δ/2)` | δ 逐档变 | 强制密度=压力源,**ψ 钉 +1(非润湿相源)**;Pc = δ/3(cs²=1/3) |
| 出口 reservoir | `set_reservoirs(res_out, −1, 1−δ/2)` | 同上 | ψ 钉 −1(润湿相汇) |
| 半透膜 x=11 / x=217 | `set_membranes(mem_r, mem_b)`,ψ 条件 bounce-back 单平面 | mem_b 挡蓝(液)、mem_r 挡红(气) | 入口只进气、出口只出液 → 开放系统压力边界 |
| y/z 方向 | periodic(`periodic_index` wrap) | — | 侧向无边界;真实立方跨面有人为连通(已知伪影) |
| 固相表面 | `set_psi_solid(ψ_solid)`,几何润湿 | 见下表 | 全域统一,无空间分区 |

**ψ_solid → 接触角注册表(液侧角)**:−0.75→21.1°,−0.68→**30°(电极口径,常用)**,−0.25→83.9°,0→95.7°,+0.25→112.9°,+0.7→157.1°。

**缓冲垫层规则(NaN 教训,勿省)**:reservoir/膜强制条件**不得直接压在真实粗糙表面上**,否则纯 equil 数百步内 NaN(探针链 A–E 见 `probe_gx1_nan.py`)。垫层 k 须满足 k ≥ res_thick+膜+余量(228 域用 14=res 8+膜 1+净通道 2+余 3);k=4(只盖部分)仍 NaN。几何生成:`make_geo_buffer.py`。

## 2. 初始条件

| 量 | 初值 | 位置 |
|---|---|---|
| ψ(相指示) | −1(电解液满孔) | 全域孔隙 |
| ψ | +1(气相预置) | 入口 reservoir + 入口膜平面 `[3, x_in]` 的孔隙 |
| 出口膜 | 保持蓝预润(ψ=−1) | — |
| ρ、f | init() 初始化;**固相节点清零**(re-init ≡ 新实例,§6a) | — |
| 平衡 | δ=0 跑 equil_steps(默认 20000)再起阶梯 | 状态跨档延续(单实现连续路径) |
| I–R 序列 | 排水臂升 δ 至 S_i → 吸渗臂降 δ 至 0 | `--ds-drain`/`--ds-imbibe` |

## 3. 输出选择(**用户规则:不要只输出头尾,2026-09-15 起为默认**)

| 输出 | 触发/默认 | 文件 | 用途 |
|---|---|---|---|
| 逐帧 ψ 快照 | **`--dump-every` 默认 20000**(0=关;两驱动同) | `frames/{phase}_d{δ}_{it:07d}.npz`(int8 ψ+it+δ+S_nw)+ `f_solid.npz` | 时间序列/过程 GIF/中断抢救。**帧名含档位**——旧版裸步数名导致后档覆盖前档(gx2_drain 只剩 d03),已修 |
| 档末保底帧 | 每档结束必存一帧(短档也有) | 同上 | 每档终态 |
| 档末切片图 | 每档自动 | `psi_d*.png`(RdBu 快检图) | 批中肉眼巡检 |
| **增量存档** | **每档结束写 `report_partial.json`**(两驱动同) | ladder 至今+args | **中断不丢已算档位**(X2 首跑被停时 final/report 皆失,只能从帧+日志抢救——此教训的修复) |
| 终态 | 全梯结束 | `final.npz`(ψ+solid;I–R 另含 sizes)、`report.json`(ladder+sentry+簇统计)、`final.png` | 定量分析主数据 |
| 测量 | `--every 500` | 进内存 + 日志 | qs 判据、umax 监控 |

### 3.1 梯档 report 字段(PR-1 instruments,2026-09-19 起)

每档结束的 ladder 行(两 driver 同 schema;旧字段 `pc` 改名,读旧 report 用 `r.get('pc_nominal', r.get('pc'))`):

| 字段 | 定义 | 说明 |
|---|---|---|
| `pc_nominal` | cs²·δ = δ/3 | 入口/出口 reservoir 密度差的名义 Pc(旧 `pc`) |
| `pc_measured` | p(band_in) − p(band_out),p = ρ/3 | **样品侧实测压差**:膜内侧各 `--pc-band`(默认 4)lu 厚 pore band 的平均压力差。band 内若跨界面,则自动包含该界面的 capillary jump——这正是样品实际承受的压差,而非缺陷 |
| `rho_in_mean` / `rho_out_mean` | reservoir 区 ρ 平均 | reservoir 每 step 被 pin,稳态下 ≈ 目标值(1±δ/2);偏离即 pinning 失效告警 |
| `p_in_mean` / `p_out_mean` | ρ/3 | 同上,压力形式 |
| `u_rms` / `u_bulk_x` | 域内 pore 的 RMS 速度 / 平均 x 向速度 | flow diagnostics(quasi-steady 多指标判据的输入,PR-3) |
| `flux_r_rate` / `flux_b_rate` | 尾窗(qs-window)内 reservoir 注入质量变化率 | net phase flux,每 lu 时间步的质量;准稳态应 → 0 |

实现:`run_common.region_stats()`(纯 numpy,不碰 solver 状态);快照复用 `measure()` 已取的 ψ/ρ/v 数组,零额外 GPU 拷贝。

帧成本参考:205×200×200 int8 ≈ 8 MB/帧(压缩后 ~3–5 MB);20k 步/帧 × 9 档 × 15 万步帽 ≈ 每 run 数百 MB,可接受。

## 4. 数值参数速查(当前基线)

CapA=0.06(σ=0.0606,3D 系数 1.012);ν_l=ν_g=0.1;qs-tol 5e-7 / 15k 窗 / min-steps 15k;max-steps 150k/档;umax-cap 0.12;ρ 允许带 ±0.11(mass sentry:leak_* 计入 report)。阶梯设计:δ 起点须低于入流估计(EDT:δ_entry≈6σ/r_max),×1.35 递增;入流档会打满步数帽,属预期。

## 5. 开新仿真时改什么

1. **换几何**:生成 `npz(solid int8, 1=solid)`;若表面粗糙/亚体素孔多 → 先跑 `make_geo_buffer.py` 式垫层(X0 审计:渗流占比、EDT 入流估计)。
2. **换润湿性**:`--psi-solid`(查 §1 注册表)。
3. **换压力范围**:`--ds`/`--ds-drain` 列表,起点 < EDT 估计的 δ_entry。
4. **分辨率 vs 尺寸**:voxel 尺寸由几何决定;喉道 p50 ≥ 2.2 lu(界面宽)才够 SC;CG 可更低但属欠分辨口径。
5. **输出密度**:`--dump-every`(20k@228³ 基准,域大按比例放大);**保持默认=遵守"不要只输出头尾"**。
6. **物理时间换算**(可选):指定 ν_phys 后 t_phys = t_lu·Δx²/ν_phys;探索级默认不换算。

## 6. 遗留开口

- 档内**中途状态 npz 自动存档**(非 int8 帧、可断点续跑)未实现——现有帧+partial report 已满足"不丢结果",真断点续跑留待需要时。
- `--dump-every` 改默认值的决定记录于两驱动 docstring(2026-09-15 用户规则)。
