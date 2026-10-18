#!/usr/bin/env python3
"""从人工核对的CSV生成毕业去向图。依赖Matplotlib；不读取或改写原始PDF。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/graduate-outcomes'
BLUE = '#1D5F8A'
ORANGE = '#B54E00'
INK = '#213547'
GREY = '#647887'


def rows(name):
    with (DATA / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def chinese_font():
    for name in ['Microsoft YaHei', 'Noto Sans CJK SC', 'Source Han Sans SC', 'SimHei', 'Arial Unicode MS']:
        try:
            font_manager.findfont(name, fallback_to_default=False)
            return name
        except ValueError:
            pass
    raise RuntimeError('未找到中文字体。请安装Microsoft YaHei或Noto Sans CJK SC后重试。')


def style_axis(ax, limit, ticks):
    ax.set_xlim(0, limit)
    ax.set_xticks(ticks)
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#DCE4EA', linewidth=.7)
    ax.tick_params(axis='both', colors=INK, length=0, pad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel('人数', loc='right', color=INK, labelpad=12)


def masters_chart(output):
    records = rows('masters.csv')
    fig = plt.figure(figsize=(11.6,8.5), facecolor='white')
    ax = fig.add_axes([.12,.225,.78,.58])
    fig.text(.055,.95,'硕士毕业去向',fontsize=23,fontweight='bold',color=INK)
    fig.text(.055,.902,'2016-2025届  |  人数与待定状态',fontsize=13,color=GREY)
    for i, row in enumerate(records):
        work, study, total = (int(row[k]) for k in ['work_column','further_study_column','total'])
        assert work + study == total
        ax.barh(i,work,height=.61,color=BLUE,edgecolor='white',linewidth=.8)
        ax.barh(i,study,left=work,height=.61,color=ORANGE,edgecolor='white',linewidth=.8)
        for start, width in [(0,work),(work,study)]:
            ax.text(start+width/2,i,str(width),ha='center',va='center',color='white',fontsize=12,fontweight='bold')
        for pending, start in [(int(row['work_pending_included']),work-int(row['work_pending_included'])),(int(row['study_pending_included']),total-int(row['study_pending_included']))]:
            if pending:
                ax.barh(i,pending,left=start,height=.61,facecolor='none',edgecolor=INK,hatch='////',linewidth=.8)
        ax.text(total+1.4,i,f'共{total}',va='center',fontsize=11,color=INK)
    ax.set_yticks(range(len(records)),[r['year']+(' †' if int(r['work_pending_included'])+int(r['study_pending_included']) else '') for r in records])
    ax.set_ylim(len(records)-.45,-.7)
    style_axis(ax,90,[0,20,40,60,80])
    legend=[Patch(facecolor=BLUE,label='工作栏'),Patch(facecolor=ORANGE,label='深造/读博栏'),Patch(facecolor='white',edgecolor=INK,hatch='////',label='其中待定（已计入原栏）')]
    fig.legend(handles=legend,loc='upper left',bbox_to_anchor=(.11,.867),ncol=3,frameon=False,fontsize=11,columnspacing=1.6,handlelength=1.8)
    notes=[
        '†2018深造栏含待定1人；2021工作栏含待定1人。2024本届无专业硕士毕业生。',
        '2016、2017深造栏分别含再次读硕1人、3人；各届人数与统计版本见正文。',
    ]
    for y,text in zip([.115,.065],notes):
        fig.text(.055,y,text,fontsize=10,color=GREY)
    fig.savefig(output,dpi=180,facecolor='white',metadata={'Title':'2016-2025届硕士毕业去向','Description':'原资料栏目人数；待定斜线已计入所在栏目。详见data/graduate-outcomes。'})
    plt.close(fig)


def undergraduate_chart(output):
    records=rows('undergraduates.csv')
    fig=plt.figure(figsize=(11.6,7.8),facecolor='white')
    left=fig.add_axes([.12,.28,.46,.44])
    right=fig.add_axes([.69,.28,.25,.44])
    fig.text(.055,.948,'本科毕业去向',fontsize=23,fontweight='bold',color=INK)
    fig.text(.055,.896,'2021-2025届  |  升学按办学地统计，就业按报告与单位清单汇总',fontsize=13,color=GREY)
    left.set_title('已列“升学”人数：按办学地整理',loc='left',fontsize=12,color=INK,pad=30)
    right.set_title('已列就业人数',loc='left',fontsize=12,color=INK,pad=30)
    for i,row in enumerate(records):
        local, abroad, total = (int(row[k]) for k in ['mainland_study_count','outside_mainland_study_count','study_count'])
        assert local+abroad == total
        left.barh(i,local,height=.54,color=BLUE,edgecolor='white',linewidth=.8)
        left.barh(i,abroad,left=local,height=.54,color=ORANGE,edgecolor='white',linewidth=.8)
        left.text(local/2,i,str(local),ha='center',va='center',color='white',fontsize=12,fontweight='bold')
        if abroad >= 3:
            left.text(local+abroad/2,i,str(abroad),ha='center',va='center',color='white',fontsize=11,fontweight='bold')
        left.text(total+1.3,i,f'共{total}',va='center',fontsize=11,color=INK)
        if row['work_count']:
            count=int(row['work_count'])
            right.barh(i,count,height=.54,color=GREY)
            right.text(count+1,i,str(count)+(' *' if row['year']=='2025' else ''),va='center',fontsize=12,color=INK)
        else:
            right.text(1,i,'未给出',va='center',fontsize=12,color='#7A8791')
    left.set_yticks(range(len(records)),[r['year'] for r in records])
    right.set_yticks([])
    for ax in [left,right]:
        ax.set_ylim(len(records)-.35,-.65)
    style_axis(left,82,[0,20,40,60,80])
    style_axis(right,36,[0,10,20,30])
    fig.legend(handles=[Patch(facecolor=BLUE,label='内地'),Patch(facecolor=ORANGE,label='内地以外（含香港）')],loc='upper left',bbox_to_anchor=(.115,.858),ncol=2,frameon=False,fontsize=11)
    notes=[
        '*2025就业29人为17个单位人数合计；2021-2023未披露就业人数。',
        '2024内地以外1人；2025升学69人，其中高校及科研机构68人、语言学校1人。',
        '升学率与去向落实率分别统计；各届升学机构和就业单位见正文及完整清单。',
    ]
    for y,text in zip([.16,.105,.05],notes):
        fig.text(.055,y,text,fontsize=10,color=GREY)
    fig.savefig(output,dpi=180,facecolor='white',metadata={'Title':'2021-2025届本科已披露毕业去向','Description':'升学按办学地整理；就业缺失不等于零，未推测毕业总数。'})
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'assets/figures')
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    font=chinese_font()
    with plt.rc_context({'font.family':font,'font.size':12,'axes.unicode_minus':False,'savefig.transparent':False}):
        masters_chart(args.output_dir/'masters-outcomes-2016-2025.png')
        undergraduate_chart(args.output_dir/'undergraduate-outcomes-2021-2025.png')
    record={'matplotlib':matplotlib.__version__,'python':platform.python_version(),'font':font,'figures':{},'input_sha256':{name:hashlib.sha256((DATA/name).read_bytes()).hexdigest() for name in ['masters.csv','undergraduates.csv']}}
    for p in sorted(args.output_dir.glob('*outcomes-*.png')):
        record['figures'][p.name]={'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
