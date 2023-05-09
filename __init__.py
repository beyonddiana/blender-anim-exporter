"""
Copyright (c) 
2023 Aglaia Resident
2022 Kyler "Félix" Eastridge
Campbell Barton
Andrea Rugliancich

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
"""

bl_info = {
    "name": "Second Life Anim Exporter",
    "blender": (3, 0, 0),
    "category": "Animation",
    "author": "Aglaia Resident",
    "version": (1, 2, 0)
}

import bpy
import struct
import argparse
import json
from math import degrees, radians, isclose
from mathutils import Matrix, Euler
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper
import re

# ---------------------------------------------- BONES --------------------------------------------

BASE_BONES = [
    "mPelvis",
    "mTorso",
    "mChest",
    "mNeck",
    "mHead",
    "mSkull",
    "mCollarLeft",
    "mShoulderLeft",
    "mElbowLeft",
    "mWristLeft",
    "mCollarRight",
    "mShoulderRight",
    "mElbowRight",
    "mWristRight",
    "mHipLeft",
    "mKneeLeft",
    "mAnkleLeft",
    "mFootLeft",
    "mToeLeft",
    "mHipRight",
    "mKneeRight",
    "mAnkleRight",
    "mFootRight",
    "mToeRight",
    "mGroin"
]

VOLUME_BONES = [
    "LEFT_PEC",
    "RIGHT_PEC",
    "PELVIS",
    "HEAD",
    "NECK",
    "R_CLAVICLE",
    "L_CLAVICLE",
    "CHEST",
    "UPPER_BACK",
    "BELLY",
    "LEFT_HANDLE",
    "RIGHT_HANDLE",
    "R_UPPER_ARM",
    "L_UPPER_ARM",
    "LOWER_BACK",
    "BUTT",
    "R_LOWER_ARM",
    "L_LOWER_ARM",
    "L_HAND",
    "R_HAND",
    "R_UPPER_LEG",
    "L_UPPER_LEG",
    "R_LOWER_LEG",
    "L_LOWER_LEG",
    "R_FOOT",
    "L_FOOT"
]

def is_sl_bone(bone):    
    # Base and Volume bones
    if bone in BASE_BONES or bone in VOLUME_BONES:
        return True

    # Fingers
    if re.search("^mHand(Thumb|Index|Middle|Ring|Pinky)(1|2|3)(Right|Left)$", bone):
        return True
    
    # Tail
    if re.search("^mTail(1|2|3|4|5|6)$", bone):
        return True
    
    # Spine
    if re.search("^mSpine(1|2|3|4)$", bone):
        return True
    
    # Wings
    if "mWingsRoot" == bone or "mWing4FanRight" == bone or "mWing4FanLeft" == bone:
        return True
    if re.search("^mWing(1|2|3|4)(Right|Left)$", bone):
        return True
    
    # Hinds Limbs
    if "mHindLimbsRoot" == bone:
        return True
    if re.search("^mHindLimb(1|2|3|4)(Right|Left)$", bone):
        return True
    
    # Face
    if re.search("^mFaceForehead(Right|Left|Center)$", bone):
        return True
    if re.search("^mFaceEyebrow(Outer|Center|Inner)(Right|Left)$", bone):
        return True
    if re.search("^mFaceEyeLid(Upper|Lower)(Right|Left)$", bone):
        return True
    if re.search("^mFaceEyeAlt(Right|Left)$", bone):
        return True
    if re.search("^mFaceEyecornerInner(Right|Left)$", bone):
        return True
    if re.search("^mFaceEar(1|2)(Right|Left)$", bone):
        return True
    if re.search("^mFaceNose(Right|Left|Center|Base|Bridge)$", bone):
        return True
    if re.search("^mFaceCheek(Upper|Lower)(Right|Left)$", bone):
        return True
    if "mFaceJaw" == bone or "mFaceChin" == bone or "mFaceJawShaper" == bone or "mFaceRoot" == bone:
        return True
    if re.search("^mFaceLip(Upper|Corner)(Right|Left|Center)$", bone):
        return True
    if re.search("^mFaceTongue(Base|Tip)$", bone):
        return True
    if re.search("^mFaceLipLower(Right|Left|Center)$", bone):
        return True
    if re.search("^mFaceTeeth(Lower|Upper)$", bone):
        return True
    
    # Eyes
    if re.search("^mEye(Right|Left)$", bone):
        return True
        
    return False

# ---------------------------------------------- ACTION TO DICTIONARY -------------------------------------

class DecoratedBone:

    def __init__(self, obj, arm, bone_name):
        
        self.name = bone_name
        
        self.rest_bone = arm.bones[bone_name]
        self.pose_bone = obj.pose.bones[bone_name]
        
        self.rot_order_str = 'ZYX'
        self.rot_order_str_reverse = self.rot_order_str[::-1]
        self.rot_order = (2, 1, 0)
        
        self.pose_mat = self.pose_bone.matrix
        self.rest_arm_mat = self.rest_bone.matrix_local
        self.rest_local_mat = self.rest_bone.matrix
        self.pose_imat = self.pose_mat.inverted()
        self.rest_arm_imat = self.rest_arm_mat.inverted()
        self.rest_local_imat = self.rest_local_mat.inverted()
         
        self.parent = None
        self.prev_euler = Euler((0.0, 0.0, 0.0), self.rot_order_str_reverse)
    
    def update_posedata(self):
        self.pose_mat = self.pose_bone.matrix
        self.pose_imat = self.pose_mat.inverted()
    
    def __repr__(self):
        if self.parent:
            return "[\"%s\" child on \"%s\"]\n" % (self.name, self.parent.name)
        else:
            return "[\"%s\" root bone]\n" % (self.name)

def getChannels(with_translations):
    channels = {"rotation_channels": [], "location_channels": []}
    obj = bpy.context.active_object
    action = obj.animation_data.action
    for fcurve in action.fcurves:
        if "pose.bones" != fcurve.data_path[0:10]:
            continue
        parts = fcurve.data_path.rpartition('.')
        pose_bone = obj.path_resolve(parts[0])
        fcurve_type = parts[2]
        if not is_sl_bone(pose_bone.name):
            continue
        if 'rotation_quaternion' == fcurve_type and not pose_bone.name in channels['rotation_channels']:
            channels['rotation_channels'].append(pose_bone.name)
        if 'location' == fcurve_type and not pose_bone.name in channels['location_channels']:
            if 'mPelvis' == pose_bone.name or with_translations:
                channels['location_channels'].append(pose_bone.name)

    return channels


def getBonesDecorated(obj, arm):
    bones_decorated = [DecoratedBone(obj, arm, bone.name) for bone in arm.bones]

    # Assign parents
    bones_decorated_dict = {dbone.name: dbone for dbone in bones_decorated}
    for dbone in bones_decorated:
        parent = dbone.rest_bone.parent
        if parent:
            dbone.parent = bones_decorated_dict[parent.name]
    del bones_decorated_dict

    return bones_decorated


def getJoints(priority, with_translations):

    context = bpy.context
    obj = context.active_object
    arm = obj.data
    offset = arm.bones[0].head / 2
    scene = context.scene

    bpy.ops.object.mode_set(mode = 'OBJECT')
    obj.rotation_euler[2] = radians(90)
    bpy.ops.object.transform_apply(rotation=True)

    joints = {}

    bones_decorated = getBonesDecorated(obj, arm)
    channels = getChannels(with_translations)
    
    frame_current = scene.frame_current
    
    wm = bpy.context.window_manager
    wm.progress_begin(0, scene.frame_end - scene.frame_start)

    for frame in range(scene.frame_start, scene.frame_end + 1):
        
        wm.progress_update(frame - scene.frame_start)
  
        scene.frame_set(frame)

        for dbone in bones_decorated:
            dbone.update_posedata()

        for dbone in bones_decorated:

            if not dbone.name in channels['rotation_channels'] and not dbone.name in channels['location_channels']:
                continue

            if frame == scene.frame_start:
                joints[dbone.name] = {"priority": priority, "position_keys": [], "rotation_keys": []}

            trans = Matrix.Translation(dbone.rest_bone.head_local)
            itrans = Matrix.Translation(-dbone.rest_bone.head_local)
            
            if dbone.parent:
                mat_final = dbone.parent.rest_arm_mat @ dbone.parent.pose_imat @ dbone.pose_mat @ dbone.rest_arm_imat
                mat_final = itrans @ mat_final @ trans
                loc = mat_final.to_translation() + (dbone.rest_bone.head_local - dbone.parent.rest_bone.head_local)
            else:
                mat_final = dbone.pose_mat @ dbone.rest_arm_imat
                mat_final = itrans @ mat_final @ trans
                loc = mat_final.to_translation() + dbone.rest_bone.head

            rot = mat_final.to_euler(dbone.rot_order_str_reverse, dbone.prev_euler)
            rot_quat = mat_final.to_quaternion()
            
            nbr_inter_frames = scene.frame_end - scene.frame_start
            frameU16 = round((frame - scene.frame_start) / nbr_inter_frames * 0xFFFF) if nbr_inter_frames > 0 else 0
            
            if dbone.name in channels['location_channels']:
                loc = loc * 0.5
                if 'mPelvis' == dbone.name:
                    loc = loc - offset
                joints[dbone.name]["position_keys"].append({"time": frameU16, "x": loc.x, "y": loc.y, "z": loc.z})
            
            if dbone.name in channels['rotation_channels']:
                joints[dbone.name]["rotation_keys"].append({
                    "time": frameU16,
                    "w": rot_quat.w,
                    "x": rot_quat.x,
                    "y": rot_quat.y,
                    "z": rot_quat.z,
                    # "eulerXYZ": f"{degrees(rot[dbone.rot_order[2]])} {degrees(rot[dbone.rot_order[1]])} {degrees(rot[dbone.rot_order[0]])}",
                })

            dbone.prev_euler = rot

    scene.frame_set(frame_current)
    wm.progress_end()

    obj.rotation_euler[2] = radians(-90)
    bpy.ops.object.transform_apply(rotation=True)
    
    return joints
    


def convertActionToDictionary(priority, loop, loop_start, loop_end, ease_in_duration, ease_out_duration, with_translations):
    scene = bpy.context.scene
    duration = (scene.frame_end - scene.frame_start) / scene.render.fps

    if loop_start < scene.frame_start:
        loop_start = scene.frame_start
        
    if loop_end > scene.frame_end:
        loop_end = scene.frame_end

    action = {
        "version": 1,
        "sub_version": 0,
        "base_priority": priority,
        "duration": duration,
        "emote_name": "",
        "loop": int(loop),
        "loop_in_point": (loop_start - scene.frame_start) / scene.render.fps,
        "loop_out_point": (loop_end - scene.frame_start) / scene.render.fps,
        "ease_in_duration": ease_in_duration,
        "ease_out_duration": ease_out_duration,
        "hand_pose": 0,
        "constraints": [],
        "joints": getJoints(priority, with_translations)
    }

    return action

# ---------------------------------------------- DICTIONARY TO ANIM ---------------------------------------

sAnimHeader = struct.Struct("<HHLf")
sAnimParams = struct.Struct("<ffLffLL")
sAnimFrame = struct.Struct("<HHHH")
sAnimUInt32 = struct.Struct("<I") #Used for various stuff
sAnimConstraint = struct.Struct("<BB16sfff16sffffffffff")

def convertDictionaryToAnim(data):
    result = b""
    result += sAnimHeader.pack(
        data["version"],
        data["sub_version"],
        data["base_priority"],
        data["duration"]
    )
    result += data["emote_name"].encode() + b"\0"
    result += sAnimParams.pack(
        data["loop_in_point"],
        data["loop_out_point"],
        data["loop"],
        data["ease_in_duration"],
        data["ease_out_duration"],
        data["hand_pose"],
        len(data["joints"])
    )
    
    for bname, joint in data["joints"].items():
        
        result += bname.encode() + b"\0"
        
        result += sAnimUInt32.pack(joint["priority"])
        
        result += sAnimUInt32.pack(len(joint["rotation_keys"]))
        
        for rot_key in joint["rotation_keys"]:
                        
            rot_w = rot_key['w']
            rot_x = rot_key['x']
            rot_y = rot_key['y']
            rot_z = rot_key['z']
  
            if rot_w < 0:
                rot_x = -rot_x
                rot_y = -rot_y
                rot_z = -rot_z
                rot_w = -rot_w
            
            
            result += sAnimFrame.pack(
                rot_key["time"],
                int(((rot_x + 1) / 2) * 0xFFFF),
                int(((rot_y + 1) / 2) * 0xFFFF),
                int(((rot_z + 1) / 2) * 0xFFFF)
            )
                    
        result += sAnimUInt32.pack(len(joint["position_keys"]))
        
        for pos_key in joint["position_keys"]:
            pos_key["x"] = min(max(-1,pos_key["x"]),1)
            pos_key["y"] = min(max(-1,pos_key["y"]),1)
            pos_key["z"] = min(max(-1,pos_key["z"]),1)
            result += sAnimFrame.pack(
                pos_key["time"],
                int(((pos_key["x"]/5)+0.5)*0xFFFF),
                int(((pos_key["y"]/5)+0.5)*0xFFFF),
                int(((pos_key["z"]/5)+0.5)*0xFFFF)
            )
    
    result += sAnimUInt32.pack(len(data["constraints"]))
    
    for constraint in data["constraints"]:
        result += sAnimConstraint.pack(
            constraint["chain_length"],
            constraint["constraint_type"],
            (constraint["source_volume"].encode()+(b"\0"*16))[0:16],
            constraint["source_offset"][0],
            constraint["source_offset"][1],
            constraint["source_offset"][2],
            (constraint["target_volume"].encode()+(b"\0"*16))[0:16],
            constraint["target_offset"][0],
            constraint["target_offset"][1],
            constraint["target_offset"][2],
            constraint["target_dir"][0],
            constraint["target_dir"][1],
            constraint["target_dir"][2],
            constraint["ease_in_start"],
            constraint["ease_in_stop"],
            constraint["ease_out_start"],
            constraint["ease_out_stop"]
        )
    
    return result

# ---------------------------------------------- CLEANING -------------------------------------------------

def removeDuplicatedFrames(data):
    def is_close_to_sibblings(previous_key, current_key, next_key, is_rotation):
        if not isclose(previous_key['x'], current_key['x'], abs_tol=0.0001) or not isclose(current_key['x'], next_key['x'], abs_tol=0.0001):
            return False
        if not isclose(previous_key['y'], current_key['y'], abs_tol=0.0001) or not isclose(current_key['y'], next_key['y'], abs_tol=0.0001):
            return False
        if not isclose(previous_key['z'], current_key['z'], abs_tol=0.0001) or not isclose(current_key['z'], next_key['z'], abs_tol=0.0001):
            return False
        if is_rotation:
            if not isclose(previous_key['w'], current_key['w'], abs_tol=0.0001) or not isclose(current_key['w'], next_key['w'], abs_tol=0.0001):
                return False
        return True
    
    for joint_name, joint in data['joints'].items():
        if len(joint['rotation_keys']) >= 3:
            to_delete = []
            for i in range(1, len(joint['rotation_keys']) - 1):
                previous_key = joint['rotation_keys'][i - 1]
                current_key = joint['rotation_keys'][i]
                next_key = joint['rotation_keys'][i + 1]
                if is_close_to_sibblings(previous_key, current_key, next_key, True):
                    to_delete.append(i)
            for i in sorted(to_delete, reverse=True):
                del data['joints'][joint_name]['rotation_keys'][i]

        if len(joint['position_keys']) >= 3:
            to_delete = []
            for i in range(1, len(joint['position_keys']) - 1):
                previous_key = joint['position_keys'][i - 1]
                current_key = joint['position_keys'][i]
                next_key = joint['position_keys'][i + 1]
                if is_close_to_sibblings(previous_key, current_key, next_key, False):
                    to_delete.append(i)
            for i in sorted(to_delete, reverse=True):
                del data['joints'][joint_name]['position_keys'][i]

    return data


# ---------------------------------------------- EXPORTER WIDGET ------------------------------------------

def writeAnimToFile(context, filepath, priority, loop, loop_start, loop_end, ease_in, ease_out, dump_json, with_translations):
    
    dictionary = convertActionToDictionary(priority, loop, loop_start, loop_end, ease_in, ease_out, with_translations)
    dictionary = removeDuplicatedFrames(dictionary)
    anim = convertDictionaryToAnim(dictionary)

    if dump_json:
        f_json = open(filepath + ".json", 'w')
        f_json.write(json.dumps(dictionary, indent=4))
        f_json.close()

    f_anim = open(filepath, 'wb')
    f_anim.write(anim)
    f_anim.close()

    return {'FINISHED'}


class ExportAnimOperator(Operator, ExportHelper):
    """Exports a .anim file for Second Life"""
    bl_idname = "sl_anim.export"
    bl_label = "Export a .anim file"

    # ExportHelper mixin class uses this
    filename_ext = ".anim"

    filter_glob: StringProperty(
        default="*.anim",
        options={'HIDDEN'},
        maxlen=255,
    )

    priority: IntProperty(
        name="Priority",
        default=4,
        min=0,
        max=6
    )
    
    with_translations: BoolProperty(
        name="Export translations?",
        default=False,
        description="If not checked, only rotations will be exported. Note that this won't affect mPelvis: mPelvis translations will be exported anyway."
    )

    loop: BoolProperty(
        name="Loop?",
        default=False,
    )
    
    loop_start: IntProperty(
        name="From",
        default=0
    )
    
    loop_end: IntProperty(
        name="To",
        default=0
    )

    ease_in: FloatProperty(
        name="In",
        default=0
    )

    ease_out: FloatProperty(
        name="Out",
        default=0
    )

    dump_json: BoolProperty(
        name="Dump as JSON?",
        default=False,
        description="This will produce an addition .json file that you can open in a text editor for debuging purpose."
    )
    
    def invoke(self, context, event):
        self.loop_start = bpy.context.scene.frame_start
        self.loop_end = bpy.context.scene.frame_end
        return ExportHelper.invoke(self, context, event)
        
    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        
        row = layout.row()
        row.label(text="SCENE DATA")
        row = layout.row()
        row.label(text=f"Start frame: {scene.frame_start}")
        row = layout.row()
        row.label(text=f"End frame: {scene.frame_end}")
        row = layout.row()
        row.label(text=f"FPS: {scene.render.fps}")
        
        row = layout.row()
        row.label(text="EXPORT TRANSLATIONS?")
        row = layout.row()
        row.prop(self, "with_translations")
        
        row = layout.row()
        row.label(text="PRIORITY")
        row = layout.row()
        row.prop(self, "priority")
        
        row = layout.row()
        row.label(text="LOOP")
        row = layout.row()
        row.prop(self, "loop")
        row = layout.row()
        row.prop(self, "loop_start")
        row.prop(self, "loop_end")
        
        row = layout.row()
        row.label(text="EASE IN/OUT")
        row = layout.row()
        row.prop(self, "ease_in")
        row.prop(self, "ease_out")
        
        row = layout.row()
        row.label(text="DEBUG")
        row = layout.row()
        row.prop(self, "dump_json")
         

    def execute(self, context):
        
        error = getError()
        if "" != error:
            self.report({'ERROR'}, error)
            return {'FINISHED'}
        
        return writeAnimToFile(
            context, self.filepath,
            self.priority,
            self.loop,
            self.loop_start,
            self.loop_end,
            self.ease_in,
            self.ease_out,
            self.dump_json,
            self.with_translations
        )


def menu_func_export(self, context):
    self.layout.operator(ExportAnimOperator.bl_idname, text="Second Life Animation (.anim)")


# ---------------------------------------------- PROCESS --------------------------------------------------

def getError():
    context = bpy.context
    obj = context.active_object
    
    if obj is None:
        return "You must select an armature"
    if not obj.type == 'ARMATURE':
        return "You must select an armature"
    if not obj.animation_data.action:
        return "Your armature has no action."
    
    return ""


def register():
    bpy.utils.register_class(ExportAnimOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportAnimOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
    bpy.ops.sl_anim.export('INVOKE_DEFAULT')
