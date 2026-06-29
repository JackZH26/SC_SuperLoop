# 瓦力瓦力 LOOP-SC Open Claw 执行说明

日期：2026-06-25

执行体：Open Claw on VPS  
负责人代号：瓦力瓦力  
任务：建立、测试、验收、改进并持续运行 LOOP-SC 超导材料研究与预测闭环

---

## 1. 总目标

瓦力瓦力负责在一台 8 核 CPU VPS 上，把 LOOP-SC 建成一个能长期运行的
superconductivity loop engineering 系统。

这个系统不是一次性脚本，也不是追求立刻宣布“室温超导”的工具。它的目标是：

1. 维护超导知识库。
2. 生成候选材料。
3. 用最小工具链完成结构、稳定性和金属性预筛。
4. 对少量高价值候选运行 Quantum ESPRESSO DFT。
5. 对更少量候选运行 phonopy 声子稳定性检查。
6. 输出候选 dossier、排行榜、失败日志和下一轮策略更新。
7. 用 benchmark 和 checker 机制防止虚假高 `Tc` 结论。
8. 将达到公开可信度标准的高质量候选定时同步到 SClib Discovery 页面。

核心 loop：

```text
Knowledge -> Hypothesis -> Candidate -> Prescreen -> DFT -> Phonon
-> Mechanism Audit -> Checker -> Publish Review -> Ranking
-> SClib Sync -> Memory Update -> Next Round
```

---

## 2. 重要约束

VPS 条件：

- 8 核 CPU。
- 无 GPU。
- 已安装 Quantum ESPRESSO。
- 已安装 Python 基础工具。
- 磁盘空间有限，必须控制缓存、下载包、DFT 输出和临时文件。

第一阶段原则：

- 不重复安装已有工具。
- 不引入过大工具链。
- 不做大规模 DFPT/EPC/Eliashberg。
- 不把 ML 结果当作最终科学证据。
- 不自动删除文件；清理建议必须先提交给用户确认。

第一阶段只考虑最小可落地工具链：

```text
pymatgen
spglib
Materials Project API / mp-api
CHGNet
Quantum ESPRESSO
phonopy
SQLite / DuckDB / Parquet
Markdown reports
```

第一阶段暂不考虑：

```text
ASE
OPTIMADE
MatGL
ALIGNN
EPW
atomate2
AiiDA
VASP
DMFT / RPA / fRG
large interface calculations
large hydride EPC screening
```

这些工具以后可以加入，但不属于 v0.1 的验收范围。

---

## 3. 独立工作区

瓦力瓦力必须先建立独立项目目录，避免和论文、下载文件、旧项目混在一起。

推荐路径：

```bash
mkdir -p ~/loop-sc-vps/{workspace,knowledge,candidates,runs,dossiers,reports,configs,scripts,benchmarks,cleanup_audit}
cd ~/loop-sc-vps
```

如果 VPS 使用 `/opt` 管理长期服务，可使用：

```bash
sudo mkdir -p /opt/loop-sc-vps/{workspace,knowledge,candidates,runs,dossiers,reports,configs,scripts,benchmarks,cleanup_audit}
sudo chown -R "$USER":"$USER" /opt/loop-sc-vps
cd /opt/loop-sc-vps
```

标准目录含义：

```text
configs/        loop 参数、QE 参数、评分规则
knowledge/      SCLib、Materials Project cache、标准化材料库
candidates/     每轮生成的候选材料
runs/           DFT、phonon、prescreen 运行产物
dossiers/       候选材料报告
reports/        leaderboard、failures、weekly digest、验收报告
scripts/        loop 脚本
benchmarks/     Nb、Pb、MgB2、H3S 等 benchmark
cleanup_audit/  磁盘清理建议和空间审计报告
workspace/      临时工作目录
```

---

## 4. 工具链确认

瓦力瓦力不要盲目安装。先检查现有工具。

### 4.1 Quantum ESPRESSO

检查：

```bash
command -v pw.x
pw.x -version
command -v ph.x || true
command -v dos.x || true
```

记录到：

```text
reports/toolchain_status.md
```

要求：

- 如果 `pw.x` 已存在，先记录版本和路径。
- 如果版本可用，第一阶段不要重复安装。
- 如果版本过旧或缺少关键模块，再提出升级建议给用户确认。
- 目标版本可设为 QE 7.5.0，但不要为了追新破坏现有可用环境。

### 4.2 Python

检查：

```bash
python3 --version
python3 -m pip --version
python3 - <<'PY'
mods = ["pymatgen", "spglib", "mp_api", "chgnet", "phonopy", "duckdb", "pandas"]
for m in mods:
    try:
        mod = __import__(m)
        print(f"{m}: OK")
    except Exception as e:
        print(f"{m}: MISSING ({e.__class__.__name__})")
PY
```

缺什么只补什么。

第一阶段建议补齐：

```bash
python3 -m pip install pymatgen spglib mp-api chgnet phonopy duckdb pandas pyarrow pydantic typer rich matplotlib
```

如果 VPS 已有 conda/micromamba 环境，应优先使用现有环境，不新建多个重复环境。

---

## 5. 磁盘空间规则

瓦力瓦力必须先做空间审计，不直接删除。

检查：

```bash
df -h
du -h -d 1 "$HOME" 2>/dev/null | sort -hr | head -40
du -h -d 1 "$HOME/Downloads" 2>/dev/null | sort -hr | head -80
du -h -d 1 "$HOME/Documents" 2>/dev/null | sort -hr | head -80
```

重点扫描：

```bash
find "$HOME" -type f \( \
  -iname "*.dmg" -o -iname "*.pkg" -o -iname "*.zip" -o -iname "*.tar.gz" -o \
  -iname "*.tgz" -o -iname "*.iso" -o -iname "*.mp4" -o -iname "*.mkv" -o \
  -iname "*.pdf" \
\) -size +100M -print 2>/dev/null
```

输出：

```text
cleanup_audit/disk_usage_recommendations.md
```

报告必须分为：

1. 可优先确认删除：安装包、重复压缩包、下载缓存。
2. 需要人工确认：大视频、旧数据集、旧计算输出。
3. 不建议删除：论文源文件、当前项目文件、未知来源科研数据。

没有用户确认，不删除任何文件。

---

## 6. LOOP-SC v0.1 模块

### 6.1 Knowledge 模块

目标：

- 接入 SCLib 或用户已有超导资料。
- 接入 Materials Project API。
- 形成标准化材料表。

输出：

```text
knowledge/materials.sqlite
knowledge/superconductors.parquet
knowledge/materials_project_cache/
reports/knowledge_update.md
```

第一阶段字段：

```text
formula
normalized_formula
family
structure_source
tc
pressure_gpa
evidence_type
paper_or_database_source
known_similar_materials
```

### 6.2 Candidate 模块

目标：

- 从模板和化学规则生成候选。
- 第一阶段优先小晶胞体系。
- 增加铜基、铁基、氧化物替代和金属元素探索分支，但先作为
  candidate generation + mechanism audit 路线，不把复杂强关联体系直接
  当作普通 phonon/EPC 高通量任务。

优先家族：

1. `AlB2` / `MgB2` 邻域。
2. 小晶胞硼化物。
3. 小型 B-C framework。
4. 铜基 cuprate 外推。
5. 铁基 iron-based 外推。
6. Al-O / STO 替代氧化物与界面相关候选。
7. Al、Ti、Pb、W 等金属或金属氧化物/硼化物/氢化物/层状化合物探索。

暂缓：

- 大 clathrate。
- LaH10 类大规模 hydride EPC。
- nickelate interface supercell。
- cuprate/iron-based 的完整强关联模型计算。
- 大界面/异质结 supercell。

输出：

```text
candidates/YYYY-MM-DD/candidate_manifest.jsonl
```

### 6.2.2 Discovery Publish 分支

目标：

1. 将内部 leaderboard 和对外 Discovery feed 分离。
2. 只把经过审查并达到可信度门槛的候选同步到 SClib。
3. 为 `https://jzis.org/sclib` 增加一级导航 `Discovery`，位置在 `timeline` 后。
4. 每 6 小时自动更新一次对外展示结果。

公开过滤标准 v0.1：

1. 非 benchmark 候选。
2. 至少达到 `E3`。
3. `checker_status=pass`。
4. 存在完整 dossier，包含 mechanism、risk、provenance、review time、next step。
5. 经 `formula + branch + prototype family` 去重。

SClib 页面要求：

1. 风格与 SClib 主站统一。
2. 顶部使用英文简介，简述材料产出方法。
3. 页面要显示最近更新时间和公开过滤标准。
4. 页面展示的是 reviewed discovery feed，不是原始内部榜单镜像。

自动化要求：

1. 增加每 6 小时执行一次的 SClib 同步任务。
2. 同步任务必须支持新增、更新、降级和撤回。
3. self-review loop 必须定期检查公开候选是否仍满足门槛。

### 6.2.1 候选材料搜索空间 v0.1+

瓦力瓦力需要把候选搜索空间扩展为以下分支。所有分支都必须参考已有
化学式、结构家族和已知物理机制进行外推，不能只做随机元素替换。

#### A. 铜基 cuprate 外推分支

参考机制：

- CuO2 平面。
- 近似 `d9` 电子构型。
- 强关联、反铁磁母体、掺杂诱导超导。
- 层状结构、charge reservoir、apical oxygen、内外压力调控。

参考模板：

```text
La2CuO4
YBa2Cu3O7-delta
Bi2Sr2CaCu2O8
Tl/Bi/Hg-based multilayer cuprates
infinite-layer CaCuO2/SrCuO2-like structures
```

生成方向：

- A-site 替换：La/Y/Ba/Sr/Ca/Bi/Tl/Hg 的低风险化学相似替换。
- charge reservoir 替换：改变层间离子以调节 CuO2 平面载流子。
- apical oxygen 调控：比较含 apical oxygen 与 infinite-layer 版本。
- 化学压力：小半径/大半径离子调节 Cu-O 键长和层间距。
- 低维到三维耦合：调整 block layer 厚度与 CuO2 层数。

VPS 第一阶段策略：

- 以文献/数据库/结构相似性和机制审计为主。
- DFT 只做母体结构、简单替换、小原胞版本。
- 不把普通 PBE 金属性当作 cuprate 超导证据。
- dossier 必须标注 `strong_correlation_risk: high`。

#### B. 铁基 iron-based 外推分支

参考机制：

- FeAs 或 FeSe 层。
- 多轨道 Fe 3d 费米面。
- spin fluctuation、nematicity、磁序竞争。
- 载流子掺杂、压力、层间距和 pnictogen/chalcogen height 调控。

参考模板：

```text
LaFeAsO / 1111
BaFe2As2 / 122
LiFeAs / 111
FeSe / 11
intercalated FeSe
```

生成方向：

- FeAs -> FeP / FeSb 轻量替换。
- FeSe -> FeS / FeTe 局部替换。
- spacer layer 替换：LaO、Ba、Sr、Ca、Li、alkali/intercalant。
- 电子/空穴掺杂的电荷平衡版本。
- 压力等效的化学压缩替换。

VPS 第一阶段策略：

- 用 DFT 检查结构、磁态倾向、DOS 和费米能附近 Fe-d 态。
- 不做 RPA/fRG/DMFT。
- dossier 必须标注磁性竞争、相关效应和低能多轨道风险。

#### C. Al-O / STO 替代与氧化物界面分支

目标：

- 探索 Al-O 体系、STO 替代体系以及氧化物界面/基底相关的潜在超导路线。
- 这里的 STO 指 SrTiO3 及其类似物或替代物。

参考机制：

- 极性界面电子气。
- 氧空位诱导载流子。
- Ti 3d 或替代金属 d 态低密度超导。
- 软声子、铁电涨落、界面前向声子耦合。
- 化学压力和介电屏蔽调控。

参考模板：

```text
SrTiO3
KTaO3
BaTiO3
CaTiO3
LaAlO3/SrTiO3
Al2O3-related oxide interfaces
TiO2-based reduced oxides
WO3 / doped WO3
```

生成方向：

- STO 中 Sr/Ba/Ca 替换。
- Ti -> Zr/Hf/Nb/Ta/W/Mo 替换。
- O vacancy ordered structures。
- LaAlO3/SrTiO3 的简化 slab 先不跑，先用 bulk proxy。
- Al-O 作为界面层、绝缘 spacer、charge reservoir 或化学压力层探索。

VPS 第一阶段策略：

- bulk proxy 优先，不做大 slab。
- 只跑小原胞氧化物和有序氧空位模型。
- 标注 `interface_required`、`oxygen_vacancy_sensitive`、
  `carrier_density_sensitive`。

#### D. Al / Ti / Pb / W 等金属可能性探索分支

目标：

- 不局限于已知高温超导家族，系统探索 Al、Ti、Pb、W 等金属元素参与的
  新化合物空间。

元素角色：

```text
Al: 轻金属、sp 电子、AlB2/MgB2 邻域、Al-O spacer/interface。
Ti: d0/d1 氧化物、STO 替代、Ti-based hydride/boride/nitride。
Pb: 强 SOC、强 EPC 金属、clathrate guest、heavy atom phonon branch。
W: WO3/doped bronze、重 d 金属、高压/氧化物/硼化物路线。
```

生成方向：

- 金属硼化物：Al-B、Ti-B、W-B、Pb-B 与混合硼化物。
- 金属碳/硼碳框架：Al/Ti/Pb/W + B-C framework。
- 金属氧化物：Al-O、Ti-O、W-O、Pb-O 及掺杂版本。
- 金属氢化物：只做小晶胞和数据库已有结构，避免大规模 hydride EPC。
- 层状化合物：金属层 + 轻元素层的二维/准二维结构。

VPS 第一阶段策略：

- 优先数据库已有结构和小原胞 prototype。
- CHGNet/Materials Project 先筛稳定性。
- QE 只跑 top candidates。
- Pb/W 相关候选标注 `SOC_check_later: true`，第一阶段可先不做 SOC。

#### E. B-C-H / B-C-N-H 轻元素框架分支

参考机制：

- B/C/N 刚性共价骨架。
- H 高频振动模。
- 客体原子或缺陷供电子使框架金属化。
- chemical precompression 降低外部压力需求。

参考模板：

```text
boron-carbon clathrate
hydride-filled B-C cage
B-C-N sodalite-like framework
BC3 / LiBC-derived frameworks
```

生成方向：

- B/C 比例调节。
- N 替换 C 或 B 来改变电子计数。
- H、BH4、NH4 或轻金属客体填充。
- K/Ca/Sr/Ba/La 等供电子客体调节金属性。

VPS 第一阶段策略：

- 优先小原胞、数据库已有或高对称 prototype。
- 大 cage 结构先走 CHGNet/Materials Project 预筛，不急于 QE。
- 标注 `metallicity_stability_conflict` 风险。

#### F. p-block 三元/多元 hydride 分支

参考机制：

- p-block 元素稳定富氢结构。
- 目标是在比 LaH10 类更低压力下获得高频 H 模和可观 EPC。

参考元素：

```text
Ga, In, Tl, Sn, Pb, Sb, Bi, Te
C, B, N, H
```

生成方向：

- `X-C-H`、`X-B-H`、`X-N-H` 三元组合。
- `XC2H8` 类结构的元素替换。
- Pb/Bi/Sb/Te 等重 p-block 元素与轻元素骨架组合。

VPS 第一阶段策略：

- 只做小晶胞和文献/数据库已有结构。
- 高压候选单独进入 high-pressure board。
- 不做大规模 EPC。

#### G. 掺杂碳/硅/硼 clathrate 与共价笼架分支

参考机制：

- 金刚石型、clathrate 型、sodalite 型强共价网络。
- 通过插层、空位或元素替换获得金属性。

参考模板：

```text
C clathrate
Si clathrate
B-rich cage
B-C clathrate
alkali/alkaline-earth filled cages
```

生成方向：

- Li/Na/K/Ca/Sr/Ba 填充。
- B/C/Si/Ge/Sn 局部替换。
- 空位或有序缺陷调节电子数。

VPS 第一阶段策略：

- 优先数据库已有 clathrate。
- 只提升小原胞或高对称版本到 QE。
- 标注 `synthesis_difficulty` 与 `metastability_risk`。

#### H. 层状氮化物 / 卤氮化物分支

参考机制：

- 层状电子气。
- 插层掺杂。
- Zr/Hf/Ti/Nb/Ta d 态与 N/Cl/F 层共同调控。

参考模板：

```text
ZrNCl
HfNCl
TiNCl-like
intercalated nitride halides
```

生成方向：

- Zr/Hf/Ti/Nb/Ta 替换。
- Cl/F/Br 层替换。
- Li/Na/K/Ca 插层。
- 氮空位或轻元素共掺杂。

VPS 第一阶段策略：

- 适合小原胞 DFT 与 DOS 检查。
- 插层/无序模型先用有序近似。

#### I. Kagome / van Hove / 平带分支

参考机制：

- kagome 晶格导致 van Hove singularity 或 flat-band 特征。
- CDW、拓扑能带、磁涨落和非常规配对竞争。

参考模板：

```text
AV3Sb5-like
Sc/V/Nb/Ta kagome nets
Fe/Sn kagome-like structures
```

生成方向：

- A-site: K/Rb/Cs/Ca/Sr/Ba。
- kagome metal: V/Nb/Ta/Cr/Mn/Fe/Co/Ni。
- ligand: Sb/Bi/Sn/Ge/Si。
- 电子计数调节使 van Hove 点靠近 Fermi level。

VPS 第一阶段策略：

- DFT 用于 band/DOS/van-Hove proxy。
- 不把 PBE 高 DOS 直接视作超导证据。
- 标注 `cdw_competition`、`magnetic_competition`。

#### J. MXene / 二维碳氮化物分支

参考机制：

- 二维 d-band。
- 表面终止基团调节电子结构和声子。
- 层间插层调控载流子密度。

参考模板：

```text
Ti3C2Tx
Nb2CTx
Mo2CTx
V2NTx
```

生成方向：

- Ti/V/Nb/Mo/Ta 基 MXene。
- O/F/OH/H 表面终止的有序近似。
- Li/Na/K 插层。

VPS 第一阶段策略：

- 表面无序很复杂，第一阶段只做小的有序模型或数据库结构。
- 标注 `surface_termination_sensitive`。

#### K. 高熵 hydride / boride / carbide / nitride 分支

参考机制：

- 多组元混合带来熵稳定。
- 多元素调节声子谱、电子态和化学预压缩。

生成方向：

- 多金属位点 hydride。
- 高熵 boride/carbide/nitride。
- 从已知稳定 binary/ternary prototype 做多元素替换。

VPS 第一阶段策略：

- 不做大 special quasirandom structures。
- 先生成 composition-level 候选和小有序近似。
- 标注 `configurational_disorder_high`。

#### L. 拓扑半金属 / 拓扑绝缘体掺杂分支

参考机制：

- 强 SOC。
- Dirac/Weyl 半金属或拓扑表面态。
- 低载流子密度配对、压力或插层诱导超导。

参考模板：

```text
Bi2Se3-like
WTe2 / MoTe2-like
Dirac/Weyl semimetal prototypes
```

生成方向：

- Cu/Sr/Nb 插层。
- Se/Te/S 替换。
- Bi/Sb 替换。
- 压力或化学压力版本。

VPS 第一阶段策略：

- 第一阶段只做结构和 DOS proxy。
- SOC 作为后续 checker，不作为每日常规计算。
- 标注 `SOC_check_later`。

#### M. 排除方向

第一阶段不要纳入：

```text
organic superconductors
COF superconductors
MOF superconductors
large molecular crystals
```

原因：

- 结构大、无序强、计算成本高。
- 第一阶段 VPS 工具链不适合。
- 不符合当前“最小可落地 loop”的目标。

#### N. 每日全覆盖与动态权重

每天每个方向都可以尝试，但生成比例不同。瓦力瓦力不能只盯一个方向；
也不能让低权重方向完全消失。

第一阶段初始候选生成权重：

```text
AlB2/MgB2/boride branch: 14%
B-C framework branch: 10%
cuprate extrapolation branch: 12%
iron-based extrapolation branch: 12%
Al-O/STO/oxide branch: 10%
Al/Ti/Pb/W exploratory metal branch: 6%
B-C-H / B-C-N-H light-framework branch: 10%
p-block hydride branch: 7%
doped carbon/silicon/boron clathrate branch: 6%
layered nitride/halonitride branch: 5%
kagome/van-Hove branch: 4%
MXene/2D carbide-nitride branch: 2%
high-entropy hydride/boride/carbide/nitride branch: 1%
topological doped system branch: 1%
```

每日最低覆盖规则：

```text
If generated candidates <= 1,000:
  each branch should receive at least 5 candidates.

If generated candidates > 1,000:
  each branch should receive at least 20 candidates.
```

动态调整规则：

- 如果某分支连续 3 轮没有 E1/E2 候选，下一轮权重降低 30%，但不低于
  每日最低覆盖。
- 如果某分支产生 E3 候选，下一轮权重增加 20%。
- 如果某分支产生 E4 候选，进入当周重点分支。
- 所有权重变化必须写入 `reports/strategy_updates.md`。

### 6.3 Prescreen 模块

目标：

- 先便宜筛，不急着跑 DFT。

筛选：

- 化学式合法性。
- 结构是否存在。
- spglib 对称性检查。
- Materials Project 是否已有类似材料。
- CHGNet 稳定性/快速 relax 预筛。
- 金属性 proxy 和轻元素骨架 proxy。

输出：

```text
reports/prescreen_leaderboard.md
reports/prescreen_failures.md
```

### 6.4 DFT 模块

目标：

- 只对少数候选跑 QE。

限制：

- 优先 `<= 20 atoms / primitive cell`。
- `20-40 atoms` 只给高优先级候选。
- `> 40 atoms` 第一阶段原则上不跑。

任务：

```text
relax / vc-relax
SCF
NSCF / DOS
简单压力点检查
```

输出：

```text
runs/dft/<candidate_id>/
dossiers/E3_dft_verified/<candidate_id>.md
```

### 6.5 Phonon 模块

目标：

- 对 DFT 通过的少量候选检查动力学稳定性。

工具：

```text
phonopy + Quantum ESPRESSO
```

限制：

- 每天最多 0-1 个 phonon 候选。
- 不做大规模 EPC。
- 第一阶段不把 EPW 作为硬要求。

输出：

```text
runs/phonon/<candidate_id>/
dossiers/E4_phonon_checked/<candidate_id>.md
```

---

## 7. Evidence 等级

每个候选必须有证据等级。

```text
E0: 只生成了化学式，尚无结构证据。
E1: 有结构或模板结构，化学合法性通过。
E2: 数据库/CHGNet/描述符预筛有利。
E3: QE relax/SCF/DOS 通过，金属性或近金属性明确。
E4: phonopy 声子稳定性通过，或虚频风险可解释。
E5: EPC/Tc 估计完成。第一阶段通常不要求。
E6: checker 复核通过。
E7: 实验建议或外部验证。
```

第一阶段验收目标：

- E3 是主要产出。
- E4 是高价值产出。
- E5 不是 v0.1 硬指标。

禁止：

- E0-E2 候选不得写预测 `Tc`。
- E3-E4 候选只能写“可能性”和机制假设。
- 只有 E5+ 才允许写数值 `Tc` 区间。

---

## 8. Ranking Rubric

LOOP-SC 的 ranking 不按单一的“预测 `Tc` 最高”排序，而按“最值得进入下一轮
计算、机制审计或实验建议”的综合价值排序。瓦力瓦力必须至少维护三张榜：

```text
reports/discovery_leaderboard.md
reports/evidence_leaderboard.md
reports/experiment_leaderboard.md
```

### 8.1 Discovery Ranking

用途：

- 决定下一轮 VPS 算力给谁。
- 决定哪些候选进入 QE、phonopy 或 checker。

公式：

```text
discovery_score =
  0.18 * stability_score
+ 0.14 * structure_confidence
+ 0.12 * metallicity_or_doping_potential
+ 0.10 * mechanism_plausibility
+ 0.10 * novelty_score
+ 0.10 * known_family_similarity
+ 0.08 * light_element_or_high_energy_scale_score
+ 0.07 * synthesis_plausibility
+ 0.06 * pressure_accessibility
+ 0.05 * uncertainty_penalty_inverse
```

字段解释：

- `stability_score`：形成能、hull distance、CHGNet 稳定性、结构是否崩塌。
- `structure_confidence`：是否有真实数据库结构、prototype 是否可信、
  spglib 是否正常。
- `metallicity_or_doping_potential`：是否金属；如果是 cuprate/iron-based，
  则看是否有合理掺杂路径。
- `mechanism_plausibility`：是否符合该家族的已知物理机制。
- `novelty_score`：不是简单重复已知材料或已失败材料。
- `known_family_similarity`：和已知超导家族是否有合理相似性。
- `light_element_or_high_energy_scale_score`：B/C/N/H、轻元素骨架、高频声子、
  van Hove、flat band 或强交换能标等潜力。
- `synthesis_plausibility`：是否有可合成 analog、已知结构邻域或合理合成路线。
- `pressure_accessibility`：常压/低压优先；高压候选进入单独 high-pressure board。
- `uncertainty_penalty_inverse`：信息越完整、模型分歧越小，分数越高。

### 8.2 Evidence Ranking

用途：

- 决定候选能用多强的语言对外描述。
- 防止 E0-E2 候选被写成“预测超导体”。

排序规则：

```text
Primary key: evidence_level
Secondary key: checker_status
Tertiary key: discovery_score
```

证据等级仍按：

```text
E0 < E1 < E2 < E3 < E4 < E5 < E6 < E7
```

语言规则：

- E0-E2：只能称为 hypothesis / candidate。
- E3-E4：可以称为 DFT-supported / phonon-checked candidate，但不能给数值
  `Tc`。
- E5：可以给 `Tc` 区间，但必须注明方法、`mu*` 扫描和收敛风险。
- E6-E7：可以进入高可信候选或实验建议榜。

### 8.3 Experiment Ranking

用途：

- 决定哪些材料值得推荐给实验合作者。
- 不等同于理论高分榜。

公式：

```text
experiment_score =
  0.20 * evidence_level_score
+ 0.15 * stability_score
+ 0.15 * synthesis_plausibility
+ 0.12 * pressure_accessibility
+ 0.10 * mechanism_clarity
+ 0.10 * novelty_score
+ 0.08 * toxicity_cost_availability_score
+ 0.05 * robustness_score
+ 0.05 * measurement_feasibility
```

必须惩罚：

- 只在极高压力下稳定的材料。
- 含 Hg、Tl、Po 等高毒或高处理风险元素的材料。
- 对氧空位、掺杂、压力或应变窗口极窄的材料。
- 只有 ML 分数、没有 DFT/phonon 证据的材料。
- checker 标记为 `revise` 或 `reject` 的材料。

### 8.4 分榜要求

瓦力瓦力至少维护以下分榜，避免高压、常压、强关联和 conventional EPC 候选
互相挤占：

```text
ambient_or_low_pressure_board
high_pressure_board
conventional_epc_board
cuprate_like_board
iron_based_like_board
oxide_interface_board
light_framework_board
exploratory_metal_board
```

每个 leaderboard 条目至少包含：

```text
rank
candidate_id
formula
branch
evidence_level
discovery_score
experiment_score
top_positive_reason
top_risk
next_action
```

核心原则：

```text
Ranking = 不是谁看起来 Tc 最大，而是谁在稳定性、机制可信度、新颖性、
可计算性和可实验性之间最值得进入下一轮。
```

---

## 9. Benchmark 顺序

瓦力瓦力必须先跑 benchmark，再跑发现候选。

顺序：

1. QE smoke test：Al 或 Si。
2. Nb：传统金属基线。
3. Pb：强耦合 conventional 基线，可暂不做 SOC/EPC。
4. MgB2：核心 benchmark，验证 `AlB2` family 和 sigma-band 机制。
5. H3S：高压小晶胞 smoke test，只做受限验证。

第一阶段暂不要求：

- LaH10 full EPC。
- nickelate realistic interface。
- full Eliashberg。

验收：

```text
benchmarks/<name>/input/
benchmarks/<name>/output/
benchmarks/<name>/dossier.md
reports/benchmark_checklist.md
```

---

## 10. 每日运行节奏

建议每天自动或半自动执行：

```text
1. refresh knowledge
2. generate candidates
3. prescreen candidates
4. promote top candidates
5. run at most 1 heavy QE job at a time
6. update dossiers
7. update leaderboard
8. write failures and strategy updates
```

每天限制：

```text
generated candidates: up to 10,000
branch coverage: every active branch receives at least the daily minimum
DFT queue promotions: up to 20
actual QE relax jobs: 1-5 depending on size
phonopy jobs: 0-1
```

---

## 11. 文件输出要求

瓦力瓦力每轮必须输出：

```text
reports/toolchain_status.md
reports/disk_usage_recommendations.md
reports/knowledge_update.md
reports/prescreen_leaderboard.md
reports/discovery_leaderboard.md
reports/evidence_leaderboard.md
reports/experiment_leaderboard.md
reports/dft_queue_status.md
reports/failures.md
reports/strategy_updates.md
reports/weekly_digest.md
```

每个候选必须有 dossier：

```text
dossiers/<evidence_level>/<candidate_id>.md
```

每个 dossier 至少包含：

```text
candidate_id
formula
family
branch
structure_source
generation_reason
parent_formula_or_template
mechanism_hypothesis
required_physics_tags
risk_tags
prescreen_score
known_similar_materials
DFT status
phonon status
mechanism note
checker status
next action
```

---

## 12. 验收标准

第 1 周验收：

- 独立工作区存在。
- 工具链状态报告存在。
- 磁盘清理建议存在。
- QE smoke test 成功或失败原因清楚。
- SCLib/Materials Project 接入计划明确。

第 2-3 周验收：

- Nb、Pb、MgB2 至少完成 DFT dossier。
- MgB2 机制说明能识别 sigma band / E2g phonon 方向。
- 失败日志能区分收敛失败、结构失败、输入失败、算力超限。

第 4-6 周验收：

- 至少 1,000 个候选完成 prescreen。
- 至少 20 个候选进入 DFT queue。
- 至少 5 个候选达到 E3。

第 7-12 周验收：

- 至少 3 个候选达到 E4。
- 形成第一版 Top-10 实验建议榜单。
- 每个 Top-10 候选都有 evidence level、机制解释和风险说明。
- strategy update 能基于失败模式调整下一轮搜索。

---

## 13. 瓦力瓦力工作准则

1. 先检查，再安装。
2. 先 benchmark，再发现。
3. 先 prescreen，再 DFT。
4. 先小晶胞，再复杂体系。
5. 先 dossier，再 leaderboard。
6. 先证据等级，再 `Tc` 数字。
7. 先提交清理建议，再删除文件。
8. 所有失败都要留下原因。
9. 所有候选都要能追溯来源。
10. 每轮 loop 都要产生下一轮策略更新。

---

## 14. 给瓦力瓦力的第一批任务

```text
Task 1: 建立 ~/loop-sc-vps 独立工作区。
Task 2: 输出 reports/toolchain_status.md，确认 QE、Python、pymatgen、spglib、mp-api、CHGNet、phonopy 状态。
Task 3: 输出 cleanup_audit/disk_usage_recommendations.md，只列建议，不删除。
Task 4: 完成 QE smoke test。
Task 5: 建立 SQLite schema 和 reports/ 空报告模板。
Task 6: 跑 Nb benchmark。
Task 7: 跑 Pb benchmark。
Task 8: 跑 MgB2 benchmark。
Task 9: 建立第一版 candidate generator。
Task 10: 生成第一版 prescreen leaderboard。
Task 11: 为 copper-based、iron-based、Al-O/STO oxide、Al/Ti/Pb/W exploratory branches 建立模板清单。
Task 12: 为每个 branch 输出至少 20 个 E0/E1 候选，并标注 parent template、mechanism hypothesis 和 risk tags。
Task 13: 将 B-C-H/B-C-N-H、p-block hydride、doped clathrate、layered nitride、kagome、MXene、高熵和拓扑掺杂方向加入每日候选生成权重表。
Task 14: 确认 organic/COF/MOF 方向已被排除在 v0.1 active branches 之外。
```

完成 Task 1-4 后，先向用户汇报确认，再继续 Task 5-14。
