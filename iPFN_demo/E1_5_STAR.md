# E1.5 星图实验

> **公开协作版本。** 本文从本地保留的历史实验协议准备，机器专用路径已改成通用环境调用。原始实验字节验收依赖本地保留、未随本 PR 公开提供的冻结源码快照；本公开文档不是原件的逐字节替代。
>
> 历史阶段中“本轮不执行 formal”等表述保留用于说明当时的授权范围，不代表正式实验尚未完成。正式结论见 [ATE 结果说明](E1_5_STAR_ATE_RESULTS.md)，公开范围见 [公开交付说明](results/e1_5_star_ate_submission_v1/README_PUBLIC.md)。Spillover 总体覆盖率为 89.75%，未达 90%。
>
> 原始 Notebook、旧结果目录、完整证据 ZIP、原始审计材料和数学核验输入均未随本 PR 提供。下文带 `--compare-notebook` 的历史示例需要本地原始 Notebook；不要把这些示例理解为公开材料已含相应输入。

原始成果在 `notebooks/E1_5_star_experiment.ipynb`，本流程不执行或改写它。
固定 N=200、M=50、中心节点 0、family=0，复用原机制生成器、
`_components`、`structural_outcome`、`arm_mean_exposure` 和冻结 J 公开接口。

从 Git 仓库根目录执行下列命令。`python` 应指向安装了项目依赖的 Python 3.12
环境（先激活已有的兼容环境，再调用 `python`，不绑定机器专用目录）。
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
$py = 'python'
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_timing.py --mode pilot --output iPFN_demo/results/e1_5_star_timing_v1_pidfix_next
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

### 实际解释器 PID 资源监测修复

原40任务的科学结果保留且验收通过，但旧外部监测使用 `Popen` 的启动器句柄，
其 CPU 0.03125 秒不代表科研解释器的 CPU 总量。旧结果不覆盖、不回填。

新版监测经标准库 bootstrap 握手获得实际 PID/父 PID，并查询原生可执行文件路径；
解释器等待监测器打开自身句柄后才导入科研依赖。所有任务的 `resources.process_pid`
必须与该 PID 一致。启动器 CPU 单独列作 `launcher_cpu_excluded`，不与解释器累加；
工作集取同一实际进程的原生高水位，不累计采样值或父子工作集。

最终握手在科研脚本返回之后，覆盖导入、推断、输出、Bootstrap、内部严格验收和
manifest 完成写入。结束暂停时核对外部/内部 CPU；允许两个 Windows 15.625 ms 计费刻度
或1%的误差，取较大值。结束暂停之后的解释器退出 CPU 另行列出，完整 CPU 从创建至退出读取。
外部最终验收在监测器进程执行，不混入科研解释器的 CPU/内存统计。
若退出后内存计数不可用或已重置，会明确标记峰值只覆盖至目标完成边界，而不保证退出清理阶段。

新目录旁的 `_resources` 目录保存 PID 握手、stdout/stderr、原生采样及进程回执；
已有输出目录或该侧目录存在均拒绝运行。不会自动重试或换种子。

当前仅批准最小验证（机制900、重复0、两次预测）：

```powershell
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_timing.py --mode smoke --output iPFN_demo/results/e1_5_resource_smoke_pidfix_20261025
```

资源专项测试不进行预测，包含虚拟环境启动器和直接解释器两条路径，以及目标尾部
CPU/内存活动、Windows计费粒度、错误PID/CPU/峰值的拒绝测试：

```powershell
cd iPFN_demo/code/sparse_j
& $py -B -m unittest scripts.test_e1_5_star_resources scripts.test_e1_5_star -v
```

40任务必须显式指定 `--mode pilot` 并再次确认；本轮不运行。

## Star ATE 适配协议 v1（2026-10-29）

入口为 `scripts/e1_5_star_ate.py`，协议标识 `e1_5_star_ate_v1`。
只扩展预测与评估格式，不改变原星图 DGP、四状态真值、随机流或 frozen-J/核模型。
调用原 `build_world` / `make_pair`，不调用 benchmark 的非星图数据生成循环。

固定 N=200、M=50、family=0、中心节点0，方法顺序为 `j, kernel-old, kernel-new`。
输入流种子仍为20261024；重复0与新增重复分别沿用原标量种子及命名空间2026102501。
配对内共享叶子处理、噪声和观测集合，中心按0、1顺序执行。
每个方法收到同一规范输入的独立副本，并检查调用没有改变输入。
模拟器的真值不传入预测器。

| cohort | 机制 | 配对重复 | 上下文 | 三方法点预测调用 | J区间调用 |
|---|---|---|---:|---:|---:|
| smoke（默认） | 900 | 0 | 2 | 6 | 2 |
| pilot | 900–903 | 0–4 | 40 | 120 | 40 |
| pilot_fresh | 904–907 | 0–4 | 40 | 120 | 40 |
| formal | 1000–1019 | 0–9 | 400 | 1200 | 400 |

初次实现仅批准一个smoke。后续已批准新增pilot_fresh并执行一次；原pilot、smoke、formal映射保留。
本轮不执行formal。cohort不改变随机流派生规则或模型，但机制ID改变会改变实际随机样本。
`fit_seed=651013+100*mechanism_id+2*pair_repeat_id+center_t` 仅作兼容记录，三个冻结方法不使用它训练或抽样。

### 格式与调用

上下文为 `f0_m{mid}_r{2*pair_repeat_id+center_t}_observed50`，保留真实机制ID；
receipt 另存 pair_repeat_id、center_t、输入/真值文件哈希。不会将中心状态当作两个独立机制。

```text
RUN/
  run_manifest.json           # 状态、冻结计划、源码/资产/输出哈希、环境、Git、分项耗时
  execution.json             # benchmark兼容 receipts，机制/配对/观测信息
  source_snapshot.zip
  factual/<context>.npz      # 严格五数组，每上下文只保存一次
  truth/f0_m<mid>.npz         # arm_means[200,4]
  predictions/<context>__<method>.npz
  evaluation/                # 原evaluate.py的四张CSV
  report_views/center_t0/     # 过滤后的execution.json和evaluation四张CSV
  report_views/center_t1/
  acceptance_report.json
```

预测文件统一保存 arm_means、ite_effects、ate_effects及支持标记。
J的 ate_lower/ate_upper[3] 是三效应95%边际后验可信区间；核模型端点为NaN且区间支持为false。
ATE始终是全体200节点的效应平均，不是观测子集、中心或叶子单独的平均。
区间不增加未来观测噪声，不保证频率覆盖率达到95%或90%。

从仓库根目录，使用已有ipfn312环境，输出路径必须尚不存在：

```powershell
$py = 'python'
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_ate.py --cohort smoke --output <全新目录>
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_ate.py --cohort pilot_fresh --output <另一全新目录>
& $py -B iPFN_demo/code/sparse_j/scripts/e1_5_star_ate.py --validate --output <已完成的新协议目录>
```

原 evaluate.py、make_figures.py、make_table.py 保持不变。
主表按 center_t=0/1 分层，分别读取对应 report_views；避免将共享随机量的两个中心状态
作为独立重复来标记无偏样本方差。全体上下文的覆盖率、RMSE作为补充。

```powershell
& $py -B iPFN_demo/code/sparse_j/make_figures.py --input <RUN>/report_views/center_t0 --output <全新图目录0> --observed 50
& $py -B iPFN_demo/code/sparse_j/make_table.py --input <RUN>/report_views/center_t0 --output <全新表目录0> --observed 50
# center_t1 使用另一对全新输出目录；总体RMSE图可读取RUN本身。
```

图、表目录放在RUN之外，避免改变验收时冻结的科学产物清单。
report_views仅供报告读取，不是独立预测运行；原始NPZ保留在RUN。

### 分母、失败与统计

- J每效应主要报告 coverage_including_failures=covered/interval_requested；同时保留有效区间覆盖率、
  区间成功率、失败数与平均宽度。支持请求中的失败、缺失、非有限或反向区间不得删除或改成不支持。
- 两个核模型区间是N/A，不是0%覆盖率，不进入区间请求分母。
- ATE支持标记在此协议中表示方法声明的目标能力；点估计是否有效由有限性及failure另行判断。
  点计算失败仍记录 point_requested=1，point_valid=0；不会冒充未请求或零误差。
- 数值预测失败保留NaN和错误类型/信息，无自动重试、重抽种子或丢任务；完整性/输入被修改等协议错误硬停止。
- 三效应按direct(10−00)、treated spillover(11−10)、total(11−00)分别报告。
- 表格绝对条件bias：每机制内误差均值取绝对值，再平均机制；方差为机制内R−1样本误差方差的平均；
  RMSE在机制内平方误差平均、机制等权平均后开方。失败导致不完整机制时明确标记并不排名。
- Smoke分层后每机制只有一次重复，因此方差应为N/A；单机制覆盖率Monte Carlo标准误也应为N/A。
  Smoke的0%、50%或100%不能当作正式覆盖率结论。不能使用旧Support差值Bootstrap区间替代ATE区间。
- 覆盖率不确定性由原evaluate.py按(family,mechanism)聚类；dev仍不能宣称为已证实独立的测试集。

验收核对冻结任务全集、配对流重建、同机制真值、三方法输入哈希、点估计/区间字段、失败请求、
全部评价CSV与分层视图、实际上游读取器、源码快照及资产/输出哈希。
只有验收通过才写complete；预测数值失败的记录可以被完整验收接纳，但会明确计数，不能解释为预测成功。
原有结果不覆盖、不改格式；新适配器只写新目录。

专项测试不加载真实模型，不进行实际预测；另行Smoke才做6次点预测及2次J区间计算：

```powershell
cd iPFN_demo/code/sparse_j
& $py -B -m unittest scripts.test_e1_5_star_ate scripts.test_e1_5_star scripts.test_e1_5_star_resources -v
```

### pilot_fresh编号及随机流（2026-10-29修订）

pilot_fresh固定为904–907，重复0–4，中心顺序0、1。它与已有900–903及正式1000–1019不重叠；
40上下文共120次点预测，40次J区间计算（120个效应区间）。旧cohort映射及其验收行为不改。
验收仍通过完整的 `plan == frozen_plan(cohort)` 核对，不接受任意编号、换种子或部分任务。

机制ID参与原 `phase5_large_network.seed_entropy`：
`(split_seed, namespace, split_code, setting_id, base_setting_id, N, mechanism_id, channel, repeat_id)`。
本实验split为dev、split_seed=331029、namespace=2026101605。X、总体均值、系数等随机通道因此是新样本。
底层生成器先生成的原图虽被星图替换，X/h/系数及星图真值均按新ID确定；不宣称与旧pilot同样本。

配对随机流仍使用PCG64：重复0的标量种子分别为20261928、20261929、20261930、20261931；
重复1–4为 `[20261024, 2026102501, mechanism_id, pair_repeat_id]`。
配对内仍共享叶子处理、噪声、观测集合；三方法仍共享同一上下文的事实输入和真值。
execution.json记录每上下文rng_entropy、bit_generator、观测索引，每机制记录生成配置及来源哈希；
run_manifest.json和源码快照记录实际派生代码及模型资产，足以追溯新随机样本。
