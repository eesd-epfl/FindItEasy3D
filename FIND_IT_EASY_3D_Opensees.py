##----- FIND IT EASY! 3D -----##
## created on May 6, 2019
## by Giuseppe Sardano, Michele Godio
## Laboratory of Earthquake Engineering and Structural Dynamics (EESD)
## Ecole Polythecnique Federale de Lausanne (EPFL), Switzerland
## Version 2.19 created on May 28, 2019
## and modified on July 1, 2019
##----------------------------##

##----- ALGORITHM DESCRIPTION -----##
# Geometry generator for 3D simplified micro models for masonry structures
# input file: 3D model developed through Rhino  (files.3dm)  
# output file: text file to generate the geometry through LiABlock software (*.3dm)

##----- DRAW YOUR STRUCTURE IN RHINO -----##
# use box elements in Rhino to draw your 3D model 
# all the other element-types are automatically deleted from the algorithm 
# it reads objects from every layer, even when the layer has been hidden/deactivated
# base of the structure at z = 0
# use "EndPoint object snap" for a more precise positioning of the blocks 
# do not use mirror or rotate commands (further development of the algorithm)

##----- DEVELOPER OPTIONS -----##
ID_Block = 0                            # type 1 to draw the Block_id in Rhino GUI, type 0 otherwise 
ID_Face  = 0                            # type 1 to draw the Face_id in Rhino GUI, type 0 otherwise 
MCP = 1000                              # maximum number of contact pairs for a single block

##----- 0. IMPORT LYBRARIES -----##
# the script makes use of the 'rhinoscriptsyntax' library only
# the user does not need to install external libraries to run this script

# import libraries
import rhinoscriptsyntax as rs

#RoundUnit = 4
##----- USER OPTIONS -----##
# define units
invalid_input = True
UnitsTag = rs.GetString("What is your unit of measure? (type: mm,cm,m)")
while invalid_input:
    if UnitsTag == 'mm':
        RoundUnit = 1
        invalid_input = False
    elif UnitsTag == 'cm':
        RoundUnit = 2
        invalid_input = False
    elif UnitsTag == 'm':
        RoundUnit = 4
        invalid_input = False
    else:
        print "Sorry, that was an invalid command!"
        UnitsTag = rs.GetString("What is your unit ? (type: mm,cm,m)")

# define tolerance to be used for contact detection
tol = 10**(-RoundUnit)                                                   


##----- 1. EXRACT INFORMATION FROM THE RHINO DRAWING -----##

# Select all the objects from Rhino sketch (hidden object are selected too)
ALL_OGG = rs.AllObjects(select=True)
N_Objects = len(ALL_OGG)

# Initialize variables
ALL_BLOCKS = range(N_Objects)       

# Select the blocks and delete the other objects
t1  = -1                                # counter
for ii in range(N_Objects):  
    if rs.ObjectType(ALL_OGG[ii]) == 1073741824:    # serial number used by Rhino for 3D prismatic objects
        t1 += 1                
        ALL_BLOCKS[t1] = ALL_OGG[ii]
    else:
        rs.DeleteObjects(ALL_OGG[ii])   # delete all the other objects
ALL_BLOCKS = ALL_BLOCKS[:t1+1]          # trim the array with only the blocks  
N_blocks = len(ALL_BLOCKS)              # number of block 
print N_blocks, "Blocks detected in the structure!"
del ALL_OGG,N_Objects

# Initialize variables
Nfaces = 6															   # number of faces per block
faces =         [0 for row in range(N_blocks)]                         # face id, each block has 6 faces
curves =        [[0 for col in range(Nfaces)]for row in range(N_blocks)]    # curve id, each face has a polyline representing the contour
lines =         [[0 for col in range(Nfaces)]for row in range(N_blocks)]    # line id, each contour has 4 lines 
face_center =   [[[0  for col in range (3)] for col in range(Nfaces)] for row in range(N_blocks)]    # x-, y-, z-coordinates of face center    
Dimensions =    [[[-1 for col in range (3)] for col in range(Nfaces)] for row in range(N_blocks)]    # face size in x-, y- and z-direction 
Block_center =  [0 for row in range(N_blocks)]                         # x-, y-, z-coordinates of block center
Volume =        [-1 for row in range(N_blocks)]                        # block volume
maxLength =     0                                                      # max block length (used for defining tolerance)

# Extract block face dimensions, block face center, max block length
for ii in range(N_blocks):
    faces[ii] =rs.ExplodePolysurfaces(ALL_BLOCKS[ii])                  # explode blocks into surfaces represeting the block faces
    for jj in range(Nfaces):
        lines[ii][jj] = rs.DuplicateEdgeCurves(faces[ii][jj])          # sketch lines along face edges (!) dev. hint: this is time consuming and can be improved
        curves[ii][jj] = rs.JoinCurves(lines[ii][jj])                  # join the lines to create polyline along face adges
        for kk in range(3):
            face_center[ii][jj][kk] = round(rs.CurveAreaCentroid(curves[ii][jj])[0][kk],RoundUnit) # read coordinates of face center
        if jj == 1 or jj == 3:                                         # faces belonging to yz-plane  
            Dimensions[ii][jj][0] = face_center[ii][jj][0]             # x-coordinate of face center
            Dimensions[ii][jj][1] = round(rs.CurveLength(lines[ii][jj][1]),RoundUnit)   # face size in y-direction
            Dimensions[ii][jj][2] = round(rs.CurveLength(lines[ii][jj][0]),RoundUnit)   # face size in z-direction
            maxLength = max(maxLength,Dimensions[ii][jj][1],Dimensions[ii][jj][2])  # # max block length
        if jj == 4 or jj == 5:                                         # faces belonging to xy-plane 
            Dimensions[ii][jj][0] = round(rs.CurveLength(lines[ii][jj][0]),RoundUnit)   # face size in x-direction
            Dimensions[ii][jj][1] = round(rs.CurveLength(lines[ii][jj][1]),RoundUnit)   # face size in y-direction
            Dimensions[ii][jj][2] = face_center[ii][jj][2]             # z-coordinate of face center
        if jj == 0 or jj == 2:                                         # faces belonging to xz-plane 
            Dimensions[ii][jj][0] = round(rs.CurveLength(lines[ii][jj][1]),RoundUnit)   # face size in x-direction
            Dimensions[ii][jj][1] = face_center[ii][jj][1]             # y-coordinate of face center
            Dimensions[ii][jj][2] = round(rs.CurveLength(lines[ii][jj][0]),RoundUnit)   # face size in z-direction
            maxLength = max(maxLength,Dimensions[ii][jj][0])           # # max block length
        rs.DeleteObjects(faces[ii][jj])                                # delete object representing the face
        rs.DeleteObjects(lines[ii][jj])                                # delete object representing the line
del faces, lines, t1                                                   # delete variables not used in what follows

# Extract block volume and block centroid
for ii in range(N_blocks):
    Volume[ii] = Dimensions[ii][1][1]*Dimensions[ii][1][2]*Dimensions[ii][4][0]
    Block_center[ii] = rs.SurfaceVolumeCentroid(ALL_BLOCKS[ii])
    for jj in range(3):                                               # approximate at the RoundUnit-th digit
        Block_center[ii][0][jj] = round(Block_center[ii][0][jj],RoundUnit)     

# Write the id of the block in its centre
if ID_Block == 1: 
    for ii in range(N_blocks):
        rs.AddText(str(ii), Block_center[ii][0],maxLength/14)
# Write the id of each face per block in its face centre
if ID_Face == 1: 
    for ii in range(N_blocks):
        for jj in range(Nfaces):
            b=rs.PointCoordinates(rs.AddPoint([face_center[ii][jj][0],face_center[ii][jj][1],face_center[ii][jj][2]]))
            rs.AddText(str(jj),b,maxLength/24)

##----- 2. FIND CONTACT PAIRS -----##

# Initialize variables
ContBlockID = [[[-1  for col in range(1)] for col in range(Nfaces)] for row in range(N_blocks)]  # contains, for each block face, the id of the block in contact with that face
ContSurfID  = [[[-1  for col in range(1)] for col in range(Nfaces)] for row in range(N_blocks)]  # contains, for each block face, the id of the face in contact with that face

# Define contact pairs in xy-plane
for ii in range(N_blocks):
    for mm in range(N_blocks):
        if mm != ii:
            for pp in range(4,6,1): # faces belonging to xy-plane
                for tt in range(4,6,1):
                    if pp != tt:
                        if abs(Dimensions[ii][pp][2] - Dimensions[mm][tt][2]) < tol:
                            if abs(face_center[ii][pp][1] - face_center[mm][tt][1]) - abs(((Dimensions[ii][pp][1] + Dimensions[mm][tt][1])*0.5)) < -tol and abs(face_center[ii][pp][0] - face_center[mm][tt][0]) - abs(((Dimensions[ii][pp][0] + Dimensions[mm][tt][0])*0.5)) < -tol:
                                ContBlockID[ii][pp].extend([mm])
                                ContSurfID [ii][pp].extend([tt])

for ii in range(N_blocks):      # Delete the first element to every matrix
    for jj in range(Nfaces):
        ContBlockID[ii][jj].pop(0)
        ContSurfID [ii][jj].pop(0)

# Define contact pairs in yz-plane 
for ii in range(N_blocks):
    for mm in range(N_blocks):
        if mm != ii:
            for pp in range(1,4,2):
                for tt in range(1,4,2):
                    if pp != tt:
                        if abs(Dimensions[ii][pp][0] - Dimensions[mm][tt][0]) < tol:
                            if abs(face_center[ii][pp][2] - face_center[mm][tt][2]) - abs(((Dimensions[ii][pp][2] + Dimensions[mm][tt][2])*0.5)) < -tol and abs(face_center[ii][pp][1] - face_center[mm][tt][1]) - abs(((Dimensions[ii][pp][1] + Dimensions[mm][tt][1])*0.5)) < -tol:
                                ContBlockID[ii][pp].extend([mm])
                                ContSurfID [ii][pp].extend([tt])

# Define contact pirs in xz-plane 
for ii in range(N_blocks):
    for mm in range(N_blocks):
        if mm != ii:
            for pp in range(0,3,2):
                for tt in range(0,3,2):
                    if pp != tt:
                        if abs(Dimensions[ii][pp][1] - Dimensions[mm][tt][1]) < tol:
                            if abs(face_center[ii][pp][2] - face_center[mm][tt][2]) - abs(((Dimensions[ii][pp][2] + Dimensions[mm][tt][2])*0.5)) < -tol and abs(face_center[ii][pp][0] - face_center[mm][tt][0]) - abs(((Dimensions[ii][pp][0] + Dimensions[mm][tt][0])*0.5)) < -tol:
                                ContBlockID[ii][pp].extend([mm])
                                ContSurfID [ii][pp].extend([tt])


##----- 3. DEFINE BLOCK and FACE POINTS -----## 

# Initialize variables
FaceCorners = [[[[-1 for col in range(4)] for col in range(MCP)] for col in range(Nfaces)]for row in range(N_blocks)]    # face corner coordinates
Index    	= [[[[-1 for col in range(4)] for col in range(MCP)] for col in range(Nfaces)]for row in range(N_blocks)]    # face corner coordinates index
BlockVertex = [[-1 for col in range(8)] for row in range(N_blocks)]                                                 	 # block vertices coordinates
VerTmp      = [[-1 for col in range(8)] for row in range(N_blocks)]                                                 	 # temp-array used to sort vertices
t5       = [[MCP for col in range(Nfaces)] for row in range(N_blocks)]                                               	 # counter
t9       = [-1 for row in range(N_blocks)]                                                                     			 # counter
BI       = 0 
SI       = 0 
dd       = 0

# Extract face corners
for ii in range(N_blocks):
    for jj in range(Nfaces):
        dd = len(ContBlockID[ii][jj])
        if dd != 0:
            for mm in range(dd):
                BI = ContBlockID[ii][jj][mm]
                SI = ContSurfID[ii][jj][mm]
                for ff in range(4):
                    FaceCorners[ii][jj][mm][ff] = rs.EvaluateCurve(curves[BI][SI],ff)
                    for kk in range(3):
                        FaceCorners[ii][jj][mm][ff][kk] = round(FaceCorners[ii][jj][mm][ff][kk],RoundUnit)

# Extract and round block vertices 
for ii in range (N_blocks):         
    for jj in range(4):
        BlockVertex[ii][jj]   = rs.CurvePoints(curves[ii][4])[jj] # vertices are defined on the xy-plane (4,5)
        BlockVertex[ii][jj+4] = rs.CurvePoints(curves[ii][5])[jj]
        for kk in range(3):
            BlockVertex[ii][jj][kk]=round(BlockVertex[ii][jj][kk],RoundUnit)
            BlockVertex[ii][jj+4][kk]=round(BlockVertex[ii][jj+4][kk],RoundUnit)

# Sort vertices wrt x-, y- and z-coordinate
for ii in range (N_blocks):
    BlockVertex[ii] = rs.SortPoints(BlockVertex[ii],order=5)

# Sort in the way LiA_Block wants 
for ii in range (N_blocks):
    VerTmp[ii][2] = BlockVertex[ii][3]
    VerTmp[ii][3] = BlockVertex[ii][2]
    VerTmp[ii][6] = BlockVertex[ii][7]
    VerTmp[ii][7] = BlockVertex[ii][6]
for ii in range (N_blocks):
    for num in [2,3,6,7]:
        BlockVertex[ii][num] = VerTmp[ii][num]
del VerTmp

# Delete the polylines drawn at the beginning
for ii in range(N_blocks):
    for jj in range(Nfaces):
        rs.DeleteObjects(curves[ii][jj])

# Add base contact
for ii in range(N_blocks):
    for jj in range(8):
        if BlockVertex[ii][jj][2] == 0:
            t9[ii] = t9[ii] + 1
            FaceCorners[ii][4][0][t9[ii]] = BlockVertex[ii][jj]

# Clean the matrix FaceCorners and Index
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for mm in range(MCP):
            if FaceCorners[ii][jj][mm][0] == -1:
                t5[ii][jj] = t5[ii][jj] - 1
for ii in range(N_blocks):
    for jj in range(Nfaces):
        del FaceCorners[ii][jj][t5[ii][jj]:] 
        del Index[ii][jj][t5[ii][jj]:]
del BI,SI,dd,t5,t9,mm


##----- 4. DEFINE CONTACT POINTS -----## 

# Initialize variables 
all_Xtmp = [[-1 for col in range(8)] for row in range(N_blocks)]    # temp variable
all_Ytmp = [[-1 for col in range(8)] for row in range(N_blocks)]    # temp variable
all_Ztmp = [[-1 for col in range(8)] for row in range(N_blocks)]    # temp variable
Max_X = [-1 for row in range(N_blocks)]                             # upper bound of the block domain in x-direction
Max_Y = [-1 for row in range(N_blocks)]                             # upper bound of the block domain in y-direction
Max_Z = [-1 for row in range(N_blocks)]                             # upper bound of the block domain in z-direction
Min_X = [-1 for row in range(N_blocks)]                             # lower bound of the block domain in x-direction                 
Min_Y = [-1 for row in range(N_blocks)]                             # lower bound of the block domain in y-direction
Min_Z = [-1 for row in range(N_blocks)]                             # lower bound of the block domain in z-direction

# Define block domain 
for ii in range(N_blocks):
    for jj in range(8):
        all_Xtmp[ii][jj] = BlockVertex[ii][jj][0]   
        all_Ytmp[ii][jj] = BlockVertex[ii][jj][1]   
        all_Ztmp[ii][jj] = BlockVertex[ii][jj][2]
    Max_X[ii] = round(max(all_Xtmp[ii]),RoundUnit)
    Max_Y[ii] = round(max(all_Ytmp[ii]),RoundUnit)
    Max_Z[ii] = round(max(all_Ztmp[ii]),RoundUnit)
    Min_X[ii] = round(min(all_Xtmp[ii]),RoundUnit)
    Min_Y[ii] = round(min(all_Ytmp[ii]),RoundUnit)
    Min_Z[ii] = round(min(all_Ztmp[ii]),RoundUnit)
del all_Xtmp,all_Ytmp,all_Ztmp

# Subdivide block 'faces' into 'inter-faces'
for ii in range(N_blocks):
    for jj in range(Nfaces): 
        for kk in range(len(FaceCorners[ii][jj])):
            for pp in range(4):
                if FaceCorners[ii][jj][kk][pp][0] - Max_X[ii] > tol: 
                    FaceCorners[ii][jj][kk][pp][0] = Max_X[ii]
                if FaceCorners[ii][jj][kk][pp][1] - Max_Y[ii] > tol:
                    FaceCorners[ii][jj][kk][pp][1] = Max_Y[ii] 
                if FaceCorners[ii][jj][kk][pp][2] - Max_Z[ii] > tol:
                    FaceCorners[ii][jj][kk][pp][2] = Max_Z[ii] 
                if FaceCorners[ii][jj][kk][pp][0] - Min_X[ii] < -tol: 
                    FaceCorners[ii][jj][kk][pp][0] = Min_X[ii]
                if FaceCorners[ii][jj][kk][pp][1] - Min_Y[ii] < -tol:
                    FaceCorners[ii][jj][kk][pp][1] = Min_Y[ii] 
                if FaceCorners[ii][jj][kk][pp][2] - Min_Z[ii] < -tol:
                    FaceCorners[ii][jj][kk][pp][2] = Min_Z[ii] 
#del Max_X,Max_Y,Max_Z,Min_X,Min_Y,Min_Z


##----- 5. DEFINE CONTACT POINT INDEXES -----## 

# Initialize variables
Num_points = 8 
sum        = [0 for row in range(N_blocks)]
Num_cont   = [[-1 for col in range(Nfaces)] for row in range(N_blocks)]
Max        = 0.
TotalContact = [0 for row in range(3)]

# Define index number all block vertices
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(FaceCorners[ii][jj])):
            for pp in range(4):
                for ff in range(8):
                    if abs(FaceCorners[ii][jj][kk][pp][0] - BlockVertex[ii][ff][0]) < tol and abs(FaceCorners[ii][jj][kk][pp][1] - BlockVertex[ii][ff][1])< 100*tol and abs(FaceCorners[ii][jj][kk][pp][2] - BlockVertex[ii][ff][2])< tol:
                        Index[ii][jj][kk][pp] = ff + 1

# Add index of points belonging to interfaces (consecutive numbers wrt vertices)
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(FaceCorners[ii][jj])):
            for pp in range(4):
                if Index[ii][jj][kk][pp] == -1:
                    Num_points= Num_points + 1
                    Index[ii][jj][kk][pp] = Num_points

# Detect which points of the previous set have the same coordinates and replace the assign the same index
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(FaceCorners[ii][jj])):
            if kk > 0:
                for tt in range(len(FaceCorners[ii][jj])):
                    if tt != kk:
                        for pp in range(4):
                            for ff in range(4):
                                if abs(FaceCorners[ii][jj][kk][pp][0] - FaceCorners[ii][jj][tt][ff][0]) < tol and abs(FaceCorners[ii][jj][kk][pp][1] - FaceCorners[ii][jj][tt][ff][1]) < tol and abs(FaceCorners[ii][jj][kk][pp][2] - FaceCorners[ii][jj][tt][ff][2]) < tol:
                                    Index[ii][jj][kk][pp] = Index[ii][jj][tt][ff]

# Count max number of contact per block and print then number of contact for each plane
for ii in range(N_blocks):
    for jj in range(Nfaces):
        Num_cont[ii][jj] = len(FaceCorners[ii][jj])
    TotalContact[0] = TotalContact[0] + Num_cont[ii][0] + Num_cont[ii][2]  # contact in XZ-plane
    TotalContact[1] = TotalContact[1] + Num_cont[ii][1] + Num_cont[ii][3]  # contact in YZ-plane
    TotalContact[2] = TotalContact[2] + Num_cont[ii][4] + Num_cont[ii][5]  # contact in XY-plane
print TotalContact[2], "Contact interfaces detected in XY plane"
print TotalContact[0], "Contact interfaces detected in XZ plane"
print TotalContact[1], "Contact interfaces detected in YZ plane"
print TotalContact[0] + TotalContact[1] + TotalContact[2], "Total contact interfaces detected"

for ii in range(N_blocks):
    for num in Num_cont[ii]:
       sum[ii]= sum[ii] + num
Max = max(sum)  
del Num_cont,sum,num,TotalContact


##----- 6. WRITE TXT FILE COMPATIBLE WITH LIABLOCK_3D SOFTWARE -----##

# Initialize variables 
Index_Excel    = [[-1 for col in range(Max)] for row in range(N_blocks)]                # contact points index
Contact_Points = [[-1 for col in range(2*Num_points)] for row in range(N_blocks)]       # contact points coordinates
t7             = [-1 for row in range(N_blocks)]                                        # counter

# Create matrix with all contact point indices in string format
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(Index[ii][jj])):
            t7[ii] = t7[ii] + 1
            sTmp = Index[ii][jj][kk][0],Index[ii][jj][kk][1],Index[ii][jj][kk][2],Index[ii][jj][kk][3]
            Index_Excel[ii][t7[ii]] = str(sTmp)
            Index_Excel[ii][t7[ii]] = Index_Excel[ii][t7[ii]].replace("(","")
            Index_Excel[ii][t7[ii]] = Index_Excel[ii][t7[ii]].replace(")","")

# Create matrix with contact points coordinates in string format
fTmp = 0
for ii in range(N_blocks):
    for jj in range(8):
        Contact_Points[ii][jj+1] = str(BlockVertex[ii][jj])
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(Index[ii][jj])):
            for pp in range(4):
                fTmp = Index[ii][jj][kk][pp]
                if fTmp > 8:
                    Contact_Points[ii][fTmp] = str(FaceCorners[ii][jj][kk][pp])
del fTmp,sTmp,t7,pp

# Open txt-file
f = open("LiAInputFile.txt", "w+")

# First row of the input file for LiaBlock_3D
f.write("&Count\t"+"&Name\t"+"&BASE\t"+"&C\t")
for ii in range(Max):
    f.write("&CONTACT_")
    f.write(str(ii+1)+"\t")
for ii in range(2*Num_points-1): 
    f.write("&POINT_")
    f.write(str(ii+1)+"\t")
f.write("&VOLUME\n")

# Fill the rest of the input file
for ii in range(N_blocks):
    f.write("1\t"+"&BLOCK_TYPE_"+str(ii)+"\t"+"&4\t"+"&"+str(Block_center[ii][0])+"\t")
    for jj in range(Max):
        if Index_Excel[ii][jj] != -1:
            f.write("&"+Index_Excel[ii][jj]+"\t")
        if Index_Excel[ii][jj] == -1:
            f.write("\t")
    for kk in range(2*Num_points):   
        if Contact_Points[ii][kk] != -1:
            f.write("&"+Contact_Points[ii][kk]+"\t")
        if Contact_Points[ii][kk] == -1:
            if kk != 0:
                f.write("\t")
    f.write("&"+str(Volume[ii])+"\n")

# Close txt-file
f.close()

##----- 7. WRITE TXT FILE COMPATIBLE WITH 3DEC VERSION 5.2 -----##

# Open txt-file
g = open("3DECInputFile.txt", "w+")

# Fill the input file
# Take two opposite vertices among the 8 present in each block
g.write("new\n")
for ii in range(N_blocks):
    g.write("poly brick\t"+str(BlockVertex[ii][0][0])+","+str(BlockVertex[ii][6][0])+"\t"+str(BlockVertex[ii][0][1])+","+str(BlockVertex[ii][6][1])+"\t"+str(BlockVertex[ii][0][2])+","+str(BlockVertex[ii][6][2])+"\n")
g.write("plot create plot Blocks\nplot block")

# Close txt-file
g.close()

##----- 8. CREATE INPUT FILE FOR OPENSEES -----##
AllIntCoord            = [[[-1 for col in range(0)] for col in range(3)] for row in range(N_blocks)]    # All internal points for each block
AllIntPts           = [[[-1 for col in range(3)] for col in range(0)] for row in range(N_blocks)]    # All internal points for each block
NodeOpenSees           = [[[-1 for col in range(3)] for col in range(0)] for row in range(N_blocks)]    # All internal points for each block
counter2             = [[0 for col in range(3)]for row in range(N_blocks)]                              # simple counter
nodecounter          = 0                                                                              # simple counter
elecounter          = 0    
N_subBlock =  [0 for row in range(N_blocks)] 
unit = [1 for row in range(4)]
IndOpenSees =  [[[[0 for col in range(4)] for col in range(MCP)] for col in range(2)] for row in range(N_blocks)]
IDnodeOpensees = [[-1 for col in range(3)]for row in range(1)]   
ZeroLengthElem = [[-1 for col in range(0)]for row in range(8*N_blocks)]   
CounterTmp = -1
CounterZeroLen = -1

# Create a regular point grid for every block
for ii in range(N_blocks):
    for jj in range(Nfaces):
        for kk in range(len(FaceCorners[ii][jj])):
            for pp in range(4):
                for ff in range(3):
                    AllIntCoord[ii][ff].append(FaceCorners[ii][jj][kk][pp][ff])
                    AllIntCoord[ii][ff].append(BlockVertex[ii][0][ff])
                    AllIntCoord[ii][ff].append(BlockVertex[ii][6][ff])
                    AllIntCoord[ii][ff].sort(reverse = True)

# Delete consecutive coordinates
for ii in range(N_blocks):
    for jj in range(3):
        while counter2[ii][jj] < len(AllIntCoord[ii][jj])-1:
            if AllIntCoord[ii][jj][counter2[ii][jj]] == AllIntCoord[ii][jj][counter2[ii][jj]+1]:
                del AllIntCoord[ii][jj][counter2[ii][jj]]
            else: counter2[ii][jj] = counter2[ii][jj] + 1

# Create the matrix with all the points
for ii in range(N_blocks):
    for zz in range(len(AllIntCoord[ii][2])):
        for yy in range(len(AllIntCoord[ii][1])):
            for xx in range(len(AllIntCoord[ii][0])):
                AllIntPts[ii].append(rs.CreatePoint(AllIntCoord[ii][0][xx],AllIntCoord[ii][1][yy],AllIntCoord[ii][2][zz]))
    AllIntPts[ii] = rs.SortPoints(AllIntPts[ii], order=5)  # respectively z,y,x 

# Sort all IntPoints indexes
for ii in range(N_blocks):
    N_subBlock[ii] = (len(AllIntCoord[ii][0])-1)*(len(AllIntCoord[ii][1])-1)*(len(AllIntCoord[ii][2])-1)
    for jj in range(N_subBlock[ii]):
        if jj == 0:
            IndOpenSees[ii][0][jj] = [len(AllIntCoord[ii][0]),0,1,len(AllIntCoord[ii][0])+1]
            IndOpenSees[ii][1][jj] = [len(AllIntCoord[ii][0])*len(AllIntCoord[ii][1])+len(AllIntCoord[ii][0]),len(AllIntCoord[ii][0])*len(AllIntCoord[ii][1]),len(AllIntCoord[ii][0])*len(AllIntCoord[ii][1])+1,len(AllIntCoord[ii][0])*len(AllIntCoord[ii][1])+len(AllIntCoord[ii][0])+1]
        else:
            IndOpenSees[ii][0][jj] = [sum(x) for x in zip(IndOpenSees[ii][0][jj-1],IndOpenSees[ii][0][jj],unit)]
            IndOpenSees[ii][1][jj] = [sum(x) for x in zip(IndOpenSees[ii][1][jj-1],IndOpenSees[ii][1][jj],unit)]
            if AllIntPts[ii][IndOpenSees[ii][0][jj][3]][0] == Max_X[ii]:
                if AllIntPts[ii][IndOpenSees[ii][0][jj][3]][1] != Max_Y[ii]:
                    IndOpenSees[ii][0][jj+1] = unit
                    IndOpenSees[ii][1][jj+1] = unit
                if AllIntPts[ii][IndOpenSees[ii][0][jj][3]][1] == Max_Y[ii]:
                    IndOpenSees[ii][0][jj+1] = [unit[i] + len(AllIntCoord[ii][0])*unit[i] for i in range(len(unit))]
                    IndOpenSees[ii][1][jj+1] = [unit[i] + len(AllIntCoord[ii][0])*unit[i] for i in range(len(unit))]
    del IndOpenSees[ii][0][N_subBlock[ii]:]
    del IndOpenSees[ii][1][N_subBlock[ii]:]

# Organize all the Nodes
for ii in range(N_blocks):
    for jj in range(len(IndOpenSees[ii][0])):
        for tt in range(2):
            for pp in range(4):
                NodeOpenSees[ii].append(AllIntPts[ii][IndOpenSees[ii][tt][jj][pp]])

# Open txt-file
opensees = open("OpenSeesInputFile.txt", "w+")

# Fill the input file
opensees.write("import openseespy.opensees as ops\n\nops.wipe()\n\nops.model('basic', '-ndm', 3, '-ndf', 3)\n\n")
opensees.write("## Definition of the geometry\n\n# Create nodes\n#\t\t tag\tX\tY\tZ\n")

# Create the nodes to define the standard blocks
for ii in range(N_blocks):
    for jj in range(len(NodeOpenSees[ii])):
        nodecounter = nodecounter + 1
        IDnodeOpensees.append(NodeOpenSees[ii][jj])
        opensees.write("ops.node("+str(nodecounter)+","+str(NodeOpenSees[ii][jj][0])+","+str(NodeOpenSees[ii][jj][1])+","+str(NodeOpenSees[ii][jj][2])+")\n")

# Add material used for the standard brick elements
opensees.write("\n# Material Definition\nops.nDMaterial(\"ElasticIsotropic3D\", 1, 2100000000., 0.3, 0.0)\n")
opensees.write("ops.uniaxialMaterial(\"Elastic\",3, 262500000.)\n")

# Define the standard blocks
opensees.write("\n# Create Standard Brick Elements\n#Element\ttag\tnode1\tnode2\tnode3\tnode4\tnode5\tnode6\tnode7\tnode8\tmatTag\n")
elecounter = nodecounter
nodecounter = 0 
for ii in range(N_blocks):
    for jj in range(N_subBlock[ii]):
        elecounter = elecounter + 1
        opensees.write("ops.element(\"stdBrick\","+str(elecounter)+",")
        for pp in range(8):
            nodecounter = nodecounter + 1
            opensees.write(str(nodecounter)+",")
        opensees.write("1)\n")

# Fix the base of each standard block
opensees.write("\n# Constraints Definition\n")
nodecounter = 0 
for ii in range(N_blocks):
    for jj in range(len(NodeOpenSees[ii])):
        nodecounter = nodecounter + 1
        if NodeOpenSees[ii][jj][2] == 0:
            opensees.write("ops.fix("+str(nodecounter)+",1,1,1)\n")


# Set equal DOF for the sub_blocks
MtsSlvNodes = [[-1 for col in range(0)]for row in range(len(IDnodeOpensees))]
nodecounter = 1 


lengh = [-1 for row in range(len(N_subBlock))] 


for ii in range(len(N_subBlock)):
    if ii == 0:
        lengh[ii] = 8*N_subBlock[ii]
    else: lengh[ii] = 8*N_subBlock[ii] + lengh[ii-1]
lengh.insert(0,0)

# Dependent nodes
for ii in range(N_blocks):
    for pp in range(nodecounter,nodecounter + 8*N_subBlock[ii]):
        nodecounter = nodecounter + 1
        for tt in range(lengh[ii]+1,lengh[ii+1]+1):
            if tt != pp:
                if IDnodeOpensees[pp] == IDnodeOpensees[tt]:
                    if IDnodeOpensees[pp][2] != 0:
                        MtsSlvNodes[pp].append(tt)

# Need to have only one master nodes and the other nodes depend on it
for ii in range(len(MtsSlvNodes)):
    for jj in range(len(MtsSlvNodes[ii])):
        for tt in range(len(MtsSlvNodes[MtsSlvNodes[ii][jj]])):
            if  MtsSlvNodes[MtsSlvNodes[ii][jj]][tt] == ii:
                MtsSlvNodes[MtsSlvNodes[ii][jj]][tt] = -1

# Write in opensees
for ii in range(len(MtsSlvNodes)):
    for jj in range(len(MtsSlvNodes[ii])):
        if MtsSlvNodes[ii][jj] != -1:
            opensees.write("ops.equalDOF("+str(ii)+","+str(MtsSlvNodes[ii][jj])+",1,2,3)\n")



# Contact zero length element
for ii in range(N_blocks):
    for jj in range(8):
        for nn in range(N_blocks):
            for pp in range(8):
                if nn != ii:
                    if BlockVertex[ii][jj] == BlockVertex[nn][pp]:
                        CounterTmp = CounterTmp + 1
                        for kk in range(len(IDnodeOpensees)):
                            if BlockVertex[ii][jj] == IDnodeOpensees[kk]:
                                ZeroLengthElem[CounterTmp].append(kk)

# Delete duplicates, only one master node
for ii in range(len(ZeroLengthElem)):
    for jj in range(len(ZeroLengthElem[ii])):
        for nn in range(len(ZeroLengthElem)):
            for pp in range(len(ZeroLengthElem[nn])):
                if nn != ii:
                    if ZeroLengthElem[ii][jj] == ZeroLengthElem[nn][pp]:
                        ZeroLengthElem[nn][pp] = -1

## Write the zero ND-length elements
#opensees.write("\n\n# ZeroLength Elements definition\n")
#for ii in range(len(ZeroLengthElem)):
#    for jj in range(len(ZeroLengthElem[ii])):
#        if jj != 0:
#            if ZeroLengthElem[ii][jj] != -1:
#                CounterZeroLen = CounterZeroLen + 1
#                opensees.write("ops.element(\"zeroLengthND\","+str(CounterZeroLen)+","+str(ZeroLengthElem[ii][0])+","+str(ZeroLengthElem[ii][jj])+",1)\n")

# Write the zero 1D-length elements
opensees.write("\n\n# ZeroLength Elements definition\n")
for ii in range(len(ZeroLengthElem)):
    for jj in range(len(ZeroLengthElem[ii])):
        if jj != 0:
            if ZeroLengthElem[ii][jj] != -1:
                CounterZeroLen = CounterZeroLen + 1
                opensees.write("ops.element(\"zeroLength\","+str(CounterZeroLen)+","+str(ZeroLengthElem[ii][0])+","+str(ZeroLengthElem[ii][jj])+",'-mat',3,'-dir',1,2,3)\n")
opensees.write("\nprint (\"Geometric model built\")\n\n")
opensees.write("\n\nN_blocks="+str(N_blocks))
opensees.write("\nNumNodes="+str(len(IDnodeOpensees)-1))

# Write the zero 1D-length elements as EqualDOF
#opensees.write("\n\n# EqualDOF definition\n")
#for ii in range(len(ZeroLengthElem)):
#    for jj in range(len(ZeroLengthElem[ii])):
#        if jj != 0:
#            if ZeroLengthElem[ii][jj] != -1:
#                CounterZeroLen = CounterZeroLen + 1
#                opensees.write("ops.equalDOF("+str(ZeroLengthElem[ii][0])+","+str(ZeroLengthElem[ii][jj])+",1,2,3)\n")
#opensees.write("\nprint (\"Geometric model built\")\n\n")
#opensees.write("\n\nN_blocks="+str(N_blocks))
#opensees.write("\nNumNodes="+str(len(IDnodeOpensees)-1))

# Close txt-file
#opensees.close()

# External Variables
IndPython = [[-1 for col in range(0)] for row in range(N_blocks)]

#for ii in range(N_blocks):
#    for jj in range(len(NodeOpenSees[ii])):
#        for pp in range(8):
#            if NodeOpenSees[ii][jj] == BlockVertex[ii][pp]:
#                IndPython[ii].append(lengh[ii] + jj)

for ii in range(N_blocks):
    for pp in range(8):
        for jj in range(len(NodeOpenSees[ii])):
            if BlockVertex[ii][pp] == NodeOpenSees[ii][jj] :
                IndPython[ii].append(lengh[ii] + jj)


#openseesVar = open("OpenSeesVariable.txt", "w+")
opensees.write("\nIndVertex=[")

for ii in range(N_blocks):
#    openseesVar.write("[")
    opensees.write("[")
    for jj in range(8):
#         openseesVar.write(str(IndPython[ii][jj])+",")
         opensees.write(str(IndPython[ii][jj])+",")
    if ii == (N_blocks-1):
#        openseesVar.write("]")
        opensees.write("]")
#    else: openseesVar.write("],")
    else: opensees.write("],")
opensees.write("]")

#openseesVar = open("OpenSeesVariable.txt", "w+")
#openseesVar.write("AllPoints=[")
#
#for ii in range(N_blocks):
#    openseesVar.write("[")
#    for jj in range(len(AllIntPts[ii])):
#        if jj == (len(AllIntPts[ii])-1):
#            openseesVar.write("\n["+str(AllIntPts[ii][jj][0])+","+str(AllIntPts[ii][jj][1])+","+str(AllIntPts[ii][jj][2])+"]\n")
#        else: openseesVar.write("\n["+str(AllIntPts[ii][jj][0])+","+str(AllIntPts[ii][jj][1])+","+str(AllIntPts[ii][jj][2])+"],\n")
#    if ii == (N_blocks-1):
#        openseesVar.write("]")
#    else: openseesVar.write("],")
#openseesVar.write("]")

opensees.close()

# Debugging end point
fine = 1