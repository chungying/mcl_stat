from math import pi,sqrt,atan2,exp,fabs,atan2,cos,sin,fabs
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm

class Pose:
  #x = 0.0
  #y = 0.0
  #a = 0.0

  def __init__(self, x=0.0, y=0.0, a=0.0):
    self.x = x
    self.y = y
    self.a = a

class Delta:
  #tran = 0.0
  #rot1 = 0.0
  #rot2 = 0.0

  def __init__(self, tran=0.0, rot1=0.0, rot2=0.0):
    self.tran = tran
    self.rot1 = rot1
    self.rot2 = rot2

def rad2eul(rad):
  return (rad/pi)*180.0

def eul2rad(eul):
  return (eul/180.0)*pi

def angleDiff(a1, a2):
  d12 = a1 - a2
  d21 = 2*pi - fabs(d12)
  if d12 > 0.0: d21 *= -1.0
  if fabs(d12) < fabs(d21):
    return d12
  else:
    return d21

def model(newx,newy,newa,oldx,oldy,olda):
  dx = newx - oldx
  dy = newy - oldy
  tran = sqrt(dx*dx + dy*dy)
  if tran <0.01:
    rot1 = 0.0
  else:
    rot1 = angleDiff(atan2(dy,dx),olda)
  rot2 = angleDiff(angleDiff(newa,olda),rot1)
  return (tran,rot1,rot2)

def delta(new, old):
  dx = new.x - old.x
  dy = new.y - old.y
  tran = sqrt(dx*dx + dy*dy)
  rot1 = angleDiff(atan2(dy, dx),old.a)
  rot2 = angleDiff(angleDiff(new.a,old.a),rot1)
  return Delta(tran,rot1,rot2)

def kinematic(old,delta):
  x = old.x + delta.tran*cos(old.a + delta.rot1)
  y = old.y + delta.tran*sin(old.a + delta.rot1)
  a = old.a + delta.rot1 + delta.rot2
  a = atan2(sin(a),cos(a))
  return Pose(x,y,a)

def prob(a,b):
  if b==0.0: return 1.0
  return (1.0 / (b * sqrt(2*pi))) * exp( a*a / (-2.0*b*b))

def motionModel(new, ut, old, alpha1, alpha2, alpha3, alpha4):
  delta_hat = delta(new, old)
  a1 = ut.rot1 - delta_hat.rot1
  b1 = alpha1*delta_hat.rot1*delta_hat.rot1 + alpha2*delta_hat.tran*delta_hat.tran;
  a2 = ut.tran - delta_hat.tran 
  b2 = alpha3*delta_hat.tran*delta_hat.tran + alpha4*delta_hat.rot1*delta_hat.rot1 + alpha4*delta_hat.rot2*delta_hat.rot2
  a3 = ut.rot2 - delta_hat.rot2 
  b3 = alpha1*delta_hat.rot2*delta_hat.rot2 + alpha2*delta_hat.tran*delta_hat.tran
  if b1 != 0.0 and a1 >= 16.0*b1: return 0.0
  if b2 != 0.0 and a2 >= 16.0*b2: return 0.0
  if b3 != 0.0 and a3 >= 16.0*b3: return 0.0
  return prob(a1,b1)*prob(a2,b2)*prob(a3,b3)

def motionModelS(u_tran, u_rot1, u_rot2, u_hat_tran, u_hat_rot1, u_hat_rot2, alphas=[0.8,0.8,0.8,0.8]):
  a1 = u_rot1 - u_hat_rot1
  b1 = alphas[0]*u_hat_rot1*u_hat_rot1 + alphas[1]*u_hat_tran*u_hat_tran
  a2 = u_tran - u_hat_tran
  b2 = alphas[2]*u_hat_tran*u_hat_tran + alphas[3]*u_hat_rot1*u_hat_rot1 + alphas[3]*u_hat_rot2*u_hat_rot2
  a3 = u_rot2 - u_hat_rot2
  b3 = alphas[0]*u_hat_rot2*u_hat_rot2 + alphas[1]*u_hat_tran*u_hat_tran
  return prob(a1,b1)*prob(a2,b2)*prob(a3,b3)

def motionModelO(u_tran, u_rot1, u_rot2, u_hat_tran, u_hat_rot1, u_hat_rot2, alphas=[0.8,0.8,0.8,0.8]):#[0.1,0.1,0.1,0.1]):
  a1 = u_rot1 - u_hat_rot1
  b1 = alphas[0]*fabs(u_hat_rot1) + alphas[1]*u_hat_tran
  a2 = u_tran - u_hat_tran
  b2 = alphas[2]*u_hat_tran + alphas[3]*fabs(u_hat_rot1) + alphas[3]*fabs(u_hat_rot2)
  a3 = u_rot2 - u_hat_rot2
  b3 = alphas[0]*fabs(u_hat_rot2) + alphas[1]*u_hat_tran
  return prob(a1,b1)*prob(a2,b2)*prob(a3,b3)
 
vmodelS=np.vectorize(motionModelS)
vmodelO=np.vectorize(motionModelO)
vkinematic=np.vectorize(model)
#genarr = lambda center, rad, gres: np.arange(center - rad, center + rad + gres, gres)
genarr = lambda center, rad, gres: np.concatenate((np.arange(center-gres,-rad,-gres)[::-1],np.arange(center,rad,gres)))
pos2str = lambda p,: '{}_{}_{}'.format(p.x,p.y,p.a)
genpose = lambda ang: Pose(0.0,0.0,ang)
vgenpose = np.vectorize(genpose)

def plotting(XX, YY, PP, saveflag=False, title='', prefix='', cstride=1, rstride=1):
  fig = plt.figure(figsize=(18,10))
  ax=fig.add_subplot(111,projection='3d')
  ax.set_title(title)
  ax.set_xlabel('x')
  ax.set_ylabel('y')
  #ax.plot_surface(XX,YY,PP,cmap=cm.coolwarm)
  ax.plot_surface(XX,YY,PP,cmap=cm.coolwarm,cstride=cstride, rstride=rstride,linewidth=0, antialiased=False)
  print 'lim:',ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
  if saveflag:
    plt.savefig('{}_{}.png'.format(prefix,title,ax.get_zlim()[1]))
  else:
    ax.view_init(elev=90,azim=-90)
    plt.show()
  
def demo(base_pose, ut, ares=(5.0/180.0 )*pi, gres = 0.05, radius = 1.0, saveflag=False):
  #genarr = lambda center, rad, gres: np.arange(center - rad, center + rad + gres, gres)
  #vkinematic=np.vectorize(model)
  #vmodelS=np.vectorize(motionModelS)
  #base_pose = Pose(0.0,0.0,eul2rad(0.0))
  #ut = Delta(1, eul2rad(0),eul2rad(0))
  #ares=(5.0/180.0 )*pi
  #gres = 0.05
  #radius = 3.0
  angle_arr = np.arange(-pi,pi,ares)
  trans_pose = kinematic(base_pose,ut)
  #alpha3 or alphas[2] is 0.1
  length = ut.tran*(1+4*0.8)
  #if length<radius: 
  #  length += radius
  #  print 'length is too short, make it longer to',length 
  X = genarr(base_pose.x, length, gres)
  Y = genarr(base_pose.y, length, gres)
  print pos2str(base_pose)
  print pos2str(trans_pose)
  XX,YY=np.meshgrid(X,Y)
  print 'dim:',XX.shape
  ones = np.ones(XX.shape)
  OX=ones*base_pose.x
  OY=ones*base_pose.y
  OA=ones*base_pose.a
  OT=ones*ut.tran
  OR1=ones*ut.rot1
  OR2=ones*ut.rot2
  P_list=[]
  Tr_list=[]
  R1_list=[]
  R2_list=[]
  for ang in angle_arr:
    Tr,R1,R2=vkinematic(XX,YY,ones*ang,OX,OY,OA)
    #P=vmodelS(OT,OR1,OR2,Tr,R1,R2)
    P=vmodelO(OT,OR1,OR2,Tr,R1,R2)
    P_list.append(P)
    Tr_list.append(Tr)
    R1_list.append(R1)
    R2_list.append(R2)

  if saveflag: resolution = 1
  else: resolution = 12
  for i in range(0,len(P_list),resolution):
    plotting(XX, YY, P_list[i], title='matidx{}_matang{}'.format(i,angle_arr[i]), prefix='_matidx{}_matang{}'.format(pos2str(base_pose),pos2str(trans_pose)), saveflag=saveflag)
  return (XX,YY,P_list,Tr_list,R1_list,R2_list)

