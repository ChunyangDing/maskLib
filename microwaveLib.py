# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 17:29:02 2019

@author: Sasha

Library for drawing standard microwave components (CPW parts, inductors, capacitors etc)

Only standard composite components (inductors, launchers) are included here- complicated / application specific composites
go in sub-libraries
"""

import maskLib.MaskLib as m
from dxfwrite import DXFEngine as dxf
from dxfwrite import const
from dxfwrite.entities import Polyline
from dxfwrite.vector2d import vadd, midpoint ,vsub, vector2angle, magnitude, distance
from dxfwrite.algebra import rotate_2d

from maskLib.Entities import SolidPline, SkewRect, CurveRect, RoundRect, InsideCurve, DogBone
from maskLib.utilities import kwargStrip, curveAB

from copy import deepcopy
from matplotlib.path import Path
from matplotlib.transforms import Bbox
import math
from copy import copy
import numpy as np 

# ===============================================================================
# perforate the ground plane with a grid of squares, which avoid any polylines 
# ===============================================================================
#TODO move to MaskLib


def waffle(chip, grid_x, grid_y=None,width=10,height=None,exclude=None,padx=0,pady=None,bleedRadius=1,layer='0'):
    radius = max(int(bleedRadius),0)
    
    if exclude is None:
        exclude = ['FRAME']
    else:
        exclude.append('FRAME')
        
    if grid_y is None:
        grid_y = grid_x
    
    if height is None:
        height = width
        
    if pady is None:
        pady=padx
        
    nx, ny = list(map(int, [(chip.width) / grid_x, (chip.height) / grid_y]))
    occupied = [[False]*ny for i in range(nx)]
    for i in range(nx):
        occupied[i][0] = True
        occupied[i][-1] = True
    for i in range(ny):
        occupied[0][i] = True
        occupied[-1][i] = True
    
    for e in chip.chipBlock.get_data():
        if isinstance(e.__dxftags__()[0], Polyline):
            if e.layer not in exclude:
                o_x_list = []
                o_y_list = []
                plinePts = [v.__getitem__('location').__getitem__('xy') for v in e.__dxftags__()[0].get_data()]
                plinePts.append(plinePts[0])
                for p in plinePts:
                    o_x, o_y = list(map(int, (p[0] / grid_x, p[1] / grid_y)))
                    if 0 <= o_x < nx and 0 <= o_y < ny:
                        o_x_list.append(o_x)
                        o_y_list.append(o_y)
                        
                        #this will however ignore a rectangle with corners outside the chip...
                if o_x_list:
                    path = Path([[pt[0]/grid_x,pt[1]/grid_y] for pt in plinePts],closed=True)
                    for x in range(min(o_x_list)-1, max(o_x_list)+2):
                        for y in range(min(o_y_list)-1, max(o_y_list)+2):
                            try:
                                if path.contains_point([x+.5,y+.5]):
                                    occupied[x][y]=True
                                elif path.intersects_bbox(Bbox.from_bounds(x,y,1.,1.),filled=True):
                                    occupied[x][y]=True
                            except IndexError:
                                pass
       

    second_pass = deepcopy(occupied)
    for r in range(radius):
        for i in range(nx):
            for j in range(ny):
                if occupied[i][j]:
                    for ip, jp in [(i+1,j), (i-1,j), (i,j+1), (i,j-1)]:
                        try:
                            second_pass[ip][jp] = True
                        except IndexError:
                            pass
        occupied = deepcopy(second_pass)
   
    for i in range(int(padx/grid_x),nx-int(padx/grid_x)):
        for j in range(int(pady/grid_y),ny-int(pady/grid_y)):
            if not second_pass[i][j]:
                pos = i*grid_x + grid_x/2., j*grid_y + grid_y/2.
                chip.add(dxf.rectangle(pos,width,height,bgcolor=chip.wafer.bg(layer),halign=const.CENTER,valign=const.MIDDLE,layer=layer) )   
                
    return chip

def waffle_bumpbond(chip, grid_x, grid_y=None, width=10, height=None, exclude=None, padx=0, pady=None, bleedRadius=1, layer1='140_IUBM', layer2='40_UBM', layer3='45_BUMP'):
    radius = max(int(bleedRadius), 0)

    if exclude is None:
        exclude = ['FRAME']
    else:
        exclude.append('FRAME')

    if grid_y is None:
        grid_y = grid_x

    if height is None:
        height = width

    if pady is None:
        pady = padx

    nx, ny = list(map(int, [(chip.width) / grid_x, (chip.height) / grid_y]))
    occupied = [[False] * ny for i in range(nx)]
    for i in range(nx):
        occupied[i][0] = True
        occupied[i][-1] = True
    for i in range(ny):
        occupied[0][i] = True
        occupied[-1][i] = True

    for e in chip.chipBlock.get_data():
        if isinstance(e.__dxftags__()[0], Polyline):
            if e.layer not in exclude:
                o_x_list = []
                o_y_list = []
                plinePts = [v.__getitem__('location').__getitem__('xy') for v in e.__dxftags__()[0].get_data()]
                plinePts.append(plinePts[0])
                for p in plinePts:
                    o_x, o_y = list(map(int, (p[0] / grid_x, p[1] / grid_y)))
                    if 0 <= o_x < nx and 0 <= o_y < ny:
                        o_x_list.append(o_x)
                        o_y_list.append(o_y)

                        # this will however ignore a rectangle with corners outside the chip...
                if o_x_list:
                    path = Path([[pt[0] / grid_x, pt[1] / grid_y] for pt in plinePts], closed=True)
                    for x in range(min(o_x_list) - 1, max(o_x_list) + 2):
                        for y in range(min(o_y_list) - 1, max(o_y_list) + 2):
                            try:
                                if path.contains_point([x + .5, y + .5]):
                                    occupied[x][y] = True
                                elif path.intersects_bbox(Bbox.from_bounds(x, y, 1., 1.), filled=True):
                                    occupied[x][y] = True
                            except IndexError:
                                pass

    second_pass = deepcopy(occupied)
    for r in range(radius):
        for i in range(nx):
            for j in range(ny):
                if occupied[i][j]:
                    for ip, jp in [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]:
                        try:
                            second_pass[ip][jp] = True
                        except IndexError:
                            pass
        second_pass = deepcopy(second_pass)

    for i in range(int(padx / grid_x), nx - int(padx / grid_x)):
        for j in range(int(pady / grid_y), ny - int(pady / grid_y)):
            if not second_pass[i][j]:
                pos = i * grid_x + grid_x / 2., j * grid_y + grid_y / 2.
                chip.add(
                    dxf.rectangle(pos, width, height, bgcolor=chip.wafer.bg(), halign=const.CENTER, valign=const.MIDDLE,
                                  layer=layer1))
                chip.add(
                    dxf.rectangle(pos, width, height, bgcolor=chip.wafer.bg(), halign=const.CENTER, valign=const.MIDDLE,
                                  layer=layer2))
                chip.add(dxf.circle(radius=7.5, center=pos, bgcolor=chip.wafer.bg(), layer=layer3))

    return chip

# ===============================================================================
# basic POSITIVE microstrip function definitions
# ===============================================================================

def Strip_straight(chip,structure,length,w=None,bgcolor=None,**kwargs): #note: uses CPW conventions
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    
    chip.add(dxf.rectangle(struct().start,length,w,valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=structure,length=length)

def Strip_taper(chip,structure,length=None,w0=None,w1=None,bgcolor=None,offset=(0,0),**kwargs): #note: uses CPW conventions
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w0 is None:
        try:
            w0 = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if w1 is None:
        try:
            w1 = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    #if undefined, make outer angle 30 degrees
    if length is None:
        length = math.sqrt(3)*abs(w0/2-w1/2)
    
    chip.add(SkewRect(struct().start,length,w0,offset,w1,rotation=struct().direction,valign=const.MIDDLE,edgeAlign=const.MIDDLE,bgcolor=bgcolor,**kwargs),structure=structure,offsetVector=vadd((length,0),offset))

def Strip_bend(chip,structure,angle=90,CCW=True,w=None,radius=None,ptDensity=120,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
        
    while angle < 0:
        angle = angle + 360
    angle = angle%360
        
    chip.add(CurveRect(struct().start,w,radius,angle=angle,ptDensity=ptDensity,ralign=const.MIDDLE,valign=const.MIDDLE,rotation=struct().direction,vflip=not CCW,bgcolor=bgcolor,**kwargs))
    struct().updatePos(newStart=struct().getPos((radius*math.sin(math.radians(angle)),(CCW and 1 or -1)*radius*(math.cos(math.radians(angle))-1))),angle=CCW and -angle or angle)


def Strip_stub_open(chip,structure,flipped=False,curve_out=True,r_out=None,w=None,allow_oversize=True,length=None,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if r_out is None:
        try:
            if allow_oversize:
                r_out = struct().defaults['r_out']
            else:
                r_out = min(struct().defaults['r_out'],w/2)
        except KeyError:
            print('r_out not defined in ',chip.chipID,'!\x1b[0m')
            r_out=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    
    if r_out > 0:
        dx = 0.
        if flipped:
            if allow_oversize:
                dx = max(length,r_out)
            else:
                dx = min(w/2,r_out)
        
        if allow_oversize:
            l=r_out
        else:
            l=min(w/2,r_out)
        
        if length is None: length=0

        chip.add(RoundRect(struct().getPos((dx,0)),max(length,l),w,l,roundCorners=[0,curve_out,curve_out,0],hflip=flipped,valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargs),structure=structure,length=max(l,length))
    else:
        if length is not None:
            if allow_oversize:
                l=length
            else:
                l=min(w/2,length)
        else:
            l=w/2
        Strip_straight(chip,structure,l,w=w,bgcolor=bgcolor,**kwargs)

def Strip_stub_short(chip,structure,r_ins=None,w=None,flipped=False,extra_straight_section=False,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID,'!\x1b[0m')
    if r_ins is None:
        try:
            r_ins = struct().defaults['r_ins']
        except KeyError:
            #print('r_ins not defined in ',chip.chipID,'!\x1b[0m')
            r_ins=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    if r_ins > 0:
        if extra_straight_section and not flipped:
            Strip_straight(chip, struct(), r_ins, w=w,rotation=struct().direction,bgcolor=bgcolor,**kwargs)
        chip.add(InsideCurve(struct().getPos((0,-w/2)),r_ins,rotation=struct().direction,hflip=flipped,bgcolor=bgcolor,**kwargs))
        chip.add(InsideCurve(struct().getPos((0,w/2)),r_ins,rotation=struct().direction,hflip=flipped,vflip=True,bgcolor=bgcolor,**kwargs))
        if extra_straight_section and flipped:
                Strip_straight(chip, struct(), r_ins, w=w,rotation=struct().direction,bgcolor=bgcolor,**kwargs)

def Strip_pad(chip,structure,length,r_out=None,w=None,bgcolor=None,**kwargs):
    '''
    Draw a pad with all rounded corners (similar to strip_stub_open + strip_straight + strip_stub_open but only one shape)

    '''
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if r_out is None:
        try:
            r_out = min(struct().defaults['r_out'],w/2)
        except KeyError:
            print('r_out not defined in ',chip.chipID,'!\x1b[0m')
            r_out=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    
    if r_out > 0:
        chip.add(RoundRect(struct().getPos((0,0)),length,w,r_out,roundCorners=[1,1,1,1],valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargs),structure=structure,length=length)
    else:
        Strip_straight(chip,structure,length,w=w,bgcolor=bgcolor,**kwargs)

# ===============================================================================
# basic NEGATIVE CPW function definitions
# ===============================================================================


def CPW_straight(chip,structure,length,w=None,s=None,bondwires=False,bond_pitch=70,incl_end_bond=True,bgcolor=None,**kwargs): #note: uses CPW conventions
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')

    if bondwires: # bond parameters patched through kwargs
        num_bonds = int(length/bond_pitch)
        this_struct = struct().clone()
        this_struct.shiftPos(bond_pitch)
        if not incl_end_bond: num_bonds -= 1
        for i in range(num_bonds):
            Airbridge(chip, this_struct, **kwargs)
            this_struct.shiftPos(bond_pitch)
    
    chip.add(dxf.rectangle(struct().getPos((0,-w/2)),length,-s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    chip.add(dxf.rectangle(struct().getPos((0,w/2)),length,s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=structure,length=length)

    return struct().getPos()
        
def CPW_taper(chip,structure,length=None,w0=None,s0=None,w1=None,s1=None,bgcolor=None,offset=(0,0),**kwargs): #note: uses CPW conventions
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w0 is None:
        try:
            w0 = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s0 is None:
        try:
            s0 = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if w1 is None:
        try:
            w1 = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s1 is None:
        try:
            s1 = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    #if undefined, make outer angle 30 degrees
    if length is None:
        length = math.sqrt(3)*abs(w0/2+s0-w1/2-s1)
    
    chip.add(SkewRect(struct().getPos((0,-w0/2)),length,s0,(offset[0],w0/2-w1/2+offset[1]),s1,rotation=struct().direction,valign=const.TOP,edgeAlign=const.TOP,bgcolor=bgcolor,**kwargs))
    chip.add(SkewRect(struct().getPos((0,w0/2)),length,s0,(offset[0],w1/2-w0/2+offset[1]),s1,rotation=struct().direction,valign=const.BOTTOM,edgeAlign=const.BOTTOM,bgcolor=bgcolor,**kwargs),structure=structure,offsetVector=(length+offset[0],offset[1]))
    
def CPW_stub_short(chip,structure,flipped=False,curve_ins=True,curve_out=True,r_out=None,w=None,s=None,length=None,bgcolor=None,**kwargs):
    allow_oversize = (curve_ins != curve_out)
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if r_out is None:
        try:
            if allow_oversize:
                r_out = struct().defaults['r_out']
            else:
                r_out = min(struct().defaults['r_out'],s/2)
        except KeyError:
            print('r_out not defined in ',chip.chipID,'!\x1b[0m')
            r_out=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    
    if r_out > 0:
        
        dx = 0.
        if flipped:
            if allow_oversize:
                dx = r_out
            else:
                dx = min(s/2,r_out)
        
        if allow_oversize:
            l=r_out
        else:
            l=min(s/2,r_out)

        chip.add(RoundRect(struct().getPos((dx,w/2)),l,s,l,roundCorners=[0,curve_ins,curve_out,0],hflip=flipped,valign=const.BOTTOM,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
        chip.add(RoundRect(struct().getPos((dx,-w/2)),l,s,l,roundCorners=[0,curve_out,curve_ins,0],hflip=flipped,valign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs),structure=structure,length=l)
    else:
        if length is not None:
            if allow_oversize:
                l=length
            else:
                l=min(s/2,length)
        else:
            l=s/2
        CPW_straight(chip,structure,l,w=w,s=s,bgcolor=bgcolor,**kwargs)
        
def CPW_stub_open(chip,structure,length=0,r_out=None,r_ins=None,w=None,s=None,flipped=False,extra_straight_section=False,bgcolor=None, polygon_overlap=False, **kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if length==0:
        length = max(length,s)
    if r_out is None:
        try:
            r_out = struct().defaults['r_out']
        except KeyError:
            print('\x1b[33mr_out not defined in ',chip.chipID,'!\x1b[0m')
            r_out=0
    if r_ins is None:
        try:
            r_ins = struct().defaults['r_ins']
        except KeyError:
            #print('r_ins not defined in ',chip.chipID,'!\x1b[0m')
            r_ins=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    dx = 0.
    if flipped:
        dx = length

    if r_ins > 0:
        if extra_straight_section and not flipped:
            CPW_straight(chip, struct(), r_ins, w=w,s=s,rotation=struct().direction,bgcolor=bgcolor,**kwargs)
        d_angle = 0
        if polygon_overlap: d_angle = 0.03
        chip.add(InsideCurve(struct().getPos((dx,w/2)),r_ins, angle=90+d_angle, rotation=struct().direction - d_angle/2,hflip=flipped,bgcolor=bgcolor,**kwargs))
        chip.add(InsideCurve(struct().getPos((dx,-w/2)),r_ins, angle=90+d_angle, rotation=struct().direction + d_angle/2,hflip=flipped,vflip=True,bgcolor=bgcolor,**kwargs))

    chip.add(RoundRect(struct().getPos((dx,0)),length,w+2*s,min(r_out,length),roundCorners=[0,1,1,0],hflip=flipped,valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargs),structure=structure,length=length)
    if extra_straight_section and flipped:
        CPW_straight(chip, struct(), r_ins, w=w,s=s,rotation=struct().direction,bgcolor=bgcolor,**kwargs)

def CPW_cap(chip,structure,gap,r_ins=None,w=None,s=None,bgcolor=None,angle=90,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if r_ins is None:
        try:
            r_ins = struct().defaults['r_ins']
        except KeyError:
            #print('r_ins not defined in ',chip.chipID,'!\x1b[0m')
            r_ins=0
    if bgcolor is None:
        bgcolor = chip.wafer.bg()

    if r_ins > 0:
        chip.add(InsideCurve(struct().getPos((0,w/2)),r_ins,rotation=struct().direction + 90,vflip=True,angle=angle,bgcolor=bgcolor,**kwargs))
        chip.add(InsideCurve(struct().getPos((0,-w/2)),r_ins,rotation=struct().direction - 90,angle=angle,bgcolor=bgcolor,**kwargs))
        # chip.add(InsideCurve(struct().getPos((gap,w/2)),r_ins,rotation=struct().direction + 90,angle=angle,bgcolor=bgcolor,**kwargs))
        # chip.add(InsideCurve(struct().getPos((gap,-w/2)),r_ins,rotation=struct().direction - 90,vflip=True,angle=angle,bgcolor=bgcolor,**kwargs))

    chip.add(dxf.rectangle(struct().start,gap,w+2*s,valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=structure,length=gap)

        
def CPW_stub_round(chip,structure,w=None,s=None,round_left=True,round_right=True,flipped=False,bgcolor=None,**kwargs):
    #same as stub_open, but preserves gap width along turn (so radii are nominally defined by w, s)
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    
    dx = 0.
    if flipped:
        dx = s+w/2

    if False:#round_left and round_right:
        chip.add(CurveRect(struct().getPos((dx,w/2)),s,w/2,angle=180,ralign=const.BOTTOM,rotation=struct().direction,hflip=flipped,bgcolor=bgcolor,**kwargs),structure=structure,length=s+w/2)
    else:
        if round_left:
            chip.add(CurveRect(struct().getPos((dx,w/2)),s,w/2,angle=90,ralign=const.BOTTOM,rotation=struct().direction,hflip=flipped,bgcolor=bgcolor,**kwargs))
        else:
            chip.add(dxf.rectangle(struct().getPos((0,w/2)),s+w/2,s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(InsideCurve(struct().getPos((flipped and s or w/2,w/2)),w/2,rotation=struct().direction,hflip=flipped,bgcolor=bgcolor,**kwargs))
            chip.add(dxf.rectangle(struct().getPos((s+w/2-dx,w/2)),-s,-w/2,rotation=struct().direction,halign = flipped and const.RIGHT or const.LEFT, bgcolor=bgcolor,**kwargStrip(kwargs)))
        if round_right:
            chip.add(CurveRect(struct().getPos((dx,-w/2)),s,w/2,angle=90,ralign=const.BOTTOM,rotation=struct().direction,hflip=flipped,vflip=True,bgcolor=bgcolor,**kwargs),structure=structure,length=s+w/2)
        else:
            chip.add(dxf.rectangle(struct().getPos((0,-w/2)),s+w/2,-s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(InsideCurve(struct().getPos((flipped and s or w/2,-w/2)),w/2,rotation=struct().direction,hflip=flipped,vflip=True,bgcolor=bgcolor,**kwargs))
            chip.add(dxf.rectangle(struct().getPos((s+w/2-dx,-w/2)),-s,w/2,rotation=struct().direction,halign = flipped and const.RIGHT or const.LEFT, bgcolor=bgcolor,**kwargStrip(kwargs)),structure=structure,length=s+w/2)
    
def CPW_bend(chip,structure,angle=90,CCW=True,w=None,s=None,radius=None,ptDensity=120,bondwires=False,incl_end_bond=True,bond_pitch=70,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
        
    while angle < 0:
        angle = angle + 360
    angle = angle%360
    angleRadians = math.radians(angle)

    startstruct = struct().clone()
        
    chip.add(CurveRect(struct().start,s,radius,angle=angle,ptDensity=ptDensity,roffset=w/2,ralign=const.BOTTOM,rotation=struct().direction,vflip=not CCW,bgcolor=bgcolor,**kwargs))
    chip.add(CurveRect(struct().start,s,radius,angle=angle,ptDensity=ptDensity,roffset=-w/2,ralign=const.TOP,valign=const.TOP,rotation=struct().direction,vflip=not CCW,bgcolor=bgcolor,**kwargs))
    struct().updatePos(newStart=struct().getPos((radius*math.sin(angleRadians),(CCW and 1 or -1)*radius*(math.cos(angleRadians)-1))),angle=CCW and -angle or angle)

    if bondwires: # bond parameters patched through kwargs
        bond_angle_density = 8
        if 'lincolnLabs' in kwargs and kwargs['lincolnLabs']: bond_angle_density = int((2*math.pi*radius)/bond_pitch)
        clockwise = 1 if CCW else -1
        bond_points = curveAB(startstruct.start, struct().start, clockwise=clockwise, angleDeg=angle, ptDensity=bond_angle_density)
        if not incl_end_bond: bond_points = bond_points[:-1]
        for i, bond_point in enumerate(bond_points[1:], start=1):
            this_struct = m.Structure(chip, start=bond_point, direction=startstruct.direction-clockwise*i*360/bond_angle_density)
            Airbridge(chip, this_struct, br_radius=radius, clockwise=clockwise, **kwargs)


def CPW_tee(chip,structure,w=None,s=None,radius=None,r_ins=None,w1=None,s1=None,bgcolor=None,hflip=False,branch_off=const.CENTER, polygon_overlap=False, **kwargs):
    
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)
    if radius is None:
        try:
            radius = 2*struct().defaults['s']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if r_ins is None: #check if r_ins is defined in the defaults
        try:
            r_ins = struct().defaults['r_ins']
        except KeyError: # quiet catch
            r_ins = None   
    
    #default to left and right branches identical to original structure
    if w1 is None:
        w1 = w
    if s1 is None:
        s1 = s
        
    #clone structure defaults
    defaults1 = copy(struct().defaults)
    #update new defaults if defined
    defaults1.update({'w':w1})
    defaults1.update({'s':s1})
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
        
    #long curves not allowed if gaps differ
    if s!=s1:
        radius = min(abs(radius),min(s,s1))
    
    #assign a inside curve radius if not defined
    if r_ins is None:
        r_ins = radius
    
    s_rad = max(radius,s1)
    
    #figure out if tee is centered, or offset
    if branch_off == const.LEFT:
        struct().translatePos((s_rad+w1/2 - 2*hflip*(s_rad+w1/2),w/2+max(radius,s)),angle=-90)
    elif branch_off == const.RIGHT:
        struct().translatePos((s_rad+w1/2 - 2*hflip*(s_rad+w1/2),-w/2-max(radius,s)),angle=90)

    chip.add(dxf.rectangle(struct().getPos((s_rad+w1 - 2*hflip*(s_rad+w1),0)),hflip and -s1 or s1,2*max(radius,s)+w,valign=const.MIDDLE,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    if s==s1:
        chip.add(CurveRect(struct().getPos((0,-w/2-s)),s,radius,hflip=hflip,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
        chip.add(CurveRect(struct().getPos((0,w/2+s)),s,radius,hflip=hflip,vflip=True,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
    else:
        if s1>s:
            chip.add(dxf.rectangle(struct().getPos((0,-w/2)),hflip and s-s1 or s1-s,-s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(dxf.rectangle(struct().getPos((0,w/2)),hflip and s-s1 or s1-s,s,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(CurveRect(struct().getPos((hflip and s-s1 or s1-s,-w/2-s)),radius,radius,hflip=hflip,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
            chip.add(CurveRect(struct().getPos((hflip and s-s1 or s1-s,w/2+s)),radius,radius,hflip=hflip,vflip=True,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
        else:#s1<s
            chip.add(CurveRect(struct().getPos((0,-w/2-radius)),radius,radius,hflip=hflip,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
            chip.add(CurveRect(struct().getPos((0,w/2+radius)),radius,radius,hflip=hflip,vflip=True,ralign=const.TOP,rotation=struct().direction,bgcolor=bgcolor,**kwargs))
            chip.add(dxf.rectangle(struct().getPos((0,-w/2-radius)),hflip and -radius or radius,-(s-s1),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(dxf.rectangle(struct().getPos((0,w/2+radius)),hflip and -radius or radius,(s-s1),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    if radius <= min(s,s1) and r_ins > 0:
        #inside edges are square
        d_angle = 0
        if polygon_overlap: d_angle = 0.03
        chip.add(InsideCurve(struct().getPos((0,w/2+s)),r_ins,hflip=hflip,vflip=True,ralign=const.TOP, angle=90+d_angle, rotation=struct().direction + d_angle/2, bgcolor=bgcolor,**kwargs))
        chip.add(InsideCurve(struct().getPos((0,-w/2-s)),r_ins,hflip=hflip,vflip=False,ralign=const.TOP, angle=90+d_angle, rotation=struct().direction - d_angle/2, bgcolor=bgcolor,**kwargs))
    
    
    if branch_off == const.CENTER:  
        s_l = struct().cloneAlong((s_rad+w1/2 - 2*hflip*(s_rad+w1/2),w/2+max(radius,s)),newDirection=90,defaults=defaults1)
        s_r = struct().cloneAlong((s_rad+w1/2 - 2*hflip*(s_rad+w1/2),-w/2-max(radius,s)),newDirection=-90,defaults=defaults1)
    
        return s_l,s_r
    elif branch_off == const.LEFT:
        s_l = struct().cloneAlong((0,0),newDirection=180)
        struct().translatePos((w/2+max(radius,s),s_rad+w1/2 - 2*hflip*(s_rad+w1/2)),angle=90)
        return s_l
    elif branch_off == const.RIGHT:
        s_r = struct().cloneAlong((0,0),newDirection=180)
        struct().translatePos((w/2+max(radius,s),-s_rad-w1/2 + 2*hflip*(s_rad+w1/2)),angle=-90)
        return s_r

# ===============================================================================
# basic NEGATIVE TwoPinCPW function definitions
# ===============================================================================

def TwoPinCPW_straight(chip,structure,length,w=None,s_ins=None,s_out=None,Width=None,s=None,bgcolor=None,**kwargs): #note: uses CPW conventions
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s is not None:
        #s overridden somewhere above
        if s_ins is None:
            s_ins = s
        if s_out is None:
            s_out = s
    if s_ins is None:
        try:
            s_ins = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s_out is None:
        if Width is not None:
            s_out = Width - w - s_ins/2
        else:
            try:
                s_out = struct().defaults['s']
            except KeyError:
                print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    
    
    chip.add(dxf.rectangle(struct().getPos((0,-s_ins/2-w)),length,-s_out,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    chip.add(dxf.rectangle(struct().getPos((0,-s_ins/2)),length,s_ins,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    chip.add(dxf.rectangle(struct().getPos((0,s_ins/2+w)),length,s_out,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=structure,length=length)

# ===============================================================================
#  NEGATIVE wire/stripline function definitions
# ===============================================================================

def Wire_bend(chip,structure,angle=90,CCW=True,w=None,radius=None,bgcolor=None,**kwargs):
    #only defined for 90 degree bends
    if angle%90 != 0:
        return
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
        
    while angle < 0:
        angle = angle + 360
    angle = angle%360
        
    if radius-w/2 > 0:
        chip.add(CurveRect(struct().start,radius-w/2,radius,angle=angle,roffset=-w/2,ralign=const.TOP,valign=const.TOP,rotation=struct().direction,vflip=not CCW,bgcolor=bgcolor,**kwargs))
    for i in range(angle//90):
        chip.add(InsideCurve(struct().getPos(vadd(rotate_2d((radius+w/2,(CCW and 1 or -1)*(radius+w/2)),(CCW and -1 or 1)*math.radians(i*90)),(0,CCW and -radius or radius))),radius+w/2,rotation=struct().direction+(CCW and -1 or 1)*i*90,bgcolor=bgcolor,vflip=not CCW,**kwargs))
    struct().updatePos(newStart=struct().getPos((radius*math.sin(math.radians(angle)),(CCW and 1 or -1)*radius*(math.cos(math.radians(angle))-1))),angle=CCW and -angle or angle)

# ===============================================================================
# composite CPW function definitions
# ===============================================================================
def CPW_pad(chip,struct,l_pad=0,l_gap=0,padw=300,pads=50,l_lead=None,w=None,s=None,r_ins=None,r_out=None,bgcolor=None,**kwargs):
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            w=0
            print('\x1b[33mw not defined in ',chip.chipID)
    CPW_stub_open(chip,struct,length=max(l_gap,pads),r_out=r_out,r_ins=r_ins,w=padw,s=pads,flipped=True,**kwargs)
    CPW_straight(chip,struct,max(l_pad,padw),w=padw,s=pads,**kwargs)
    if l_lead is None:
        l_lead = max(l_gap,pads)
    CPW_stub_short(chip,struct,length=l_lead,r_out=r_out,r_ins=r_ins,w=w,s=pads+padw/2-w/2,flipped=False,curve_ins=False,**kwargs)


def CPW_launcher(chip,struct,l_taper=None,l_pad=0,l_gap=0,padw=300,pads=160,w=None,s=None,r_ins=0,r_out=0,bgcolor=None,**kwargs):
    CPW_stub_open(chip,struct,length=max(l_gap,pads),r_out=r_out,r_ins=r_ins,w=padw,s=pads,flipped=True,**kwargs)
    CPW_straight(chip,struct,max(l_pad,padw),w=padw,s=pads,**kwargs)
    CPW_taper(chip,struct,length=l_taper,w0=padw,s0=pads,**kwargs)

def CPW_taper_cap(chip,structure,gap,width,l_straight=0,l_taper=None,s1=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if s1 is None:
        try:
            s = struct().defaults['s']
            w = struct().defaults['w']
            s1 = width*s/w
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
            print('\x1b[33ms not defined in ',chip.chipID)
    if l_taper is None:
        l_taper = 3*width
    if l_straight<=0:
        try:
            tap_angle = math.degrees(math.atan(2*l_taper/(width-struct().defaults['w'])))
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
            tap_angle = 90
    else:
        tap_angle = 90
        
    CPW_taper(chip,structure,length=l_taper,w1=width,s1=s1,**kwargs)
    if l_straight > 0 :
        CPW_straight(chip,structure,length=l_straight,w=width,s=s1,**kwargs)
    CPW_cap(chip, structure, gap, w=width, s=s1, angle=tap_angle, **kwargs)
    if l_straight > 0 :
        CPW_straight(chip,structure,length=l_straight,w=width,s=s1,**kwargs)
    CPW_taper(chip,structure,length=l_taper,w0=width,s0=s1,**kwargs)
    
def CPW_directTo(chip,from_structure,to_structure,to_flipped=True,w=None,s=None,radius=None,CW1_override=None,CW2_override=None,flip_angle=False,debug=False,**kwargs):
    def struct1():
        if isinstance(from_structure,m.Structure):
            return from_structure
        else:
            return chip.structure(from_structure)
    if radius is None:
        try:
            radius = struct1().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    #struct2 is only a local copy
    struct2 = isinstance(to_structure,m.Structure) and to_structure or chip.structure(to_structure)
    if to_flipped:
        struct2.direction=(struct2.direction+180.)%360
    
    CW1 = vector2angle(struct1().getGlobalPos(struct2.start)) < 0
    CW2 = vector2angle(struct2.getGlobalPos(struct1().start)) < 0

    target1 = struct1().getPos((0,CW1 and -2*radius or 2*radius))
    target2 = struct2.getPos((0,CW2 and -2*radius or 2*radius))
    
    #reevaluate based on center positions
    
    CW1 = vector2angle(struct1().getGlobalPos(target2)) < 0
    CW2 = vector2angle(struct2.getGlobalPos(target1)) < 0
    
    if CW1_override is not None:
        CW1 = CW1_override
    if CW2_override is not None:
        CW2 = CW2_override

    center1 = struct1().getPos((0,CW1 and -radius or radius))
    center2 = struct2.getPos((0,CW2 and -radius or radius))
    
    if debug:
        chip.add(dxf.line(struct1().getPos((-3000,0)),struct1().getPos((3000,0)),layer='FRAME'))
        chip.add(dxf.line(struct2.getPos((-3000,0)),struct2.getPos((3000,0)),layer='FRAME'))
        chip.add(dxf.circle(center=center1,radius=radius,layer='FRAME'))
        chip.add(dxf.circle(center=center2,radius=radius,layer='FRAME'))
    
    correction_angle=math.asin(abs(2*radius*(CW1 - CW2)/distance(center2,center1)))
    angle1 = abs(struct1().direction - math.degrees(vector2angle(vsub(center2,center1)))) + math.degrees(correction_angle)
    if flip_angle:
        angle1 = 360-abs(struct1().direction - math.degrees(vector2angle(vsub(center2,center1)))) + math.degrees(correction_angle)
    
    if debug:
        print(CW1,CW2,angle1,math.degrees(correction_angle))
    
    if angle1 > 270:
        if debug:
            print('adjusting to shorter angle')
        angle1 = min(angle1,abs(360-angle1))
    '''
    if CW1 - CW2 == 0 and abs(angle1)>100:
        if abs((struct1().getGlobalPos(struct2.start))[1]) < 2*radius:
            print('adjusting angle')
            angle1 = angle1 + math.degrees(math.asin(abs(2*radius/distance(center2,center1))))
            '''
    CPW_bend(chip,from_structure,angle=angle1,w=w,s=s,radius=radius, CCW=CW1,**kwargs)
    CPW_straight(chip,from_structure,distance(center2,center1)*math.cos(correction_angle),w=w,s=s,**kwargs)
    
    angle2 = abs(struct1().direction-struct2.direction)
    if angle2 > 270:
        angle2 = min(angle2,abs(360-angle2))
    CPW_bend(chip,from_structure,angle=angle2,w=w,s=s,radius=radius,CCW=CW2,**kwargs)

#Various wiggles (meander) definitions 

def wiggle_calc(chip,structure,length=None,nTurns=None,maxWidth=None,Width=None,start_bend = True,stop_bend=True,w=None,s=None,radius=None,debug=False,**kwargs):
    #figure out 
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            s = 0
    #prevent dumb entries
    if nTurns is None:
        nTurns = 1
    elif nTurns < 1:
        nTurns = 1
    
    #debug
    if debug:
        print('w=',w,' s=',s,' nTurns=',nTurns,' length=',length,' Width=',Width,' maxWidth=',maxWidth)
    
    #is length constrained?
    if length is not None:
        if nTurns is None:
            nTurns = 1
        h = (length - nTurns*2*math.pi*radius - (start_bend+stop_bend)*(math.pi/2-1)*radius)/(4*nTurns)

        #is width constrained?
        if Width is not None or maxWidth is not None:
            #maxWidth corresponds to the wiggle width, while Width corresponds to the total width filled
            if maxWidth is not None:
                if Width is None:
                    Width = maxWidth
                else:
                    maxWidth = min(maxWidth,Width)
            else:
                maxWidth = Width
            while h+radius+w/2+s/2>maxWidth:
                nTurns = nTurns+1
                h = (length - nTurns*2*math.pi*radius - (start_bend+stop_bend)*(math.pi/2-1)*radius)/(4*nTurns)
    else: #length is not contrained
        h= maxWidth-radius-w/2-s
    h = max(h,radius)
    return {'nTurns':nTurns,'h':h,'length':length,'maxWidth':maxWidth,'Width':Width}

def CPW_wiggles(chip,structure,length=None,nTurns=None,maxWidth=None,CCW=True,start_bend = True,stop_bend=True,w=None,s=None,radius=None,bgcolor=None,debug=False,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    
    params = wiggle_calc(chip,structure,length,nTurns,maxWidth,None,start_bend,stop_bend,w,s,radius,**kwargs)
    [nTurns,h,length,maxWidth]=[params[key] for key in ['nTurns','h','length','maxWidth']]
    if (length is None) or (h is None) or (nTurns is None):
        print('not enough params specified for CPW_wiggles!')
        return
    if debug:
        chip.add(dxf.rectangle(struct().start,(nTurns*4 + start_bend + stop_bend)*radius,2*h,valign=const.MIDDLE,rotation=struct().direction,layer='FRAME'))
        chip.add(dxf.rectangle(struct().start,(nTurns*4 + start_bend + stop_bend)*radius,2*maxWidth,valign=const.MIDDLE,rotation=struct().direction,layer='FRAME'))
    if start_bend:
        CPW_bend(chip,structure,angle=90,CCW=CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
        if h > radius:
            CPW_straight(chip,structure,h-radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
    else:
        CPW_straight(chip,structure,h,w=w,s=s,bgcolor=bgcolor,**kwargs)
    CPW_bend(chip,structure,angle=180,CCW=not CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
    CPW_straight(chip,structure,h+radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
    if h > radius:
        CPW_straight(chip,structure,h-radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
    CPW_bend(chip,structure,angle=180,CCW=CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
    if h > radius:
        CPW_straight(chip,structure,h-radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
    for n in range(nTurns-1):
        CPW_straight(chip,structure,h+radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
        CPW_bend(chip,structure,angle=180,CCW=not CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
        CPW_straight(chip,structure,h+radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
        if h > radius:
            CPW_straight(chip,structure,h-radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
        CPW_bend(chip,structure,angle=180,CCW=CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
        if h > radius:
            CPW_straight(chip,structure,h-radius,w=w,s=s,bgcolor=bgcolor,**kwargs)
    if stop_bend:
        CPW_bend(chip,structure,angle=90,CCW=not CCW,w=w,s=s,radius=radius,bgcolor=bgcolor,**kwargs)
    else:
        CPW_straight(chip,structure,radius,w=w,s=s,bgcolor=bgcolor,**kwargs)

def Strip_wiggles(chip,structure,length=None,nTurns=None,maxWidth=None,CCW=True,start_bend = True,stop_bend=True,w=None,radius=None,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    
    params = wiggle_calc(chip,structure,length,nTurns,maxWidth,None,start_bend,stop_bend,w,0,radius,**kwargs)
    [nTurns,h,length,maxWidth]=[params[key] for key in ['nTurns','h','length','maxWidth']]
    if (h is None) or (nTurns is None):
        print('not enough params specified for Microstrip_wiggles!')
        return

    if start_bend:
        Strip_bend(chip,structure,angle=90,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        if h > radius:
            Strip_straight(chip,structure,h-radius,w=w,bgcolor=bgcolor,**kwargs)
    else:
        Strip_straight(chip,structure,h,w=w,bgcolor=bgcolor,**kwargs)
    Strip_bend(chip,structure,angle=180,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    Strip_straight(chip,structure,h+radius,w=w,bgcolor=bgcolor,**kwargs)
    if h > radius:
        Strip_straight(chip,structure,h-radius,w=w,bgcolor=bgcolor,**kwargs)
    Strip_bend(chip,structure,angle=180,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    if h > radius:
        Strip_straight(chip,structure,h-radius,w=w,bgcolor=bgcolor,**kwargs)
    for n in range(nTurns-1):
        Strip_straight(chip,structure,h+radius,w=w,bgcolor=bgcolor,**kwargs)
        Strip_bend(chip,structure,angle=180,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        Strip_straight(chip,structure,h+radius,w=w,bgcolor=bgcolor,**kwargs)
        if h > radius:
            Strip_straight(chip,structure,h-radius,w=w,bgcolor=bgcolor,**kwargs)
        Strip_bend(chip,structure,angle=180,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        if h > radius:
            Strip_straight(chip,structure,h-radius,w=w,bgcolor=bgcolor,**kwargs)
    if stop_bend:
        Strip_bend(chip,structure,angle=90,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    else:
        Strip_straight(chip,structure,radius,w=w,bgcolor=bgcolor,**kwargs)

def Inductor_wiggles(chip,structure,length=None,nTurns=None,maxWidth=None,Width=None,CCW=True,start_bend = True,stop_bend=True,pad_to_width=None,w=None,s=None,radius=None,bgcolor=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if radius is None:
        try:
            radius = struct().defaults['radius']
        except KeyError:
            print('\x1b[33mradius not defined in ',chip.chipID,'!\x1b[0m')
            return
    if bgcolor is None:
        bgcolor = chip.wafer.bg()
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID,'!\x1b[0m')
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')

    if pad_to_width is None and Width is not None:
        pad_to_width = True
    params = wiggle_calc(chip,structure,length,nTurns,maxWidth,Width,start_bend,stop_bend,w,0,radius,**kwargs)
    [nTurns,h,length,maxWidth,Width]=[params[key] for key in ['nTurns','h','length','maxWidth','Width']]
    if (h is None) or (nTurns is None):
        print('not enough params specified for CPW_wiggles!')
        return
    
    pm = (CCW - 0.5)*2
    
    #put rectangles on either side to line up with max width
    if pad_to_width:
        if Width is None:
            print('\x1b[33mERROR:\x1b[0m cannot pad to width with Width undefined!')
            return
        if start_bend:
            chip.add(dxf.rectangle(struct().getPos((0,h+radius+w/2)),(2*radius)+(nTurns)*4*radius,Width-(h+radius+w/2),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(dxf.rectangle(struct().getPos((0,-h-radius-w/2)),(stop_bend)*(radius+w/2)+(nTurns)*4*radius + radius-w/2,(h+radius+w/2)-Width,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
        else:
            chip.add(dxf.rectangle(struct().getPos((-h-radius-w/2,w/2)),(h+radius+w/2)-Width,(radius-w/2)+(nTurns)*4*radius,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
            chip.add(dxf.rectangle(struct().getPos((h+radius+w/2,-radius)),Width-(h+radius+w/2),(stop_bend)*(radius+w/2)+(nTurns)*4*radius + w/2,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    #begin wiggles
    if start_bend:
        chip.add(dxf.rectangle(struct().getPos((0,pm*w/2)),radius+w/2,pm*(h+radius),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
        Wire_bend(chip,structure,angle=90,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        if h > radius:
            chip.add(dxf.rectangle(struct().getPos((0,-pm*w/2)),h+w/2,pm*(radius-w/2),valign=const.BOTTOM,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=struct(),length=h-radius)
        else:
            chip.add(dxf.rectangle(struct().getPos((0,-pm*w/2)),radius+w/2,pm*(radius-w/2),valign=const.BOTTOM,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    else:
        chip.add(dxf.rectangle(struct().getPos((0,-pm*w/2)),2*radius+w/2,pm*(radius-w/2),valign=const.BOTTOM,rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=struct(),length=radius)
        #struct().shiftPos(h)
    chip.add(dxf.rectangle(struct().getPos((0,pm*w/2)),-h-max(h,radius)-radius-w/2,pm*(2*radius-w),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    Wire_bend(chip,structure,angle=180,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    struct().shiftPos(h+radius)
    if h > radius:
        struct().shiftPos(h-radius)
    chip.add(dxf.rectangle(struct().getPos((0,-pm*w/2)),-h-max(h,radius)-radius-w/2,pm*(-2*radius+w),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
    Wire_bend(chip,structure,angle=180,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    if h > radius:
        struct().shiftPos(h-radius)
    for n in range(nTurns-1):
        struct().shiftPos(h+radius)
        chip.add(dxf.rectangle(struct().getPos((0,pm*w/2)),-h-max(h,radius)-radius-w/2,pm*(2*radius-w),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
        Wire_bend(chip,structure,angle=180,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        struct().shiftPos(2*h)
        chip.add(dxf.rectangle(struct().getPos((0,-pm*w/2)),-h-max(h,radius)-radius-w/2,pm*(-2*radius+w),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
        Wire_bend(chip,structure,angle=180,CCW=CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
        struct().shiftPos(h-radius)
    chip.add(dxf.rectangle(struct().getLastPos((-radius-w/2,pm*w/2)),w/2+h,pm*(radius-w/2),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=struct())
    if stop_bend:
        chip.add(dxf.rectangle(struct().getPos((radius+w/2,-pm*w/2)),h+radius,pm*(radius+w/2),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)))
        Wire_bend(chip,structure,angle=90,CCW=not CCW,w=w,radius=radius,bgcolor=bgcolor,**kwargs)
    else:
        #CPW_straight(chip,structure,radius,w=w,s=s,bgcolor=bgcolor)
        chip.add(dxf.rectangle(struct().getPos((0,pm*w/2)),radius,pm*(radius-w/2),rotation=struct().direction,bgcolor=bgcolor,**kwargStrip(kwargs)),structure=struct(),length=radius)
        
def TwoPinCPW_wiggles(chip,structure,w=None,s_ins=None,s_out=None,s=None,Width=None,maxWidth=None,**kwargs):
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s is not None:
        #s overridden somewhere above
        if s_ins is None:
            s_ins = s
        if s_out is None:
            s_out = s
    if s_ins is None:
        try:
            s_ins = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if s_out is None:
        if Width is not None:
            s_out = Width - w - s_ins/2
        else:
            try:
                s_out = struct().defaults['s']
            except KeyError:
                print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
                
    s0 = struct().clone()
    maxWidth = wiggle_calc(chip,struct(),Width=Width,maxWidth=maxWidth,w=s_ins+2*w,s=0,**kwargs)['maxWidth']
    Inductor_wiggles(chip, s0, w=s_ins+2*w,Width=Width,maxWidth=maxWidth,**kwargs)
    Strip_wiggles(chip, struct(), w=s_ins,maxWidth=maxWidth-w,**kwargs)

def CPW_pincer(chip,structure,pincer_w,pincer_l,pincer_padw,pincer_tee_r=0,pad_r=None,w=None,s=None,pincer_flipped=False,bgcolor=None, polygon_overlap=True, **kwargs):
    '''
    pincer_w :      
    pincer_l :      length of pincer arms
    pincer_padw :   pincer pad trace width
    pincer_tee_r :  radius of tee
    pad_r:          inside radius of pincer bends
    w:              original trace width
    s:              pincer trace gap
    pincer_flipped: equivalent to hflip
    '''
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            w=0
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
    if pad_r is None:
        pincer_r = pincer_padw/2 + s
        pad_r=0
    else:
        pincer_r = pincer_padw/2+s+abs(pad_r)#prevent negative entries
        pad_r = abs(pad_r)
        
    if not pincer_flipped: s_start = struct().clone()
    else:
        struct().shiftPos(pincer_padw+pincer_tee_r+2*s,angle=180)
        s_start = struct().clone()


    s_left, s_right = CPW_tee(chip, struct(), w=w, s=s, w1=pincer_padw, s1=s, radius=pincer_tee_r + s, polygon_overlap=polygon_overlap, **kwargs)

    CPW_straight(chip, s_left, length=(pincer_w-w-2*s-2*pincer_tee_r)/2-pad_r, **kwargs)
    CPW_straight(chip, s_right, length=(pincer_w-w-2*s-2*pincer_tee_r)/2-pad_r, **kwargs)

    if pincer_l > s:
        CPW_bend(chip, s_left, CCW=True, w=pincer_padw, s=s, radius=pincer_r, **kwargs)
        CPW_straight(chip, s_left, length=pincer_l - s-pad_r, **kwargs)
        CPW_stub_open(chip, s_left, w=pincer_padw, s=s, polygon_overlap=polygon_overlap, **kwargs)

        CPW_bend(chip, s_right, CCW=False, w=pincer_padw, s=s, radius=pincer_r, **kwargs)
        CPW_straight(chip, s_right, length=pincer_l - s-pad_r, **kwargs)
        CPW_stub_open(chip, s_right, w=pincer_padw, s=s, polygon_overlap=polygon_overlap, **kwargs)
    else:
        s_left = s_left.cloneAlong(vector=(0,pincer_padw/2+s/2))
        Strip_bend(chip, s_left, CCW=True, w=s, radius=pincer_r + pincer_padw/2 - s/2, **kwargs)
        s_left = s_left.cloneAlong(vector=(s/2,s/2), newDirection=-90)
        Strip_straight(chip, s_left, length=pad_r + pincer_padw/2, w=s)

        s_right = s_right.cloneAlong(vector=(0,-pincer_padw/2-s/2))
        Strip_bend(chip, s_right, CCW=False, w=s, radius=pincer_r + pincer_padw/2 - s/2, **kwargs)
        s_right = s_right.cloneAlong(vector=(s/2,-s/2), newDirection=90)
        Strip_straight(chip, s_right, length=pad_r + pincer_padw/2, w=s)



    if not pincer_flipped:
        s_start.shiftPos(pincer_padw+pincer_tee_r+2*s)
        struct().updatePos(s_start.getPos())
    else: 
        struct().updatePos(s_start.getPos(),angle=180)
        #struct.direction = s_start.direction + 180
        
def CPW_tee_stub(chip,structure,stub_length,stub_w,tee_r=0,outer_width=None,w=None,s=None,pincer_flipped=False,bgcolor=None,**kwargs):
    '''
    stub_length :    end-to-end length of stub pin (not counting gap) 
    stub_w :   pincer pad trace width
    pincer_tee_r :  radius of tee
    pad_r:          inside radius of pincer bends
    w:              original trace width
    s:              pincer trace gap
    pincer_flipped: equivalent to hflip
    '''
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            w=0
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID,'!\x1b[0m')
        
    if not pincer_flipped: s_start = struct().clone()
    else:
        struct().shiftPos(stub_w+2*s,angle=180)
        #struct().direction += 180
        s_start = struct().clone()

    s_left, s_right = CPW_tee(chip, struct(), w=w, s=s, w1=stub_w, s1=s, radius=tee_r + s, **kwargs)

    CPW_straight(chip, s_left, length=(stub_length-w-2*s-stub_w)/2, **kwargs)
    CPW_stub_round(chip, s_left,**kwargs)
    CPW_straight(chip, s_right, length=(stub_length-w-2*s-stub_w)/2, **kwargs)
    CPW_stub_round(chip, s_right,**kwargs)

    if not pincer_flipped:
        s_start.shiftPos(stub_w+2*s)
        struct().updatePos(s_start.getPos())
    else: 
        struct().updatePos(s_start.getPos(),angle=180)
        #struct.direction = s_start.direction + 180
    
# ===============================================================================
# Airbridges (Lincoln Labs designs)
# ===============================================================================
def setupAirbridgeLayers(wafer:m.Wafer,BRLAYER='BRIDGE',RRLAYER='TETHER',brcolor=41,rrcolor=32):
    #add correct layers to wafer, and cache layer
    wafer.addLayer(BRLAYER,brcolor)
    wafer.BRLAYER=BRLAYER
    wafer.addLayer(RRLAYER,rrcolor)
    wafer.RRLAYER=RRLAYER

def Airbridge(
    chip, structure, cpw_w=None, cpw_s=None, xvr_width=None, xvr_length=None, rr_width=None, rr_length=None,
    rr_br_gap=None, rr_cpw_gap=None, shape_overlap=0, br_radius=0, clockwise=False, lincolnLabs=False, BRLAYER=None, RRLAYER=None, **kwargs):
    """
    Define either cpw_w and cpw_s (refers to the cpw that the airbridge goes across) or xvr_length.
    xvr_length overrides cpw_w and cpw_s.
    """
    assert lincolnLabs, 'Not implemented for normal usage'
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if cpw_w is None:
        try:
            cpw_w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if cpw_s is None:
        try:
            cpw_s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)

    #get layers from wafer
    if BRLAYER is None:
        try:
            BRLAYER = chip.wafer.BRLAYER
        except AttributeError:
            setupAirbridgeLayers(chip.wafer)
            BRLAYER = chip.wafer.BRLAYER
    if RRLAYER is None:
        try:
            RRLAYER = chip.wafer.RRLAYER
        except AttributeError:
            setupAirbridgeLayers(chip.wafer)
            RRLAYER = chip.wafer.RRLAYER

    if lincolnLabs:
        rr_br_gap = 1.5 # RR.BR.E.1
        if rr_cpw_gap is None: rr_cpw_gap = 2 # LL requires >= 0 (RR.E.1)
        else: assert rr_cpw_gap + rr_br_gap >= 1.5 # RR.E.1

        if xvr_length is None:
            xvr_length = cpw_w + 2*cpw_s + 2*(rr_cpw_gap)

        if 5 <= xvr_length <= 16: # BR.W.1, RR.L.1
            xvr_width = 5
            rr_length = 8
        elif 16 < xvr_length <= 27: # BR.W.2, RR.L.2
            xvr_width = 7.5
            rr_length = 10
        elif 27 < xvr_length <= 32: # BR.W.3, RR.L.3
            xvr_width = 10
            rr_length = 14
        rr_width = xvr_width + 3 # RR.W.1
        shape_overlap = 0.1 # LL requires >= 0.1
        delta = 0
        if br_radius > 0:
            r = br_radius - cpw_w/2 - cpw_s
            delta = r*(1-math.sqrt(1-1/r**2*((rr_width + 2*rr_br_gap)/2)**2))
        # this code does not check if your bend is super severe and the necessary delta
        # changes the necessary xvr_widths and rr_lengths, so don't do anything extreme

    if clockwise:
        delta_left = 0
        delta_right = delta
    else:
        delta_right = 0
        delta_left = delta

    chip.add(DogBone(struct().start,
                     xvr_width,
                     xvr_length,
                     rr_width,
                     rr_length,
                     rr_br_gap,
                     delta_left,
                     delta_right,
                     rotation=struct().direction, layer=BRLAYER, **kwargs),
             structure=struct().clone())

    s_left = struct().cloneAlong(vector=(0, xvr_length/2+delta_left+rr_br_gap))
    s_left.direction += 90
    Strip_straight(chip, s_left, length=rr_length, w=rr_width, layer=RRLAYER, **kwargs)

    s_right = struct().cloneAlong(vector=(0, -(xvr_length/2+delta_left+rr_br_gap)))
    s_right.direction -= 90
    Strip_straight(chip, s_right, length=rr_length, w=rr_width, layer=RRLAYER, **kwargs)

    s_l = s_left.cloneAlong(vector=(rr_br_gap,0))
    s_r = s_right.cloneAlong(vector=(rr_br_gap,0))

    return s_l, s_r


def CPW_bridge(chip, structure, xvr_length=None, w=None, s=None, lincolnLabs=False, BRLAYER=None, RRLAYER=None, **kwargs):
    """
    Draws an airbridge to bridge two sections of CPW, as well as the necessary connections.
    w, s are for the CPW we want to connect.
    structure is oriented at the same place as the structure for Airbridge.
    """
    assert lincolnLabs, 'Not implemented for normal usage'
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
        else:
            return chip.structure(structure)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)

    if lincolnLabs:
        rr_br_gap = 1.5 # RR.BR.E.1
        rr_cpw_gap = 0 # LL requires >= 0 (RR.E.1)
        if xvr_length is None:
            xvr_length = w + 2*s + 2*(rr_cpw_gap)
        if 5 <= xvr_length <= 16:
            xvr_width = 5
            rr_length = 8
        elif 16 < xvr_length <= 27:
            xvr_width = 7.5
            rr_length = 10
        elif 27 < xvr_length <= 32:
            xvr_width = 10
            rr_length = 14
        else:
            assert False, f'xvr_length {xvr_length} is out of range'
        rr_width = xvr_width + 3

    s_left, s_right = Airbridge(chip, struct(), xvr_length=xvr_length, lincolnLabs=lincolnLabs, **kwargs)

    w0 = rr_width+2*rr_br_gap
    s0 = s/w * w0

    s_left.shiftPos(-rr_length - 2*rr_br_gap - rr_cpw_gap)
    CPW_straight(chip, s_left, length=rr_length + 2*rr_br_gap + rr_cpw_gap, w=rr_width + 2*rr_br_gap, s=s0, **kwargs)
    CPW_taper(chip, s_left, length=rr_length + 2*rr_br_gap, w0=w0, s0=s0, w1=w, s1=s, **kwargs)

    s_right.shiftPos(-rr_length - 2*rr_br_gap - rr_cpw_gap)
    CPW_straight(chip, s_right, length=rr_length + 2*rr_br_gap + rr_cpw_gap, w=rr_width + 2*rr_br_gap, s=s0, **kwargs)
    CPW_taper(chip, s_right, length=rr_length + 2*rr_br_gap, w0=w0, s0=s0, w1=w, s1=s, **kwargs)

    return s_left, s_right



def Capa_linker(chip, pos, length, width, dist_ground_height, 
                dist_ground_width, dist_ground_strip, width_pad,
                 height_pad, radius,rotation, w=None, s=None,
                 bondwires=False,bond_pitch=70,incl_end_bond=True,
                 bgcolor=None, XLAYER=None, MLAYER=None, **kwargs):

    thisStructure = None
    if isinstance(pos,tuple):
        thisStructure = m.Structure(chip,start=pos,direction=rotation)
        
    def struct():
        if isinstance(pos,m.Structure):
            return pos
        elif isinstance(pos,tuple):
            return thisStructure
        else:
            return chip.structure(pos)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)



    #get layers from wafer
    if XLAYER is None:
        try:
            XLAYER = chip.wafer.XLAYER
        except AttributeError:
            chip.wafer.setupXORlayer()
            XLAYER = chip.wafer.XLAYER



    if len(width_pad)==1:
        width_pad = [width_pad[0]]*2
    if len(height_pad)==1:
        height_pad = [height_pad[0]]*2
    if len(dist_ground_width)==1:
        dist_ground_width = [dist_ground_width[0]]*2
    if len(dist_ground_height)==1:
        dist_ground_height = [dist_ground_height[0]]*2

    dl = 10e-3


    def Linker(chip, pos, length, width, width_pad, height_pad, radius,rotation, **kwargs):

        # adujst the length of the linker to account for the width of the pads

        length = length - width_pad[0] - width_pad[1]
        sin = np.sin(np.pi/180*rotation)
        cos = np.cos(np.pi/180*rotation)

        # draw the first pad as a rounded rectangle

        start_point = (pos[0] + sin*height_pad[0]/2, pos[1]- cos*height_pad[0]/2)

        
        
        
        pad1 = RoundRect(start_point, height=height_pad[0], radius=radius,width=width_pad[0], roundCorners=[1,1,1,1],
                                            rotation= rotation,**kwargs)
        chip.add(pad1)


        # draw the linker as a rectangle

        start_point = (pos[0] + sin*width/2 + (width_pad[0]-dl)*cos, pos[1]- cos*width/2 + (width_pad[0] - dl)*sin)


        linker = RoundRect(start_point, height=width, width=length, radius=0, rotation= rotation,
                            roundCorners=[0,0,0,0], **kwargs)
        
        chip.add(linker)

        # draw the second pad as a rounded rectangle

        start_point = (start_point[0] + (length-2*dl)*cos + sin*(height_pad[1]/2 - width/2) , start_point[1] + (length-2*dl)*sin - cos*(height_pad[1]/2 - width/2))

        pad2 = RoundRect(start_point, height=height_pad[1], radius=radius,width=width_pad[1], roundCorners=[1,1,1,1],
                                            rotation= rotation, **kwargs)
        
        chip.add(pad2)

    #add the linker to the structure

    start = pos

    Linker(chip, start, length, width, width_pad, height_pad, radius,rotation,layer=MLAYER,bgcolor=chip.bg(MLAYER))

    #add the ground plane to the structure
    # correct the pad size to account for ground plane distance 

    width_pad = [width_pad[0] + 2*dist_ground_width[0], width_pad[1] + 2*dist_ground_width[1]]
    height_pad = [height_pad[0] + 2*dist_ground_height[0], height_pad[1] + 2*dist_ground_height[1]]

    length_ground = length + dist_ground_width[0] + dist_ground_width[1]
    width_ground = width + 2*dist_ground_strip


    sin = np.sin(np.pi/180*rotation)
    cos = np.cos(np.pi/180*rotation)
    

    start_ground = (start[0] - cos*(dist_ground_width[0] -dl),start[1] - sin*(dist_ground_width[0] - dl))
    Linker(chip, start_ground, length_ground, width_ground, width_pad, height_pad, radius,rotation)

    if bondwires: # bond parameters patched through kwargs
        num_bonds = int(length/bond_pitch)
        this_struct = struct().clone()
        this_struct.shiftPos(bond_pitch)
        if not incl_end_bond: num_bonds -= 1
        for i in range(num_bonds):
            Airbridge(chip, this_struct, **kwargs)
            this_struct.shiftPos(bond_pitch)


def Capa_linker_tee(chip, pos, length, width, dist_ground_height, 
                dist_ground_width, dist_ground_strip, width_pad,
                 height_pad, radius,rotation,width_tee=[0], height_tee=[0], w=None, s=None,
                 bondwires=False,bond_pitch=70,incl_end_bond=True,
                 bgcolor=None, XLAYER=None, MLAYER=None, **kwargs):

    thisStructure = None
    if isinstance(pos,tuple):
        thisStructure = m.Structure(chip,start=pos,direction=rotation)
        
    def struct():
        if isinstance(pos,m.Structure):
            return pos
        elif isinstance(pos,tuple):
            return thisStructure
        else:
            return chip.structure(pos)
    if w is None:
        try:
            w = struct().defaults['w']
        except KeyError:
            print('\x1b[33mw not defined in ',chip.chipID)
    if s is None:
        try:
            s = struct().defaults['s']
        except KeyError:
            print('\x1b[33ms not defined in ',chip.chipID)



    #get layers from wafer
    if XLAYER is None:
        try:
            XLAYER = chip.wafer.XLAYER
        except AttributeError:
            chip.wafer.setupXORlayer()
            XLAYER = chip.wafer.XLAYER



    if len(width_pad)==1:
        width_pad = [width_pad[0]]*2
    if len(height_pad)==1:
        height_pad = [height_pad[0]]*2
    if len(dist_ground_width)==1:
        dist_ground_width = [dist_ground_width[0]]*2
    if len(dist_ground_height)==1:
        dist_ground_height = [dist_ground_height[0]]*2
    if len(width_tee)==1:
        width_tee = [width_tee[0]]*2
    if len(height_tee)==1:
        height_tee = [height_tee[0]]*2

    dl = 10e-3


    def Linker_tee(chip, pos, length, width, width_pad, height_pad, width_tee, height_tee, radius,rotation, **kwargs):

        # adujst the length of the linker to account for the width of the pads

        length = length - width_pad[0] - width_pad[1]
        sin = np.sin(np.pi/180*rotation)
        cos = np.cos(np.pi/180*rotation)

        # draw the first pad as a rounded rectangle

        start_point = (pos[0] + sin*height_pad[0]/2, pos[1]- cos*height_pad[0]/2)

        
        
        if width_tee[0] != 0:

            pad1 = RoundRect(start_point, height=height_pad[0], radius=radius,width=width_pad[0], roundCorners=[0,1,1,0],
                                                rotation= rotation,**kwargs)
            chip.add(pad1)

        else:

            pad1 = RoundRect(start_point, height=height_pad[0], radius=radius,width=width_pad[0], roundCorners=[1,1,1,1],
                                                rotation= rotation,**kwargs)
            chip.add(pad1)


        if width_tee[0] != 0:

            start_point = (pos[0] + sin*(height_pad[0]/2) - cos*(width_tee[0]), pos[1]- cos*(height_pad[0]/2) - sin*width_tee[0])

            tee1_up = RoundRect(start_point, height=height_tee[0], radius=radius,width=width_tee[0], roundCorners=[1,0,0,1],
                                                rotation= rotation,**kwargs)
            
            chip.add(tee1_up)

            # start_point = (pos[0] - sin*(height_pad[0]/2) - cos*(width_tee[0]), pos[1]+ cos*(height_pad[0]/2) + sin*width_tee[0]) 
            # start_point = (pos[0] - cos*(width_tee[0]), pos[1] + sin*width_tee[0]) 
            # start_point = (pos[0] -sin*(height_pad[0]/2 - height_tee[0]/2), pos[1] - cos*(height_pad[0]/2 - height_tee[0]/2))
            start_point = (pos[0] -sin*(height_pad[0]/2-height_tee[0]) -cos*width_tee[0], pos[1] + cos*(height_pad[0]/2-height_tee[0])-sin*width_tee[0])

            tee1_down = RoundRect(start_point, height=height_tee[0], radius=radius,width=width_tee[0], roundCorners=[1,0,0,1],
                                                rotation= rotation,**kwargs)
            
            chip.add(tee1_down)


        # draw the linker as a rectangle

        start_point = (pos[0] + sin*width/2 + (width_pad[0]-dl)*cos, pos[1]- cos*width/2 + (width_pad[0] - dl)*sin)


        linker = RoundRect(start_point, height=width, width=length, radius=0, rotation= rotation,
                            roundCorners=[0,0,0,0], **kwargs)
        
        chip.add(linker)

        # draw the second pad as a rounded rectangle

        start_point = (start_point[0] + (length-2*dl)*cos + sin*(height_pad[1]/2 - width/2) , start_point[1] + (length-2*dl)*sin - cos*(height_pad[1]/2 - width/2))

        if width_tee[1] != 0:

            pad2 = RoundRect(start_point, height=height_pad[1], radius=radius,width=width_pad[1], roundCorners=[1,0,0,1],
                                                rotation= rotation, **kwargs)
            
            chip.add(pad2)

        else:

            pad2 = RoundRect(start_point, height=height_pad[1], radius=radius,width=width_pad[1], roundCorners=[1,1,1,1],
                                                rotation= rotation, **kwargs)
            
            chip.add(pad2)

        # add the tee to the second pad

        if width_tee[1] != 0:

            start_point = (start_point[0] + cos*width_pad[1], start_point[1]+ sin*width_pad[1])

            tee2_up = RoundRect(start_point, height=height_tee[1], radius=radius,width=width_tee[1], roundCorners=[0,1,1,0],
                                                rotation= rotation,**kwargs)
            
            chip.add(tee2_up)

            start_point = (start_point[0] - sin*(height_pad[1] - height_tee[1]), start_point[1] + cos*(height_pad[1] - height_tee[1]))

            tee2_down = RoundRect(start_point, height=height_tee[1], radius=radius,width=width_tee[1], roundCorners=[0,1,1,0],
                                                rotation= rotation,**kwargs)
            
            chip.add(tee2_down)

            

    #add the linker to the structure

    start = pos

    Linker_tee(chip, start, length, width, width_pad, height_pad, width_tee, height_tee,radius,rotation,layer=MLAYER,bgcolor=chip.bg(MLAYER))

    #add the ground plane to the structure
    # correct the pad size to account for ground plane distance 

    width_pad = [width_pad[0] + 2*dist_ground_width[0], width_pad[1] + 2*dist_ground_width[1]]
    height_pad = [height_pad[0] + 2*dist_ground_height[0], height_pad[1] + 2*dist_ground_height[1]]

    length_ground = length + dist_ground_width[0] + dist_ground_width[1]
    width_ground = width + 2*dist_ground_strip

    # width_tee = [width_tee[0] + 2*dist_ground_width[0], width_tee[1] + 2*dist_ground_width[1]]
    height_tee = [height_tee[0] + 2*dist_ground_height[0], height_tee[1] + 2*dist_ground_height[1]]


    sin = np.sin(np.pi/180*rotation)
    cos = np.cos(np.pi/180*rotation)
    

    start_ground = (start[0] - cos*(dist_ground_width[0] -dl),start[1] - sin*(dist_ground_width[0] - dl))
    Linker_tee(chip, start_ground, length_ground, width_ground, width_pad, height_pad, width_tee, height_tee,radius,rotation)

    if bondwires: # bond parameters patched through kwargs
        num_bonds = int(length/bond_pitch)
        this_struct = struct().clone()
        this_struct.shiftPos(bond_pitch)
        if not incl_end_bond: num_bonds -= 1
        for i in range(num_bonds):
            Airbridge(chip, this_struct, **kwargs)
            this_struct.shiftPos(bond_pitch)

