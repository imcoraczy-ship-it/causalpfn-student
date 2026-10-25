# E1.5 星图实验

原始成果在 `notebooks/E1_5_star_experiment.ipynb`，本流程不执行或改写它。
固定 N=200、M=50、中心节点 0、family=0，复用原机制生成器、
`_components`、`structural_outcome`、`arm_mean_exposure` 和冻结 J 公开接口。

从 Git 仓库根目录执行下列命令。`python` 应指向安装了项目依赖的 Python 3.12
环境（本机已有环境为 `C:\Users\48228\.venvs\ipfn312\Scripts\python.exe`）。
环境依赖定义在 `iPFN_demo/code/sparse_j/requirements.txt`。

```powershell
python -B iPFN_demo/code/sparse_j/scripts/e1_5_star.py --output iPFN_demo/results/e1_5_smoke_new --compare-notebook iPFN_demo/notebooks/E1_5_star_experiment.ipynb
```

默认仅运行机制 0、配对重复 0、中心 T=0/1，即两次预测。输出目录必须不存在。
可从任意工作目录以脚本绝对路径运行；相对输出路径以当前工作目录为准。

设计检查（不加载模型、不做预测）：

```powershell
cd iPFN_demo/code/sparse_j
python -B -m unittest scripts.test_e1_5_star -v
```

## 随机性和配对

- `--mechanism-ids` 和 `--repeat-ids` 接受显式整数列表；默认均为 `0`。
- `--seed` 默认 `20261024`，只控制处理、噪声和观测集合；机制自身的种子与
  dev 配置由原生成器控制，并在 manifest 中记录。
- 重复 0 使用 `default_rng(seed + mechanism_id)`，抽取顺序严格保持原 Notebook：
  叶子处理、噪声、观测排列。
- 新增重复使用 `SeedSequence([seed, 2026102501, mechanism_id, repeat_id])`。
  配对内共享叶子处理、噪声和观测索引，只改变中心处理。
- 每个任务独立进行后验条件化，配对间不累积模型状态。权重冻结，CPU/BLAS 线程数固定为 1。

## 文件和指标

- `manifest.json`：完成状态、Git commit、源码/资源 SHA256、依赖、模型配置、
  机制配置、随机流、观测索引、中心是否被观测、逐任务推断时间及外推耗时。
- `m*_r*_t*_input.npz`：严格五个事实输入数组，不含隐藏结果和模拟真值。
- `m*_r*_t*_evaluation.npz`：真值、预测、节点效应及逐节点带符号误差；仅供评测，不能当成模型输入。
- `metrics.csv`：每任务 × 中心/叶子的四状态 RMSE、三效应 RMSE、偏差及类别平均效应真值/预测。
- `support.csv`：每任务 × 中心/叶子 × 四状态的已观测数量、经验覆盖标记及状态 RMSE。
- `notebook_comparison.json`：可选，与 Notebook 保存的机制 0 配对表格比较。
  原表只显示四位小数，因此 RMSE 容差为 0.000051；计数和布尔值要求完全一致。

三效应按 `10−00`、`11−10`、`11−00` 定义。中心效应 RMSE 是单节点绝对误差。
Support 指已观测结果中状态是否出现，不是设计正概率或可识别性证明。
叶子暴露等于中心处理；该配对比较不能单独识别 Support 的因果作用。
统计汇总应以机制为独立单位，不能把两次中心分配、各状态或叶子视作独立机制。

`status=complete` 表示全部结果写出且所请求的 Notebook 对照通过。
异常退出可能留下 `running` 状态；请保留该目录并用新目录重试。
输出文件的哈希记录在 manifest 中，不包括 manifest 自身。

## 完整性与 Windows 换行

保留原始字节 SHA256 校验：全部 experiment 配置资源以及 regional 推断源码都检查，
J 加载器还会自行校验权重。`.gitattributes` 仅将三个参与哈希的文本路径固定为 LF。
没有对哈希输入做运行时归一化，也没有修改权重或预期哈希。

## 当前验证范围

本轮只验证机制 0 的一组配对，不运行 20 机制 × 10 重复。
Notebook 中单次探索案例使用 `20261022/20261023`，与五机制配对的随机流不同；
本脚本对照的是五机制配对表格中机制 0 的两行中心分配，而非那个单次案例。
当前机制仍来自原 dev 生成配置，不能宣称已经完成独立测试集验证。
批量耗时按一次加载 + 20 次机制生成 + 200 组配对外推，只有一个样本，含首次推断效应，
未计解释器/依赖导入，不是正式性能基准。

## 2026-10-25 小规模验证记录

本地 Notebook 检查点：`631841b`，仅该 Notebook 被提交。Notebook 字节 SHA256
保持 `0FBC87BBB6C9C11A18B3510F179783F323D6922CA8488CAEDC462C7FF594D1A4`。

使用已有 ipfn312 环境：Python 3.12.10、NumPy 2.1.3、PyTorch 2.8.0、
threadpoolctl 3.5.0。四项设计检查通过；干净进程只执行机制 0、重复 0 的两次预测。
输出目录：`results/e1_5_smoke_20261025/`，状态 `complete`。

| 中心 T | 类别 | 四状态 RMSE | Direct RMSE | Spillover RMSE | Total RMSE |
|---|---|---:|---:|---:|---:|
| 0 | 中心 | 0.2491 | 0.4591 | 0.0047 | 0.4637 |
| 0 | 叶子 | 0.7720 | 0.3006 | 1.0041 | 0.9921 |
| 1 | 中心 | 0.3676 | 0.3803 | 0.0261 | 0.4064 |
| 1 | 叶子 | 0.4041 | 0.2662 | 0.5312 | 0.5197 |

40 项 Notebook 保存输出对照通过；最大 RMSE 差异为 0.0000480683，处于
四位小数舍入范围内。中心未被观测；叶子覆盖数量从 `[22,0,28,0]`
切换到 `[0,22,0,28]`，与原表完全一致。原 Notebook 没有保存完整预测数组，
所以这里验证了保存表格的一致性，不能宣称全精度预测逐元素等同于原内核变量。

保存结果又经过独立读回核对：五输入键、数组形状、观测索引、逐类别 RMSE、
16 行 Support 及全部输出文件哈希均通过。

- 进程外部 Stopwatch：2.6359 秒，含启动、依赖导入和全部文件输出。
- 依赖导入计时：1.6262 秒；导入后流程：0.2583 秒。
- 模型加载：0.0357 秒；机制生成及真值检查：0.0223 秒。
- 两次推断：0.0630、0.0046 秒；整组配对（含输出）：0.0761 秒。
- 一进程运行 20 机制 × 10 配对的简单外推：15.7104 秒，加一次启动/导入。
  首次推断较慢且只有一组实测，外推偏保守，实际批量耗时仍待测。

没有启动 400 次实验，也没有提交新增代码或结果、推送、创建 PR。

## 扩展 dev 星图评测 v1（冻结方案）

以下为新增的 schema 2 流程。原 schema 1 小规模结果原样保留，不适用新版严格验收器。
本轮只执行测速，不运行正式机制 1000–1019。

| 条件 | 正式方案 | 独立测速 |
|---|---|---|
| 机制编号 | 1000–1019 | 900–903 |
| 配对重复 | 0–9 | 0–4 |
| 中心处理 | 每组 0、1 | 每组 0、1 |
| 预测任务数 | 400 | 40 |
| 任务种子 | 20261024 | 20261024 |
| 图与观测 | N=200、M=50、family=0、中心 0 | 相同 |

仍使用原 dev 机制流：split_seed=331029，机制的图替换、特征、系数、真值、噪声
和 frozen-J 均不变。机制编号不重叠不代表已证明未参与模型训练或选择。
checkpoint 缺少可核实的训练/选择记录，因此结果只称扩展 dev 评测。

### Support 零计数

`support.csv` 新增 `full_graph_count`、`support_reason`、`center_observed`。
`metrics.csv` 也单独记录中心是否被观测。

- `conditional_structural_zero`：固定中心 T=c 后，叶子的 S≠c，或中心自身 T≠c。
  这是条件分配下不可覆盖，不能解释为原 IID 设计中的全局不可能状态。
- `assignment_zero`：该条件设计允许，但完整图在本次处理分配中没有该事实状态。
- `observation_sampling_zero`：完整图有该事实状态，观测子集没有。
- `covered`：已观测该事实状态。

中心是否被观测独立保存，不替代上述原因，也不与处理分配缺失合并。

### 主要指标与机制 Bootstrap

对机制 m、重复 r、叶子状态 a=(t,s)：

`delta[m,r,a] = RMSE(center=1-s, a) - RMSE(center=s, a)`。

先等权平均四状态，再平均同机制的重复，最后等权平均机制。
允许覆盖的分配即使恰好没有经验样本，也保留，不删行、不重新抽样。
使用种子 **2026102502** 做 **10000 次完整机制块重采样**，报告百分位 95% 区间。
只对最终机制均值重采样，等价于携带其全部重复与四状态整体重采样。
单机制时区间为 null；测速只有 4 机制，区间仅作探索性诊断。
这里是条件关联，不是 Support 的因果效应，不包含模型训练过程的不确定性。

新增输出：

- `paired_contrasts.csv`：每机制/重复/状态的配对差值。
- `mechanism_primary.csv`：每机制的主要指标。
- `mechanism_metrics.csv`：各机制、中心处理、节点类别的平均任务指标；不是池化 RMSE。
- `summary.json`：主要指标、机制数、Bootstrap 参数、区间与解释。
- `source_snapshot.zip`：完整包的 Python/JSON/依赖文件及实验说明、测试、换行配置的原始字节快照。
- manifest 增加 Git 分支/提交/状态/diff、命令、安装包版本、线程库、PyTorch 构建配置及逐任务资源探针。

### 严格验收

生成器先写 `running`，输出齐全后进入 `validating`，只有完整验收通过才写 `complete`。
任何异常都返回非零退出码；验证失败写 `validation_failed`，保留全部证据。
没有自动重试、换种子、跳过失败任务或覆盖已有目录。

验收重新从固定流生成事实数据，不执行任何模型预测，核对：
任务/配对/机制唯一性及冻结编号、五输入键、50 个唯一索引、(200,4) 预测、有限数值、
配对共享叶子处理/噪声/观测集合、同机制真值、全部 CSV 与 NPZ 指标、Bootstrap 汇总、
源码快照、现有源码、资产和输出哈希及完成状态。正式结果应为 400 任务、800 指标行、
3200 Support 行、800 个 NPZ；测速为 40/80/320/80。

从仓库根目录独立验收已完成的新目录：

```powershell
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_analysis.py iPFN_demo/results/e1_5_star_timing_v1_20261025
```

### 40 次测速命令与资源规则

```powershell
$py = 'C:\Users\48228\.venvs\ipfn312\Scripts\python.exe'
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_timing.py --output iPFN_demo/results/e1_5_star_timing_v1_20261025
```

监测器固定运行上述 40 次预测，独立新进程，一次模型加载，不增加暖机预测。
Windows 原生 API 以约 20 ms 采样工作集与私有内存，每任务另有进程资源探针。
记录首次/后续推断、外部实际墙钟、进程 CPU、原生工作集峰值、物理内存、CPU、
样本序列、stdout/stderr 及输出体积；不依赖额外安装。

内存增长诊断预先固定：排除前 4 任务，比较剩余序列首尾四分位的私有内存中位数，
当增量 >32 MiB 且斜率 >0.5 MiB/任务时标记 `investigate_growth` 并退出失败。
短试运行未触发不能证明长期没有内存泄漏。

`runtime_measurement.json` 与 `resource_samples.csv` 为外部监测回执；
`acceptance_report.json` 为进程结束后的独立验收；它们与 stdout/stderr 明确作为外部回执，
不纳入子进程在退出前生成的输出哈希清单。它们不替代内部科学结果验收。
400 次耗时外推为实测固定开销 +20 次机制生成 +200 组配对 +保守的 10 倍测速验收开销，
不宣称已经测过正式实验。
