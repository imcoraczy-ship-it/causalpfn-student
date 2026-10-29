# E1.5 Star 节点误差与 Support：公开补充分析

本目录是已有正式预测的纯后处理公开摘要，协议为 `e1_5_star_saved_node_support_v1`。没有新增模型预测、训练、DGP 或正式实验，也没有重跑原 `--validate`。保留全部20个机制、200组配对、400个上下文及1200个方法—上下文组合，无任务筛除。

原正式 ATE 结果不变：Direct 386/400=96.50%，Spillover **359/400=89.75%，未达到90%目标**，Total 373/400=93.25%。baseline 区间仍为 N/A。不能由本分析宣称 J 全面优于 baseline。

全部结果来自已经保存的真值、事实输入和预测；没有模型调用、训练、DGP生成或 --validate。冻结函数以只含四个函数的 AST 提取方式执行，没有导入项目推断模块。

## 指标与汇总

- 中心为节点0，叶子为节点1–199；每个上下文先在类别内部平均，未用199个叶子扩充机制权重。
- 四状态为00、01、10、11；Direct=10−00，Spillover=11−10，Total=11−00。
- bias=mean(pred−truth)，MAE=mean(abs(pred−truth))，MSE=mean((pred−truth)^2)，上下文RMSE=sqrt(MSE)。
- 先平均同机制的10次重复，再等权平均20机制；中心T=0/1分别报告。汇总列rmse（亦列为mean_context_rmse）是上下文RMSE的平均，保持冻结summarize语义；pooled_rmse是sqrt(平均MSE)，是另一个指标。
- center_minus_leaf文件的true_mean/pred_mean是中心平均效应减叶子平均效应；bias/MAE/RMSE描述该差异估计的误差。额外center_minus_leaf_bias/mae/rmse列是两类误差指标的差，不能与差异估计的MAE/RMSE混称。
- Support保留conditional_structural_zero、assignment_zero、observation_sampling_zero、covered四个冻结名称；另列结构允许、实际产生、实际观测。center_observed是独立字段。
- model_arm_supported是模型能力标记，不是经验Support；没有把全体ATE或ATE区间当作中心/叶子效应或节点区间。

## 中心/叶子误差

以下为冻结四状态合并响应RMSE的上下文均值，先按机制平均；不是四个状态RMSE的简单平均。逐状态均值、bias、MAE和RMSE见 [响应分层汇总](response_overall_by_center.csv) 和 [机制级响应](response_mechanism.csv)。

| 中心T | 方法 | 中心响应RMSE | 叶子响应RMSE |
|---:|---|---:|---:|
| 0 | j | 0.468063 | 0.602225 |
| 0 | kernel-old | 0.467046 | 0.638793 |
| 0 | kernel-new | 0.488948 | 0.643881 |
| 1 | j | 0.431337 | 0.524968 |
| 1 | kernel-old | 0.385468 | 0.511814 |
| 1 | kernel-new | 0.395020 | 0.508793 |

节点效应误差（rmse为上下文RMSE的机制等权均值）：

| 中心T | 方法 | 效应 | 中心RMSE | 叶子RMSE |
|---:|---|---|---:|---:|
| 0 | j | direct | 0.358992 | 0.344393 |
| 0 | j | spillover | 0.044276 | 0.769667 |
| 0 | j | total | 0.373520 | 0.885179 |
| 0 | kernel-old | direct | 0.351074 | 0.351843 |
| 0 | kernel-old | spillover | 0.044057 | 0.771703 |
| 0 | kernel-old | total | 0.363752 | 0.895181 |
| 0 | kernel-new | direct | 0.350678 | 0.359255 |
| 0 | kernel-new | spillover | 0.043524 | 0.817547 |
| 0 | kernel-new | total | 0.369433 | 0.951457 |
| 1 | j | direct | 0.327920 | 0.396330 |
| 1 | j | spillover | 0.032931 | 0.638342 |
| 1 | j | total | 0.329732 | 0.666197 |
| 1 | kernel-old | direct | 0.338712 | 0.410457 |
| 1 | kernel-old | spillover | 0.032778 | 0.580891 |
| 1 | kernel-old | total | 0.335347 | 0.641445 |
| 1 | kernel-new | direct | 0.320345 | 0.393613 |
| 1 | kernel-new | spillover | 0.030821 | 0.576527 |
| 1 | kernel-new | total | 0.319471 | 0.649957 |

## Support 原因与误差关联

支持原因计数以一个上下文×一个类别×一个状态为一例（每中心状态800例），不是800个独立样本。三方法共享事实输入，因此计数相同，仅列J避免三倍计数。

| 中心T | 类别 | 原因 | 例数/800 |
|---:|---|---|---:|
| 0 | center | conditional_structural_zero | 400/800 |
| 0 | center | assignment_zero | 200/800 |
| 0 | center | observation_sampling_zero | 159/800 |
| 0 | center | covered | 41/800 |
| 0 | leaf | conditional_structural_zero | 400/800 |
| 0 | leaf | assignment_zero | 0/800 |
| 0 | leaf | observation_sampling_zero | 0/800 |
| 0 | leaf | covered | 400/800 |
| 1 | center | conditional_structural_zero | 400/800 |
| 1 | center | assignment_zero | 200/800 |
| 1 | center | observation_sampling_zero | 159/800 |
| 1 | center | covered | 41/800 |
| 1 | leaf | conditional_structural_zero | 400/800 |
| 1 | leaf | assignment_zero | 0/800 |
| 1 | leaf | observation_sampling_zero | 0/800 |
| 1 | leaf | covered | 400/800 |

冻结主差值为叶子四状态“条件性结构不可覆盖中心分配下RMSE − 允许覆盖中心分配下RMSE”，先平均四状态、再平均同机制重复、再平均机制。允许覆盖不等于实际已观测。

| 方法 | 平均差值 | 机制Bootstrap 95%区间 |
|---|---:|---|
| j | 0.393021 | [0.276944, 0.526606] |
| kernel-old | 0.354566 | [0.226638, 0.512343] |
| kernel-new | 0.361717 | [0.233498, 0.505945] |

## 解释与验收边界

四状态合并响应先在每个上下文的类别×四状态内计算 RMSE，再平均重复和机制；不能用四份已经汇总的逐状态 RMSE 简单平均替代，依据为 `frozen_metrics_mechanism.csv` 的 `arm_rmse`。

三种方法的叶子 Spillover、Total 节点误差均高于中心。J 的叶子 Spillover 有符号 bias 在 T=0/1 分别为0.174886/0.202082，Total 为0.218041/0.174435。T=1 下两个核 baseline 的叶子 Spillover 和 Total RMSE 都低于 J。中心节点在82/400个上下文中被观测；T=0/1各41/200，该字段独立于四类Support原因。

`conditional_structural_zero`：固定中心T时，叶子的暴露状态不等于中心T，或中心自身处理不等于固定T。这里的“结构”是对固定中心处理条件而言，不能解释为两种中心分配下均不可能。
`assignment_zero`：条件允许，但完整事实图未产生该类别/状态；`observation_sampling_zero`：完整图存在，但50个观测样本中未覆盖；`covered`：观测计数大于0。分类先后顺序保留冻结函数定义。中心“未被观测”不与其他原因合并。

经验Support来自事实图和观测索引，`model_arm_supported` 只是模型支持该输出的能力标记。本次模型标记全为真，但经验Support并非全覆盖。Support主差值配对比较同机制、同重复、同一状态的两种中心分配；先平均4状态差值，再平均10次重复，再等权平均20机制。允许覆盖不等于实际观测覆盖。

Bootstrap保留整个机制的配对和重复结构，使用固定种子2026102502进行10000次整机制有放回抽样，取均值分布2.5%和97.5%分位数（linear）。这是条件关联的机制Bootstrap区间，不是Support因果效应，不是ATE后验区间，也不是节点级后验区间。中心处理同时改变事实输入和模型条件化。当前分析**没有生成节点级后验区间**。

20个机制才是独立统计单位；199个叶子和400个上下文不会扩充机制样本量。两种中心状态分别报告；Support主差值本身使用配对依赖，不能把其两端视为独立样本。dev 与训练、验证、模型选择是否独立仍证据不足。原覆盖率不足与其他限制保留。

独立审核直接从保存数组复算全部18份本地CSV，核对623745项字段和原说明43行主要数字，并独立重算三方法Bootstrap。9项原确定性夹具通过；公开测试另加入4项公开汇总检查，共13项，覆盖机制等权、pooled RMSE、Support计数和Bootstrap。具体范围见 [公开审核摘要](AUDIT_PUBLIC.json)。它是经过选择的公开摘要，不是原 manifest、原验收报告或原字节验收记录的替代。

完整原始实验输入、逐节点真值/预测、原始证据ZIP、manifest、receipt、冻结源码ZIP和详细本地审计记录未随PR公开。公开CSV足以复算这里的机制到总体汇总及Bootstrap，但不足以独立核对原逐节点数组或完成完整原始验收；完整复验需要另行获准取得原始证据及匹配资产。

## 公开文件与复用

以下12份CSV是已审核本地补充产物的逐字节副本，未重新生成科学结果。此目录的 [局部Git属性](.gitattributes) 为CSV使用 `-text` 保留LF字节；说明及公开审核摘要固定LF。原始目录、来源哈希和正式冻结快照未修改。

| 文件 | 行数 | 用途 |
|---|---:|---|
| [response_mechanism.csv](response_mechanism.csv) | 960 | 四状态、类别、机制指标 |
| [response_overall_by_center.csv](response_overall_by_center.csv) | 48 | 中心T分层机制等权总体 |
| [effects_mechanism.csv](effects_mechanism.csv) | 720 | 三效应、类别、机制指标 |
| [effects_overall_by_center.csv](effects_overall_by_center.csv) | 36 | 三效应分层总体 |
| [effect_center_leaf_mechanism.csv](effect_center_leaf_mechanism.csv) | 360 | 中心减叶子效应与误差差异 |
| [effect_center_leaf_overall_by_center.csv](effect_center_leaf_overall_by_center.csv) | 18 | 中心减叶子差异总体 |
| [support_mechanism.csv](support_mechanism.csv) | 960 | Support原因和阶段的机制计数/率 |
| [support_overall_by_center.csv](support_overall_by_center.csv) | 48 | Support分层总体计数/率 |
| [frozen_metrics_mechanism.csv](frozen_metrics_mechanism.csv) | 240 | 冻结四状态合并RMSE与效应指标 |
| [support_primary_by_mechanism.csv](support_primary_by_mechanism.csv) | 60 | 机制内配对主差值 |
| [support_primary_summary.csv](support_primary_summary.csv) | 3 | 机制Bootstrap区间 |
| [support_reason_counts_by_center.csv](support_reason_counts_by_center.csv) | 48 | Support原因计数；不是独立样本数 |

分析脚本：[analyze_node_support.py](../../../code/sparse_j/scripts/analyze_node_support.py)；测试：[test_node_support.py](../../../code/sparse_j/scripts/test_node_support.py)。脚本与本地审核版本字节一致，测试仅适配公开纯函数来源和新增公开汇总检查；来源SHA256见公开审核摘要。未公开上下文级CSV，避免重复大表与原始输入披露。

在仓库根目录运行公开确定性测试（只需现有兼容Python和NumPy环境，不安装依赖）：

```powershell
python -B -m unittest discover -s iPFN_demo/code/sparse_j/scripts -p test_node_support.py -v
```

默认测试只将公开源码中的四个纯函数装入临时测试包，不导入推断/DGP模块，不把这个测试包宣称为原始冻结快照。有权取得私有正式目录后，可以通过环境变量 `E1_5_SOURCE_RUN` 显式选择原冻结函数来源；公开CSV检查仍使用本目录。

分析脚本需要已有完整正式产物；公开PR不提供这些输入。另行获准取得后，只向全新输出目录运行：

```powershell
python -B iPFN_demo/code/sparse_j/scripts/analyze_node_support.py --input <existing-formal-results> --output <new-output-directory>
```

完整来源哈希检查不会绕过；不需要重新预测。脚本未来运行时会生成包含执行环境的本地provenance，不应未经隐私审查直接公开。

返回 [公开交付范围](../README_PUBLIC.md) 或 [正式ATE结果说明](../../../E1_5_STAR_ATE_RESULTS.md)。
