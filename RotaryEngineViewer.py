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
        self._orbit_radius = 0.01
        self._delay = 10  # ms


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


    def toggle_animation(self, delay=0.01):
        self.animating = not self.animating
        print(f"{'Starting' if self.animating else 'Stopping'} animation")

        if self.animating:
            self._angle = 0
            self._animation_step()


    def _animation_step(self):
        if not self.animating:
            return

        axis_vector = [0, 1, 0]
        degrees_per_step = 5
        crank_name = "crankshaft.stl"
        rotors = ["front_rotor.stl", "back_rotor.stl"]

        if crank_name in self.components:
            crank_mesh = self.components[crank_name].GetMapper().GetInputAsDataSet()
            center = crank_mesh.center
            transform = pv.transformations.axis_angle_rotation(axis_vector, degrees_per_step, point=center)
            crank_mesh.transform(transform, inplace=True)

        for rotor_name in rotors:
            if rotor_name in self.components and rotor_name in self.original_meshes:
                new_mesh = self.original_meshes[rotor_name].copy(deep=True)
                transform = pv.transformations.axis_angle_rotation(axis_vector, self._angle, point=center)
                new_mesh.transform(transform, inplace=True)

                # transform = pv.transformations.axis_angle_rotation(axis_vector, self._angle)
                # new_mesh.transform(transform, inplace=True)

                self.components[rotor_name].mapper.SetInputData(new_mesh)
                self.components[rotor_name].mapper.Update()

        self._angle += degrees_per_step
        self.plotter.render()

        QTimer.singleShot(self._delay, self._animation_step)


    def run(self):
        self.load_parts()
        self.add_checkboxes_with_labels()
        self.plotter.add_key_event("space", lambda: self.toggle_animation(delay=0.01))


if __name__ == "__main__":
    viewer = RotaryEngineViewer("./models")
    viewer.run()

    app = QApplication.instance()
    app.exec_()
