# CG3D 两相驱动的边界/初始条件/输出设置参考(v1,2026-09-15)

适用:`2phase/run_pcs_cg3d.py`(排水阶梯)、`2phase/run_ir_cg3d.py`(排水+吸渗 I–R)、`run_imbibition_cg3d.py`(直接吸渗,§7,2026-09-21 起),求解器 `lbm_solver_cg3d.py`。
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
| 入口 reservoir `[3,11)` | `set_reservoirs(res_in, +1, 1+δ/2)` | δ 逐档变 | 强制密度=压力源,**ψ 钉 +1(非润湿相源)**;Pc_nominal = δ/3(cs²=1/3);实测压差见 `pc_measured`(§3.1) |
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

### 3.2 PR-3 后处理字段(2026-09-19 起)

**双口径 saturation**(任务 2.5):梯档行新增 `s_nw_binary`(psi>0 的 pore 格占比);既有 `s_nw` 保持 continuous 口径(psi 积分)。I–R 终态 `s_nr` 保持 binary 口径(legacy),新增 `s_nr_continuous`。两口径差值 ~ 界面体积占比,是分辨率诊断。

**多指标收敛**(任务 2.4):每档行新增 `convergence` dict,回答"为什么这一档退出":

```json
{"saturation_slope": ..., "pc_drift": ..., "phase_flux": ..., "u_rms_rel": ...,
 "criteria_passed": [...], "thresholds": {...}, "exit": {"mode": "sat|multi", "reason": "..."}}
```

退出规则 `--qs-mode`:`sat`(默认,legacy——仅 saturation 斜率,与 baseline 可比)或 `multi`(saturation AND pressure AND flux AND kinetic)。**无论哪种模式,convergence 记录总是完整写入**(max-steps 退出的档也能看到哪项判据未过)。阈值全部 CLI 化:`--pc-drift-tol`(0.01)、`--flux-tol`(1e-6/pore/step)、`--u-rel-tol`(0.05)。

**cluster topology**(任务 2.6/2.7):I–R 终态连通性 `--conn {6,18,26}`(默认 6=legacy);**y/z periodic merge 恒开**(solver 是 y/z 周期的,旧的非周期 labeling 会把跨缝 cluster 拆开——n_clusters 高估、largest 低估);report 记录 `cluster_topology = {conn, periodic}`。周期合并改变 X3 类结果的 n/largest 数值(baseline 存档不受影响,Phase 5 量化差异)。实现:`run_common.label_periodic`(非周期 label + 缝平面 union-find;注意单层 wrap padding 方案不可行,pad 拷贝与原格不同 label)。

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

## 7. 直接吸渗 direct imbibition(`run_imbibition_cg3d.py`,CG3D-IMB-001,2026-09-21)

独立新场景:气饱和电极从一侧接触电解液的自发吸渗。**与 I–R 完全独立**(无排水 checkpoint、不继承残余液);两既有驱动与其 drainage 口径不受影响(回归见 `tests/test_direct_imbibition_layout.py` L4/L5 与 `tests/test_checkpoint_resume.py`)。

布局(与 §1 相同的 buffer 几何,左右相角色对调):

```
x:  0    3        11   12  14         14+N              214  217  218       225  228
    |wall| 液res   |M_r |buf| 预润N层   剩余真实孔隙(气)    |buf| M_b | 气res   |wall|
              ψ=−1  只过液  液    液|气界面(初始)   气        气   只过气  ψ=+1
```

- **膜方向互换**:入口 x=11 放 **mem_r**(挡红/气→液进),出口 x=217 放 **mem_b**(挡蓝/液→气出);drainage 口径(§1)恰相反。
- **真实域边界(R1 返工,2026-09-21)**:显式来源,优先级 `--real-bounds LO HI` > 几何 npz 结构化字段 `real_x=[lo,hi)`(make_geo_buffer.py 写入,生产几何=[14,214))。**绝不从 solid 占据推导**(真实电极切片可能以全孔隙平面开头);两处都没有 → 快速报错指引。drainage 不需要该边界(npz 无 real_x 也照常,全开放合成几何亦有效)。
- **IC**:左液 reservoir+膜面+左 buffer+真实结构前 `--prewet-layers N` 层孔隙(自显式真实域入口数起)=液(ψ=−1),其余真实孔隙/右 buffer/右膜面/右 reservoir=气(ψ=+1);固相 ψ=0 不变。
- **驱动**:`--delta`(默认 0)→ 两 reservoir 名义密度相等(1.0/1.0),纯自发/毛吸驱动;`--delta≠0` 为压力辅助吸渗(未验证的未来工作)。δ>0 = 液侧高压。
- **无平衡步**:δ=0 下毛吸从第 1 步就起作用,跑 equil 等于提前跑实验;IC 本身即交付物(`psi_ic.npz` + `ic.png` 每次必写)。
- **协议复用**:单 rung 走 `run_hold`(d=--delta),收敛判据/帧/报告 schema 与 §3.1/§3.2 相同;输出根目录 `results_imb_cg3d/<tag>`。终态 checkpoint 与 rolling live ckpt 支持,`--resume` 尚未接入(已知缺口)。
- **终态 gas 口径(R2 返工)**:开放系统中剩余气≠困气(可能仍连着气出口)。终态 report 只报中性量:`gas_saturation_dom`(binary ψ>0,全域含 buffer)、`gas_saturation_real`(binary,真实域)、`gas_saturation_real_continuous`;`report['trapped_gas_analysis']='NOT_IMPLEMENTED...'` 显式声明**出口连通性困气分析未实现**(留待后续任务);不做 gas 集群统计。
- **参数**:`--prewet-layers` **必填**(最优值未定,4 lu 仅为临时数值样例,勿当物理验证值);`--psi-solid` 默认 −0.68(电极口径;两 drainage 驱动默认 −0.75/Finney 线)。
- **IC QA 图**(无求解器,NumPy+matplotlib,复用同一 `build_layout`):`python -m cg3d.ic_figs --geo geo_graphite_228b14.npz --prewet 2 6 --out <dir>` → x 方向逐平面相分数 profile + 中央 x-z 切片 + 双值对比图;证据图在 `.agent/evidence/CG3D-IMB-001/figures/`。
- 验证证据(布局/膜方向/回归/零偏置 + smoke + R1/R2 返工项):`tests/test_direct_imbibition_{layout,runtime}.py` + `.agent/evidence/CG3D-IMB-001/validation_summary.md`。
