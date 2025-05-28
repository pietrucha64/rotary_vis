import os
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
        self._angle = 0
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
        #TODO: slider ktory zmienia wartosc degrees_per_step
        # ewentualnie może dodawać self.delay gdy degrees_per step jest wystarczająco niskie
        return

    def toggle_animation(self):
        self.animating = not self.animating
        print(f"{'Starting' if self.animating else 'Stopping'} animation")

        if self.animating:
            self._animation_step()


    def _animation_step(self):
        if not self.animating:
            return

        axis_vector = [0, 1, 0]
        degrees_per_step = 10
        crank_name = "crankshaft.stl"
        rotors = ["front_rotor.stl", "back_rotor.stl"]

        if crank_name in self.components:
            crank_mesh = self.components[crank_name].GetMapper().GetInputAsDataSet()
            center = crank_mesh.center
            transform = pv.transformations.axis_angle_rotation(axis_vector, degrees_per_step, point=center)
            crank_mesh.transform(transform, inplace=True)

        for rotor_name in rotors:
            if rotor_name in self.components and rotor_name in self.original_meshes:
                rotor_actor = self.components[rotor_name]
                mesh = rotor_actor.GetMapper().GetInputAsDataSet()

                # Reset points from original
                original = self.original_meshes[rotor_name]
                mesh.points[:] = original.points.copy()

                # Apply transforms
                t1 = pv.transformations.axis_angle_rotation(axis_vector, self._angle, point=center)
                mesh.transform(t1, inplace=True)

                rotor_center = mesh.center_of_mass()

                t2 = pv.transformations.axis_angle_rotation(axis_vector, -self._angle * 2 / 3, point=rotor_center)
                mesh.transform(t2, inplace=True)

        self._angle += degrees_per_step
        self.plotter.render()

        QTimer.singleShot(self._delay, self._animation_step)


    def run(self):
        self.load_parts()
        self.add_checkboxes_with_labels()
        self.plotter.add_key_event("space", lambda: self.toggle_animation())


viewer = RotaryEngineViewer("./models")
viewer.run()

app = QApplication.instance()
app.exec_()
