import bpy
import bmesh
import os
from mathutils import Vector, Euler
import json

def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def create_basic_humanoid(name="Avatar", location=(0, 0, 0)):
    """Create a basic humanoid figure."""
    # Create body (torso)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0], location[1], location[2] + 1))
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    body.scale = (0.8, 0.4, 1.2)
    
    # Create head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(location[0], location[1], location[2] + 2.2))
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    
    # Create arms
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(location[0] + 1, location[1], location[2] + 1.5))
    arm_right = bpy.context.active_object
    arm_right.name = f"{name}_Arm_Right"
    arm_right.scale = (1, 0.5, 2)
    
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(location[0] - 1, location[1], location[2] + 1.5))
    arm_left = bpy.context.active_object
    arm_left.name = f"{name}_Arm_Left"
    arm_left.scale = (1, 0.5, 2)
    
    # Create legs
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(location[0] + 0.3, location[1], location[2] - 0.5))
    leg_right = bpy.context.active_object
    leg_right.name = f"{name}_Leg_Right"
    leg_right.scale = (0.8, 0.8, 2)
    
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(location[0] - 0.3, location[1], location[2] - 0.5))
    leg_left = bpy.context.active_object
    leg_left.name = f"{name}_Leg_Left"
    leg_left.scale = (0.8, 0.8, 2)
    
    return [body, head, arm_right, arm_left, leg_right, leg_left]

def create_materials(avatar_parts, skin_color=(0.9, 0.8, 0.7, 1.0)):
    """Create and apply materials to avatar parts."""
    # Skin material
    skin_material = bpy.data.materials.new(name="Skin_Material")
    skin_material.use_nodes = True
    bsdf = skin_material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = skin_color  # Base Color
    bsdf.inputs[7].default_value = 0.3  # Roughness
    bsdf.inputs[12].default_value = 1.4  # IOR for skin
    
    # Apply skin material to head and body
    for part in avatar_parts[:2]:  # Head and body
        part.data.materials.append(skin_material)
    
    # Clothing material
    clothing_material = bpy.data.materials.new(name="Clothing_Material")
    clothing_material.use_nodes = True
    clothing_bsdf = clothing_material.node_tree.nodes["Principled BSDF"]
    clothing_bsdf.inputs[0].default_value = (0.2, 0.3, 0.8, 1.0)  # Blue clothing
    clothing_bsdf.inputs[7].default_value = 0.8  # Roughness
    
    # Apply clothing material to arms and legs
    for part in avatar_parts[2:]:  # Arms and legs
        part.data.materials.append(clothing_material)

def setup_basic_rig(avatar_parts):
    """Create a basic armature for the avatar."""
    # Add armature
    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature = bpy.context.active_object
    armature.name = "Avatar_Armature"
    
    # Enter edit mode to add bones
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Clear default bone
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.armature.delete()
    
    # Create spine bone
    spine_bone = armature.data.edit_bones.new('Spine')
    spine_bone.head = (0, 0, 0.5)
    spine_bone.tail = (0, 0, 2)
    
    # Create head bone
    head_bone = armature.data.edit_bones.new('Head')
    head_bone.head = (0, 0, 2)
    head_bone.tail = (0, 0, 2.5)
    head_bone.parent = spine_bone
    
    # Create arm bones
    arm_right_bone = armature.data.edit_bones.new('Arm_Right')
    arm_right_bone.head = (0.5, 0, 1.8)
    arm_right_bone.tail = (1.5, 0, 1.8)
    arm_right_bone.parent = spine_bone
    
    arm_left_bone = armature.data.edit_bones.new('Arm_Left')
    arm_left_bone.head = (-0.5, 0, 1.8)
    arm_left_bone.tail = (-1.5, 0, 1.8)
    arm_left_bone.parent = spine_bone
    
    # Create leg bones
    leg_right_bone = armature.data.edit_bones.new('Leg_Right')
    leg_right_bone.head = (0.3, 0, 0.5)
    leg_right_bone.tail = (0.3, 0, -1.5)
    leg_right_bone.parent = spine_bone
    
    leg_left_bone = armature.data.edit_bones.new('Leg_Left')
    leg_left_bone.head = (-0.3, 0, 0.5)
    leg_left_bone.tail = (-0.3, 0, -1.5)
    leg_left_bone.parent = spine_bone
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return armature

def setup_lighting(lighting_type="studio"):
    """Set up lighting for the scene."""
    if lighting_type == "studio":
        # Key light
        bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
        key_light = bpy.context.active_object
        key_light.name = "Key_Light"
        key_light.data.energy = 100
        key_light.data.size = 2
        key_light.rotation_euler = (0.8, 0, 0.8)
        
        # Fill light
        bpy.ops.object.light_add(type='AREA', location=(-2, -3, 3))
        fill_light = bpy.context.active_object
        fill_light.name = "Fill_Light"
        fill_light.data.energy = 50
        fill_light.data.size = 3
        fill_light.rotation_euler = (0.6, 0, -0.6)
        
        # Rim light
        bpy.ops.object.light_add(type='SPOT', location=(0, 4, 3))
        rim_light = bpy.context.active_object
        rim_light.name = "Rim_Light"
        rim_light.data.energy = 80
        rim_light.rotation_euler = (-0.5, 0, 3.14)
        
    elif lighting_type == "natural":
        # Sun light
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
        sun = bpy.context.active_object
        sun.name = "Sun_Light"
        sun.data.energy = 3
        sun.rotation_euler = (0.3, 0.3, 0)
        
        # Sky light (world)
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        
        world.use_nodes = True
        bg_node = world.node_tree.nodes["Background"]
        bg_node.inputs[0].default_value = (0.5, 0.7, 1.0, 1.0)  # Sky blue
        bg_node.inputs[1].default_value = 0.3

def setup_camera(target_location=(0, 0, 1.5)):
    """Set up camera to frame the avatar."""
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "Avatar_Camera"
    
    # Point camera at avatar
    direction = Vector(target_location) - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    return camera

def create_avatar_from_config(config_dict, output_path):
    """Create avatar based on configuration dictionary."""
    # Clear scene
    clear_scene()
    
    # Extract config values
    name = config_dict.get('name', 'Avatar')
    gender = config_dict.get('gender', 'neutral')
    skin_color = config_dict.get('skin_color', [0.9, 0.8, 0.7, 1.0])
    lighting = config_dict.get('lighting', 'studio')
    
    # Create avatar parts
    avatar_parts = create_basic_humanoid(name)
    
    # Apply materials
    create_materials(avatar_parts, tuple(skin_color))
    
    # Create armature
    armature = setup_basic_rig(avatar_parts)
    
    # Set up lighting
    setup_lighting(lighting)
    
    # Set up camera
    setup_camera()
    
    # Set render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True
    
    # Enable screen space reflections and ambient occlusion
    scene.eevee.use_ssr = True
    scene.eevee.use_gtao = True
    
    # Save the file
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"Avatar created and saved to: {output_path}")
    
    return {
        'success': True,
        'avatar_parts': [part.name for part in avatar_parts],
        'armature': armature.name,
        'output_path': output_path
    }

if __name__ == "__main__":
    # Example usage
    config = {
        'name': 'TestAvatar',
        'gender': 'female',
        'skin_color': [0.9, 0.8, 0.7, 1.0],
        'lighting': 'studio'
    }
    
    output_file = "/tmp/test_avatar.blend"
    result = create_avatar_from_config(config, output_file)
    print(json.dumps(result, indent=2))