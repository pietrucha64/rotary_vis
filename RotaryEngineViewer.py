import os
import numpy as np
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QTimer

class RotaryEngineViewer:
    def __init__(self, stl_folder):
        self.stl_folder = stl_folder
        self.plotter = BackgroundPlotter()
        self.components = {}
        self.animating = False
        self._animation_thread = None
        self.original_meshes = {}
        self.exploded = False
        self.angle = 0
        self.degrees_per_step = 10
        self._delay = 0  # ms


    def load_parts(self):
        for filename in os.listdir(self.stl_folder):
            if filename.endswith(".stl"):
                path = os.path.join(self.stl_folder, filename)
                mesh = pv.read(path)
                self.original_meshes[filename] = mesh.copy(deep=True)
                actor = self.plotter.add_mesh(mesh, name=filename, color="lightgrey", show_edges=False)
                self.components[filename] = actor


    def add_checkboxes_with_labels(self):
        checkbox_x = 10
        label_x = 40
        y_start = 10
        y_step = 30

        for i, name in enumerate(self.components):
            y = y_start + i * y_step

            def make_callback(n=name):
                def toggle(flag):
                    self.components[n].SetVisibility(flag)
                    self.plotter.render()
                return toggle

            self.plotter.add_checkbox_button_widget(
                make_callback(),
                value=True,
                position=(checkbox_x, y),
                size=20,
                color_on="green",
                color_off="red",
            )
            self.plotter.add_text(
                name.replace('.stl', ''),
                position=(label_x, y),
                font_size=10,
                name=f"label_{name}",
            )
        
    def add_animation_speed_slider(self):
        def set_animation_speed(value):
            self.degrees_per_step = value
        
        self.plotter.add_slider_widget(
            callback = set_animation_speed,
            rng = (1, 180),
            value = 10,
            title = "engine speed (deg/step)",
            pointa=(0.7, 0.1),
            pointb=(0.9, 0.1),
        )
    def add_explode_view_button(self):
        x = 300
        y = 10

        def toggle_explode(flag):
            self.exploded = flag
            step = 0.1  # Distance between components (adjust as needed)
            d = 0
            for i, (name, actor) in enumerate(self.components.items()):
                if name != "4crankshaft.stl" and name != "5middle_plate.stl":
                    d+=1
                mesh = actor.GetMapper().GetInputAsDataSet()
                offset = np.array([0, -step * d, 0]) if flag else np.array([0, step * d, 0])
                mesh.translate(offset, inplace=True)

                self.original_meshes[i] = mesh

            self.plotter.render()

        self.plotter.add_checkbox_button_widget(
            callback=toggle_explode,
            value=False,
            position=(x, y),
            size=20,
            color_on="green",
            color_off="red",
        )
        self.plotter.add_text("Explode View", position=(x + 30, y), font_size=10)


    def toggle_animation(self):
        self.animating = not self.animating
        print(f"{'Starting' if self.animating else 'Stopping'} animation")

        if self.animating:
            self.animation_step()


    def animation_step(self):
        if not self.animating:
            return

        axis_vector = [0, 1, 0]
        crank_name = "4crankshaft.stl"
        rotors = ["6front_rotor.stl", "2back_rotor.stl"]

        if crank_name in self.components:
            crank_mesh = self.components[crank_name].GetMapper().GetInputAsDataSet()
            center = crank_mesh.center
            transform = pv.transformations.axis_angle_rotation(axis_vector, self.degrees_per_step, point=center)
            crank_mesh.transform(transform, inplace=True)

        for rotor_name in rotors:
            if rotor_name in self.components and rotor_name in self.original_meshes:
                rotor_actor = self.components[rotor_name]
                mesh = rotor_actor.GetMapper().GetInputAsDataSet()

                original = self.original_meshes[rotor_name]
                mesh.points[:] = original.points.copy()

                t1 = pv.transformations.axis_angle_rotation(axis_vector, self.angle, point=center)
                mesh.transform(t1, inplace=True)

                rotor_center = mesh.center_of_mass()

                t2 = pv.transformations.axis_angle_rotation(axis_vector, -self.angle * 2 / 3, point=rotor_center)
                mesh.transform(t2, inplace=True)

        self.angle += self.degrees_per_step
        self.plotter.render()

        QTimer.singleShot(self._delay, self.animation_step)


    def run(self):
        self.load_parts()
        self.add_checkboxes_with_labels()
        self.add_animation_speed_slider()
        self.add_explode_view_button()
        self.plotter.add_key_event("space", lambda: self.toggle_animation())


viewer = RotaryEngineViewer("./models")
viewer.run()

app = QApplication.instance()
app.exec_()
