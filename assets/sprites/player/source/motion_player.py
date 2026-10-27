"""Recepta dopracowania istniejących akcji. Eksporter odtwarza zapisane klucze, nie tę receptę."""
import math
import bpy
from mathutils import Vector, Matrix
from build_player import ik, transform
TAU=math.tau
RIG=None
CAPE=None
REST={}

def bind():
    global RIG,CAPE,REST
    RIG=bpy.data.objects['Bohater_RIG']
    CAPE=bpy.data.objects['Krótki płaszcz / miękkie fałdy']
    REST={b.name:(b.head_local.copy(),b.tail_local.copy()) for b in RIG.data.bones}

def foot_target(phase, side, walking=True):
    sign=1 if side=='L' else -1
    if not walking:return Vector((.045 if sign==1 else -.045,sign*.126,.0778)),0
    p=(phase+(0 if side=='L' else .5))%1
    if p<.6:
        x=.26-.52*p/.6; lift=0
        pitch=-.19*(1-p/.12)**2 if p<.12 else (.30*((p-.44)/.16)**2 if p>.44 else 0)
        # Heel / toe pivot: keep the sole contact at ground height.
        pivot=Vector((-.054 if pitch<0 else .168,0,-.0778))
        offset=pivot-Matrix.Rotation(pitch,4,'Y')@pivot
        return Vector((x+offset.x,sign*.126,.0778+offset.z)),pitch
    else:
        s=(p-.6)/.4
        x=-.26+.52*(.5-.5*math.cos(math.pi*s)); lift=.095*math.sin(math.pi*s)
        pitch=.30*(1-s)-.19*s + .20*math.sin(math.pi*s)
    pivot=Vector((-.054 if pitch<0 else .168,0,-.0778))
    offset=pivot-Matrix.Rotation(pitch,4,'Y')@pivot
    return Vector((x+offset.x,sign*.126,.0778+offset.z+lift)),pitch


def set_pose(phase, walking=True, frame=None):
    bob=-.008*math.cos(TAU*phase*2) if walking else .002*math.sin(TAU*phase)
    sway=.018*math.cos(TAU*phase) if walking else .002*math.sin(TAU*phase)
    pelvis=Vector((.0133,sway,(.890 if walking else .929)+bob))
    base=Vector((.0133,0,.935))
    bodyyaw=.065*math.cos(TAU*phase) if walking else .008*math.sin(TAU*phase)
    pmat=Matrix.Translation(pelvis)@Matrix.Rotation(bodyyaw,4,'Z')@Matrix.Rotation(.022*math.cos(TAU*phase) if walking else .004*math.sin(TAU*phase),4,'X')@Matrix.Translation(-base)
    chestpivot=REST['chest'][0]
    cm=pmat@Matrix.Translation(chestpivot)@Matrix.Rotation(-bodyyaw*1.7,4,'Z')@Matrix.Rotation(.035,4,'Y')@Matrix.Translation(-chestpivot)
    head=cm@Matrix.Translation(REST['head'][0])@Matrix.Rotation(-bodyyaw*.38,4,'Z')@Matrix.Rotation(-.025 if walking else .012*math.sin(TAU*phase-.6),4,'Y')@Matrix.Translation(-REST['head'][0])
    maps={'pelvis':pmat,'spine':pmat,'chest':cm,'neck':cm,'head':head}
    audit={'feet':{}}
    for side,sign in [('L',1),('R',-1)]:
        th,sh='thigh.'+side,'shin.'+side
        hip=pmat@REST[th][0]
        ankle,pitch=foot_target(phase,side,walking)
        l1=(REST[th][1]-REST[th][0]).length;l2=(REST[sh][1]-REST[sh][0]).length
        knee=ik(hip,ankle,l1,l2,(1,0,0))
        maps[th]=transform(*REST[th],hip,knee);maps[sh]=transform(*REST[sh],knee,ankle)
        restfoot=REST['foot.'+side]
        rot=Matrix.Rotation(pitch,4,'Y')
        maps['foot.'+side]=Matrix.Translation(ankle)@rot@Matrix.Translation(-restfoot[0])
        shoulder=cm@REST['upper_arm.'+side][0]
        arm_phase=TAU*(phase+(0 if side=='L' else .5))
        hand=Vector((.075-(.095*math.cos(arm_phase-.18) if walking else .002*math.sin(arm_phase)),
                     sign*(.265+( .008*math.sin(arm_phase) if walking else 0)),
                     .985+bob+(.017*math.sin(arm_phase-.25) if walking else 0)))
        if side=='R':
            # A sword is carried with a modest elbow bend, not swung exactly
            # like an empty hand. Keep the blade low and outside the body.
            hand=Vector((.19-(.030*math.cos(arm_phase-.2) if walking else 0),-.335-.009*math.sin(arm_phase),1.025+bob+.007*math.sin(arm_phase)))
        up,fore='upper_arm.'+side,'forearm.'+side
        l1=(REST[up][1]-REST[up][0]).length;l2=(REST[fore][1]-REST[fore][0]).length
        # Keep arm targets on their reachable sphere as equipment subtly swings.
        delta=hand-shoulder
        if delta.length>l1+l2-.007:hand=shoulder+delta.normalized()*(l1+l2-.007)
        elbow=ik(shoulder,hand,l1,l2,(-1,sign*.7,0))
        maps[up]=transform(*REST[up],shoulder,elbow);maps[fore]=transform(*REST[fore],elbow,hand)
        maps['hand.'+side]=maps[fore]
        if side=='R':
            wrist_rotation=(Matrix.Rotation(.045*math.sin(arm_phase-.25) if walking else 0,4,'Y')
                            @ Matrix.Rotation(bodyyaw,4,'Z'))
            maps['hand.R']=(Matrix.Translation(hand)@wrist_rotation
                            @ Matrix.Translation(-REST['hand.R'][0]))
        p=(phase+(0 if side=='L' else .5))%1
        audit['feet'][side]={'ankle_m':list(ankle),'stance':bool(walking and p<.6),'pitch_rad':pitch,'plant_reference_m':(.26-.52*p/.6) if walking and p<.6 else None}
    def depth(b):return 0 if b.parent is None else 1+depth(b.parent)
    desired={name:maps[name]@RIG.data.bones[name].matrix_local for name in maps}
    for b in sorted(RIG.pose.bones,key=depth):
        # Assign the basis from explicit parent/rest matrices. Setting .matrix
        # successively uses stale evaluated parents and disconnects joints.
        rest=b.bone.matrix_local
        if b.parent:
            b.matrix_basis=(rest.inverted() @ b.parent.bone.matrix_local
                            @ desired[b.parent.name].inverted() @ desired[b.name])
        else:
            b.matrix_basis=rest.inverted()@desired[b.name]
        b.rotation_mode='QUATERNION'
        if frame is not None:
            b.keyframe_insert('location',frame=frame)
            b.keyframe_insert('rotation_quaternion',frame=frame)
            b.keyframe_insert('scale',frame=frame)
    if CAPE:
        for i,key in enumerate(list(CAPE.data.shape_keys.key_blocks)[1:]):
            key.slider_min=-1
            key.value=(.36 if walking else .055)*math.sin(TAU*phase-.7-i*.9)
            if frame is not None:key.keyframe_insert('value',frame=frame)
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.data.shape_keys or obj==CAPE:continue
        for key in list(obj.data.shape_keys.key_blocks)[1:]:
            key.slider_min=-1
            key.value=(.75 if walking else .12)*math.sin(TAU*phase-.8)
            if frame is not None:key.keyframe_insert('value',frame=frame)
    bpy.context.view_layer.update()
    gaps=[];length_errors=[]
    for side in ['L','R']:
        for child,parent in [('forearm','upper_arm'),('hand','forearm'),('shin','thigh'),('foot','shin')]:
            gaps.append((RIG.pose.bones[child+'.'+side].head-RIG.pose.bones[parent+'.'+side].tail).length)
    for b in RIG.pose.bones:
        length_errors.append(abs((b.tail-b.head).length-b.bone.length))
    audit['max_joint_gap_m']=max(gaps)
    audit['max_bone_length_error_m']=max(length_errors)
    if audit['max_joint_gap_m']>.0001 or audit['max_bone_length_error_m']>.0001:
        raise ValueError('Niespójny szkielet: '+str(audit))
    return audit


