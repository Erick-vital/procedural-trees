"""Campo suave de crecimiento, sin recortar/proyectar la geometría ni llenar vacíos."""
import math


def smooth(value):
    t=max(0.,min(1.,value));return t*t*(3-2*t)


class CrownField:
    def __init__(self,preset,phase):
        self.h=preset['height_m'];self.m=preset['maturity'];self.p=preset['crown_balance'];self.phase=phase
        self.radius=self.h*self.p['radius_ratio']*(.70+.40*self.m)*preset['crown_spread']/1.12
        self.path_budget=self.h*self.p['path_ratio']*(.8+.4*self.m)

    def level(self,point):
        x,y,z=point;angle=math.atan2(y,x)
        # Perfil redondeado vertical; los armónicos conservan regiones desiguales.
        vertical=(z/self.h-(.57+.04*(1-self.m)))/self.p['vertical_ratio']
        section=math.sqrt(max(.20,1-vertical*vertical))
        irregular=1+self.p['irregularity']*(.65*math.sin(angle+self.phase)+.35*math.cos(2*angle-.7*self.phase))
        anisotropy=1+.06*math.cos(2*angle+self.phase)
        return math.hypot(x,y)/(self.radius*section*irregular*anisotropy)

    def growth_factor(self,point):
        return 1-self.p['strength']*.65*smooth((self.level(point)-.50)/.65)

    def penalty(self,point):
        return self.p['strength']*1.8*max(0,self.level(point)-.65)**2

    def axis_budget(self,requested,root,path_to_root,order):
        remaining=max(self.h*.02,self.path_budget-path_to_root)
        factor=1-self.p['strength']*.40*smooth((self.level(root)-.35)/.7) if order>1 else 1.
        target=min(requested*factor,remaining*.85) if order>1 else requested
        return requested*(1-self.p['strength'])+target*self.p['strength']
