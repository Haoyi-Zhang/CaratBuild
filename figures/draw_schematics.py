"""Draw the declared accounting protocol directly as a vector PDF.

Requires Python 3.9+ and Matplotlib; no TeX engine or network is used.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)





def draw(out):
    d=Drawing((-.15,-1.0,17.56,3.5))
    d.box('observe',1.425,1.2,2.9,1.7,'Payload observations\ncannot determine\nwork identity')
    d.box('declare',4.94,1.2,3.5,1.7,'Connector declarations\nmint, present, transform\neffect, and seal')
    d.edge('observe','declare',sa='e',sb='w')
    for name,x,y,index in [('n0',7.79,2.4,0),('n1',9.785,2.4,1),
                          ('n2',7.79,1,2),('n3',9.785,1,3),('n4',8.7875,-.4,4)]:
        d.box(name,x,y,1.7,.7,'Process '+str(index))
    d.edge('declare','n0',sa='e',sb='w')
    for a,b,sa,sb in [('n0','n1','e','w'),('n0','n2','s','n'),('n1','n3','s','n'),
                      ('n2','n3','e','w'),('n2','n4','s','nw'),('n3','n4','s','ne')]:
        d.ax.add_patch(FancyArrowPatch(d.point(a,sa),d.point(b,sb),arrowstyle='<->',
            mutation_scale=7.5,linewidth=.55,color='black',shrinkA=0,shrinkB=0,
            linestyle=(0,(4,3)),zorder=1))
    d.frame(6.76,-.95,4.055,3.9);d.text(8.7875,3.25,'Complete-fact exchange; five logs')
    d.box('final',12.54,2.2,2.9,1.5,'Window checker\nroster + intervals\nrelations + IDs')
    d.box('retain',12.54,.1,2.9,1.45,r'$f+1$ retention'+'\nReceipts +\ndurable pins')
    d.edge('n1','final',sa='e',sb='w');d.edge('n3','retain',sa='e',sb='w')
    d.edge('final','retain')
    d.box('answer',15.96,2.2,2.9,1.2,'Provisional / final\nor refused')
    d.box('project',15.96,.1,2.9,1.5,'Non-holder projection\naggregates + exact\nreplay/conflict fence')
    d.edge('final','answer',sa='e',sb='w');d.edge('retain','project',sa='e',sb='w')
    d.save(out,'overview')

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parent)
    out=parser.parse_args().output
    out.mkdir(parents=True,exist_ok=True)
    draw(out)
