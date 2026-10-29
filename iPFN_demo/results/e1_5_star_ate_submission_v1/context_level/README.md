# E1.5 Star：公开上下文级证据

本目录仅整理已经保存的正式结果与节点/Support后处理产物，没有运行DGP、模型预测、模型区间推断或正式 `--validate`。设计仍为20个机制、每机制10组配对重复、每组中心T=0/1：200组配对、400个上下文，三方法1200个方法—上下文组合、3600条ATE效应评价记录。

原结果不变：Direct **386/400=96.50%**；Spillover **359/400=89.75%，未达到90%目标**；Total **373/400=93.25%**。20个机制才是独立统计单位。中心状态分层是主分析，合并配对状态的方差仅作描述性补充。Support关联不是因果效应；没有节点级后验区间。

## 文件和来源

| 文件 | 行数 | 内容 |
|---|---:|---|
| [context_identity.csv](context_identity.csv) | 400 | execution上下文与三方法receipt一致后，仅投影context_id、mechanism_id、pair_repeat_id、center_t；不是完整receipt |
| [ate_context_metrics.csv](ate_context_metrics.csv) | 3600 | 正式评价记录，使用真实配对编号；附保存的总体ATE真值、点估计和区间端点标量 |
| [response_context.csv](response_context.csv) | 9600 | 中心/叶子、四状态的均值和误差摘要 |
| [effects_context.csv](effects_context.csv) | 7200 | 中心/叶子的Direct、Spillover、Total效应误差摘要 |
| [effect_center_leaf_context.csv](effect_center_leaf_context.csv) | 3600 | 中心减叶子效应，以及两类误差指标的差异 |
| [support_context.csv](support_context.csv) | 9600 | 经验Support计数、冻结原因分类及独立模型能力标记 |
| [frozen_metrics_context.csv](frozen_metrics_context.csv) | 2400 | 冻结四状态合并响应RMSE和节点类别效应指标 |
| [support_paired_arm_contrasts.csv](support_paired_arm_contrasts.csv) | 2400 | 机制×配对重复×状态×方法的既有Support差值 |

后六份CSV为现有节点分析产物的逐字节副本。前两份是独立公开展示派生物：保留稳定context_id；历史ID中的r仍为 `2*pair_repeat_id+center_t`，但公开ATE的repeat现明确等于pair_repeat_id。3420条历史repeat被纠正，不改原CSV。缺失的pair_repeat_id/center_t列在本公开表显式补充；机制别名mechanism保留，并与mechanism_id核对。

ATE表保留原有计数、误差与状态。baseline不支持区间时，覆盖率、宽度、成功率、上下端点表示为 **N/A**，请求数/有效数/covered等计数仍依法为0；N/A不是0%覆盖率。原有nan转N/A仅为表示规范，9600个既有不适用单元的语义未变。新增interval_failure是receipt失败状态的布尔投影，不公开完整错误回执。

ate_true由保存的200×4真值按冻结定义求总体均值；ate_pred、ate_lower、ate_upper取自保存预测NPZ，未重新推断。四状态顺序为00、01、10、11；Direct=10−00，Spillover=11−10，Total=11−00。这里的区间是**全体200节点ATE区间**，不是中心、叶子或单节点后验区间。

## 公开材料能核验什么

[验证器](verify_public_evidence.py)仅读取公开表格与 [公开清单](PUBLIC_EVIDENCE_MANIFEST.json)，不访问私有目录或模型。可核验：

- 400个上下文、三方法、三效应的唯一组合；所有表与最小身份投影一致。原receipt一致性已在本地逐项核对，但公开身份投影不构成第三方对私有receipt真实性的独立证明。
- 从ATE标量复算有符号误差、平方误差、区间覆盖、区间宽度、有效与失败分母，以及baseline N/A状态。
- 从上下文摘要复算 [机制级/总体节点表](../node_support/README.md)，区分平均上下文RMSE与sqrt(平均MSE)的pooled_rmse；叶子先在上下文内汇总，不以199倍权重扩充机制样本。
- 从公开计数核对Support分类、结构允许/实际分配/观测覆盖阶段；中心是否观测单列，模型arm_supported不等于经验Support。
- 复算2400条配对Support差值、60条机制差值及3个机制整体Bootstrap区间：种子2026102502，10000次整机制重抽样，linear分位数。
- 核对原 [ATE展示表](../README_PUBLIC.md)、图表源CSV和180条机制/中心诊断。中心状态直接使用center_t，绝不使用真实repeat的奇偶性。

这些检查不证明模型假设或外推正确，也不改变89.75%未达目标的结论。

## 不能独立复核的来源

完整原始证据ZIP、原manifest、完整receipt、冻结源码快照、模型权重、原始逐节点预测/真值数组和事实输入仍未公开。本目录不是完整原始实验复现或正式字节验收包。

公开材料不包含199个叶子的逐节点误差，因此不能从原始节点数组独立重算叶子MAE/MSE；可以核对公开摘要恒等式并重算后续汇总。公开材料也不包含完整处理分配与观测索引，因此不能从原始事实输入重新计数Support；可以核对给定计数与分类的一致性。原始来源身份、推断、全部上下文的后验数学及完整冻结验收仍需另行获准取得原始材料。

## 校验与运行

PUBLIC_EVIDENCE_MANIFEST.json记录本目录每个其他文件的相对路径、SHA-256、字节数、CSV行数、列名和生成依据，并锚定19份未修改的公开汇总CSV。清单不含本机路径或私有输入内容。**公开哈希仅证明公开文件自身完整性，不能冒充原始输入哈希证明。** 清单不对自身作循环哈希；请使用另行报告的清单SHA-256或已审核Git版本作为外部参照。

需要Python标准库及已有NumPy（仅用于保持冻结PCG64 Bootstrap流），不需要PyTorch、模型、SciPy或pandas，也不安装依赖：

```powershell
python -B iPFN_demo/results/e1_5_star_ate_submission_v1/context_level/verify_public_evidence.py --self-test
python -B iPFN_demo/results/e1_5_star_ate_submission_v1/context_level/verify_public_evidence.py
```

自测只用内存夹具；完整验证只读公开CSV和清单，无文件写入。任何缺失、重复、哈希或数值不一致都会报错，不删除记录、不重试或换种子。局部 [.gitattributes](.gitattributes) 对CSV使用-text，其余公开文本固定LF，保留已记录字节。没有更改原根属性或Git配置。

历史报告脚本只适用于其原编码。若未来消费本修正表，中心状态必须取显式center_t；不得照搬旧repeat%2筛选。原历史脚本和报告未改。

返回 [公开交付说明](../README_PUBLIC.md) 或 [正式结果说明](../../../E1_5_STAR_ATE_RESULTS.md)。
