# Windows 首次启动：交给 Z Code 执行

本文用于让 Windows 上的 Z Code 桌面会话完成一次性设置，并运行真实 dummy Round 1。日常任务由 Controller 启动 headless Z Code；桌面会话只负责本次安装与启动。

## 给 Z Code 的任务

请先阅读本仓库 `AGENTS.md`、`.agent/README.md` 和本文，然后执行以下步骤。可以创建专用 clone、复制本地配置、运行 Controller；Controller 可以向本仓库 control branch 和 dummy task branch 提交及 push。不得 merge、force-push、修改 Controller 实现或科学代码，不运行 GPU simulation，不安装软件或修改凭据。缺依赖或登录时停止并告诉用户具体需要操作什么。

不要让 executor 自己监听 GitHub，也不要由桌面会话直接完成 `ads_dummy.txt`；该文件必须由 Controller 调用的 headless executor 创建。

## 1. 检查现有环境

在 PowerShell 中检查：

```powershell
git --version
python --version
node --version
Test-Path 'C:\Program Files\ZCode\resources\glm\zcode.cjs'
node 'C:\Program Files\ZCode\resources\glm\zcode.cjs' --version
```

需要 Python 3.10+、Git、Node 和已登录的 Z Code。使用本机现有 Git 登录；若后续 push 要求认证，由用户完成，不读取或展示 token。版本检查不等于真实执行验收。

## 2. 准备专用 Controller clone

默认位置如下；若目录已存在，先确认它的 remote、当前分支和工作区状态。仅在它确为本仓库的干净专用 clone 时复用并 `git pull --ff-only`，否则选择新的空路径，不能覆盖已有目录或切换用户正在使用的工作区。

```powershell
git clone --branch agent-dev/step0-protocol `
  https://github.com/YangCui1994/cg3d-graphite.git `
  C:\dev\cg3d-graphite-controller

cd C:\dev\cg3d-graphite-controller
git status --short --branch
```

每条命令检查退出码，失败就停止，不能继续执行依赖该步骤的命令。确认 clone 内存在 `.agent/controller/controller.py`；缺失表示最新实现尚未推送或没有拉到正确分支。

## 3. 创建本地配置

仅在 `config.json` 不存在时复制，已有配置先读取，不能盲目覆盖：

```powershell
Copy-Item .agent\controller\config.example.json `
  .agent\controller\config.json
```

由 Z Code 核对、必要时修改这个被 Git 忽略的本地文件：

- `repository_path`：保持 `../..`，相对于配置文件，指向专用 clone。
- `control_branch`：`agent-dev/step0-protocol`。
- `worktree_root`：建议明确设为 `C:/dev/cg3d-agent-worktrees`。
- `worker_id`：`windows-zcode-01`。
- `zcode.command`：确认 Node 与 `C:/Program Files/ZCode/resources/glm/zcode.cjs` 可用。

不需要另装 Python 包。机器路径只保存在本地 `config.json`，不提交。

## 4. 运行真实 Dummy Round 1

先读取 `.agent/state.json`。首次运行应为 `ADS-DUMMY-001`、`round: 1`、`READY_FOR_EXECUTION`，并阅读对应 `.agent/tasks/ADS-DUMMY-001/round-01/TASK.md`。

若状态已是 `RUNNING`、`ERROR` 或 `AWAITING_REVIEW`，先报告实际状态并停止，不能重置状态或重复派单。

```powershell
python .agent\controller\controller.py `
  --config .agent\controller\config.json `
  --once
```

等待退出后检查实际状态及远端结果，不能仅凭退出码宣称成功：

```powershell
git fetch origin agent-dev/step0-protocol
git show origin/agent-dev/step0-protocol:.agent/state.json
git show origin/agent-dev/step0-protocol:.agent/tasks/ADS-DUMMY-001/round-01/evidence/process.json
git show origin/agent-dev/step0-protocol:.agent/tasks/ADS-DUMMY-001/round-01/EXECUTION_REPORT.md
```

成功交接应为 `AWAITING_REVIEW`，具有非空 session ID、candidate commit，以及远端 execution report 和 evidence。向用户汇报这些引用与实际错误（若有）。这证明真实 Round 1 的执行交接完成，仍需 ChatGPT 审查；不要自行写 PASS 或启动 Round 2。

## 5. 后续轮次

用户回到 ChatGPT 说“继续审查 ADS-DUMMY-001”。ChatGPT 检查真实证据后，决定是否写 Round 1 REVIEW 并发布 Round 2。Round 2 沿用 candidate 和 session ID。

下一轮 READY 已发布后，可再次执行上述 `--once` 命令。需要持续等待新任务时，在独立 PowerShell 窗口运行：

```powershell
cd C:\dev\cg3d-graphite-controller
python .agent\controller\controller.py `
  --config .agent\controller\config.json
```

第一轮验收阶段使用 `--once` 即可；不创建服务或计划任务。
