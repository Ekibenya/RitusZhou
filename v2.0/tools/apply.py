# -*- coding: utf-8 -*-
"""把 v2.0/dist/game.json 装进游戏主文件，产出一份**新的** HTML，绝不改动原版。

    python3 v2.0/tools/apply.py                 # 产出 v2.0/dist/zhouji.v2.html
    python3 v2.0/tools/apply.py --in-place      # 真的替换掉线上那份（需要显式加这个开关）

原版主文件：core/vendor/three/build/chunks/9d717bc0/658d009400d1.html
里面有一行 `window.__GAME__ = {…}`，整张卡的开局与世界书都在这个 JSON 里。
本脚本只替换这一个 JSON 字面量，其余一个字节都不动。
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
HTML = os.path.join(REPO, 'core', 'vendor', 'three', 'build', 'chunks',
                    '9d717bc0', '658d009400d1.html')
GAME = os.path.join(ROOT, 'dist', 'game.json')
OUT = os.path.join(ROOT, 'dist', 'zhouji.v2.html')

MARK = 'window.__GAME__ = '


def main():
    in_place = '--in-place' in sys.argv
    for p in (HTML, GAME):
        if not os.path.exists(p):
            print('找不到 %s' % p)
            return 1

    src = io.open(HTML, encoding='utf-8').read()
    i = src.find(MARK)
    if i < 0:
        print('主文件里找不到 %s' % MARK)
        return 1
    start = src.index('{', i)
    obj, length = json.JSONDecoder().raw_decode(src[start:])
    end = start + length

    new = io.open(GAME, encoding='utf-8').read().strip()
    json.loads(new)  # 再解析一次，坏 JSON 绝不写进 HTML

    old_keys = list(obj.keys())
    new_keys = list(json.loads(new).keys())
    if old_keys != new_keys:
        print('顶层字段不一致，拒绝写入')
        print('  原版 %s' % old_keys)
        print('  新版 %s' % new_keys)
        return 1

    dst = HTML if in_place else OUT
    io.open(dst, 'w', encoding='utf-8').write(src[:start] + new + src[end:])
    print('已写入 %s' % dst)
    print('  原 JSON %d 字节 → 新 JSON %d 字节' % (end - start, len(new)))
    if not in_place:
        print('  原版未改动。确认满意后再跑一次加 --in-place。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
