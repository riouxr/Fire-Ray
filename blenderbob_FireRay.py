# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Fire is inspired by Navkit by Laurent Taillefer. 
# Blender version first written by Debuk https://github.com/debukgit/
# and modified by Danny Di Donato and Debuk under Blender Bob's supervision (Real by Fake)

# This addon will place an empty at the correct position in 3D space IF the tracking is perfect.
# Create an empty and place it where you want to add a "tracking point"
# Press the Fire button in the tool tab. This will fire an edge from the camera passing through the empty
# Move to another frame on the timeline
# Using snap to edge, move the empty along the edge until it matches the place you wanted to track.
# Your empty is now correctly placed in 3D space.  


bl_info = {
    "name": "Fire",
    "author": "Blender Bob, Danny Di Donato, Debuk",
    "blender": (2, 80, 0),
    "version": (1, 0, 1),
    'license': 'GPL v3',
    "location": "3D View > Toolbox > Tool",
    "description": "Create an empty at desired place on a tracked camera",
    "category": "Object",
}

import bpy
from mathutils import Vector


class FIRE_OT_custom(bpy.types.Operator):
    """Draw mesh between camera and empty"""  # Use this as a tooltip for menu items and buttons.
    bl_idname = "blenderbob.fire"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Fire"  # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        sel_objs = bpy.context.selected_objects
        first_sel_empty = None
        
        for obj in sel_objs:
            if obj.type == 'EMPTY':
                first_sel_empty = obj
                break
        return first_sel_empty is not None

    def execute(self, context):  # execute() is called when running the operator.
        maincam = bpy.context.scene.camera
        sel_objs = bpy.context.selected_objects
        first_sel_empty = None
        
        for obj in sel_objs:
            if obj.type == 'EMPTY':
                first_sel_empty = obj
                break
                
        if not first_sel_empty:
            raise RuntimeError('No empty selected')
        objs_to_delete = []
        
        for obj in bpy.context.scene.objects:
            if obj.name.startswith('CamToEmptyCurve'):
                objs_to_delete.append(obj)
                
        for object_to_delete in objs_to_delete:
            bpy.data.objects.remove(object_to_delete, do_unlink=True)
        new_curve = bpy.data.curves.new('path_curve', type='CURVE')
        new_curve.dimensions = '3D'
        path = new_curve.splines.new('POLY')

        path.points.add(2)
        path.points[0].co = Vector((0, 0, 0, 1))
        main_cam_translation = maincam.matrix_world.to_translation()
        vec_e = Vector((first_sel_empty.location.x, first_sel_empty.location.y, first_sel_empty.location.z, 1))
        vec_c = Vector((main_cam_translation.x, main_cam_translation.y, main_cam_translation.z, 1))
        path.points[1].co = (vec_e - vec_c) * 1000

        curve_obj = bpy.data.objects.new('CamToEmptyCurve', new_curve)
        curve_obj.location = main_cam_translation
        scene = bpy.context.scene
        scene.collection.objects.link(curve_obj)
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        bpy.context.view_layer.objects.active = first_sel_empty
        curve_obj.select_set(False)
        first_sel_empty.select_set(True)
        return {'FINISHED'}  # Lets Blender know the operator finished successfully.


class FIRE_PT_custom(bpy.types.Panel):
    """Creates a Sub-Panel in the Property Area of the 3D View"""
    bl_label = "Fire"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "FIRE_PT_custom"
    bl_category = "Tool"

    def draw(self, context):
        obj = context.object
        layout = self.layout
        row = layout.row()
        operator = row.operator(FIRE_OT_custom.bl_idname)
        # operator.enabled = obj.type == 'EMPTY'


def register():
    bpy.utils.register_class(FIRE_PT_custom)
    bpy.utils.register_class(FIRE_OT_custom)


def unregister():
    bpy.utils.unregister_class(FIRE_OT_custom)
    bpy.utils.unregister_class(FIRE_PT_custom)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
