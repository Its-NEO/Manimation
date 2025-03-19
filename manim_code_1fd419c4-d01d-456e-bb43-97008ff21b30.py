from manim import *

class FixedErrorExample(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)
        
        sphere = Sphere(radius=1, resolution=(20, 20))
        sphere.set_color(BLUE)
        
        self.add(axes, sphere)
        self.wait()
        
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        
        formula = MathTex(r"S = 4\pi r^2")
        formula.to_corner(UL)
        self.add_fixed_in_frame_mobjects(formula)
        self.play(Write(formula))
        
        self.wait(2)

if __name__ == "__main__":
    scene = FixedErrorExample()
    scene.render()
