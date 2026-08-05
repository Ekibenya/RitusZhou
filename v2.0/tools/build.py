# -*- coding: utf-8 -*-
"""把 v2.0/data/ 下的分散源文件合成为一份 window.__GAME__ 用的 game.json。

    python3 v2.0/tools/build.py

输入
    v2.0/data/meta.json            panelSpec / name / description / personality /
                                   scenario / system_prompt / post_history_instructions /
                                   mes_example
    v2.0/data/openings/NN.md       首行是 JSON 头 {"id","era","scene","year"}，其余是正文
    v2.0/data/lore/*.json          世界书条目数组
                                   cat / title / keys / content
                                   可选：constant（常驻）、from/to（生效年份区间，
                                   负数是公元前）、pin（钉住）、ord（还原原版注入顺序）

输出
    v2.0/dist/game.json            与原版 window.__GAME__ 同构，字段顺序也一致

顺带做结构校验：字段缺失、id 重复、开局数量、世界书字段类型、明清穿帮词，
有问题直接非零退出，不产出半成品。
"""
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
DIST = os.path.join(ROOT, 'dist')

# 与原版 window.__GAME__ 完全一致的顶层字段顺序
TOP_ORDER = ['panelSpec', 'name', 'description', 'personality', 'scenario',
             'system_prompt', 'post_history_instructions', 'mes_example',
             'openings', 'lorebook']

# 原版 15 个开局的 id / year / era，一个字都不许动（游戏按 year 匹配时代与三维城池）
ANCHORS = [
    (1, -221, '前221年，咸阳宫'),
    (2, -212, '前212年，咸阳宫偏殿'),
    (3, -519, '前519年，洛邑王城'),
    (4, -517, '前517年，洛邑守藏室外'),
    (5, -499, '前499年，洛邑'),
    (6, -415, '前415年，洛邑明堂'),
    (7, -409, '前409年，洛邑'),
    (8, -247, '前247年，洛邑书库'),
    (9, -203, '前203年，洛阳'),
    (11, -110, '元封元年（前110年），洛阳圣域'),
    (12, 196, '建安元年（196年），洛阳圣域'),
    (13, 311, '永嘉五年（311年），洛阳圣域'),
    (14, 493, '太和十七年（493年），洛阳圣域'),
    (15, 605, '大业元年（605年），洛阳圣域'),
    (10, 730, '开元十八年（730年），洛阳圣域'),
]

# 明清与后世穿帮词。这张卡的时代考据是铁则，穿帮直接算构建失败。
LATE_ERA = ['丫鬟', '太监', '银子', '银两', '银票', '铜板', '圣旨', '奉天承运', '娘娘',
            '万岁爷', '奴才', '皇上', '太师椅', '青楼', '妓院', '衙门', '一炷香',
            '一盏茶', '女诫', '三从四德', '贞节牌坊', '缠足', '浸猪笼', '八股',
            '辣椒', '花生', '玉米', '土豆', '西瓜', '炒菜', '烧酒', '石狮子']

errors = []
warns = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warns.append(msg)


def load_meta():
    p = os.path.join(DATA, 'meta.json')
    if not os.path.exists(p):
        err('缺少 data/meta.json')
        return {}
    m = json.load(io.open(p, encoding='utf-8'))
    for k in TOP_ORDER:
        if k in ('openings', 'lorebook'):
            continue
        if k not in m:
            err('meta.json 缺字段 %s' % k)
        elif k != 'panelSpec' and not str(m[k]).strip():
            err('meta.json 字段 %s 是空的' % k)
    return m


def load_openings():
    files = sorted(glob.glob(os.path.join(DATA, 'openings', '*.md')))
    out = []
    for f in files:
        raw = io.open(f, encoding='utf-8').read()
        lines = raw.split('\n')
        if not lines or not lines[0].strip().startswith('{'):
            err('%s 首行不是 JSON 头' % os.path.basename(f))
            continue
        try:
            head = json.loads(lines[0].strip())
        except Exception as e:
            err('%s 首行 JSON 解析失败：%s' % (os.path.basename(f), e))
            continue
        text = '\n'.join(lines[1:]).strip()
        if not text:
            err('%s 正文是空的' % os.path.basename(f))
        for k in ('id', 'era', 'scene', 'year'):
            if k not in head:
                err('%s 头里缺 %s' % (os.path.basename(f), k))
        if '<mvu_panel>' not in text or '</mvu_panel>' not in text:
            err('%s 正文没有 <mvu_panel> 状态栏' % os.path.basename(f))
        for w in LATE_ERA:
            if w in text:
                err('%s 出现明清穿帮词「%s」' % (os.path.basename(f), w))
        for k in ('id', 'year'):
            if not isinstance(head.get(k), int):
                err('%s 的 %s 必须是整数（原版就是整数，写成字符串游戏会认不出）'
                    % (os.path.basename(f), k))
        out.append({'id': head.get('id'), 'era': head.get('era'),
                    'scene': head.get('scene'), 'text': text,
                    'year': head.get('year')})
    if len(out) != len(ANCHORS):
        err('开局数量是 %d，应为 %d' % (len(out), len(ANCHORS)))
    got = {(o['id'], o['year'], o['era']) for o in out}
    for a in ANCHORS:
        if a not in got:
            err('开局锚点丢失或被改动：id=%s year=%s era=%s' % a)
    ids = [o['id'] for o in out]
    if len(set(ids)) != len(ids):
        err('开局 id 有重复：%s' % ids)
    # 按原版顺序排列，游戏的择局界面依赖这个顺序
    order = {a[0]: i for i, a in enumerate(ANCHORS)}
    out.sort(key=lambda o: order.get(o['id'], 999))
    return out


def load_lore():
    files = sorted(glob.glob(os.path.join(DATA, 'lore', '*.json')))
    if not files:
        err('data/lore/ 下没有文件')
        return []
    out = []
    seen = {}
    for f in files:
        try:
            arr = json.load(io.open(f, encoding='utf-8'))
        except Exception as e:
            err('%s JSON 解析失败：%s' % (os.path.basename(f), e))
            continue
        if not isinstance(arr, list):
            err('%s 顶层不是数组' % os.path.basename(f))
            continue
        for i, e in enumerate(arr):
            where = '%s[%d]' % (os.path.basename(f), i)
            for k in ('cat', 'title', 'keys', 'content'):
                if k not in e:
                    err('%s 缺字段 %s' % (where, k))
            if not isinstance(e.get('keys'), list):
                err('%s 的 keys 不是数组' % where)
            if not str(e.get('content', '')).strip():
                err('%s 的 content 是空的' % where)
            t = e.get('title')
            if t in seen:
                err('世界书标题重复：%s（%s 与 %s）' % (t, seen[t], where))
            else:
                seen[t] = where
            for w in LATE_ERA:
                # 【铁则】明清禁令清单这类条目本身就要列举禁语，放行
                if w in str(e.get('content', '')) and '禁' not in e.get('title', ''):
                    warn('%s「%s」正文出现明清词「%s」，确认是不是在举反例'
                         % (where, t, w))
            # 字段顺序与原版一致；constant/from/to/pin 有则原样带过，
            # 没有就不写——from/to 是时代生效区间，pin 是钉住，都会真的影响注入
            item = {'cat': e['cat'], 'title': e['title'],
                    'keys': e['keys'], 'content': e['content']}
            for k in ('constant', 'from', 'to', 'pin'):
                if k in e:
                    item[k] = e[k]
            if 'from' in item and 'to' in item and item['from'] > item['to']:
                err('%s 的 from(%s) 大于 to(%s)' % (where, item['from'], item['to']))
            # ord 只用来还原原版的注入顺序，不进成品
            out.append((e.get('ord', 10000 + len(out)), item))
    out.sort(key=lambda x: x[0])
    return [x[1] for x in out]


def main():
    # --lore-only：只校验世界书。开局正在被别的工序改写时用，
    # 免得因为半成品的开局报错而挡住世界书这边的自查。
    if '--lore-only' in sys.argv:
        lore = load_lore()
        for w in warns:
            print('警告  %s' % w)
        if errors:
            for e in errors:
                print('错误  %s' % e)
            print('\n世界书校验失败，共 %d 处错误。' % len(errors))
            return 1
        print('世界书校验通过  %d 条，正文合计 %d 字，常驻 %d 条'
              % (len(lore), sum(len(e['content']) for e in lore),
                 sum(1 for e in lore if e.get('constant'))))
        return 0

    meta = load_meta()
    openings = load_openings()
    lore = load_lore()

    game = {}
    for k in TOP_ORDER:
        if k == 'openings':
            game[k] = openings
        elif k == 'lorebook':
            game[k] = lore
        elif k in meta:
            game[k] = meta[k]

    for w in warns:
        print('警告  %s' % w)
    if errors:
        print('')
        for e in errors:
            print('错误  %s' % e)
        print('\n构建失败，共 %d 处错误。' % len(errors))
        return 1

    if not os.path.isdir(DIST):
        os.makedirs(DIST)
    out = os.path.join(DIST, 'game.json')
    s = json.dumps(game, ensure_ascii=False, separators=(',', ':'))
    io.open(out, 'w', encoding='utf-8').write(s)

    n_chars = sum(len(o['text']) for o in openings)
    n_lore = sum(len(e['content']) for e in lore)
    print('构建成功  %s' % out)
    print('  开局    %d 篇，正文合计 %d 字，最短 %d，最长 %d'
          % (len(openings), n_chars,
             min(len(o['text']) for o in openings),
             max(len(o['text']) for o in openings)))
    print('  世界书  %d 条，正文合计 %d 字' % (len(lore), n_lore))
    print('  常驻条目 %d 条' % sum(1 for e in lore if e.get('constant')))
    print('  JSON    %d 字节' % len(s.encode('utf-8')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
