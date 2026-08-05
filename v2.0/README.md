# 周纪·千年天下 v2.0

原版留在 `core/` 下，一个字节没动，方便对比。这个目录是全新重写的一版。

## 换掉了什么

1.0 的问题是**文风**：第二人称的岁月静好回忆录，一千字讲完，主角是个「懒散爱吐槽、万事无所谓」的好人。

2.0 把开局与世界书从头重写，全程套用韩国轻小说中译体写作 skill：

- **十五个开局全部重写**，第一人称，先写韩语稿再逐行直译。正文从原来的 850～1290 字扩到 1846～3364 字，合计 3.5 万字。
- **一百八十三条世界书全部重写**，制度体：写定额、期限、帐簿、经手人、复核、例外条款、罚则，不写形容词。
- **姬瑶整个人推翻重做**。1.0 给她留了三处免罪台阶（「处刑是下面人抢着做的」「她本人毫不在意」「是无知不是冷酷」），一处不留全删。
- **卡片的六个字段全部重写**：description / personality / scenario / system_prompt / post_history_instructions / mes_example，system_prompt 从四条铁则扩到十四条。

## 目录

```
ranobe/          写作 skill（周纪特化版）
  SKILL.md       skill 全文
  references/    madness / devices / workflow 三份
  corpus/        七本韩国轻小说中译语料
  scripts/       measure.py — 自动评分器
  BIBLE.md       v2.0 设定圣经：姬瑶人格、十五局症状台账、写手交接单
data/
  meta.json      卡片六字段 + 状态栏规格
  openings/      十五篇开局（首行是 JSON 头）
  openings/ko/   十五篇韩语稿
  lore/          世界书，按分类分成十一个文件
tools/
  build.py       data/ → dist/game.json（顺带校验字段、锚点、穿帮词）
  card.py        game.json → SillyTavern 角色卡 JSON + 图片卡 PNG
  apply.py       把 game.json 装进游戏主文件，默认产出新文件
dist/
  game.json            可直接替换进游戏的 window.__GAME__
  zhouji.v2.card.json  SillyTavern 角色卡（chara_card_v3）
  zhouji.v2.card.png   图片角色卡（chara / ccv3 双 tEXt 块）
  zhouji.v2.html       装好新数据的游戏主文件
```

## 怎么用

```bash
python3 v2.0/tools/build.py                 # 合成 game.json
python3 v2.0/tools/card.py                  # 产出角色卡 JSON 与 PNG
python3 v2.0/tools/apply.py                 # 产出 dist/zhouji.v2.html，原版不动
python3 v2.0/tools/apply.py --in-place      # 确认满意后，真的替换线上那份
python3 v2.0/ranobe/scripts/measure.py v2.0/data/openings/*.md   # 十五篇全部重跑评分
```

角色卡 PNG 直接拖进 SillyTavern 就能导入，世界书随卡带过去。

## 评分器改了哪四处

`ranobe/scripts/measure.py` 是姊妹卡那套评分器的周纪特化版，只动了四个地方：

| 项 | 改动 |
|---|---|
| `C7` | 世界说明的检出词从「马娘」换成「不老的周天子」，并改成距离判定（中文语序自由，原版的前后固定顺序会漏判） |
| `Q1` | 新增明清与后世穿帮词检查（这张卡的时代考据是铁则），只在开局上发火 |
| `C24` | 见下し词表里去掉「奴才」——它本身是明清词，跟 Q1 打架 |
| `S2b` | 「老子」加例外：老聃是本卡主要人物，只抓第一人称粋がり的那个「老子」 |

原七本语料的自测结果与改前一致，没改坏。

## 当前状态

- 十五篇开局：`measure.py` 全项通过，15 / 15
- 世界书：183 条（原 177 条，重写时补了 6 条），`build.py` 校验零错误
- 开局的 `id` / `year` / `era` 三个字段与原版逐字一致，世界书的 `constant` / `from` / `to` / `pin` 全部原样保留 —— 游戏按 `year` 匹配时代与三维城池，按 `from`/`to` 决定条目在哪个时代生效，动了就会错位
