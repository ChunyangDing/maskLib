# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 12:35:23 2018

@author: sasha
"""
import math

from dxfwrite import const
#force all 2D polylines by disabling 3D polyline flags
const.POLYLINE_3D_POLYLINE=0

from dxfwrite import DXFEngine as dxf

from dxfwrite.vector2d import vadd,midpoint,vmul_scalar,vsub
from dxfwrite.algebra import rotate_2d



# ===============================================================================
#  LOOKUP DICTIONARIES FOR COMMON TERMS 
# ===============================================================================
waferDiameters = {'2in':50800,'3in':76200,'4in':101600,'6in':152400}
sawWidths = {'4A':101.6,'8A':203.2}

# ===============================================================================
#  MARKER FUNCTIONS (Deprecated- use functions from masklib.markerLib)
# ===============================================================================
#Define Marker Function for numbers 0-9
#High visibility markers composed of a grid of six squares
def HiVisMarker09(dwg,xpos,ypos,number,width,bg=None,**kwargs):
    #>>>>>>>> Deprecated, use markerLib.HiVisMarker09 instead <<<<<<<<<<
    shapes = [[],  [[0,0]],  [[0,0],[1,1]],    [[0,0],[1,1],[0,1]],  [[0,0],[0,1],[2,0],[2,1]],
             [[0,1],[1,0],[2,1]],  [[0,0],[1,0],[2,0],[1,1]],   [[0,0],[0,1],[1,0],[1,1],[2,1]], [[0,0],[0,1],[1,0],[1,1]],
             [[0,0],[1,0],[1,1],[2,1]]]
    number = number % len(shapes)
    for v in shapes[number]:
        dwg.add(dxf.rectangle((xpos+v[0]*width,ypos+v[1]*width),width,width,bgcolor=bg,**kwargs))
   
# ===============================================================================
#  UTILITY FUNCTIONS  (Deprecated - use functions from masklib.utilities)
# ===============================================================================
def curveAB(a,b,clockwise,angleDeg,ptDensity):
    #>>>>>>>> Deprecated, use utilities.curveAB instead <<<<<<<<<<
    
    #generate a segmented curve from A to B specified by angle. Point density = #pts / revolution
    #return list of points
    angle = math.radians(angleDeg)
    segments = int(angle/(2*math.pi) *ptDensity)
    center = vadd(midpoint(a,b),vmul_scalar(rotate_2d(vsub(b,a),-clockwise*math.pi/2),0.5/math.tan(angle/2)))
    points = []
    for i in range(segments+1):
        points.append(vadd(center,rotate_2d(vsub(a,center),-clockwise*i*angle/segments)))
    return points

def corner(vertex,quadrant,clockwise,L,ptDensity):
    #>>>>>>>> Deprecated, use utilities.cornerRound instead <<<<<<<<<<
    
    #quadrant corresponds to quadrants 1-4
    #generate a curve to replace the vertex
    ptA = vadd(vertex,rotate_2d((0,L),quadrant * math.pi/2))
    ptB = vadd(vertex,rotate_2d((0,L),(quadrant+1) * math.pi/2))

    return clockwise>0 and curveAB(ptA,ptB,1,90,ptDensity) or curveAB(ptB,ptA,-1,90,ptDensity)

def transformedQuadrants(UD=1,LR=1):
    #>>>>>>>> Deprecated, use utilities.transformedQuadrants instead <<<<<<<<<<
    
    #return quadrant list with up/down left/right flips applied
    return UD==1 and (LR==1 and [0,1,2,3,4] or [0,2,1,4,3]) or (LR==1 and [0,4,3,2,1] or [0,3,4,1,2])

def skewRect(corner,width,height,offset,newLength,edge=1,**kwargs):
    #>>>>>>>> Deprecated, use Entities.SkewRect instead <<<<<<<<<<
    
    #quadrangle drawn counterclockwise starting from bottom left
    #edges are indexed 0-3 correspondingly
    #edge 1 is default (east edge )
    pts =  [(corner[0],corner[1]),(corner[0]+width,corner[1]),
            (corner[0]+width,corner[1]+height),(corner[0],corner[1]+height)]
    direction = edge//2 > 0 and -1 or 1
    if(edge%2==0): #horizontal
        delta = 0.5*(newLength-width)*direction
        pts[edge] = (pts[edge][0]+offset[0]-delta,pts[edge][1]+offset[1])
        pts[(edge+1)%4] = (pts[(edge+1)%4][0]+offset[0]+delta,pts[(edge+1)%4][1]+offset[1])
    else: #vertical
        delta = 0.5*(newLength-height)*direction
        pts[edge] = (pts[edge][0]+offset[0],pts[edge][1]+offset[1]-delta)
        pts[(edge+1)%4] = (pts[(edge+1)%4][0]+offset[0],pts[(edge+1)%4][1]+offset[1]+delta)
        
    taper = dxf.polyline(points = pts,flags=0,**kwargs)
    taper.close()
    return taper

# ===============================================================================
#  WAFER CLASS  
#       master class designed to handle all layers, main dxf drawing and stores chips
# ===============================================================================
class Wafer:

    def __init__(self,name,path,chipWidth,chipHeight,waferDiameter=50800,padding=2500,sawWidth=203.2,frame=True,markers=True,solid=False,multiLayer=True,singleChipRow=False,singleChipColumn=False):
        # initialize drawing
        self.fileName = name
        self.path = path
        self.drawing = dxf.drawing(path + name + '.dxf')
        
        #get rid of extra layers (we still want '0', and 'VIEWPORTS')
        self.drawing.tables.layers.clear()
        self.drawing.add_layer('0')
        self.drawing.add_layer('VIEWPORTS',color=8)
        
        # set default wafer properties
        self.waferDiameter = waferDiameter
        self.padding = padding
        self.sawWidth = sawWidth
        self.chipX = chipWidth + sawWidth
        self.chipY = chipHeight + sawWidth
        self.frame = frame              #draw frame layer?
        self.markers = markers
        self.solid = solid              #draw things solid?
        self.multiLayer = multiLayer    #draw in multiple layers?
        self.singleChipRow = singleChipRow #draw only one row of chips? (horizontal row)
        self.singleChipColumn = singleChipColumn #draw only one column of chips? (vertical column)
        
        # initialize default layers
        self.layerNames = ['0']
        self.layerColors = {'0':7} #colors corresponding to layers
        self.layerNums = {'0':0} #colors corresponding to layers
        self.defaultLayer = '0' #default layer to draw chips on
        
        # initialize private variables
        self.chipPts = [] #chip offsets, measring from lower left corner
        self.chipColumns = [] #chip columns
        self.chips = [] #cached chip references
        self.defaultChip = None
        
        
    # for changing wafer properties later
    def setProperties(self,chipWidth,chipHeight,waferDiameter=50800,padding=2500,sawWidth=203.2,frame=True,markers=True,solid=False,multiLayer=True):
        # set the basic properties of the wafer
        self.waferDiameter = waferDiameter
        self.padding = padding
        self.sawWidth = sawWidth
        self.chipY = chipWidth + sawWidth
        self.chipX = chipHeight + sawWidth
        self.frame = frame              #draw frame layer?
        self.markers = markers
        self.solid = solid              #draw things solid?
        self.multiLayer = multiLayer    #draw in multiple layers?
    
    #copy properties from a parent wafer
    def copyPropertiesFrom(self,wafer):
        self.waferDiameter = wafer.waferDiameter
        self.padding = wafer.padding
        self.sawWidth = wafer.sawWidth
        self.chipY = wafer.chipY
        self.chipX = wafer.chipX
        self.frame = wafer.frame              #draw frame layer?
        self.markers = wafer.markers
        self.solid = wafer.solid              #draw things solid?
        self.multiLayer = wafer.multiLayer    #draw in multiple layers?
        
        self.layerColors = wafer.layerColors
        self.layerNums = wafer.layerNums
        self.layerNames = wafer.layerNames
        self.defaultLayer = wafer.defaultLayer 
        
        #ignore private vars
    
    def save(self):
        self.drawing.save()
        print('Saved as: '+ '\x1b[36m' + self.path + self.fileName + '.dxf'+'\x1b[0m')
    
    def lyr(self,layerName):
        return self.multiLayer and layerName or '0'
    
    def bg(self,layerName=None):
        # return the fill color
        if layerName is None:
            return self.solid and const.BYLAYER or None
        else:
            return self.solid and self.layerColors[self.lyr(layerName)] or None
    
    def addLayer(self,layerName,layerColor):
        if layerName not in self.layerNames:
            self.layerNames.append(layerName)
            self.layerColors[layerName]=layerColor
            self.layerNums[layerName]=len(self.layerNames)-1

    def addLayerAt(self, layerName, layerColor, layerNumber=-1):
        if layerName in self.layerNames: return
        numLayers = len(self.layerNames)
        if layerNumber == -1: layerNumber = numLayers
        if layerNumber < numLayers: return
        fillerLayers = [f'{layerNum}' for layerNum in range(numLayers, layerNumber)]
        for fillerLayerName in fillerLayers:
            self.addLayer(fillerLayerName, -1)
        self.addLayer(layerName, layerColor)
    
    def setDefaultChip(self,chip=None):
        # update default chip and chip list
        
        if chip is None: 
            if self.defaultChip is None:
                self.defaultChip = Chip(self,'BLANK',self.defaultLayer)
                self.defaultChip.save(self)
            else:
                print('Default chip already set in '+self.fileName)
        else:
            self.defaultChip = chip
            self.defaultChip.save(self)
        
        #populate wafer with default chips
        if len(self.chips)>0:
            for i in range(len(self.chips)):
                self.chips[i]=self.defaultChip
        else:
            for i in range(len(self.chipPts)):
                self.chips.append(self.defaultChip)
    
    def init(self, FRAME_LAYER=['FRAME',8,-1], MARKER_LAYER=['MARKERS',5,-1]):
        #self.frame and self.markers override presence/absence of FRAME_LAYER/MARKER_LAYER params
        #verify frame is off is multilayer is off
        self.frame = self.multiLayer and self.frame or 0
        #finish setup of DXF file
        if self.multiLayer:
            if self.frame:
                self.addLayerAt(*FRAME_LAYER)
            if self.markers:
                self.addLayerAt(*MARKER_LAYER)
        #add layers
        for layer in self.layerNames:
            self.drawing.add_layer(layer,color=self.layerColors[layer])
            
        #cache frame layer string
        fr = self.lyr(FRAME_LAYER[0])
        #draw wafer for debugging purposes
        if self.frame:
            self.drawing.add(dxf.circle(radius=self.waferDiameter/2,center=(0,0),layer=fr))
            self.drawing.add(dxf.circle(radius=self.waferDiameter/2-self.padding,center=(0,0),layer=fr))
        #determine number of chips, chip layout and coordinates
        nx=0
        ny=0
        if self.singleChipColumn:
            if self.singleChipRow:
                #only one chip on the wafer
                self.chipPts.append([-0.5*self.chipX,-0.5*self.chipY])
                self.chipColumns.append(1)
            else:
                #vertical column of chips, symmetric about X axis
                while((ny+1)*self.chipY)**2 + ((0.5)*self.chipX)**2 < (self.waferDiameter/2 - self.padding)**2:
                    self.chipPts.append([-0.5*self.chipX,ny*self.chipY])
                    self.chipPts.append([-0.5*self.chipX,(-ny-1)*self.chipY])
                    ny += 1
                self.chipColumns.append(2*ny)
                nx += 1
        elif self.singleChipRow:
            #horizontal row of chips, symmetric about Y axis
            while ((nx+1)*self.chipX)**2 + self.chipY**2 < (self.waferDiameter/2 - self.padding)**2:
                self.chipPts.append([nx*self.chipX,-0.5*self.chipY])
                self.chipPts.append([(-nx-1)*self.chipX,-0.5*self.chipY])
                self.chipColumns.append(1)
                nx += 1
        else:
            #grid of chips, symmetric about X and Y axis
            while ((nx+1)*self.chipX)**2 + self.chipY**2 < (self.waferDiameter/2 - self.padding)**2:
                ny=0
                while((ny+1)*self.chipY)**2 + ((nx+1)*self.chipX)**2 < (self.waferDiameter/2 - self.padding)**2:
                    self.chipPts.append([nx*self.chipX,ny*self.chipY])
                    self.chipPts.append([nx*self.chipX,(-ny-1)*self.chipY])
                    self.chipPts.append([(-nx-1)*self.chipX,ny*self.chipY])
                    self.chipPts.append([(-nx-1)*self.chipX,(-ny-1)*self.chipY])
                    ny += 1
                self.chipColumns.append(2*ny)
                nx += 1
        #sort chip indices left to right, then bottom to top
        self.chipPts.sort()
        print('Number of Chips: '+str(len(self.chipPts)))
        #reverse column counts to go from left to center
        self.chipColumns = self.chipColumns[::-1]
        
        self.setDefaultChip()
        
        #setup the viewport
        self.drawing.add_vport('*ACTIVE',ucs_icon=0,circle_zoom=1000,grid_on=1,center_point=(0,0),aspect_ratio=2*(self.waferDiameter))
    
    def initChipOnly(self,center=False, FRAME_LAYER=['FRAME',8,-1], MARKER_LAYER=['MARKERS',5,-1]):
        #self.frame and self.markers override presence/absence of FRAME_LAYER/MARKER_LAYER params
        #initialize drawing assuming we only want to draw a single chip
        #verify frame is off is multilayer is off
        self.frame = self.multiLayer and self.frame or 0
        #finish setup of DXF file
        if self.multiLayer:
            if self.frame:
                self.addLayerAt(*FRAME_LAYER)
            if self.markers:
                self.addLayerAt(*MARKER_LAYER)
        #add layers
        for layer in self.layerNames:
            self.drawing.add_layer(layer,color=self.layerColors[layer])
        if center:
            self.chipPts =[[-self.chipX/2,-self.chipY/2]]
        else:
            self.chipPts =[[0,0]]
            
        #setup the default chip
        self.setDefaultChip()

        #setup the viewport
        self.drawing.add_vport('*ACTIVE',ucs_icon=0,circle_zoom=1000,grid_on=1,center_point=(0,0),aspect_ratio=2*(max(self.chipX,self.chipY)))
    
    def SetupLayers(self,layers):
        #format: ['layername',color_int,layer_num (optional)]
        #first layer is default
        if self.multiLayer:
            for l in layers:
                if len(l) == 2: l.append(-1)
                self.addLayerAt(*l)
            self.defaultLayer=layers[0][0]
            
    
    #dicing saw border
    def DicingBorder(self,maxpts=0,minpts=0,thin=5,thick=20,short=40,long=100,dash=400,layer='MARKERS'):
        '''
        # maxpts:     where in chip list to stop putting a dicing border 
        # minpts:     where in chip list to start putting dicing border
        # thin:5      #thin section of crosshair
        # thick:20    #thick section of crosshair AND dash thickness
        # short:40    #short section of crosshair
        # long:100    #long section of crosshair
        # dash:400    #spacing between dashes
        '''
        if maxpts < 0:
            maxpts = len(self.chipPts)+maxpts
        
        #determine filling
        bg = self.bg(layer)
        offsetX = ((self.chipX-2*short-2*long)%(dash)+dash)/2
        offsetY = ((self.chipY-2*short-2*long)%(dash)+dash)/2
        border = dxf.block('DICINGBORDER')
        border.add(dxf.rectangle((0,0),short+thin,thin,bgcolor=bg))
        border.add(dxf.rectangle((short+thin,0),long,thick,bgcolor=bg))
        border.add(dxf.rectangle((0,thin),thin,short,bgcolor=bg))
        border.add(dxf.rectangle((0,thin+short),thick,long,bgcolor=bg))
        
        for x in range(int(short+long),int(self.chipX-short-long-dash),dash):
            border.add(dxf.rectangle((x+offsetX,0),thick,thick,bgcolor=bg))
        
        border.add(dxf.rectangle((self.chipX,0),-short-thin,thin,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX-short-thin,0),-long,thick,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX,thin),-thin,short,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX,thin+short),-thick,long,bgcolor=bg))
        
        for y in range(int(short+long),int(self.chipY-short-long-dash),dash):
            border.add(dxf.rectangle((0,y+offsetY),thick,thick,bgcolor=bg))
        
        border.add(dxf.rectangle((0,self.chipY),short+thin,-thin,bgcolor=bg))
        border.add(dxf.rectangle((short+thin,self.chipY),long,-thick,bgcolor=bg))
        border.add(dxf.rectangle((0,-thin+self.chipY),thin,-short,bgcolor=bg))
        border.add(dxf.rectangle((0,-thin-short+self.chipY),thick,-long,bgcolor=bg))
        
        for x in range(int(short+long),int(self.chipX-short-long-dash),dash):
            border.add(dxf.rectangle((x+offsetX-thick,self.chipY),thick,-thick,bgcolor=bg))
        
        border.add(dxf.rectangle((self.chipX,self.chipY),-short-thin,-thin,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX-short-thin,self.chipY),-long,-thick,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX,-thin+self.chipY),-thin,-short,bgcolor=bg))
        border.add(dxf.rectangle((self.chipX,-thin-short+self.chipY),-thick,-long,bgcolor=bg))
        
        for y in range(int(short+long),int(self.chipY-short-long-dash),dash):
            border.add(dxf.rectangle((self.chipX,y+offsetY-thick),-thick,thick,bgcolor=bg))
        
        self.drawing.blocks.add(border)

        for index,pt in enumerate(self.chipPts):
            if (maxpts==0 or index<maxpts) and index>=minpts:
                self.drawing.add(dxf.insert('DICINGBORDER',insert=(pt[0],pt[1]),layer=self.lyr(layer)))
                
    def writeChip(self,chip,index):
        #insert a chip at specified index
        self.drawing.add(dxf.insert(chip.ID,insert=self.chipSpace(self.chipPts[index]),layer=self.lyr(chip.layer)))
        
    #write all chips in the chips buffer
    def populate(self):
        for i,chip in enumerate(self.chips):
            self.writeChip(chip,i)
    
    def setChipBuffer(self,chip,index):
        self.chips[index]=chip
    
    #define high visibility markers as blocks '00' - '09'
    def defineHiVisMarker09(self,width,layer):
        for i in range(10):
            num = dxf.block('0'+str(i))
            HiVisMarker09(num,0,0,i,width,self.bg(layer))
            self.drawing.blocks.add(num)
    
    #draw a high visibility marker on each chip in the lower left corner
    def mark1000(self,markHeight,start,stop,layer):
        width = markHeight/4
        #default spacing is 
        for i in range(start,stop+1):
            n=i-start
            self.drawing.add(dxf.insert('0'+str(n//100),insert=self.chipSpace(vadd((width,width),self.chipPts[i])),layer=self.lyr(layer)))
            self.drawing.add(dxf.insert('0'+str(n%100//10),insert=self.chipSpace(vadd((width*5,width),self.chipPts[i])),layer=self.lyr(layer)))
            self.drawing.add(dxf.insert('0'+str(n%10),insert=self.chipSpace(vadd((width*9,width),self.chipPts[i])),layer=self.lyr(layer)))
    
    #return chip centered coordinates in wafer space
    def center(self,xy=(0,0)):
        return (xy[0]+self.chipX/2,xy[1]+self.chipY/2)

    def cx(self,x):
        return self.chipX/2 + x
    
    def cy(self,y):
        return self.chipY/2 + y
    
    #chip space:
    #coordinates centered on corner of actual chip
    def chipSpace(self,xy):
        return (xy[0]+self.sawWidth/2,xy[1]+self.sawWidth/2)
    
    #shortcut for add function
    def add(self,obj):
        self.drawing.add(obj)
    
    # --------------------------  Common layer setup functions  ----------------------------------
    
    def setupJunctionLayers(self,JLAYER='JUNCTION',jcolor=1,ULAYER='UNDERCUT',ucolor=2,bandaid=False,BLAYER='BANDAID',bcolor=3):
        #add correct layers to wafer, and cache layer
        self.addLayer(JLAYER,jcolor)
        self.JLAYER=JLAYER
        self.addLayer(ULAYER,ucolor)
        self.ULAYER=ULAYER
        if bandaid:
            self.addLayer(BLAYER,bcolor)
            self.BLAYER=BLAYER
    
    def setupJunctionAngles(self,JANGLES=[0,90]):
        '''
        Angles are defined as the angle in degrees *from which the evaporation is coming*.
        For example, if the first evaporation comes from the East, and the second from the north,
        the angles would be [0,90]. Add more angles to the list as needed.
        '''
        self.JANGLES = [angle % 360 for angle in JANGLES]
        
    def setupManhattanJAngles(self,JANGLE1=0,flip=False):
        '''
        Sets up angles specifically for manhattan junction (Angle 2 is 90 deg CW or CCW from angle 1)
        '''
        JANGLE2 = JANGLE1 + 90
        if flip:
            JANGLE2 = JANGLE1 - 90
        self.setupJunctionAngles(self,[JANGLE1 % 360,JANGLE2 % 360])
        
    def setupXORlayer(self,XLAYER='XOR',xcolor=6):
        '''
        Sets a layer for XOR operations on all other layers. 
        OUT = ( LAYER1 or LAYER2 ... or LAYERN ) xor XLAYER 
        '''
        self.XLAYER=XLAYER
        self.addLayer(XLAYER, xcolor)
       
    def setupAirbridgeLayers(self,BRLAYER='BRIDGE',RRLAYER='TETHER',IBRLAYER='IBRIDGE',IRRLAYER='ITETHER',brcolor=36,rrcolor=41):
        #add correct layers to wafer, and cache layer
        self.addLayer(BRLAYER,brcolor)
        self.BRLAYER=BRLAYER
        self.addLayer(RRLAYER,rrcolor)
        self.RRLAYER=RRLAYER
        self.addLayer(IBRLAYER,brcolor)
        self.IBRLAYER=IBRLAYER
        self.addLayer(IRRLAYER,rrcolor)
        self.IRRLAYER=IRRLAYER

    
# ===============================================================================
#  CHIP CLASS  
#       basic class with a blank chip
# ===============================================================================
        
class Chip:
    #contains 
    chipID = '0'
    width = 0
    height = 0
    layer = '0'
    center = (0,0)
    structures = [] 
    #cached chip propoerties
    solid = 1
    frame = 1
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None, FRAME_NAME='FRAME'):
        self.wafer = wafer
        self.width = wafer.chipX - wafer.sawWidth
        self.height = wafer.chipY - wafer.sawWidth
        self.chipID = chipID #string (usually)
        self.ID = 'CHIP_'+str(chipID)
        self.solid = wafer.solid
        self.frame = wafer.frame
        self.layer = layer
        if defaults is None:
            self.defaults = {}
        else:
            self.defaults = defaults.copy()
        #setup centering
        self.center = (self.width/2,self.height/2)
        #initialize the block
        self.chipBlock = dxf.block(self.ID)
        
        #setup structures
        if structures is not None:
            self.structures = structures
            
        #add a debug frame for actual chip area
        if wafer.frame:
            self.add(dxf.rectangle((0,0),self.width,self.height,layer=wafer.lyr(FRAME_NAME)))
    
    def save(self,wafer,drawCopyDXF=False,dicingBorder=True,center=False, FRAME_LAYER=['IChipEdge',8,-1], MARKER_LAYER=['MARKERS',5,-1]):
        wafer.drawing.blocks.add(self.chipBlock)
        if drawCopyDXF:
            #make a copy DXF with only the chip
            temp_wafer = Wafer(wafer.fileName+'_'+self.ID,wafer.path,10,10)
            #height and width don't matter since the next line copies all settings
            temp_wafer.copyPropertiesFrom(wafer)
            temp_wafer.drawing.blocks.add(self.chipBlock)
            temp_wafer.initChipOnly(center=center, FRAME_LAYER=FRAME_LAYER, MARKER_LAYER=MARKER_LAYER)
            if dicingBorder:
                temp_wafer.DicingBorder()
            temp_wafer.setDefaultChip(self)
            temp_wafer.populate()
            temp_wafer.save()
        return self
        
    def add(self,obj,structure=None,length=None,offsetVector=None,absolutePos=None,angle=0,newDir=None):
        self.chipBlock.add(obj)
        def struct():
            if isinstance(structure,Structure):
                return structure
            elif isinstance(structure,tuple):
                return Structure(self,structure)
            else:
                return self.structures[structure]
        if length is not None:
            struct().shiftPos(length, angle=angle, newDir=newDir)
        elif offsetVector is not None:
            struct().translatePos(vector=offsetVector, angle=angle, newDir=newDir)
        elif absolutePos is not None:
            struct().updatePos(newStart=absolutePos, angle=angle, newDir=newDir)
        
    #return chip centered coordinates in chip space
    def centered(self,xy=(0,0)):
        return (xy[0]+self.center[0],xy[1]+self.center[1])
    
    #return chip centered x coordinate in chip space
    def cx(self,x):
        return self.center[0] + x
    
    #return chip centered y coordinate in chip space
    def cy(self,y):
        return self.center[1] + y
    
    #chip space:
    #coordinates centered on corner of actual chip
    def chipSpace(self,xy):
        return (xy[0]+self.wafer.sawWidth/2,xy[1]+self.wafer.sawWidth/2)
    
    #get structure by index
    def structure(self,i):
        return self.structures[i]
    
    #get structure start by index
    def getStart(self,i):
        return self.structures[i].start
    
    #get structure direction by index
    def getDir(self,i):
        return self.structures[i].direction
    
    #get background color from layer
    def bg(self,layerName=None):
        return self.wafer.bg(layerName)
    
    #get layer from wafer 
    def lyr(self,layerName):
        return self.wafer.lyr(layerName)

   
# ===============================================================================
#  STRUCTURE CLASS  
#       Coordinate system. keeps track of current location and direction, as well as any defaults
# ===============================================================================    

class Structure:
    #start = current coordinates, direction is angle of +x axis in degrees
    
    def __init__(self,chip,start=(0,0),direction=0,defaults=None,current_length=0.0):
        self.chip = chip #parent block reference
        self.start = start
        self.direction = direction #in degrees
        self.last = start
        self.last_direction = direction #in degrees
        self.current_length = current_length #for keeping track of length
        self.last_length = current_length
        if defaults is None:
            self.defaults = chip.defaults.copy()
        else:
            self.defaults = defaults.copy()
        
    def zeroLength(self):
        self.current_length=0.0
    
    def updatePos(self,newStart=(0,0), angle=0, newDir=None): #set exact start position, add angle to direction, or set new direction
        self.last = self.start
        self.last_direction = self.direction
        self.start = newStart
        if newDir is not None:
            self.direction = newDir
        else:
            self.direction = self.direction + angle
            
    def translatePos(self,vector=(0,0), angle=0, newDir=None): 
        #move by a specified vector, set new direction
        self.updatePos(newStart = self.getPos(vector),angle=angle,newDir=newDir)
    
    def shiftPos(self, distance, angle=0, newDir=None):
        #move by a specified distance, set new direction
        self.updatePos(newStart = vadd(self.start,rotate_2d((distance,0),math.radians(self.direction))),angle=angle,newDir=newDir)
        
    def getPos(self,vector=None,distance=None,angle=0):
        #return global position from local position based on current location and direction
        if vector is not None:
            return vadd(self.start,rotate_2d(vector,math.radians(self.direction)))
        elif distance is not None:
            return vadd(self.start,rotate_2d((distance,0),math.radians(angle+self.direction)))
        else:
            return self.start
        
    def getLastPos(self,vector=None,distance=None,angle=0):
        #return global position from local position based on previous location and direction
        if vector is not None:
            return vadd(self.last,rotate_2d(vector,math.radians(self.last_direction)))
        elif distance is not None:
            return vadd(self.last,rotate_2d((distance,0),math.radians(angle+self.last_direction)))
        else:
            return self.last
        
    def getGlobalPos(self,pos=(0,0)):
        #return local position from global position based on current location and direction
        localPos = vsub(pos,self.start)
        return rotate_2d(localPos,-math.radians(self.direction))
    
    def getLastGlobalPos(self,pos=(0,0)):
        #return local position from global position based on previous location and direction
        localPos = vsub(pos,self.last)
        return rotate_2d(localPos,-math.radians(self.last_direction))
    
    def clone(self,defaults=None):
        return Structure(self.chip,start=self.start,direction=self.direction,defaults=defaults is not None and defaults or self.defaults)
    
    def cloneAlong(self,vector=None,distance=None,angle=0,newDirection=0,defaults=None):
        return Structure(self.chip,start=self.getPos(vector=vector,distance=distance,angle=angle),direction=self.direction+newDirection,defaults=defaults is not None and defaults or self.defaults)
    
    def cloneAlongLast(self,vector=None,distance=None,angle=0,newDirection=0,defaults=None):
        return Structure(self.chip,start=self.getLastPos(vector=vector,distance=distance,angle=angle),direction=self.direction+newDirection,defaults=defaults is not None and defaults or self.defaults)

# ===============================================================================
#  BEGIN CUSTOM CLASS DEFINITIONS        
# ===============================================================================
#  7mm CHIP CLASS  
#       chip with 8 structures corresponding to the launcher positions
#       NOTE: chip size still needs to be set in the wafer settings, this just determines structure location
# ===============================================================================

class Chip7mm(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None):
        Chip.__init__(self,wafer,chipID,layer,structures=structures)
        self.defaults = {'w':10, 's':5, 'radius':25,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
                    Structure(self,start=(500,self.height/2),direction=0,defaults=self.defaults),
                    Structure(self,start=(500,700),direction=45,defaults=self.defaults),
                    Structure(self,start=(2500,500),direction=90,defaults=self.defaults),
                    Structure(self,start=(4500,500),direction=90,defaults=self.defaults),
                    Structure(self,start=(self.width-500,700),direction=135,defaults=self.defaults),
                    Structure(self,start=(self.width-500,self.height/2),direction=180,defaults=self.defaults),
                    Structure(self,start=(self.width-500,self.height-700),direction=225,defaults=self.defaults),
                    Structure(self,start=(4500,self.height-500),direction=270,defaults=self.defaults),
                    Structure(self,start=(2500,self.height-500),direction=270,defaults=self.defaults),
                    Structure(self,start=(500,self.height-700),direction=315,defaults=self.defaults)]
        if wafer.frame:
            self.add(dxf.rectangle(self.center,6000,6000,layer=wafer.lyr('FRAME'),halign = const.CENTER,valign = const.MIDDLE,linetype='DOT'))

# ===============================================================================
#  7mm CHIP CLASS, specific for fluxonium
#       chip with 8 structures corresponding to the launcher positions
#       NOTE: chip size still needs to be set in the wafer settings, this just determines structure location
# ===============================================================================


class ChipHelin(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None):
        Chip.__init__(self,wafer,chipID,layer,structures=structures)
        self.defaults = {'w':10, 's':5, 'radius':25,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
                    Structure(self,start=(800,self.height/2 - 995),direction=0,defaults=self.defaults),
                    Structure(self,start=(800,self.height/2 + 1005),direction=0,defaults=self.defaults),
                    Structure(self,start=(self.width / 2 - 1905, self.height-800), direction=270, defaults=self.defaults),
                    Structure(self,start=(self.width / 2 - 5, self.height-800), direction=270,defaults=self.defaults),
                    Structure(self,start=(self.width / 2 + 1895, self.height-800), direction=270,defaults=self.defaults),
                    Structure(self,start=(self.width-800, self.height / 2 + 1005), direction=180,defaults=self.defaults),
                    Structure(self,start=(self.width-800, self.height / 2 - 995), direction=180, defaults=self.defaults),
                    Structure(self,start=(self.width / 2 + 1895, 800), direction=90,defaults=self.defaults),
                    Structure(self,start=(self.width / 2 - 5,    800), direction=90,defaults=self.defaults),
                    Structure(self,start=(self.width / 2 - 1905, 800), direction=90,defaults=self.defaults)]
        if wafer.frame:
            self.add(dxf.rectangle(self.center,6000,6000,layer=wafer.lyr('FRAME'),halign = const.CENTER,valign = const.MIDDLE,linetype='DOT'))

# ===============================================================================
#  10mm CHIP CLASS  
#       chip with 8 structures corresponding to the launcher positions
#       NOTE: chip size still needs to be set in the wafer settings, this just determines structure location
# ===============================================================================

class Chip10mm(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None):
        Chip.__init__(self,wafer,chipID,layer,structures=structures)
        self.defaults = {'w':10, 's':5, 'radius':25,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
                    #TODO update these for 10mm IBM board
                    Structure(self,start=(500,self.height/2),direction=0,defaults=self.defaults),
                    Structure(self,start=(500,700),direction=45,defaults=self.defaults),
                    Structure(self,start=(2500,500),direction=90,defaults=self.defaults),
                    Structure(self,start=(4500,500),direction=90,defaults=self.defaults),
                    Structure(self,start=(self.width-500,700),direction=135,defaults=self.defaults),
                    Structure(self,start=(self.width-500,self.height/2),direction=180,defaults=self.defaults),
                    Structure(self,start=(self.width-500,self.height-700),direction=225,defaults=self.defaults),
                    Structure(self,start=(4500,self.height-500),direction=270,defaults=self.defaults),
                    Structure(self,start=(2500,self.height-500),direction=270,defaults=self.defaults),
                    Structure(self,start=(500,self.height-700),direction=315,defaults=self.defaults)]
        if wafer.frame:
            self.add(dxf.rectangle(self.center,6000,6000,layer=wafer.lyr('FRAME'),halign = const.CENTER,valign = const.MIDDLE,linetype='DOT'))

# ===============================================================================
#  LARGE MARKER CHIP CLASS  
#       chip with large centered rectangle for high visibility
#       NOTE: ribs enabled greatly increases file size
# ===============================================================================

class MarkerLarge(Chip):
    filling = 0
    def __init__(self,wafer,chipID,layer,filling,ribs=0):
        Chip.__init__(self,wafer,chipID,layer)
        self.filling = filling
        if ribs>0:
            for i in range(int(self.height/ribs)):
                self.add(dxf.rectangle((self.cx(-self.width*filling/2),i*ribs),self.width*filling,ribs/2,bgcolor = wafer.bg(layer)))
        else:
            self.add(dxf.rectangle((self.cx(-self.width*filling/2),0),self.width*filling,self.height,bgcolor = wafer.bg(layer)))
        
# ===============================================================================
#  BLANK CENTERED WR10 CHIP CLASS  
#       chip with a rectangle marking dimensions of wr10 waveguide
# ===============================================================================

class BlankCenteredWR10(Chip):
    def __init__(self,wafer,chipID,layer,offset=(0,0)):
        Chip.__init__(self,wafer,chipID,layer)
        self.center = self.centered(offset)
        if wafer.frame:
            self.add(dxf.rectangle(self.centered((-1270,-635)),2540,1270,layer=wafer.lyr('FRAME')))  

# ===============================================================================
# CHIP CLASS FOR LINCOLN LABS DESIGNS
# ===============================================================================

class ChipLL_2port(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None, FRAME_NAME='FRAME'):
        Chip.__init__(self,wafer,chipID,layer,structures=structures, FRAME_NAME=FRAME_NAME)
        self.defaults = {'w':10, 's':6, 'radius':50,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
            Structure(self,start=(self.width/2, 100),direction=90,defaults=self.defaults),
            Structure(self,start=(self.width/2, self.height-100),direction=-90,defaults=self.defaults),
            ]

class ChipLL_6port(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None, FRAME_NAME='FRAME'):
        Chip.__init__(self,wafer,chipID,layer,structures=structures, FRAME_NAME=FRAME_NAME)
        self.defaults = {'w':10, 's':6, 'radius':50,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
            Structure(self,start=(100,1200),direction=0,defaults=self.defaults),
            Structure(self,start=(100,self.height-1200),direction=0,defaults=self.defaults),
            Structure(self,start=(self.width/2,self.height-100),direction=-90,defaults=self.defaults),
            Structure(self,start=(self.width-100,self.height-1200),direction=180,defaults=self.defaults),
            Structure(self,start=(self.width-100,1200),direction=180,defaults=self.defaults),
            Structure(self,start=(self.width/2,100),direction=90,defaults=self.defaults),
            ]

class ChipLL_20port(Chip):
    def __init__(self,wafer,chipID,layer,structures=None,defaults=None, FRAME_NAME='FRAME'):
        Chip.__init__(self,wafer,chipID,layer,structures=structures, FRAME_NAME=FRAME_NAME)
        self.defaults = {'w':10, 's':6, 'radius':50,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
            Structure(self,start=(100,700),direction=0,defaults=self.defaults),
            Structure(self,start=(100,1900),direction=0,defaults=self.defaults),
            Structure(self,start=(100,3100),direction=0,defaults=self.defaults),
            Structure(self,start=(100,4300),direction=0,defaults=self.defaults),

            Structure(self,start=(625, self.height-25),direction=-90,defaults=self.defaults),
            Structure(self,start=(1375,self.height-100),direction=-90,defaults=self.defaults),
            Structure(self,start=(2125,self.height-100),direction=-90,defaults=self.defaults),
            Structure(self,start=(2875,self.height-100),direction=-90,defaults=self.defaults),
            Structure(self,start=(3625,self.height-100),direction=-90,defaults=self.defaults),
            Structure(self,start=(4375,self.height-25),direction=-90,defaults=self.defaults),

            Structure(self,start=(self.width-100,4300),direction=180,defaults=self.defaults),
            Structure(self,start=(self.width-100,3100),direction=180,defaults=self.defaults),
            Structure(self,start=(self.width-100,1900),direction=180,defaults=self.defaults),
            Structure(self,start=(self.width-100,700),direction=180,defaults=self.defaults),

            Structure(self,start=(4375,25),direction=90,defaults=self.defaults),
            Structure(self,start=(3625,100),direction=90,defaults=self.defaults),
            Structure(self,start=(2875,100),direction=90,defaults=self.defaults),
            Structure(self,start=(2125,100),direction=90,defaults=self.defaults),
            Structure(self,start=(1375,100),direction=90,defaults=self.defaults),
            Structure(self,start=(625,25),direction=90,defaults=self.defaults),
            ]


class Linqer_36Port(Chip):
    """
    36 ports, 10.15mm chip for the linker 
    """
    def __init__(self, wafer, chipID, layer, structures=None, defaults=None, FRAME_NAME='FRAME'):
        Chip.__init__(self,wafer,chipID,layer,structures=structures, FRAME_NAME=FRAME_NAME)
        self.defaults = {'w':10, 's':6, 'radius':50,'r_out':0,'r_ins':0}
        if defaults is not None:
            #self.defaults = defaults.copy()
            for d in defaults:
                self.defaults[d]=defaults[d]
        if structures is not None:
            #override default structures
            self.structures = structures
        else:
            self.structures = [#hardwired structures
                Structure(self,start=(100,1600 + i*850),direction=0,defaults=self.defaults) for i in range(9)] + \
                [Structure(self,start=(1600 + i*850,self.height - 100 ),direction=-90,defaults=self.defaults) for i in range(9)] + \
                [Structure(self,start=(self.width - 100 ,1600 + i*850 ),direction=180,defaults=self.defaults) for i in range(9)][::-1] + \
                [Structure(self,start=(1600 + i*850 ,100 ),direction=90,defaults=self.defaults) for i in range(9)][::-1]





# ===============================================================================
#  END CLASS DEFINITIONS   
# ===============================================================================

