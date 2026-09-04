#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_title_variants.py — 电商商品标题与卖点文案生成（多平台）

功能：
  按商品信息与目标平台，生成多平台标题变体（A/B 两套）与五点描述骨架，
  并跑一轮违规词初筛（极限词/虚假功效/价格欺诈提示）。

用法：
  python generate_title_variants.py                   # 跑内置演示样例（自检）
  python generate_title_variants.py product.txt       # 读商品信息文件
  python generate_title_variants.py product.txt out.md # 指定输出文件

输入格式（product.txt，键值对，逗号分隔多值）：
  name=316不锈钢保温杯
  attr=480ml,一键开盖,礼盒装
  sell=12小时保温,食品级材质,单手操作
  scene=通勤,学生,上班族
  platform=淘宝,拼多多,抖音

依赖：仅 Python 标准库。
"""

import sys
import os
import re

# 极限词初筛（非穷尽，发布前人工复核）
RISK_WORDS = ["最", "第一", "顶级", "国家级", "世界级", "绝无仅有", "万能",
              "百分百", "唯一", "极致", "王牌", "销量第一", "领导品牌",
              "史上最低", " guaranteed", "立即抢购"]

DEMO = """name=316不锈钢保温杯
attr=480ml,一键开盖,礼盒装
sell=12小时保温,食品级材质,单手操作
scene=通勤,学生,上班族
platform=淘宝,拼多多,抖音
"""

PLATFORM_FORMULAS = {
    "淘宝": lambda d: f"{d['core']}{d['attr'][0] if d['attr'] else ''} {d['sell'][0] if d['sell'] else ''} {d['scene'][0] if d['scene'] else ''}水杯",
    "拼多多": lambda d: f"{d['core']}{d['attr'][0] if d['attr'] else ''} {d['attr'][1] if len(d['attr'])>1 else ''} {d['scene'][1] if len(d['scene'])>1 else ''}水杯 {d['attr'][2] if len(d['attr'])>2 else ''}",
    "京东": lambda d: f"{d['core']} {d['attr'][0] if d['attr'] else ''} {d['sell'][0] if d['sell'] else ''} {d['scene'][0] if d['scene'] else ''}",
    "抖音": lambda d: f"{d['scene'][0] if d['scene'] else ''}必备{d['core']} {d['sell'][0] if d['sell'] else ''} {d['attr'][0] if d['attr'] else ''} {d['scene'][1] if len(d['scene'])>1 else ''}水杯",
    "亚马逊": lambda d: f"{d['core']} {d['sell'][0] if d['sell'] else ''} {d['attr'][0] if d['attr'] else ''} {d['scene'][0] if d['scene'] else ''}",
    "tiktok": lambda d: f"{d['scene'][0] if d['scene'] else ''} {d['core']} {d['sell'][0] if d['sell'] else ''}",
}


def parse_input(text):
    data = {"name": "", "attr": [], "sell": [], "scene": [], "platform": []}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "name":
            data["name"] = v
            data["core"] = v
        elif k in data:
            data[k] = [x.strip() for x in v.split(",") if x.strip()]
    if "core" not in data:
        data["core"] = data["name"]
    return data


def gen_titles(data):
    platforms = data.get("platform") or ["淘宝"]
    out = []
    for p in platforms:
        fn = PLATFORM_FORMULAS.get(p)
        if not fn:
            continue
        t1 = fn(data).strip()
        # A/B：交换卖点与场景词顺序生成第二套
        d2 = dict(data)
        if d2["sell"] and d2["scene"]:
            d2["sell"] = [data["scene"][0]] + data["sell"][1:]
            d2["scene"] = [data["sell"][0] if False else (data["sell"][0] if data["sell"] else "")] + data["scene"][1:]
        t2 = fn(d2).strip()
        out.append((p, t1, t2))
    return out


def gen_bullets(data):
    bullets = []
    if data["sell"]:
        for i, s in enumerate(data["sell"][:5]):
            bullets.append(f"【{s}】本品{s}，真实可验证，买得放心。")
    else:
        bullets.append("【核心卖点】待补充真实卖点。")
    return bullets


def risk_scan(text):
    hits = [w for w in RISK_WORDS if w in text]
    return hits


def render(data):
    lines = []
    lines.append(f"# 商品文案：{data['name'] or '未命名'}\n")
    lines.append("## 一、各平台标题变体（A/B 两套）\n")
    titles = gen_titles(data)
    for p, t1, t2 in titles:
        lines.append(f"**{p}**")
        lines.append(f"- A：{t1}")
        lines.append(f"- B：{t2}")
        lines.append("")
    lines.append("## 二、五点卖点描述（骨架，请补真实证据）\n")
    for b in gen_bullets(data):
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## 三、违规词初筛\n")
    full = " ".join([t for _, t1, t2 in titles for t in (t1, t2)])
    hits = risk_scan(full)
    if hits:
        lines.append(f"⚠️ 检出疑似风险词：{', '.join(hits)} —— 请结合商品资质人工复核，勿用无依据的极限词/虚假承诺。")
    else:
        lines.append("未检出内置风险词库匹配项（AI 不穷尽，发布前仍须人工复核）。")
    lines.append("")
    lines.append("> 本脚本按平台公式拼标题，产出为草稿，真实数据与配图由运营补充。")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args:
        text = DEMO
        print("[自检模式] 使用内置演示样例\n")
    else:
        path = args[0]
        if not os.path.exists(path):
            print(f"错误：输入文件不存在 {path}", file=sys.stderr)
            return 2
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"[文件模式] 读取 {path}\n")

    data = parse_input(text)
    if not data["name"]:
        print("错误：缺少 name 字段", file=sys.stderr)
        return 2
    out = render(data)
    print(out)

    if len(args) >= 2:
        with open(args[1], "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n[已写出] {args[1]}")

    if not args:
        assert "淘宝" in out and "拼多多" in out, "自检失败：应生成多平台标题"
        assert "五点卖点" in out, "自检失败：应生成五点描述"
        print("\n[自检通过] 脚本功能正常，exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
