# -*- coding: utf-8 -*-
"""把 v2.0/dist/game.json 转成 SillyTavern 角色卡：JSON（chara_card_v3）＋ 图片卡 PNG。

    python3 v2.0/tools/card.py [封面.png]

产出
    v2.0/dist/zhouji.v2.card.json
    v2.0/dist/zhouji.v2.card.png

对应关系（正文一个字不动，只是把结构摆成 V3 的样子）
    openings[0].text   → first_mes
    openings[1:].text  → alternate_greetings
    lorebook[]         → character_book.entries（keys/constant/ord/title 原样带过）
    panelSpec 与各开局的年代信息 → data.extensions.zhouji

图片卡按实测过的成品卡结构：chara 与 ccv3 两个 tEXt 块。新版酒馆读 ccv3，
旧版读 chara。封面里原有的文本类块（tEXt/zTXt/iTXt/eXIf）一律剥掉。
打包前扫一遍禁字，打包后回读比对，任何一步不过就拒绝产出。
"""
import base64
import io
import json
import os
import re
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
GAME = os.path.join(ROOT, 'dist', 'game.json')
CJSON = os.path.join(ROOT, 'dist', 'zhouji.v2.card.json')
CPNG = os.path.join(ROOT, 'dist', 'zhouji.v2.card.png')
ART = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'docs', 'shots', 'v2-title.png')

FORBID = re.compile('|'.join(['cla' 'ude', 'anthro' 'pic', 'yen' 'wa', 'ai ' 'assistant']), re.I)


def chunk(typ, data):
    return (struct.pack('>I', len(data)) + typ + data
            + struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff))


def dedupe(seq):
    seen, out = set(), []
    for x in seq or []:
        x = str(x).strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_card(g):
    ops = g['openings']
    entries = []
    for i, e in enumerate(g['lorebook']):
        keys = dedupe(e.get('keys'))
        if not keys and not e.get('constant'):
            raise SystemExit('第 %d 条既无 keys 又非常驻，永远不会触发：%s' % (i, e.get('title')))
        ext = {'cat': e.get('cat', '')}
        for k in ('from', 'to', 'pin'):
            if k in e:
                ext[k] = e[k]
        entries.append({
            'id': i + 1,
            'keys': keys,
            'secondary_keys': [],
            'comment': e.get('title', ''),
            'content': e.get('content', ''),
            'constant': bool(e.get('constant', False)),
            'selective': False,
            'insertion_order': i,
            'enabled': True,
            'position': 'before_char',
            'case_sensitive': False,
            'name': e.get('title', ''),
            'priority': 10,
            'extensions': {'zhouji': ext},
        })
    return {
        'spec': 'chara_card_v3',
        'spec_version': '3.0',
        'data': {
            'name': g.get('name', '') + ' v2',
            'description': g.get('description', ''),
            'personality': g.get('personality', ''),
            'scenario': g.get('scenario', ''),
            'first_mes': ops[0]['text'],
            'mes_example': g.get('mes_example', ''),
            'creator_notes': '十五个开局横跨前519年到730年，'
                             '每个开局都是独立的第一章，从任意一个进都能玩。'
                             '导入后建议一并启用随卡的世界书。',
            'system_prompt': g.get('system_prompt', ''),
            'post_history_instructions': g.get('post_history_instructions', ''),
            'alternate_greetings': [o['text'] for o in ops[1:]],
            'group_only_greetings': [],
            'tags': ['历史', '角色扮演', '多开局', '黑暗', '第一人称'],
            'creator': 'ekibenya',
            'character_version': '2.0',
            'extensions': {
                'zhouji': {
                    'panelSpec': g.get('panelSpec', {}),
                    'openings': [{'id': o['id'], 'year': o['year'],
                                  'era': o['era'], 'scene': o['scene']} for o in ops],
                },
            },
            'character_book': {
                'name': '周纪·千年世界书 v2',
                'description': '',
                'scan_depth': 4,
                'token_budget': 4096,
                'recursive_scanning': False,
                'extensions': {},
                'entries': entries,
            },
        },
    }


def write_png(card):
    payload = json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    hits = FORBID.findall(payload.decode('utf-8'))
    if hits:
        raise SystemExit('卡数据含禁字 %r，拒绝打包' % sorted({h.lower() for h in hits}))
    b64 = base64.b64encode(payload)

    raw = io.open(ART, 'rb').read()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit('封面不是 PNG：%s' % ART)
    out, i, inserted = [raw[:8]], 8, False
    while i < len(raw):
        ln = struct.unpack('>I', raw[i:i + 4])[0]
        typ = raw[i + 4:i + 8]
        blk = raw[i:i + 12 + ln]
        i += 12 + ln
        if typ in (b'tEXt', b'zTXt', b'iTXt', b'eXIf'):
            continue                      # 剥掉封面原有的一切文本块
        if typ == b'IEND' and not inserted:
            out.append(chunk(b'tEXt', b'chara\x00' + b64))
            out.append(chunk(b'tEXt', b'ccv3\x00' + b64))
            inserted = True
        out.append(blk)
    io.open(CPNG, 'wb').write(b''.join(out))

    # 回读比对：从产物里把两个块再解出来，跟源数据逐字节对
    raw2 = io.open(CPNG, 'rb').read()
    got = {}
    j = 8
    while j < len(raw2):
        ln = struct.unpack('>I', raw2[j:j + 4])[0]
        typ = raw2[j + 4:j + 8]
        dat = raw2[j + 8:j + 8 + ln]
        if typ == b'tEXt':
            k, _, v = dat.partition(b'\x00')
            got[k.decode()] = v
        j += 12 + ln
    for k in ('chara', 'ccv3'):
        if k not in got:
            raise SystemExit('产物里没有 %s 块' % k)
        if base64.b64decode(got[k]) != payload:
            raise SystemExit('%s 块回读不一致' % k)
    return len(payload)


def main():
    g = json.load(io.open(GAME, encoding='utf-8'))
    card = build_card(g)
    io.open(CJSON, 'w', encoding='utf-8').write(
        json.dumps(card, ensure_ascii=False, indent=1))
    n = write_png(card)
    d = card['data']
    print('角色卡 JSON  %s' % CJSON)
    print('图片卡 PNG   %s（封面 %s）' % (CPNG, os.path.basename(ART)))
    print('  卡名        %s' % d['name'])
    print('  first_mes   %d 字' % len(d['first_mes']))
    print('  备用开场白  %d 条' % len(d['alternate_greetings']))
    print('  世界书      %d 条，常驻 %d 条'
          % (len(d['character_book']['entries']),
             sum(1 for e in d['character_book']['entries'] if e['constant'])))
    print('  载荷        %d 字节' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
