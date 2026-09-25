"""Dimensioned ribbon installation drawing (matplotlib is an optional CAD tool)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from assembly_fit import EXPECTED,FFC_WIDTHS,cable_path,SPACER_BOXES,PI_TOP
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'hw/mechanical/t1-ribbon-guide'
fig,ax=plt.subplots(1,3,figsize=(18,7),gridspec_kw={'width_ratios':[1.1,1.2,1]})
fig.suptitle('T1 FPGA ribbons - installation geometry',fontsize=20,x=.06,ha='left')
colors={'J86':'#607a92','J87':'#0084b4','J88':'#607a92','J89':'#0084b4'}
a=ax[0];a.add_patch(Rectangle((0,0),85,56,fill=False,lw=2,color='#202c39'))
for ref,(x,y,angle) in EXPECTED.items():
 w=FFC_WIDTHS[ref];a.add_patch(Rectangle((x-w/2,y-2.6),w,5.2,facecolor=colors[ref],alpha=.8));a.text(x,y,ref,ha='center',va='center',color='white',weight='bold')
 a.plot([x,x],[y-2.6 if not angle else y+2.6,56],color=colors[ref],alpha=.45,lw=2)
for x,y in [(3.5,3.5),(61.5,3.5),(3.5,52.5),(61.5,52.5)]:a.add_patch(plt.Circle((x,y),1.35,fill=False,color='#202c39'))
a.add_patch(Rectangle((5.25,56),68.5,2,facecolor='#efb642'))
a.annotate('Guide projects 2 mm',xy=(38,57),xytext=(8,69),arrowprops={'arrowstyle':'->'},fontsize=10)
a.annotate('J83 shifted left',xy=(4.7,12),xytext=(13,-8),arrowprops={'arrowstyle':'->'},fontsize=10)
a.text(42.5,79,'85 x 56 mm PCB | four Pi mounting points',ha='center',fontsize=10)
a.set(xlim=(-3,88),ylim=(83,-13),title='Underside layout (board XY)',xlabel='X / mm',ylabel='Y / mm');a.set_aspect('equal')
a=ax[1]
for ref in ['J88','J89']:
 path=cable_path(ref,*EXPECTED[ref][:2]);a.plot([v[1] for v in path],[v[2] for v in path],label=ref+' (nominal slot Z)',lw=2.5,color=colors[ref])
a.add_patch(Rectangle((0,-1.6),56,1.6,facecolor='#42745b'))
a.add_patch(Rectangle((0,PI_TOP-1.6),56,1.6,facecolor='#42745b'))
a.add_patch(Rectangle((2.5,PI_TOP),52,16,facecolor='#bcc4cd',alpha=.5))
a.add_patch(Rectangle((56,-11.4),2,5.5,fill=False,lw=2,edgecolor='#bf8617'))
a.text(4,.7,'HAT top Z = 0',fontsize=10)
a.text(4,PI_TOP-3.7,'Pi top Z = -28.779 mm',fontsize=10)
a.text(20,-17,'Pi port height envelope',fontsize=10,color='#526270')
a.text(28,-7,'-7.2 mm',fontsize=10,color=colors['J89']);a.text(28,-11.8,'-10.2 mm',fontsize=10,color=colors['J88'])
a.annotate('1 mm straight tip exit\n>=1.5 mm inner radius',xy=(14.8,-5),xytext=(2,-22),arrowprops={'arrowstyle':'->'},fontsize=10)
a.set(xlim=(0,78),ylim=(-34,4),title='Right ribbons (Y-Z side view)',xlabel='Y / mm',ylabel='Z / mm');a.set_aspect('equal');a.legend(loc='lower right',fontsize=9)
a=ax[2]
for name,(x,y,z,X,Y,Z) in SPACER_BOXES.items():a.add_patch(Rectangle((x,z),X-x,Z-z,facecolor='#aeb6c0',edgecolor='#657386'))
for z,label,c in [(-7.2,'J89',colors['J89']),(-10.2,'J88',colors['J88'])]:a.plot([41.75,72.25],[z,z],lw=3,color=c);a.text(73,z,label,va='center',fontsize=10)
a.plot([61.5,61.5],[-1.6,-5.1],color='#303a48',lw=2);a.plot([61.5,61.5],[PI_TOP,PI_TOP+5],color='#303a48',lw=2)
a.text(32,-18,'Offset web',fontsize=10,rotation=90)
a.annotate('Separate blind M2.5 threads\nNo through-bolt',xy=(61.5,-3),xytext=(31,1.5),arrowprops={'arrowstyle':'->'},fontsize=10)
a.annotate('27.179 mm surface gap',xy=(63.8,-23),xytext=(43,-32),arrowprops={'arrowstyle':'->'},fontsize=10)
a.set(xlim=(27,83),ylim=(-35,5),title='Windowed spacer (X-Z envelope)',xlabel='X / mm',ylabel='Z / mm');a.set_aspect('equal')
for a in ax:a.grid(alpha=.15);a.spines[['top','right']].set_visible(False)
fig.text(.06,.035,'Short-tip custom FPC required: body <=0.15 mm; mating tip 0.30 +/-0.03 mm; exposed reinforcement <=0.5 mm. Dimensions govern; do not scale.',fontsize=11)
fig.text(.06,.009,'CAD clearance only. Form with a 3 mm mandrel, fit the guide, and verify first-article seating, clearance and strain relief. See mechanical README.',fontsize=10,color='#53616e')
fig.tight_layout(rect=(.025,.14,.99,.93))
for ext in ('svg','png'):fig.savefig(out/('assembly-layout.'+ext),dpi=150)
