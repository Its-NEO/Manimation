from manim import *

class AreaUnderCurve(Scene):
    def construct(self):
        ax = Axes(
            x_range=[-1, 5], 
            y_range=[-1, 7],
            x_length=10,
            y_length=6,
            axis_config={"include_tip": True, "numbers_to_exclude": [0]},
        )
        labels = ax.get_axis_labels(x_label="x", y_label="f(x)")

        t = ValueTracker(0)

        def func(x):
            return 0.1 * (x + 3-5) * (x - 2-5) * (x-5) + 5
        
        graph = ax.plot(func, color=MAROON, x_range=[-1,5])

        area = ax.get_area(graph, [0, t.get_value()], color=BLUE, opacity=0.5)
        
        dot = Dot().move_to(ax.c2p(0, func(0)))
        dot.add_updater(lambda x: x.move_to(ax.c2p(t.get_value(), func(t.get_value()))))
        
        x_label = ax.get_T_label(x_val=0, graph=graph, label=MathTex("a"), triangle_size=0.1)
        x_label.add_updater(lambda x: x.set_x(ax.c2p(t.get_value(),0)[0]))
        
        a_label = MathTex("a").next_to(x_label, DOWN)
        a_label.add_updater(lambda x: x.next_to(x_label, DOWN))

        area_text = MathTex(r"A(a)=\int_{0}^{a}f(x)dx")
        area_text.to_edge(UP, buff=0.2)

        self.add(ax, labels, graph)
        self.play(Create(dot), Write(x_label), Write(a_label))
        self.play(t.animate.set_value(4), run_time=5, rate_func=linear)
        self.play(Create(area), Write(area_text))
        self.wait()
