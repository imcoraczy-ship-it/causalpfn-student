# E1.5 Star ATE 公开交付说明

本 PR 提供星图实验代码、专项测试、正式结果说明和可读展示副本。**完整原始证据 ZIP、原始 SHA256 清单、原始审计材料及数学核验输入未随本 PR 公开提供，仅在本地保留。** 本公开目录不能替代完整原始产物的字节验收，也不承诺已经交付全部复验输入。

## 科学结果与范围

设计为 20 个机制 × 每机制 10 次配对重复 × 中心 T=0/1，即 200 组配对、400 个上下文。三方法共 1200 次点预测，J 共 400 次 95% 区间计算；原正式记录显示全部成功、失败数为 0。

| J 效应 | covered / requested | covered / valid | 总体覆盖率 |
|---|---:|---:|---:|
| Direct | 386/400 | 386/400 | 96.50% |
| Spillover | 359/400 | 359/400 | **89.75%，未达到90%目标** |
| Total | 373/400 | 373/400 | 93.25% |

主分析按中心 T=0/1 分层。T=0 Total 为 89.00%，T=1 Spillover 为 89.50%，同样未达90%。两个核 baseline 的区间为 N/A，不是0%。T=1 下 Spillover 和 Total RMSE 均有 baseline 优于 J，不能声称 J 全面领先。

20 个机制才是独立统计单位，400 个上下文不是400个独立机制；合并中心状态的方差仅为描述性补充。dev 是否独立于模型训练、验证和选择仍证据不足。独立数学核验只覆盖指定16个 pilot 上下文、48个效应区间，不能表述为独立复算全部正式实验。

完整定义、随机流、分层统计与局限性见 [正式结果说明](../../E1_5_STAR_ATE_RESULTS.md)。历史协议的公开版本见 [E1_5_STAR.md](../../E1_5_STAR.md)。未因覆盖率不足而调整区间、筛选机制、删除失败或重抽种子。

## 公开展示文件

以下文件来自原有正式报告，没有重新运行预测或报告算法。三个 `ate_accuracy.svg` 展示副本各仅删除了69行中的行尾空格，未重新生成图表，未改科学数字、坐标、图例、文字或图形元素；这三个 SVG 已不与来源逐字节相同。其他展示文件保持来源字节，没有脱敏。原始来源文件及原始 SHA256 清单均未修改。

| 内容 | T=0 主分析 | T=1 主分析 | 总体补充 |
|---|---|---|---|
| PNG | [图](preview/center_t0/ate_accuracy.png) | [图](preview/center_t1/ate_accuracy.png) | [图](preview/overall/ate_accuracy.png) |
| PDF | [图](preview/center_t0/ate_accuracy.pdf) | [图](preview/center_t1/ate_accuracy.pdf) | [图](preview/overall/ate_accuracy.pdf) |
| SVG | [图](preview/center_t0/ate_accuracy.svg) | [图](preview/center_t1/ate_accuracy.svg) | [图](preview/overall/ate_accuracy.svg) |
| 图表源 CSV | [数据](preview/center_t0/ate_accuracy_source.csv) | [数据](preview/center_t1/ate_accuracy_source.csv) | [数据](preview/overall/ate_accuracy_source.csv) |
| 统计表 CSV | [表](preview/center_t0/ate_m50.csv) | [表](preview/center_t1/ate_m50.csv) | [表](preview/overall/ate_m50.csv) |
| LaTeX | [表](preview/center_t0/ate_m50.tex) | [表](preview/center_t1/ate_m50.tex) | [表](preview/overall/ate_m50.tex) |

另提供 [分机制及中心状态覆盖诊断 CSV](preview/j_coverage_by_mechanism_and_center.csv)，保留机制1008 Spillover 0/20和机制1013 10/20等未覆盖情况。图上机制点不代表置信区间。

每个中心目录有6个展示文件，共18个，另加1份机制诊断表，合计19份。来源为本地原正式报告的对应 figures/tables 及机制诊断 CSV。原始 manifest、receipt、模型资产哈希和报告 provenance 留在本地证据中，未随本 PR 提供。

预览目录通过 [局部 .gitattributes](preview/.gitattributes) 的 `*.svg -text`、`*.csv -text`、`*.tex -text`，关闭13份预览文本（3个SVG、7个CSV、3个TEX）的 Git 自动换行转换，保留工作区现有换行字节。该规则只适用于预览目录，不扩展到代码或其他目录。三个SVG已仅清理行尾空格，因此仍不与来源逐字节一致；其他展示文件未改。

局部属性文件新增1项，公开 PR 候选由33个增为34个；19份展示文件及400个实验上下文均未增加。展示文件不使用原始 manifest 为其字节背书。要验证原实验字节，需要本地保留的原始证据及原校验记录，不能用公开副本代替。

## 代码与复验边界

[ATE 适配器](../../code/sparse_j/scripts/e1_5_star_ate.py) 复用星图生成、冻结 J/核模型预测及现有 ATE 评估入口。[专项测试](../../code/sparse_j/scripts/test_e1_5_star_ate.py) 覆盖真值、区间、失败分母、baseline N/A、配对、统计汇总及产物验收。[独立区间诊断脚本](../../code/sparse_j/scripts/diagnose_e1_5_intervals.py) 需要本地保留的 pilot_fresh 输入和哈希匹配的冻结权重。

本 PR 的公开文档已经将机器专用路径改为通用环境调用。原实验的字节验收依赖本地保留的冻结源码快照；公开文档不是该快照的逐字节替代。不能在公开工作树中忽略原验收器报告的源码哈希不匹配。

若后续另行获准取得完整原始证据，可在全新隔离目录恢复其 source_snapshot.zip，并提供哈希匹配的模型资产后，使用冻结源码中的 --validate。该入口不重新预测，但会确定性重建 DGP 和配对流核对输入。本轮只准备文件，没有运行它或任何预测实验，也没有重新执行测试。

## 未公开的材料

本公开目录没有原始证据 ZIP、原始校验清单、METADATA_REVIEW.md、metadata_scan.json、manifest、receipt、source_snapshot.zip、数学核验输入、原始 Notebook、模型权重副本或旧 Smoke/timing 结果。不能根据这些材料曾经在本地通过检查，宣称它们已经随 PR 公开交付。

如需要完整原始证据供评审复验，应另行决定受控提供方式。本 README 是公开范围说明，不是对原始审计材料的替换，也不是已脱敏的原始证据包。
