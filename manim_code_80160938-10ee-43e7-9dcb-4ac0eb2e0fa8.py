from manim import *

class IntegrationVisualization(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-1, 5],
            y_range=[-1, 5],
            axis_config={"color": BLUE},
        )
        
        graph = axes.plot(lambda x: x**2, color=YELLOW)
        
        area = axes.get_area(graph, x_range=(0, 2), color=GREEN, opacity=0.5)
        
        title = Text("Integration").scale(0.8).to_edge(UP)
        
        self.play(Write(title))
        self.play(Create(axes), Create(graph))
        
        integral_text = MathTex(r"\int_0^2 x^2 dx").next_to(title, DOWN)
        self.play(Write(integral_text))
        
        self.play(FadeIn(area))
        
        riemann_rects = axes.get_riemann_rectangles(
            graph, x_range=(0, 2), dx=0.2, color=PURPLE, fill_opacity=0.5
        )
        self.play(Create(riemann_rects))
        
        for dx in [0.1, 0.05, 0.01]:
            new_rects = axes.get_riemann_rectangles(
                graph, x_range=(0, 2), dx=dx, color=PURPLE, fill_opacity=0.5
            )
            self.play(Transform(riemann_rects, new_rects))
        
        result = MathTex(r"= \frac{8}{3}").next_to(integral_text, RIGHT)
        self.play(Write(result))
        
        area_value = Text("Area ≈ 2.67").scale(0.8).next_to(result, DOWN)
        self.play(Write(area_value))
        
        self.wait(2)