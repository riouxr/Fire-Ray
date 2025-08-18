bl_info = {
    "name": "Reality Capture & Fire Ray tools",
    "author": "ChatGPT + User",
    "version": (2, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > Tool tab",
    "description": "Photogrammetry camera setup (background + markers) and Fire ray tool",
    "category": "3D View",
}

import bpy
import os
from mathutils import Vector

# -------------------------------------------------------------------
# Fire Ray onto Empty
# -------------------------------------------------------------------

class FIRE_OT_custom(bpy.types.Operator):
    """Draws straight curve between camera and empty"""
    bl_idname = "blenderbob.fire"
    bl_label = "Select Empty and Fire!"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sel_objs = context.selected_objects
        return any(obj.type == 'EMPTY' for obj in sel_objs)

    def execute(self, context):
        maincam = context.scene.camera
        sel_objs = context.selected_objects
        first_sel_empty = next((obj for obj in sel_objs if obj.type == 'EMPTY'), None)

        if not first_sel_empty:
            raise RuntimeError('No empty selected')

        # Remove old curves
        for obj in list(context.scene.objects):
            if obj.name.startswith('CamToEmptyCurve'):
                bpy.data.objects.remove(obj, do_unlink=True)

        new_curve = bpy.data.curves.new('path_curve', type='CURVE')
        new_curve.dimensions = '3D'
        path = new_curve.splines.new('POLY')

        path.points.add(2)
        path.points[0].co = Vector((0, 0, 0, 1))
        main_cam_translation = maincam.matrix_world.to_translation()
        vec_e = Vector((*first_sel_empty.location, 1))
        vec_c = Vector((*main_cam_translation, 1))
        path.points[1].co = (vec_e - vec_c) * 1000

        curve_obj = bpy.data.objects.new('CamToEmptyCurve', new_curve)
        curve_obj.location = main_cam_translation
        context.scene.collection.objects.link(curve_obj)
        context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        context.view_layer.objects.active = first_sel_empty
        curve_obj.select_set(False)
        first_sel_empty.select_set(True)
        return {'FINISHED'}


class CREATE_EMPTY_OT_custom(bpy.types.Operator):
    """Creates an empty in the scene"""
    bl_idname = "blenderbob.create_empty"
    bl_label = "Create Empty"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        return {'FINISHED'}

# -------------------------------------------------------------------
# Photogrammetry Setup
# -------------------------------------------------------------------

class VIEW3D_OT_photogrammetry_setup(bpy.types.Operator):
    """Assign BG images to cameras and mark them sequentially"""
    bl_idname = "view3d.photogrammetry_setup"
    bl_label = "Setup"
    bl_options = {'REGISTER', 'UNDO'}

    frame_step: bpy.props.IntProperty(
        name="Frame Step",
        description="Frames between each camera marker",
        default=1,
        min=1,
        soft_max=120
    )

    def execute(self, context):
        scene = context.scene
        start_frame = scene.frame_current
        blend_dir = os.path.dirname(bpy.data.filepath)
        if not blend_dir:
            self.report({'ERROR'}, "Blend file must be saved first.")
            return {'CANCELLED'}

        cams = [obj for obj in scene.objects if obj.type == 'CAMERA' and obj.name.lower().endswith(".png")]
        if not cams:
            self.report({'WARNING'}, "No cameras with '.png' in name found.")
            return {'CANCELLED'}

        frame = start_frame

        for cam in cams:
            # Step 1: background image
            image_path = os.path.join(blend_dir, cam.name)
            if os.path.exists(image_path):
                img = bpy.data.images.load(image_path, check_existing=True)
                cam.data.show_background_images = True
                if not cam.data.background_images:
                    bg = cam.data.background_images.new()
                else:
                    bg = cam.data.background_images[0]
                bg.image = img

            # Step 2: marker + bind
            m = scene.timeline_markers.new(name=cam.name, frame=frame)
            try:
                m.camera = cam
            except Exception:
                for mk in scene.timeline_markers:
                    mk.select = False
                m.select = True
                context.view_layer.objects.active = cam
                bpy.ops.marker.bind()

            frame += self.frame_step

        scene.camera = cams[0]
        self.report({'INFO'}, f"Setup complete for {len(cams)} cameras.")
        return {'FINISHED'}

# -------------------------------------------------------------------
# Panel
# -------------------------------------------------------------------

class FIRE_PT_custom(bpy.types.Panel):
    bl_label = "Reality Capture & Fire Setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "FIRE_PT_custom"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        # Photogrammetry first
        layout.label(text="Reality Capture Setup")
        layout.operator("view3d.photogrammetry_setup", icon="CAMERA_DATA")

        layout.separator()

        # Fire Ray section
        layout.label(text="Fire Ray onto Empty")
        layout.operator(CREATE_EMPTY_OT_custom.bl_idname, icon="EMPTY_AXIS")
        layout.operator(FIRE_OT_custom.bl_idname, icon="FORWARD")

# -------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------

classes = (
    FIRE_OT_custom,
    CREATE_EMPTY_OT_custom,
    VIEW3D_OT_photogrammetry_setup,
    FIRE_PT_custom,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
