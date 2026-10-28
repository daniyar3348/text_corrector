from manim import *

KK = "Arial"   # has Kazakh Cyrillic glyphs (қ ә ң ұ ү ғ і ө һ)


class KazakhCorrection(Scene):
    def construct(self):
        self.camera.background_color = "#000000"

        corr = ["Бул", "маселе", "оте", "манызды", "болып", "тур"]
        gold = ["Бұл", "мәселе", "өте", "маңызды", "болып", "тұр"]
        err = [i for i in range(len(corr)) if corr[i] != gold[i]]

        title = Text("Correcting Kazakh «ka2ru» typos", font=KK, weight=BOLD,
                     font_size=40).to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.4)
        self.wait(0.3)

        cwords = [Text(w, font=KK, font_size=46) for w in corr]
        crow = VGroup(*cwords).arrange(RIGHT, buff=0.5).move_to(ORIGIN + UP * 0.3)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.25) for w in cwords],
                              lag_ratio=0.15), run_time=1.8)
        cap = Text("Kazakh letters typed as Russian look-alikes",
                   font=KK, font_size=24, color=GREY_B).next_to(crow, DOWN, buff=0.55)
        self.play(FadeIn(cap))
        self.wait(0.5)

        det = Text("1 · detector  →  KEEP / ERROR", font=KK, font_size=28,
                   color=BLUE_B).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(det))
        anims = []
        for i, w in enumerate(cwords):
            col = GREEN if i not in err else RED
            anims.append(AnimationGroup(Indicate(w, color=col, scale_factor=1.18),
                                        w.animate.set_color(col)))
        self.play(LaggedStart(*anims, lag_ratio=0.25), run_time=3.0)
        self.wait(0.6)

        # focus on one ERROR word: манызды -> маңызды
        j = 3
        self.play(FadeOut(cap), FadeOut(det))
        fcopy = cwords[j].copy()
        self.play(fcopy.animate.scale(1.7).move_to(UP * 1.4),
                  crow.animate.set_opacity(0.3))

        cand_str = ["маңызды", "маңыз", "манызда"]
        cands = VGroup(*[Text(c, font=KK, font_size=32, color=GREY_B) for c in cand_str]
                       ).arrange(DOWN, buff=0.32).next_to(fcopy, DOWN, buff=0.7)
        clbl = Text("2 · candidates  (inverse subs ∪ OSA)", font=KK,
                    font_size=24, color=GREY_B).next_to(cands, DOWN, buff=0.45)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.25) for c in cands],
                              lag_ratio=0.2), FadeIn(clbl), run_time=1.6)
        self.wait(0.4)

        rlbl = Text("3 · context re-rank  →  pick best", font=KK,
                    font_size=24, color=BLUE_B).move_to(clbl)
        box = SurroundingRectangle(cands[0], color=GREEN, buff=0.12, corner_radius=0.08)
        self.play(Transform(clbl, rlbl), Create(box),
                  cands[0].animate.set_color(GREEN))
        self.wait(0.5)

        target = Text("маңызды", font=KK, font_size=int(46 * 1.7),
                      color=GREEN).move_to(fcopy)
        self.play(ReplacementTransform(fcopy, target),
                  FadeOut(box), FadeOut(cands), FadeOut(clbl))
        self.play(Flash(target, color=GREEN, line_length=0.3))
        self.wait(0.4)

        # correct the whole sentence
        self.play(FadeOut(target), crow.animate.set_opacity(1.0))
        gwords = [Text(g, font=KK, font_size=46, color=GREEN) for g in gold]
        grow = VGroup(*gwords).arrange(RIGHT, buff=0.5).move_to(crow)
        self.play(LaggedStart(*[ReplacementTransform(cwords[i], gwords[i])
                                for i in range(len(corr))], lag_ratio=0.12),
                  run_time=2.6)
        self.wait(0.5)

        end = Text("detect  →  generate  →  re-rank", font=KK, font_size=30,
                   color=GREY_B).next_to(grow, DOWN, buff=0.7)
        self.play(Write(end), FadeOut(title), run_time=1.4)
        self.wait(1.8)
