from manim import *

class GaussianBlurExample(Scene):
    def construct(self):
        title = Text("Gaussian Blur")
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        image = ImageMobject("gaussian_blur_image.png").scale(0.8)
        self.play(FadeIn(image))
        self.wait(1)
        
        arrow = Arrow(LEFT, RIGHT)
        arrow.next_to(image, RIGHT)
        self.play(GrowArrow(arrow))
        
        blurred_image = image.copy().blur(5)
        blurred_image.next_to(arrow, RIGHT)
        self.play(FadeIn(blurred_image))
        
        self.wait(2)