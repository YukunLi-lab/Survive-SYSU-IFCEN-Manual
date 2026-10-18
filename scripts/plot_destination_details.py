#!/usr/bin/env python3
"""从核对后的CSV重绘集团、学位与学校分组图；依赖Matplotlib和NumPy。"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

from plot_graduate_outcomes import chinese_font

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/graduate-outcomes'
OUTPUT = ROOT / 'assets/figures'
INK = '#213547'
GREY = '#5F7180'
EMPLOYERS = ['中广核', '中核', '国家电投', '华能', '其他单位', '单位未明', 'total']
SCHOOLS = ['清北复交', '西交', '中大本校', '其他211', '其他内地高校', '科研院所',
           'QS前200', 'QS201-500', 'QS500+', '境外未列综合排名', '待定', 'total']
DEGREES = ['doctor', 'master', 'unspecified', 'non_degree', 'pending', 'total']


def records(name, degree):
    with (DATA / name).open(encoding='utf-8', newline='') as f:
        return [r for r in csv.DictReader(f) if r['degree'] == degree]


def matrix(ax, rows, columns, labels, vmax, group_separators=()):
    values = np.array([[float(r[c]) if r[c] != '' else np.nan for c in columns] for r in rows])
    for row in values:
        if not np.isnan(row[-1]):
            assert np.nansum(row[:-1]) == row[-1]
    cmap = colors.LinearSegmentedColormap.from_list('count', ['#F3F7FA', '#A9CCDF', '#1D5F8A'])
    cmap.set_bad('#E4E7EA')
    # Total is an arithmetic check, not a second observation in the color scale.
    colored = values.copy()
    colored[:, -1] = np.nan
    ax.imshow(colored, cmap=cmap, vmin=0, vmax=vmax, aspect='auto', interpolation='nearest')
    for i in range(len(rows)):
        for j in range(len(columns)):
            value = values[i, j]
            if j == len(columns)-1:
                ax.add_patch(plt.Rectangle((j-.5, i-.5), 1, 1, facecolor='#EDF2F5', edgecolor='white'))
            txt = '—' if np.isnan(value) else str(int(value))
            dark = j != len(columns)-1 and not np.isnan(value) and value >= vmax*.64
            ax.text(j, i, txt, ha='center', va='center', fontsize=12,
                    color='white' if dark else INK,
                    fontweight='bold' if j==len(columns)-1 or (not np.isnan(value) and value>0) else 'normal')
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(rows)), [r['cohort'] for r in rows])
    ax.xaxis.tick_top()
    ax.tick_params(axis='both', length=0, pad=10, labelsize=11, colors=INK)
    ax.set_xticks(np.arange(-.5,len(labels),1), minor=True)
    ax.set_yticks(np.arange(-.5,len(rows),1), minor=True)
    ax.grid(which='minor', color='white', linewidth=2)
    ax.tick_params(which='minor', length=0)
    for x in group_separators: ax.axvline(x-.5,color='#758A99',linewidth=1.2)
    for spine in ax.spines.values(): spine.set_visible(False)


def save(fig, name):
    fig.savefig(OUTPUT / name, dpi=160, facecolor='white', metadata={'Title':name.rsplit('.',1)[0]})
    plt.close(fig)


def employment(degree, title, name):
    rows = records('employment-groups.csv', degree)
    height = 7.1 if degree=='master' else 5.4
    fig=plt.figure(figsize=(11.8,height),facecolor='white')
    fig.text(.06,.94,title,fontsize=23,fontweight='bold',color=INK)
    fig.text(.06,.875,'按集团归并下属公司、研究院与核电站  |  单位：人',fontsize=12,color=GREY)
    ax=fig.add_axes([.12,.22,.81,.52 if degree=='master' else .46])
    matrix(ax,rows,EMPLOYERS,['中广核','中核','国家电投\n（国电投）','华能','其他单位','单位未明','合计'],60 if degree=='master' else 20,[4,6])
    if degree=='master':
        notes=['单位未明：2019、2020各差1人；2025有1人单位名不清。0表示明细中未列该集团。',
               '2021细分46人；该届总览为51人，属于不同统计快照，不能逐栏相减。']
    else:
        notes=['— 表示未披露或无法归组；2021—2023就业总数未知，2024只披露就业9人。',
               '2025各单位合计29人；这些人数不能用于推算未披露的本科毕业总数。']
    for y,t in zip([.115,.055],notes):fig.text(.06,y,t,fontsize=10.5,color=GREY)
    save(fig,name)


def schools(degree,title,name):
    rows=records('study-groups.csv',degree)
    fig=plt.figure(figsize=(14.7,7.3 if degree=='master' else 5.7),facecolor='white')
    fig.text(.045,.94,title,fontsize=23,fontweight='bold',color=INK)
    fig.text(.045,.875,'学校分组互斥  |  QS统一采用2025世界大学综合排名  |  单位：人',fontsize=12,color=GREY)
    ax=fig.add_axes([.075,.235,.89,.49 if degree=='master' else .42])
    labels=['清北\n复交','西交','中大\n本校','其他\n211','其他内地\n高校','科研\n院所',
            'QS\n前200','QS\n201—500','QS\n500+','未列综合榜\n／归属未明','待定','合计']
    matrix(ax,rows,SCHOOLS,labels,55 if degree=='bachelor' else 12,[6,10,11])
    fig.text(.075,.795,'内地',fontsize=11,color=GREY)
    fig.text(.52,.795,'内地以外（含香港）',fontsize=11,color=GREY)
    notes=['其他211排除已单列学校；中国科学院大学、香港城市大学（东莞）列其他内地高校。',
           '未列综合榜／归属未明单列，包括研究机构、未核定综合榜的学校与校区不明条目。',
           '颜色随人数加深，直接数字为计数；0表示此套名单中该组没有条目。']
    for y,t in zip([.15,.095,.04],notes):fig.text(.045,y,t,fontsize=10.5,color=GREY)
    save(fig,name)


def degrees():
    fig=plt.figure(figsize=(13.8,9.2),facecolor='white')
    fig.text(.045,.95,'继续深造：目标学位能确认到哪一步？',fontsize=23,fontweight='bold',color=INK)
    fig.text(.045,.899,'按附件明确标签计数；不根据毕业时的学历推断下一阶段学位  |  单位：人',fontsize=12,color=GREY)
    labels=['博士','硕士','学位\n未注明','语言学校\n（非学位）','待定','合计']
    for degree,rect,title,limit in [
        ('master',[.075,.23,.415,.55],'硕士毕业生 · 2016—2025届',15),
        ('bachelor',[.56,.23,.415,.55],'本科毕业生 · 2021—2025届',70)]:
        ax=fig.add_axes(rect)
        matrix(ax,records('degree-types.csv',degree),DEGREES,labels,limit,[5])
        fig.text(rect[0],.849,title,fontsize=13,fontweight='bold',color=INK)
    fig.text(.045,.13,'硕士毕业生：明确读博143人、再读硕士4人、待定1人。',fontsize=12,color=INK)
    fig.text(.045,.075,'本科毕业生：268人仅注明“升学”、未写目标学位；另有语言学校1人。0表示明确标签人数为0。',fontsize=11,color=GREY)
    save(fig,'further-study-degree-types.png')


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'font.family':chinese_font(),'axes.unicode_minus':False,'font.size':11}):
        employment('master','硕士就业：集团细分 · 2016—2025届','masters-employment-groups-2016-2025.png')
        employment('bachelor','本科就业：集团细分 · 2021—2025届','undergraduate-employment-groups-2021-2025.png')
        schools('master','硕士深造：学校分组 · 2016—2025届','masters-study-groups-2016-2025.png')
        schools('bachelor','本科升学：学校分组 · 2021—2025届','undergraduate-study-groups-2021-2025.png')
        degrees()
    print(json.dumps({p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUTPUT.glob('*.png'))},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
