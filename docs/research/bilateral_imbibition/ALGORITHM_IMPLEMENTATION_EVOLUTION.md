# 双侧渗吸验证：算法与实现演进记录

> **Document type:** Living technical note / algorithm & implementation evolution log  
> **Scope:** CG3D color-gradient LBM，用于锂电池极片/界面润湿与后续 bilateral imbibition 验证  
> **Status:** 更新至 V1b external scientific review；V1c 尚未执行  
> **Primary concern:** 记录“算法/实现到底改了什么，以及 simulation 精度为何改善”，而不是仅记录 agent workflow

---

## 0. 文档目的

这份文档回答四个问题：

1. **核心求解器算法有没有改？**
2. **每一次 numerical / boundary / validation implementation 改动是什么？**
3. **simulation 指标具体改善了多少？**
4. **当前剩余误差来自 core solver，还是来自边界、分辨率、测量方法？**

本文件与 `.agent/evidence/**` 的区别：

- `.agent/evidence/**`：面向审计，记录一次具体执行/评审；
- 本文件：面向长期研发，追踪算法与实现的演进逻辑。

后续 V1c、V2、V3，以及真实 graphite / gap / PCS 阶段，都应继续追加本文件，而不是另起一套“历史”。

---

# 1. 当前核心算法基线

当前核心求解器位于：

`lbm_solver_cg3d.py`

算法基线：

| 模块 | 当前实现 |
|---|---|
| 多相模型 | Rothman–Keller / Leclaire 系 color-gradient LBM |
| 格子 | D3Q19 |
| 碰撞 | MRT |
| 相场 | `psi=(rho_r-rho_b)/(rho_r+rho_b)` |
| 密度比 | unit density ratio |
| 表面张力 | `sigma = 1.012 * CapA` |
| recoloring | Latva–Kokko-type pairwise recoloring |
| wetting | per-node `psi_solid` wall colour |
| baseline viscosity | `nu_l = nu_g = 0.1` |
| pressure | `p = rho/3` |
| open BC | density/psi reservoirs + phase-selective membranes |
| backend | Taichi / CUDA |

关键已知基线：

- interface width ≈ **2.2 lu**；
- `psi_solid=-0.68` 在已有 flat-plate droplet registry 中对应 liquid-side angle ≈ **30°**；
- `CapA=0.06` 时 `sigma≈0.06072`。

## 1.1 本轮 V0 → V1 → V1b 的重要事实

> **截至 V1b，没有修改 core solver physics。**

没有修改：

- MRT collision；
- equilibrium moments；
- surface-tension perturbation；
- recoloring；
- wall-colour wetting implementation；
- viscosity interpolation；
- streaming；
- membrane kernel；
- reservoir kernel。

因此 V1/V1b 中 simulation 改善主要来自：

1. boundary-condition layout；
2. reference equation；
3. pressure/front measurement；
4. validation geometry；
5. provenance / evidence implementation。

这一区分很重要：当前不能把 V1b 的“精度提升”描述成 core CG-LBM 算法精度本身被优化了。

---

# 2. 变动分类

后续所有算法记录统一分成五类。

| 标签 | 含义 |
|---|---|
| **SOLVER** | core collision / force / recoloring / wettability 等求解算法 |
| **BC** | reservoir / membrane / wall / buffer 等边界实现 |
| **VAL** | benchmark/reference relation/acceptance method |
| **DIAG** | pressure/front/mass 等测量算法 |
| **HARNESS** | 测试、provenance、review、artifact 生成方式 |

---

# 3. 演进时间线

| Stage | 主要改动 | 类型 | Core solver changed? | 结果 |
|---|---|---|---|---|
| V0 | 修复 Laplace test 的 `np.save -> np.savez` | HARNESS | **No** | baseline suite clean PASS |
| V1 | 新增 single-front spontaneous filling；识别 matched-viscosity 下应为恒速 generalized Washburn | VAL/DIAG | **No** | 暴露 ~58–74% 速度亏损 |
| V1 | 原 reservoir/membrane layout 无 clean buffer separation | BC | **No** | 发现 ~190 lu 等效附加阻力 |
| V1b | 分离 reservoir / membrane / open buffer / active slit | BC | **No** | h26 front speed +29% |
| V1b | same-slit static Pc calibration | VAL/DIAG | **No** | 暴露 resolution dependence |
| V1b | far-field Pc measurement + length differential | DIAG/VAL | **No** | h26 incremental hydraulic slope error仅 3.4% |
| V1c（planned） | h60/h80 static convergence + h40 2L differential | VAL/DIAG | No planned | 待运行 |

---

# 4. V0 — 基线验证与测试实现修复

## 4.1 改动

Candidate:

`280a46fed488b12975c3de96b5493362942822ec`

唯一 product change：

`tests/levelb_laplace.py`

修复：

```python
np.save(...)
```

为：

```python
np.savez(...)
```

原因：原代码使用 named arrays，但 `np.save` 不支持这一签名。

这不是 physics change，也没有修改 gate、reference 或 solver。

## 4.2 Baseline simulation 指标

| Validation | 结果 |
|---|---:|
| Poiseuille mean-flow efficiency | **0.9933** |
| Poiseuille velocity-profile L2 error | **0.0075** |
| Laplace sigma relative error | **0.29%** |
| Laplace fit R² | **1.00000** |
| Contact angle | **30.3°** |
| Colour-mass drift | **3.58e-7** |
| Required tests | **6/6 exit 0** |

### 技术含义

V0 给出当前 solver 的基本 sanity baseline：

- bulk hydrodynamics；
- surface tension；
- static contact angle；
- infrastructure；
- postprocessing

均处于已有项目阈值内。

**V0 没有提高 solver 精度，只是让已有 Laplace regression 可以正确完成并返回 verdict。**

---

# 5. V1 — Single-front spontaneous filling

Candidate:

`e9540bcadb86257c70b805afc98f2eec9626c64e`

新增主要实现：

- `tests/levelc_imbibition.py`
- single-front slit geometry；
- front tracking；
- pressure diagnostics；
- h=26 / h=40 resolution comparison。

---

## 5.1 Reference equation 的第一次关键修正

最初 Stage Contract 使用 classical Lucas–Washburn：

[
x^2 propto t
]

但 V1 中实际模型为：

- liquid / gas matched viscosity；
- 两端 equal-pressure baths；
- 两相均承担 viscous resistance。

因此：

[
Delta p_{visc}
=
rac{12mu V}{h^2}
(L_l+L_g)
]

而：

[
L_l+L_g=L_{tot}
]

所以 post-transient 应为：

[
x=x_0+Vt
]

其中：

[
V=
rac{P_c h^2}
{12mu L_{tot}}
]

### 变化性质

**VAL change，不是 SOLVER change。**

### 结论

原 `R²(x²,t)` gate 被证明不是当前配置的物理判别量。

后续不再把 classical `x²~t` 当作 matched-viscosity case 的 hard gate。

---

# 6. V1 simulation 结果：暴露系统性速度亏损

## 6.1 h=26

[
V_{meas}=3.857	imes10^{-3}
]

nominal analytic prediction：

[
V_{nom}=9.263	imes10^{-3}
]

所以：

[
V_{meas}/V_{nom}=0.416
]

速度亏损：

**−58.4%**

## 6.2 h=40

[
V_{meas}=3.746	imes10^{-3}
]

[
V_{nom}=14.251	imes10^{-3}
]

所以：

[
V_{meas}/V_{nom}=0.263
]

速度亏损：

**−73.7%**

## 6.3 同时出现的正面结果

虽然绝对速度错误很大，但：

- front 单调；
- front 近似恒速；
- h26 `R²[x,t]` ≈ 1；
- h40 `R²[x,t]` ≈ 1；
- 无 NaN/Inf；
- velocity stability cap 未触发；
- reservoir densities 正常。

因此 V1 暴露的问题更接近：

> **pressure/resistance budget 不对，而不是 front dynamics 完全错误。**

---

# 7. V1 问题分解：发现 boundary artifact

V1 h26 pressure profile 中：

far-field bulk pressure gradients 与 observed velocity 的 plane-Poiseuille gradient 基本一致。

但出现两个额外贡献。

## 7.1 Moving-meniscus pressure jump

nominal：

[
P_{c,nominal}
=
4.045	imes10^{-3}
]

far-field extrapolated moving-meniscus：

[
P_{c,dynamic}
approx
3.086	imes10^{-3}
]

比值：

[
P_{c,dynamic}/P_{c,nominal}
approx0.763
]

## 7.2 Boundary pressure loss

reservoir / membrane transition 额外损失：

[
Delta p_{boundary}
approx1.294	imes10^{-3}
]

按 observed Poiseuille gradient：

[
|dp/dx|
approx6.85	imes10^{-6}/lu
]

折算：

[
L_{eq,boundary}
approx189 lu
]

独立 doubled-length diagnostic 给出：

[
L_{eq}
approx193 lu
]

两种独立方法结果非常接近。

### 结论

V1 的主要误差源之一被定位为：

> **open-system reservoir/membrane implementation 引入的大型 localized hydraulic resistance。**

---

# 8. V1 的 boundary implementation 问题

原 V1 layout：

- liquid reservoir；
- inlet membrane；
- active slit；
- outlet membrane；
- gas reservoir。

但关键缺陷是：

- pinned reservoir 和 membrane 的分离方式不够干净；
- active flow region 与 forcing transition 距离不足；
- 与项目中真实 graphite open-system 已验证的 buffer convention 不一致。

因此 V1 不能用于直接判定 wall-colour dynamic wetting 的精度。

---

# 9. V1b — Boundary / Static Pc / Dynamic Pc Separation

Candidate：

`a9c6db87da2eeb3572607152391fe6863394ebee`

主要新实现：

`tests/levelc_v1b.py`

这一阶段仍然 **没有修改 core solver**。

---

# 10. V1b 改动 1：open boundary layout 重构

## Before

V1 中 boundary forcing 与 active flow region 耦合过强。

## After

V1b 使用：

```text
3 lu wall
| 8 lu pinned reservoir
| 1 lu membrane
| 2 lu open buffer
| active slit
| 2 lu open buffer
| 1 lu membrane
| 8 lu pinned reservoir
| 3 lu wall
```

例如 h26 short case：

```text
liq_res  [3,11)
mem_in   x=11
buffer   [12,14)
slit     [14,250)
buffer   [250,252)
mem_out  x=252
gas_res  [253,261)
```

关键改变：

- reservoir mask 与 membrane 不重叠；
- membrane 与 active slit 之间加入普通 fluid buffer；
- h26 / h40 只改变 y-height，不改变 x-boundary architecture。

### 类型

**BC implementation change**

---

# 11. V1 → V1b：直接 simulation 改善

## 11.1 h26 front speed

V1：

[
V=3.8572	imes10^{-3}
]

V1b：

[
V=4.9743	imes10^{-3}
]

提升：

[
+28.96%
]

即约 **+29%**。

---

## 11.2 Raw hydraulic mismatch

V1 h26：

**58.4%**

V1b h26：

**26.2%**

误差幅值减少约：

**55%**

h40：

- V1：73.7%
- V1b：43.8%

误差幅值减少约：

**41%**

> 注意：这里的 raw mismatch 后来被证明不是最佳 validation metric，因为它默认 localized boundary intercept = 0。

---

# 12. V1b 改动 2：same-slit static capillary calibration

V1b 新增：

- x-periodic straight slit；
- no reservoirs；
- no membranes；
- no forcing；
- same `psi_solid=-0.68`；
- h=26 / h=40。

目的：

> 判断已有 droplet contact-angle registry 是否能直接移植到 slit geometry。

## 结果

| h | Pc_static | C_static = Pc·h/(2σ) | θ_static_slit |
|---:|---:|---:|---:|
| 26 | 3.1316e-3 | **0.6705** | **47.9°** |
| 40 | 2.2845e-3 | **0.7525** | **41.2°** |

droplet registry：

[
cos30^circ=0.8660
]

### 当前解释

h26 → h40 时 C_static 明显向 registry 靠近。

h26/h40 relative difference：

**11.53%**

略高于 V1b 原 10% consistency gate。

但这一结果更合理的解释是：

> **static slit calibration 尚未 resolution-converged。**

而不是已经证明 wall-colour registry 失效。

两点 `1/h` 线性外推仅作为诊断：

[
C(h)=C_infty-a/h
]

由 h26 / h40 两点得到：

[
C_inftyapprox0.905
]

对应约：

[
	heta_inftyapprox25.2^circ
]

这与 30° registry 属于相近范围，但两点不足以支持正式外推结论。

---

# 13. V1b 改动 3：pressure measurement 算法升级

## V1

早期 diagnostic 曾使用 near-interface fixed slabs。

问题：

- diffuse interface；
- curved meniscus；
- wall geometry

会污染局部 pressure measurement。

## V1b

改为：

1. liquid far-field linear pressure fit；
2. gas far-field linear pressure fit；
3. 两条线 extrapolate 到 meniscus reference position；
4. 得到：

[
P_{c,dynamic}
]

### 类型

**DIAG implementation change**

### 仍存在的问题

固定离 meniscus 12 lu 的 band 仍会部分碰到 interface-distortion zone。

V1b reviewer 发现绝对 Pc_dynamic 对 band choice 仍约有 **8–9%** methodology sensitivity。

因此 V1c 将继续改成：

> bulk-phase clearance based band selection，而不是固定 x-distance。

---

# 14. V1b 改动 4：长度差分验证替代绝对速度验证

这是目前最重要的 validation improvement。

原 raw gate：

[
V_{meas}
stackrel{?}{=}
rac{P_c h^2}
{12mu L}
]

它隐含：

[
L_{local}=0
]

但 simulation 已经证明 open boundary 存在 localized resistance。

因此定义：

[
L_{eff}
=
rac{P_{c,dynamic}h^2}
{12mu V_{meas}}
]

并使用：

[
L_{eff}=aL+L_0
]

其中：

- (a)：bulk slit hydraulic slope；
- (L_0)：localized boundary resistance 的 equivalent-length intercept。

---

# 15. h26 differential hydraulic result

## Short case

[
L_1=241
]

[
P_{c,1}=2.884386	imes10^{-3}
]

[
V_1=4.974326	imes10^{-3}
]

得到：

[
L_{eff,1}=326.65
]

## Long case

[
L_2=477
]

[
P_{c,2}=3.038931	imes10^{-3}
]

[
V_2=3.000209	imes10^{-3}
]

得到：

[
L_{eff,2}=570.60
]

所以：

[
a
=
rac{Delta L_{eff}}{Delta L}
=
1.034
]

理想 plane-Poiseuille：

[
a=1
]

bulk hydraulic differential error：

[
3.4%
]

### 当前最重要的 numerical result

> **h26 下，增加普通 slit 长度所增加的 hydraulic resistance 与 plane-Poiseuille 理论只差约 3.4%。**

这说明：

- bulk viscous transport 基本正确；
- raw front-speed mismatch 的主要问题不是 distributed slit resistance；
- 剩余主要表现为 localized intercept。

拟合：

[
L_{eff}approx1.034L+77.5
]

---

# 16. Localized resistance 的改善

V1 boundary equivalent-length estimate：

[
sim189-193 lu
]

V1b h26 differential fit intercept：

[
sim77.5 lu
]

按约 190 lu baseline 计算：

**约减少 59%**。

因此 boundary layout 重构确实取得了实质改善。

注意另一种不校正 Pc 差异的 two-speed formula 得到约 117.7 lu。

两者不同的原因是 short/long cases 的 `Pc_dynamic` 本身相差约 5%。

因此后续优先使用：

[
L_{eff}=rac{P_ch^2}{12mu V}
]

的 Pc-aware differential method。

---

# 17. 当前“精度”应该怎样表述

截至 V1b，不应该只用一个“误差百分比”描述整个算法。

更合理的是拆成四层。

## 17.1 Core bulk hydrodynamics

Poiseuille baseline：

- efficiency = 0.9933；
- ≈ **0.67% mean-flow error**。

V1b h26 differential bulk slope：

- 1.034；
- ≈ **3.4% differential resistance error**。

**状态：较好。**

## 17.2 Surface tension

Laplace：

- σ relative error ≈ **0.29%**；
- R² = **1.00000**。

**状态：较好。**

## 17.3 Static wettability

flat droplet：

- ≈30°。

slit：

- h26 ≈47.9°；
- h40 ≈41.2°；
- 尚未 resolution-converged。

**状态：需要 V1c resolution study。**

## 17.4 Open-boundary dynamic filling

V1 → V1b：

- h26 front speed +29%；
- localized resistance 约减少 59%；
- 但 absolute raw `V/V_hyd` 仍不等于 1。

**状态：bulk law 已显著澄清，boundary intercept 尚存在。**

---

# 18. 哪些结论目前不能说

当前还不能声称：

- “dynamic contact angle 已被验证”；
- “30° static droplet angle 可直接用于 slit dynamics”；
- “open reservoir boundary 已无附加阻力”；
- “真实 battery filling time 已定量验证”；
- “V1b raw V/Vhyd fail 说明 CG solver 错”。

当前可以说：

1. bulk single-phase hydrodynamics 正确；
2. surface tension calibration 正确；
3. matched-viscosity two-phase front obeys constant-velocity form；
4. V1 原 boundary layout 有显著 artifact；
5. V1b boundary layout 使该 artifact 明显下降；
6. h26 incremental slit resistance 已在约 3.4% 内满足 hydraulic theory；
7. static slit wettability 存在明显 resolution dependence。

---

# 19. 实现文件映射

## V0

`tests/levelb_laplace.py`

- harness/output bug fix；
- no numerical model change。

## V1

`tests/levelc_imbibition.py`

主要实现：

- single-front slit；
- front extraction；
- constant-velocity / x² 两种 fit；
- reservoir mass accounting；
- pressure/velocity diagnostics。

辅助：

- `tests/levelc_diag_front.py`
- `tests/levelc_diag_axial.py`
- `tests/levelc_diag_lscan.py`

## V1b

`tests/levelc_v1b.py`

主要实现：

- corrected reservoir/membrane/buffer layout；
- x-periodic static slit Pc calibration；
- improved dynamic pressure budget；
- h26/h40 corrected dynamic run；
- h26 2L length differential；
- producer-bound provenance。

---

# 20. Simulation evidence 位置

## V0

Control evidence：

`.agent/evidence/BI-VALIDATION-001/V0/V0/`

## V1

Product results：

`results/levelc_v1/`

Control review：

`.agent/evidence/BI-VALIDATION-001/V1/V1/`

## V1b

Product branch：

`agent-task/BI-V1B-DIAGNOSTIC-001`

Product results：

`results/levelc_v1b/`

主要文件：

- `EXECUTION_REPORT.md`
- `PROVENANCE.md`
- `MANIFEST.json`
- `summary.json`
- `pressure_budget.csv`
- per-run CSV / JSON / log

Control review：

`.agent/evidence/BI-V1B-DIAGNOSTIC-001/`

---

# 21. V1c 计划：下一次精度闭合

V1c 不计划修改 solver。

只补两个问题。

## 21.1 Static resolution convergence

新增：

- h=60；
- h=80。

与：

- h=26；
- h=40

一起分析：

[
C_{static}(h)
]

以及：

[
	heta_{static}(h)
]

判断是否收敛到稳定 plateau / continuum trend。

## 21.2 h40 differential hydraulic check

新增：

- h40 short；
- h40 approximately 2L。

计算：

[
a_{40}
=
rac{Delta L_{eff}}{Delta L}
]

hard engineering target：

[
|a_{40}-1|le10%
]

同时使用新的 bulk-clearance pressure bands 重新计算 h26 differential slope。

### V1c 之后的核心判据

如果：

[
a_{26}approx1
]

且：

[
a_{40}approx1
]

并且 static `C(h)` 显示 coherent convergence，

则可以认为：

> single-front capillary-flow 的 bulk hydraulic mechanism 已得到足够验证，可进入 bilateral-front interaction V2。

---

# 22. 后续强制更新规则

从 V1c 开始，每个 scientific stage 都必须追加本文件。

每次更新至少包含：

```text
Stage / Task ID
Base SHA
Candidate SHA

Change class:
SOLVER / BC / VAL / DIAG / HARNESS

Problem before change:
...

Implementation delta:
...

Files changed:
...

Simulation cases:
...

Before metrics:
...

After metrics:
...

Accuracy change:
...

What improved:
...

What did NOT improve:
...

Interpretation:
...

Remaining limitations:
...

Evidence paths:
...
```

---

# 23. 当前总体状态

截至 V1b：

```text
Core CG-LBM solver
        │
        ├─ bulk hydrodynamics      validated baseline
        ├─ surface tension         validated baseline
        ├─ static droplet wetting  validated baseline
        │
        └─ single-front slit
             │
             ├─ reference law corrected
             ├─ boundary layout improved
             ├─ front speed +29%
             ├─ localized resistance ~59% lower
             ├─ h26 bulk differential error ~3.4%
             └─ static slit resolution convergence unresolved
                        ↓
                       V1c
```

当前没有证据要求修改 core solver。

下一阶段重点仍然是：

> **把 boundary / finite-resolution / measurement effects 从 core solver accuracy 中彻底剥离。**
