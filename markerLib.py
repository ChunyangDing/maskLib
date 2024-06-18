#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:38:27 2021

@author: sasha
"""
from dxfwrite import DXFEngine as dxf
from dxfwrite import const
from dxfwrite.vector2d import vadd

import maskLib.MaskLib as m
from maskLib.utilities import kwargStrip
from maskLib.Entities import SolidPline

# ===============================================================================
#  MARKER FUNCTIONS
# ===============================================================================

#Define High Visiblity Marker Function for numbers 0-9
#High visibility markers composed of a grid of six squares
def HiVisMarker09(dwg,xpos,ypos,number,width,bg=None,**kwargs):
    shapes = [[],  [[0,0]],  [[0,0],[1,1]],    [[0,0],[1,1],[0,1]],  [[0,0],[0,1],[2,0],[2,1]],
             [[0,1],[1,0],[2,1]],  [[0,0],[1,0],[2,0],[1,1]],   [[0,0],[0,1],[1,0],[1,1],[2,1]], [[0,0],[0,1],[1,0],[1,1]],
             [[0,0],[1,0],[1,1],[2,1]]]
    number = number % len(shapes)
    for v in shapes[number]:
        dwg.add(dxf.rectangle((xpos+v[0]*width,ypos+v[1]*width),width,width,bgcolor=bg,**kwargs))
        
def MarkerRect(w,pos,width,height,bgcolor=None,layer=None,chipCentered=False,**kwargs):
    if layer is None:
        layer = w.defaultLayer
    else:
        layer = w.lyr(layer)
    if bgcolor is None:
        bgcolor = w.bg(layer)
    if chipCentered:
        try:
            pos = w.centered(pos)
        except:
            print('does not have centered argument')
    w.add(dxf.rectangle(pos,width,height,valign=const.MIDDLE,halign=const.CENTER,bgcolor=bgcolor,layer=layer,**kwargStrip(kwargs)))
    
def MarkerSquare(w,pos,width=80,bgcolor=None,layer=None,**kwargs):
    MarkerRect(w,pos,width,width,bgcolor=bgcolor,layer=layer,**kwargs)

def MarkerCross(w,pos,size=(200,200),linewidth=80,bgcolor=None,layer=None,chipCentered=False,**kwargs):
    if layer is None:
        layer = w.defaultLayer
    else:
        layer = w.lyr(layer)
    if bgcolor is None:
        bgcolor = w.bg(layer)
    if chipCentered:
        try:
            pos = w.centered(pos)
        except:
            print('does not have centered argument')
    w.add(dxf.rectangle(pos,size[0],linewidth,valign=const.MIDDLE,halign=const.CENTER,bgcolor=bgcolor,layer=layer,**kwargStrip(kwargs)))
    w.add(dxf.rectangle(vadd(pos,(0,linewidth/2)),linewidth,size[1]/2-linewidth/2,valign=const.TOP,halign=const.CENTER,bgcolor=bgcolor,layer=layer,**kwargStrip(kwargs)))
    w.add(dxf.rectangle(vadd(pos,(0,-linewidth/2)),linewidth,size[1]/2-linewidth/2,valign=const.BOTTOM,halign=const.CENTER,bgcolor=bgcolor,layer=layer,**kwargStrip(kwargs)))

# ===============================================================================
# DRAW TEXT SHAPES
# (adapted from slab maskmaker)  
# ===============================================================================
alphanum_dict = {
'a': [[(0,0), (0,16), (12,16), (12,0), (8,0), (8,14), (4,14), (4,0), (0,0)], [(4,8), (4,10), (8,10), (8,8), (4,8)]],
'b': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,0), (8,0), (12,2), (12,6), (8,8), (12,10), (12,14), (8,16), (4,16), (4,14), (8,14), (8,10), (4,10), (4,6), (8,6), (8,2), (4,2), (4,0)]],
'c': [[(0,0), (0,16), (12,16), (12,14), (4,14), (4,2), (12,2), (12,0), (0,0), (0,0)]],
'd': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,0), (8,0), (12,2), (12,14), (8,16), (4,16), (4,14), (8,14), (8,2), (4,2), (4,0)]],
'e': [[(0,0), (0,16), (12,16), (12,14), (4,14), (4,10), (8,10), (8,8), (4,8), (4,2), (12,2), (12,0), (0,0), (0,0)]],
'f': [[(0,0), (0,16), (12,16), (12,14), (4,14), (4,10), (8,10), (8,8), (4,8), (4,0), (0,0), (0,0)]],
'g': [[(0,0), (12,0), (12,8), (6,8), (6,6), (8,6), (8,2), (4,2), (4,14), (12,14), (12,16), (0,16), (0,0), (0,0)]],
'h': [[(0,0), (4,0), (4,8), (8,8), (8,0), (12,0), (12,16), (8,16), (8,10), (4,10), (4,16), (0,16), (0,0), (0,0)]],
'i': [[(0,0), (12,0), (12,2), (8,2), (8,14), (12,14), (12,16), (0,16), (0,14), (4,14), (4,2), (0,2), (0,0), (0,0)]],
'j': [[(0,0), (12,0), (12,16), (8,16), (8,2), (4,2), (4,6), (0,6), (0,0), (0,0)]],
'k': [[(0,0), (4,0), (4,6), (8,0), (12,0), (6,8), (12,16), (8,16), (4,10), (4,16), (0,16), (0,0), (0,0)]],
'l': [[(0,0), (0,16), (4,16), (4,2), (12,2), (12,0), (0,0), (0,0)]],
'm': [[(0,0), (4,0), (4,8), (6,2), (8,8), (8,0), (12,0), (12,16), (8,16), (6,10), (4,16), (0,16), (0,0), (0,0)]],
'n': [[(0,0), (4,0), (4,10), (8,0), (12,0), (12,16), (8,16), (8,4), (4,16), (0,16), (0,0), (0,0)]],
'o': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,0), (12,0), (12,16), (4,16), (4,14), (8,14), (8,2), (4,2), (4,0)]],
'p': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,8), (12,8), (12,16), (4,16), (4,14), (8,14), (8,10), (4,10), (4,8)]],
'q': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,2), (6,2), (6,4), (8,4), (8,14), (4,14), (4,16), (12,16), (12,-1), (8,-1), (8,0), (4,0), (4,2)]],
'r': [[(0.,0.), (4.,0.), (4.,16.), (0.,16.), (0.,0.)], [(4.,8.), (8.,0.), (12.,0.), (8.,8.), (12.,8.), (12.,16.), (4.,16.), (4.,14.), (8.,14.), (8.,10.), (4.,10.), (4.,8.)]],
's': [[(0,0), (12,0), (12,10), (4,10), (4,14), (12,14), (12,16), (0,16), (0,8), (8,8), (8,2), (0,2), (0,0), (0,0)]],
't': [[(4,0), (8,0), (8,14), (12,14), (12,16), (0,16), (0,14), (4,14), (4,0), (4,0)]],
'u': [[(0,0), (12,0), (12,16), (8,16), (8,2), (4,2), (4,16), (0,16), (0,0), (0,0)]],
'v': [[(4,0), (8,0), (12,16), (8,16), (6,6), (4,16), (0,16), (4,0), (4,0)]],
'w': [[(0,0), (4,0), (6,3), (8,0), (12,0), (12,16), (8,16), (8,4), (6,7), (4,4), (4,16), (0,16), (0,0), (0,0)]],
'x': [[(0,0), (4,0), (6,6), (8,0), (12,0), (8,8), (12,16), (8,16), (6,10), (4,16), (0,16), (4,8), (0,0), (0,0)]],
'y': [[(4,0), (8,0), (8,6), (12,16), (8,16), (6,8), (4,16), (0,16), (4,6), (4,0), (4,0)]],
'z': [[(0,0), (12,0), (12,2), (4,2), (12,14), (12,16), (0,16), (0,14), (8,14), (0,2), (0,0), (0,0)]],
# '0': [[(0,2), (4,0), (4,16), (0,14), (0,2)], [(4,0), (8,0), (12,2), (12,14), (8,16), (4,16), (4,14), (8,14), (8,2), (4,2), (4,0)], [(4,2), (6,2), (8,13), (8,14), (6,14), (4,3), (4,2)]],
'0': [[(0,2), (4,0), (4,16), (0,14), (0,2)], [(4,0), (8,0), (12,2), (12,14), (8,16), (4,16), (4,14), (8,14), (8,2), (4,2), (4,0)], [(4,3), (6,2), (8,13), (6,14), (4,3)]],
'1': [[(0,0), (12,0), (12,2), (8,2), (8,16), (4,16), (0,14), (0,12), (4,12), (4,2), (0,2), (0,0), (0,0)]],
'2': [[(0,0), (12,0), (12,2), (4,2), (4,4), (12,12), (12,16), (0,16), (0,14), (8,14), (8,12), (0,4), (0,0), (0,0)]],
'3': [[(0,0), (12,0), (12,16), (0,16), (0,14), (8,14), (8,9), (4,9), (4,7), (8,7), (8,2), (0,2), (0,0), (0,0)]],
'4': [[(8,0), (12,0), (12,16), (8,16), (8,10), (4,10), (4,16), (0,16), (0,8), (8,8), (8,0), (8,0)]],
'5': [[(0,0), (12,0), (12,10), (4,10), (4,14), (12,14), (12,16), (0,16), (0,8), (8,8), (8,2), (0,2), (0,0), (0,0)]],
'6': [[(0,0), (4,0), (4,16), (0,16), (0,0)], [(4,0), (12,0), (12,8), (4,8), (4,6), (8,6), (8,2), (4,2), (4,0)]],
'7': [[(8,0), (12,0), (12,16), (0,16), (0,14), (8,14), (8,0), (8,0)]],
'8': [[(0,0), (4,0), (4,16), (0,16), (0,10), (4,8), (0,6), (0,0)], [(4,0), (12,0), (12,6), (8,8), (12,10), (12,16), (4,16), (4,14), (8,14), (8,10), (4,10), (4,6), (8,6), (8,2), (4,2), (4,0)]],
'9': [[(8,0), (12,0), (12,16), (8,16), (8,0)], [(8,16), (0,16), (0,8), (8,8), (8,10), (4,10), (4,14), (8,14), (8,16)]],
'+': [[(0,6),(4,6),(4,2),(8,2),(8,6),(12,6),(12,10),(8,10),(8,14),(4,14),(4,10),(0,10),(0,6)]],
'.': [[(4,0),(8,0),(8,4),(4,4)]]
}

def AlphaNumStr(chip, structure, string, size, centered=False, bgcolor=None, **kwargs):
    """
    Draws block letters with size (x, y).
    """
    def struct():
        if isinstance(structure,m.Structure):
            return structure
        elif isinstance(structure,tuple):
            return m.Structure(chip,structure)
            #BUG - below struct().shiftPos is used so using pos instead doesn't work
        else:
            return chip.structure(structure)
    if bgcolor is None:
        bgcolor = chip.wafer.bg()

    if centered: struct().shiftPos(-size[0]*len(string)/2)
    for letter in string:
        letter = letter.lower()
        assert letter in alphanum_dict.keys()
        scaled_size = (size[0] / 16., size[1] / 16.)
        for pts in alphanum_dict[letter]:
            scaled_pts = [(p[0]*scaled_size[0], p[1]*scaled_size[1]) for p in pts]
            chip.add(SolidPline(insert=struct().getPos(), rotation=struct().direction, points=scaled_pts, **kwargs))
        struct().shiftPos(size[0])