# 算法说明 — 3D color-gradient 两相 LBM（CG3D）

本文说明 `lbm_solver_cg3d.py` 实现的方法，以及 `run_pcs_cg3d.py` /
`run_ir_cg3d.py` 的驱动方式。开新 run 时改什么参数，见操作参考
[`BC_IC_OUTPUT.md`](BC_IC_OUTPUT.md)。英文版：[`ALGORITHM.md`](ALGORITHM.md)。

## 1. 模型概览

| 项 | 选择 |
|---|---|
| 格式 | Rothman–Keller **color-gradient** 两相 LBM（Leclaire 系） |
| Lattice | D3Q19 |
| 碰撞 | MRT，19 moment，Lallemand–Luo 型基（cond(M)=4.3） |
| 相 | "red" = non-wetting（gas），"blue" = wetting（liquid），密度比 1 |
| 表面张力 | 直接输入：参数 `CapA`，实测 σ = **1.012·CapA** |
| 润湿性 | 逐节点 `psi_solid` 场（几何 adhesion），无伪液膜 |
| 驱动 | ρ-Dirichlet ψ 边界 reservoir + 双色 semi-permeable membrane → 带压力边界的开放系统，capillary pressure 阶梯 |
| 后端 | Taichi；默认 GPU（CUDA），`LBM_ARCH=cpu` 强制 CPU |

界面宽 ≈ 2.2 lu，recoloring 各向异性 < 0.1 %（静态液滴实测）。

## 2. 颜色场与相语义

每个流体节点携带两个 distribution function：f_r 与 f_b。颜色（序参量）场为

```
psi = (rho_r - rho_b) / (rho_r + rho_b)
```

ψ = +1 为纯 red（non-wetting / gas），ψ = −1 为纯 blue（wetting /
liquid）。总密度 ρ = ρ_r + ρ_b 承载压力（p = cs²ρ，cs² = 1/3），由
reservoir 规定；颜色场由下述 recoloring 步骤输运。上游代码在此公式有一个
括号 bug（`rho_r - rho_b/(rho_r+rho_b)`）；本代码用上面的正确形式。

## 3. 碰撞：含 ρ 的 19-moment MRT 平衡态

MRT 碰撞将 moment m = M·f 弛豫到多项式平衡态 meq = M·feq(ρ, u)。本移植的
关键数值贡献：**完整携带 ρ 的 19 个平衡 moment 闭式**（上游 3D 代码缺 ρ
因子——在 ρ ≡ 1 时不可见，一旦 density-driven 压力边界把 ρ 推离 1 即失效）：

```
m0  = rho                                  (density)
m1  = rho * u^2                            (energy)
m2  = 0                                    (eps)
m3, m5, m7   = rho*ux, rho*uy, rho*uz      (momenta)
m4, m6, m8   = 0                           (energy fluxes)
m9  = rho*(2ux^2 - uy^2 - uz^2)            (pxx)
m11 = rho*(uy^2 - uz^2)                    (pww)
m13, m14, m15 = rho*ux*uy, rho*uy*uz, rho*ux*uz   (shears)
m10, m12, m16, m17, m18 = 0
```

一次性推导并与直接 M·feq 乘积核对到 4.4e-16（200 个随机 ρ/u 点，f64）。

Relaxation 布局（S）：conserved moment 0,3,5,7 不弛豫；stress 族
1,2,9–15 承载黏性弛豫 `sv`；其余 4,6,8,16,17,18 用 `sother`。

## 4. 表面张力与 recoloring

表面张力以**平衡 moment 扰动**的形式注入（打进五个 stress/trace moment
1, 9, 11, 13, 14, 15），由 `CapA` 参数化。在本代码中 CapA 就是 lattice
unit 下的表面张力：σ = 1.012·CapA（13 液滴 Laplace 拟合，R² = 1.0000）——
与 pseudopotential（Shan–Chen）模型不同，σ 是直接输入而非涌现输出。

碰撞后，**Latva–Kokko recoloring** 在界面处重新分离两色：f_r/f_b 按局部
颜色梯度方向沿各 lattice 方向重新分配，并通过方向对
kk = 1,3,5,7,9,11,13,15,17 施加 anti-anisotropy 修正。界面因此保持在
~2.2 lu 宽、各向异性 <0.1 %——这是在欠分辨真实几何上相对 diffuse-interface
模型的决定性优势。

## 5. 黏度

随附 run 中两相黏度匹配（ν_r = ν_b = 0.1）。solver 在界面处用标准的
colour-mass 加权公式插值弛豫频率（wl/wg/lg0/l1/l2/g1/g2），因此支持不等
黏度，但石墨线未测试（μ_r ≠ 1 是母项目的 open item）。

## 6. 润湿性

Solid 节点携带逐节点 `psi_solid` ∈ [−1, +1] 场（"壁色"）。润湿性由
recoloring 在固体表面几何地涌现——无伪液膜，且写入空间变化场即可实现
mixed-wet。标定的 contact-angle registry（平板液滴，液侧角）：

| psi_solid | −0.75 | **−0.68** | −0.25 | 0 | +0.25 | +0.7 |
|---|---|---|---|---|---|---|
| θ_liq | 21.1° | **≈30°（电池电极口径）** | 83.9° | 95.7° | 112.9° | 157.1° |

本 repo 所有石墨 run 用 ψ_solid = −0.68（θ ≈ 30°）。

## 7. 上游来源与四个已修复缺陷

数值表（moment matrix M、bounce-back 映射、张力注入模式、recoloring 对、
relaxation 布局）取自上游模块
[yjhp1016/taichi_LBM3D](https://github.com/yjhp1016/taichi_LBM3D) 的
`lbm_solver_3d_2phase.py`；class 结构、infrastructure 与 kernel 顺序来自
本项目已验证的 2D canonical solver。上游四个已知缺陷**未**被继承：

1. meq 缺 ρ 因子（破坏 ρ-pressure 驱动；已修复——§3）；
2. ψ 括号 bug（§2）；
3. ψ_solid 只支持标量（已修复：逐节点场）；
4. 模块级网格全局变量、无 infrastructure（已修复：class-based，含
   race-free 双色 membrane 与 f64 flux 计数 reservoir）。

## 8. 开放系统压力边界

域是沿 x（流动方向）开放的 slab，两端在 reservoir 之后由墙封死：

```
x:  0        3            11 12  14                    214  217 218        225   228
    | wall   | res_in     | M |buf|   GRAPHITE (真实结构)  |buf| M  | res_out  | wall |
    | 3 lu   | 8 lu       | 1 |2lu|        200 lu        |3lu| 1  | 8 lu     | 3 lu |
      BB       rho=1+d/2   只过气   开放 buffer            开放    只过液      BB
               psi=+1              (NaN 修复, §10)                  psi=-1
```

- **Reservoir**（8 lu）：规定 ρ（ρ_in = 1+δ/2，ρ_out = 1−δ/2）并钉住 ψ
  （+1 气源 / −1 液汇）。Capillary pressure 为 Pc = δ/3（cs² = 1/3）。
  升/降 δ 即 drainage/imbibition 驱动。
- **Semi-permeable membrane**（1 lu）：单平面 ψ 条件 bounce-back——入口膜
  只过 red（气），出口膜只过 blue（液）。双色 race-free 实现；石墨 run 实测
  泄漏 ~2e-8 pore volume/步。
- **墙**：普通 bounce-back（无滑移）。**y/z**：periodic（真实立方跨面的人为
  连通性为已声明伪影）。

两相都能经由各自的膜离开域，因此系统是真正开放的：drainage 时气从入口进、
液从出口出，imbibition 反向——没有 closed-system 的 saturation 伪影。

## 9. Timestep 顺序与 run 协议

每步 kernel 顺序（与 2D canonical 一致）：`collision(+recolor) → F=0 →
streaming1（atomic accumulate，ψ 条件 membrane bounce-back）→
Boundary_condition → streaming3 → Boundary_condition_psi →
apply_reservoirs`。

Run 协议（两个驱动相同）：

1. **Equilibration**：δ = 0 跑 20 000 步。初始条件：孔隙充满液（ψ=−1）；
   入口 reservoir + 入口膜预置气。
2. **阶梯**：对 `--ds` 中每个 δ，跑到 quasi-steady（颜色通量容差 5e-7 /
   15 000 步窗 / 最少 15 000 步）或 150 000 步帽；每 500 步记录
   saturation 与通量；每 20 000 步落一帧 ψ 快照（`--dump-every`），每档
   末加保底帧，并写增量 `report_partial.json`。
3. **Imbibition**（`run_ir_cg3d.py`）：排水臂停在目标 S_i，`--ds-imbibe`
   逐档降 δ 到 0，状态单实现跨档延续（一条连续压力路径历史）。

## 10. 粗糙面 buffer 规则

在亚体素粗糙的真实几何上，reservoir/membrane 强制条件**不得**压在固体面上：
1 lu 宽的喉道同时承受"规定 ρ/ψ"与"两壁 bounce-back"的不相容约束，ρ 塌 0
并在 ~200 平衡步内发散（`probe_gx1_nan.py` 五变体探针链定位；同布局在光滑
球堆表面稳定）。修复是纯几何的、**solver 零改动**：两端各垫
k ≥ reservoir(8) + 膜(1) + 净通道(2) + 余量 lu 的开放孔隙（此处 k = 14；
k = 4 仍 NaN）。`make_geo_buffer.py` 实现之。

## 11. 验证状态（母项目）

Solver 在接触真实几何前经过了独立的验证阶梯（数字来自母项目验证报告；对应
驱动脚本不在本 repo 内）：

- Laplace：σ = 1.012·CapA，13 液滴，逐例 ΔP–1/R 拟合 R² ≥ 0.9999；
- §6 的 contact-angle registry；infrastructure 套件 8/8（含 250k 步
  longrun 与 membrane/reservoir 质量核算）；
- 有序球堆单相渗透率 vs Sangani–Acrivos 解析界：solid fraction 0.3–0.971
  范围内 0.98–1.04（在 superficial-velocity 修正之后——Darcy flux 必须对
  *全部*节点平均，绝不能只对流体节点）；
- Finney random close packing 排水：percolation knee 在 C = Pc·R/σ = 6.38，
  落在文献 θ = 0°/30° 网络模型曲线之间；imbibition 圈闭 S_nr = 0.162–0.200，
  与网络模型带一致。

`RESULTS_zh.md` 中的石墨数字继承这一验证谱系，但携带自身的分辨率 caveat
（见其 §6）。

## 12. 单位与参数约定

所有参数为 lattice unit（lu）。σ = 1.012·CapA；Pc = δ/3；随附几何的
voxel 尺寸 0.128 µm（BIL 原生）。驱动支持物理时间换算
t_phys = t_lu·Δx²/ν_phys，探索级 run 未启用（只做 dimensionless-group
匹配）。随附 run 基线：CapA = 0.06，ψ_solid = −0.68，ν_r = ν_b = 0.1。
