from manim import *

class MathScene(Scene):
    def construct(self):
        # Equation from the text: InfoNCE loss
        # InfoNCE loss can be mathematically divided \citep{wang2020understanding} into: 1) a representation \textit{alignment} term that minimizes the distance between normalized prediction and target embeddings, and 2) a \textit{uniformity} regularization term that pushes embeddings in a batch apart from each other
        
        # Simplified equation for visualization
        equation = MathTex(
            "L_{InfoNCE}",
            "=",
            "-",
            "\\sum_{i=1}^{N}",
            "\\log",
            "\\left( \\frac{e^{sim(\\hat{S}_Y^i, S_Y^i)}}{\\sum_{j=1}^{N} e^{sim(\\hat{S}_Y^i, S_Y^j)}} \\right)",
        )
        
        # Explanation elements
        alignment_term = MathTex(
            "\\text{Alignment Term: minimizes } d(\\hat{S}_Y, S_Y)"
        ).scale(0.7)
        
        uniformity_term = MathTex(
            "\\text{Uniformity Term: maximizes distance between embeddings}"
        ).scale(0.7)
        
        sim_explanation = MathTex(
            "sim(\\mathbf{x}, \\mathbf{y}) = \\frac{\\mathbf{x} \\cdot \\mathbf{y}}{\\|\\mathbf{x}\\| \\cdot \\|\\mathbf{y}\\|}"
        ).scale(0.6)
        
        # Initial state: Show the simplified equation
        equation.move_to(ORIGIN)
        self.play(Write(equation))
        self.wait(2)
        
        # Highlight alignment term
        self.play(Indicate(equation[3:7], color=YELLOW))
        self.play(Write(alignment_term.next_to(equation, DOWN, buff=0.5)))
        self.wait(1.5)
        self.play(FadeOut(alignment_term))
        
        # Highlight uniformity term
        self.play(Indicate(equation[7:], color=GREEN))
        self.play(Write(uniformity_term.next_to(equation, DOWN, buff=0.5)))
        self.wait(1.5)
        self.play(FadeOut(uniformity_term))
        
        # Explain similarity function
        self.play(Write(sim_explanation.next_to(equation, DOWN, buff=0.5)))
        self.wait(2)
        self.play(FadeOut(sim_explanation))
        
        # Final state: Show the full equation
        self.play(FadeOut(equation))
        equation = MathTex(
            "L_{InfoNCE}",
            "=",
            "-",
            "\\sum_{i=1}^{N}",
            "\\log",
            "\\left( \\frac{e^{sim(\\hat{S}_Y^i, S_Y^i)}}{\\sum_{j=1}^{N} e^{sim(\\hat{S}_Y^i, S_Y^j)}} \\right)",
        )
        equation.move_to(ORIGIN)
        self.play(Write(equation))
        self.wait(2)