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
    "name": "Anim Exporter",
    "blender": (3, 0, 0),
    "category": "Object"
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

def getChannels():

    channels = {"rotation_channels": [], "location_channels": []}

    obj = bpy.context.active_object
    action = obj.animation_data.action
    for fcurve in action.fcurves:
        bone_name = fcurve.group.name
        parts = fcurve.data_path.split('.')
        type = parts[-1]
        if 'rotation_quaternion' == type and not bone_name in channels['rotation_channels']:
            channels['rotation_channels'].append(bone_name)
        if 'location' == type and not bone_name in channels['location_channels']:
            channels['location_channels'].append(bone_name)

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


def getJoints(priority):

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
    channels = getChannels()

    for frame in range(scene.frame_start, scene.frame_end + 1):
  
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

    obj.rotation_euler[2] = radians(-90)
    bpy.ops.object.transform_apply(rotation=True)
    
    return joints
    


def convertActionToDictionary(priority, loop, loop_at_frame, ease_in_duration, ease_out_duration):
    scene = bpy.context.scene
    duration = (scene.frame_end - scene.frame_start) / scene.render.fps

    if loop_at_frame < scene.frame_start:
        loop_at_frame = scene.frame_start

    action = {
        "version": 1,
        "sub_version": 0,
        "base_priority": priority,
        "duration": duration,
        "emote_name": "",
        "loop": int(loop),
        "loop_in_point": (loop_at_frame - scene.frame_start) / scene.render.fps,
        "loop_out_point": duration,
        "ease_in_duration": ease_in_duration,
        "ease_out_duration": ease_out_duration,
        "hand_pose": 0,
        "constraints": [],
        "joints": getJoints(priority)
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

def writeAnimToFile(context, filepath, priority, loop, loop_at_frame, ease_in, ease_out, dump_json):
    check()
    dictionary = convertActionToDictionary(
        priority=priority,
        loop=loop,
        loop_at_frame=loop_at_frame,
        ease_in_duration=ease_in,
        ease_out_duration=ease_out
    )
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
    bl_idname = "export.anim"
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
        default=4
    )

    loop: BoolProperty(
        name="Loop?",
        default=False,
    )

    loop_at_frame: IntProperty(
        name="Loop starts at frame",
        default=1
    )

    ease_in: FloatProperty(
        name="Ease in",
        default=0.8
    )

    ease_out: FloatProperty(
        name="Ease out",
        default=0.8
    )

    dump_json: BoolProperty(
        name="Dump JSON?",
        default=False
    )

    def execute(self, context):
        return writeAnimToFile(
            context, self.filepath,
            self.priority,
            self.loop,
            self.loop_at_frame,
            self.ease_in,
            self.ease_out,
            self.dump_json
        )


def menu_func_export(self, context):
    self.layout.operator(ExportAnimOperator.bl_idname, text="Second Life Animation (.anim)")


# ---------------------------------------------- PROCESS --------------------------------------------------

def check():
    context = bpy.context
    obj = context.active_object
    if not obj:
        raise("You must select an armature")
    if obj.type != 'ARMATURE':
        raise("You must select an armature")
    if not obj.animation_data.action:
        raise("The armature has no action")


def register():
    bpy.utils.register_class(ExportAnimOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportAnimOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
