from manim import *

class GaussianBlurExample(Scene):
    def construct(self):
        title = Text("Gaussian Blur")
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        image = ImageMobject("gaussian_blur_image.jpg").scale(0.8)
        self.play(FadeIn(image))
        self.wait(1)
        
        blurred_image = image.copy().apply_gaussian_blur(sigma=5.0)
        self.play(Transform(image, blurred_image))
        self.wait(2)