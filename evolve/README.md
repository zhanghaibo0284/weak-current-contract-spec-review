# 进化工作区（EVO）

本目录存放**离线进化**所需的黄金集与说明，不参与规则指纹之外的判定；`verify_skill.py` 会校验索引与用例的一致性。

## 1. 目录

```text
evolve/
├── README.md               本说明
└── golden/
    ├── schema.json         用例结构契约
    ├── index.json          用例索引（文件数必须与 cases 一致）
    └── cases/
        ├── G-001.json      匿名化种子用例
        ├── G-002.json
        └── G-003.json
```

黄金集只做回归基线：每题给出材料清单、六项参数轴，以及期望台账行（编号 / 结论 / 风险等级）。用例不得包含真实项目名称、金额与坐标。

## 2. 进化分级

| 级别 | 对象 | 审批 | P3 状态 |
|---|---|---|---|
| A 类 | 阈值、召回档位、quick 档规则子集 | 单人审批 | 开放自动提案 |
| B 类 | 维度归属、升级条件、分支映射 | 双人审批 + 灰度 | **未开放**，提案直接拒绝 |
| C 类 | 规则文本、7 字段、六步顺序、编号命名空间、边界声明 | 人工版本升级 | 永久禁止自动进化 |

白名单与区间定义在 `guard/evolve.py` 的 `ALLOWED_KEYS`；B 类键见 `B_CLASS_KEYS`。

## 3. 流水线

```text
提案 → 静态校验 → 黄金集回测 → 五道门 → 人工审批 → shadow → release → 监控/回滚
```

1. **提案**：版本号递增、证据运行 ≥30 次、变更键在 A 类白名单内。
2. **回测**：用黄金集评分，召回不降、误报增幅 ≤2 个百分点、等级一致率不下降。
3. **五道门**：5 次确定性复跑、召回、误报、覆盖 =187、耗时 ≤1.2 倍。
4. **shadow**：只写入 `versions/shadow/<版本>/`，线上指针不动。
5. **release**：校验 shadow 存在、门禁通过、审批人非空后，写入 `versions/released/<版本>/` 并原子切换 `versions/current.json`。
6. **rollback**：把指针切回任一已发布版本，旧目录保留。

`versions/` 为运行期数据，已在 `.gitignore` 中忽略；仓库只保留脚本与黄金集。

## 4. 命令行

在技能根目录执行：

```powershell
python guard/evolve_cli.py status
python guard/evolve_cli.py validate --proposal proposal.json
python guard/evolve_cli.py score --actual actual.json
python guard/evolve_cli.py shadow --proposal proposal.json
python guard/evolve_cli.py release --version 1.3.1 --approved-by PM-张三 --release-date 2026-11-23 --metrics metrics.json
python guard/evolve_cli.py rollback --version 1.3.0 --approved-by PM-张三 --release-date 2026-11-24
```

`actual.json` 形如 `{"G-001": [{"编号": "RISK-T01", "结论": "存在风险", "风险等级": "高"}]}`；
`metrics.json` 形如 `{"baseline": {"recall": 0.9, "false_positive_rate": 0.1}, "candidate": {"recall": 0.92, "false_positive_rate": 0.11, "coverage": 187, "runtime_ratio": 1.05, "determinism_runs": 5}}`。

## 5. 边界

- 进化只在离线批处理发生，审查运行期规则与配置只读；
- 黄金集评分是**回归门槛**，不等于现场召回率；
- 门禁不过一律作废提案，线上版本不变；
- 历史产物始终保留当时的 `ruleset_checksum` 与 `output_hash`，可原指纹复核。
