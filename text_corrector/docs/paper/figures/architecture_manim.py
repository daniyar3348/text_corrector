from manim import *


class Architecture(Scene):
    def construct(self):
        self.camera.background_color = "#0f1420"

        title = Text("Turan — shared-encoder, two-pass corrector",
                     weight=BOLD).scale(0.55).to_edge(UP, buff=0.45)

        def node(ttl, sub, color, dashed=False):
            frame = RoundedRectangle(corner_radius=0.16, width=2.6, height=1.25,
                                     stroke_color=color, stroke_width=4,
                                     fill_color=color, fill_opacity=0.13)
            shape = DashedVMobject(frame, num_dashes=46) if dashed else frame
            if dashed:
                shape.set_stroke(color, width=4)
            t = Text(ttl, weight=BOLD).scale(0.28).set_color(WHITE)
            s = Text(sub).scale(0.21).set_color(GREY_B)
            lbl = VGroup(t, s).arrange(DOWN, buff=0.12)
            g = VGroup(shape, lbl)
            lbl.move_to(shape.get_center())
            return g

        n1 = node("Input", "BPE sub-tokens", GREY_BROWN)
        n2 = node("1  KazRoBERTa x6", "cls head -> KEEP/ERROR", BLUE)
        n3 = node("2  Candidates", "inverse u OSA / lexicon", GREY_BROWN)
        n4 = node("3  MLM head", "context re-rank (new)", BLUE, dashed=True)
        n5 = node("Corrected", "output sentence", GREEN)
        nodes = [n1, n2, n3, n4, n5]
        row = VGroup(*nodes).arrange(RIGHT, buff=0.5)
        row.scale_to_fit_width(13).next_to(title, DOWN, buff=0.65)

        arrows = [
            Arrow(nodes[k].get_right(), nodes[k + 1].get_left(),
                  buff=0.07, stroke_width=4, color=GREY_B,
                  max_tip_length_to_length_ratio=0.22)
            for k in range(len(nodes) - 1)
        ]

        enc = Text("Encoder layer x6:  multi-head self-attention  "
                   "softmax(Q.K^T / sqrt(d_k)).V   +   FFN(GELU)",
                   ).scale(0.3).set_color(GREY_A)
        f1 = Text("Re-rank:   s(c) = α·log P_MLM(c | context)  "
                  "+  β·(−d(c, w_i))  +  γ·log f(c)",
                  weight=BOLD).scale(0.34).set_color(WHITE)
        f2 = Text("c* = argmax s(c),    c ∈ C(w_i)",
                  weight=BOLD).scale(0.34).set_color(WHITE)
        panel = VGroup(enc, f1, f2).arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        panel.next_to(row, DOWN, buff=0.8)
        frame = SurroundingRectangle(panel, color=GREY, buff=0.35,
                                     corner_radius=0.12, stroke_width=2)

        legend = VGroup(
            VGroup(Square(0.22, color=BLUE, fill_opacity=0.13, stroke_width=3),
                   Text("neural (shared KazRoBERTa)").scale(0.22).set_color(GREY_B)
                   ).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.22, color=GREY_BROWN, fill_opacity=0.13, stroke_width=3),
                   Text("symbolic").scale(0.22).set_color(GREY_B)
                   ).arrange(RIGHT, buff=0.15),
        ).arrange(RIGHT, buff=0.7).next_to(frame, DOWN, buff=0.4)

        self.add(title, row, *arrows, frame, panel, legend)
