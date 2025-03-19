from manim import *

class DifferentiationVisualization(Scene):
    def construct(self):
        title = Tex("Differentiation").scale(1.5)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        func = MathTex("f(x) = x^2").next_to(title, DOWN)
        self.play(Write(func))
        self.wait(1)

        axes = Axes(
            x_range=[-3, 3], y_range=[-1, 10], 
            x_length=6, y_length=6,
            axis_config={"include_tip": True}
        )
        axes_labels = axes.get_axis_labels(x_label="x", y_label="f(x)")
        graph = axes.plot(lambda x: x**2, color=BLUE)
        
        self.play(Create(axes), Create(axes_labels))
        self.play(Create(graph))
        self.wait(1)

        x_tracker = ValueTracker(1)
        dx_tracker = ValueTracker(1)

        def get_secant_line():
            x = x_tracker.get_value()
            dx = dx_tracker.get_value()
            p1 = axes.c2p(x, x**2)
            p2 = axes.c2p(x + dx, (x + dx)**2)
            secant = Line(p1, p2, color=GREEN)
            return secant

        def get_dot():
            x = x_tracker.get_value()
            dot = Dot(axes.c2p(x, x**2), color=RED)
            return dot

        secant = always_redraw(get_secant_line)
        dot = always_redraw(get_dot)

        self.play(Create(dot))
        self.play(Create(secant))
        self.wait(1)

        self.play(dx_tracker.animate.set_value(0.001), run_time=3)
        self.wait(1)

        deriv_func = MathTex("f'(x) = 2x").next_to(func, DOWN)
        self.play(Write(deriv_func))
        self.wait(2)

        self.play(
            *[FadeOut(mob) for mob in [axes, axes_labels, graph, secant, dot, func, deriv_func]],
            title.animate.move_to(ORIGIN)
        )
        self.wait(1)
