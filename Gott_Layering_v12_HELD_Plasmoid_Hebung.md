**Gott Layering v12 – Der HELD bespielt den GOTT-Layer**
**Hebung vom gebundenen fluiden Raum in den plasmoiden Raum**
**(formal-mathematisch, heroisiert)**

> **Stand:** v12.0.0 · Fortschreibung von [`Gott_Layering_v11_TopDown_Herleitung.md`](Gott_Layering_v11_TopDown_Herleitung.md)
> **Modul:** [`fusion_hero_os/core/plasmoid_lift.py`](fusion_hero_os/core/plasmoid_lift.py) · **Beweise:** `tests/test_plasmoid_lift.py`

---

## 0. Die Frage

v11 konstruiert das Gott Layering strikt **top-down** als kontrahierende Kette

\[
L_6^\omega \twoheadrightarrow L_5 \twoheadrightarrow L_4 \twoheadrightarrow L_3 \twoheadrightarrow L_2 \twoheadrightarrow L_1 \twoheadrightarrow L_0 .
\]

Damit ist gesagt, **woher** Struktur kommt. Nicht gesagt ist, **was der Held darin tut**.
Denn Axiom 1 (Top-Down) verbietet ihm, aus \(L_n\) heraus \(L_{n+1}\) zu ändern. Ein Held,
der nichts ändern darf, wäre Dekoration.

Die Auflösung ist keine Aufweichung des Axioms, sondern seine genaue Lesart:

> Der Held ändert die von oben gesetzte **Invariante** nicht.
> Er senkt die **Energie** *innerhalb* der Fläche, die sie aufspannt —
> bis der Zustand **kraftfrei** ist.

Das ist die Hebung: kein Aufstand gegen den Layer, sondern Relaxation im Inneren einer
Bindung. Der Held *bespielt* den Gott-Layer, er stürzt ihn nicht.

---

## 1. Die beiden Räume

Sei \(V=\mathbb{R}^n\), \(S=S^{\mathsf T}\) invertierbar — der diskrete Curl-Operator.
(Der Curl ist auf divergenzfreien Feldern selbstadjungiert; das ist das
Chandrasekhar-Kendall-Setting.) Für ein Feld \(x\) mit Potential \(A=S^{-1}x\):

| Größe | Definition | Rolle im Layering |
|---|---|---|
| Energie | \(W(x)=\tfrac12\langle x,x\rangle\) | **was der Held senkt** |
| Helizität | \(H(x)=\langle x,S^{-1}x\rangle\) | **Layer-\(\omega\)-Invariante — unantastbar** |
| Bindung | \(r(x)=Sx-\rho(x)\,x,\quad \rho(x)=\frac{\langle x,Sx\rangle}{\langle x,x\rangle}\) | **was gehoben wird** |

Damit:

\[
\underbrace{\mathfrak{F}_h:=\{x: H(x)=h,\ r(x)\neq 0\}}_{\textbf{gebundener fluider Raum}}
\qquad
\underbrace{\mathfrak{P}:=\{x\neq 0:\ Sx=\alpha x\}}_{\textbf{plasmoider Raum}}
\]

Der plasmoide Raum ist genau die **kraftfreie** (force-free, Beltrami-) Menge \(r(x)=0\).
Der fluide Raum ist gebunden, weil in ihm eine Restspannung \(r(x)\neq 0\) steht.

Die **Hebung** ist der Operator

\[
\Lambda_h:\ \mathfrak{F}_h \longrightarrow \mathfrak{P},
\]

der helizitätserhaltende Energieabstieg.

---

## 2. Die Sätze

### SATZ P1 — Kritisch heißt kraftfrei (Woltjer, diskret)

Für \(x\neq 0\) ist \(x\) genau dann kritischer Punkt von \(W\) eingeschränkt auf
\(\{y:H(y)=H(x)\}\), wenn \(Sx=\alpha x\).

*Beweis.* \(\nabla W(x)=x\), \(\nabla H(x)=2S^{-1}x\neq 0\) für \(x\neq 0\) — die
Niveaufläche ist regulär, Lagrange anwendbar. Kritisch \(\iff \exists\lambda: x=2\lambda S^{-1}x\).
Anwenden von \(S\): \(Sx=2\lambda x\). Umgekehrt liefert \(Sx=\alpha x\) sofort
\(\nabla H(x)=\tfrac{2}{\alpha}x \parallel \nabla W(x)\). ∎

**Layer-Lesart:** Ein Zustand ist genau dann *fertig*, wenn keine Kraft mehr an ihm zieht.
Nicht der Wille beendet die Hebung, sondern die Kraftfreiheit.

### SATZ P2 — Die Taylor-Schranke

Sei \(\alpha_g\) der betragskleinste Eigenwert mit \(\operatorname{sign}(\alpha_g)=\operatorname{sign}(h)\).
Dann gilt für **alle** \(x\in V\):

\[
2W(x)\ \ge\ \alpha_g\,H(x),
\]

mit Gleichheit genau dann, wenn \(x\) im Eigenraum zu \(\alpha_g\) liegt.

*Beweis.* Orthonormalbasis aus Eigenvektoren, \(x=\sum c_iu_i\). Dann
\(2W=\sum c_i^2\), \(H=\sum c_i^2/\alpha_i\), also

\[
2W(x)-\alpha_g H(x)=\sum_i c_i^2\Bigl(1-\frac{\alpha_g}{\alpha_i}\Bigr).
\]

Bei gleichem Vorzeichen ist \(|\alpha_i|\ge|\alpha_g|\), also \(\alpha_g/\alpha_i\in(0,1]\)
und der Summand \(\ge 0\); bei verschiedenem Vorzeichen ist \(\alpha_g/\alpha_i<0\),
also der Summand \(>1\cdot c_i^2\ge0\). Gleichheit erzwingt \(c_i=0\) für alle
\(\alpha_i\neq\alpha_g\). ∎

**Layer-Lesart:** Es gibt einen **Boden**. Der Held kann nicht beliebig tief sinken —
bei fester Invariante ist \(W\ge \alpha_g h/2\), und dieser Wert wird exakt erreicht.
Das ist der Fixpunkt im heroischen Raum, kein asymptotisches Versprechen.

### SATZ P3 — Die Hebung selbst

Der Fluss \(\dot x=-P(x)\nabla W(x)\), \(P(x)\) die Projektion auf \((S^{-1}x)^{\perp}\), erfüllt:

| | Aussage | Bedeutung |
|---|---|---|
| (a) | \(\dfrac{dH}{dt}=0\) | **Axiom 1 gewahrt** — die Layer-\(\omega\)-Invariante bleibt exakt |
| (b) | \(\dfrac{dW}{dt}\le 0\) | **Axiom 2 erfüllt** — strikte Kontraktion in der Energie |
| (c) | \(\dfrac{dW}{dt}=0\iff Sx=\alpha x\) | **Gleichgewichte = plasmoider Raum** |

*Beweis.* Mit \(g:=S^{-1}x\) ist \(\dot x=-\bigl(x-\tfrac{\langle x,g\rangle}{\langle g,g\rangle}g\bigr)\).
(a) \(\dot H=2\langle g,\dot x\rangle=-2\bigl(\langle g,x\rangle-\tfrac{\langle x,g\rangle}{\langle g,g\rangle}\langle g,g\rangle\bigr)=0\).
(b) \(\dot W=\langle x,\dot x\rangle=-\bigl(\|x\|^2-\tfrac{\langle x,g\rangle^2}{\|g\|^2}\bigr)\le 0\) (Cauchy-Schwarz).
(c) Gleichheit in Cauchy-Schwarz \(\iff x\parallel S^{-1}x \iff Sx=\alpha x\). ∎

**Das ist die formale Fassung des Satzes „der Held bespielt den Gott-Layer".**
(a) sagt: er greift nicht nach oben. (b) sagt: er wirkt trotzdem. (c) sagt: er kommt an.

---

## 3. Einordnung in die Layer-Kette

| v11-Struktur | v12-Entsprechung |
|---|---|
| \(L_6^\omega\) MasterSeed | die Invariante \(H\) — gesetzt, nicht verhandelt |
| Kontraktionsaxiom \(d_I\) fallend | \(dW/dt\le0\), SATZ P3(b) |
| Internalisierungsoperator \(C\) | die Hebung \(\Lambda_h\) selbst |
| \(L_0\) Immutable Foundation | \(\mathfrak{P}\cap\{H=h\}\): \(r=0\), keine Kraft zieht weiter |
| Invarianzaxiom | Reprojektion hält \(H\) bitgenau (Drift \(\sim10^{-15}\)) |

Die Kette von v11 beschreibt, **woher** die Bindung kommt.
v12 beschreibt, **was in ihr geschieht**. Beides zusammen ist erst der Layer.

**Quantisierung.** \(\mathfrak{P}\) ist die Vereinigung der Eigenräume — eine *diskrete*
Menge von Zuständen. Die Hebung landet also nie „irgendwo", sondern immer auf einem
Spektralwert \(\alpha\). Der plasmoide Raum ist gequantelt; das ist keine Deutung,
sondern SATZ P1.

---

## 4. Geltung (ehrlich)

Nach Repo-Konvention (vgl. [`proof_registry.yaml`](proof_registry.yaml), [`docs/ops/J_SPACES_HIGGS.md`](docs/ops/J_SPACES_HIGGS.md)):

| Aussage | Status |
|---|---|
| P1, P2, P3(a)(b)(c) | **SATZ** — bewiesen oben, verifiziert in Sandbox + pytest |
| Hebung erreicht den **Grundzustand** \(\alpha_g\) | **GENERISCH, kein Satz** — s. u. |
| Deutung als Plasma / Plasmoid | **MODELL / operative Analogie** |

**Zur Einschränkung.** Die Gleichgewichtsmenge ist \(\mathfrak{P}\) — *alle* Eigenräume,
nicht nur der Grundzustand. Startet man exakt in einem höheren Eigenraum, bleibt die
Hebung dort stehen, strikt über der Taylor-Schranke. Das ist als Negativ-Referenz
in `test_p4_is_not_a_universal_law_all_eigenspaces_are_equilibria` verankert.

Im Sweep (Seed 7, 4000 Ziehungen, \(n\in[3,9)\), Spektrum \(\pm[0.5,4.0]\), Budget 4000
Schritte) waren 2492 Läufe nutzbar; **4** davon landeten nicht auf der Schranke. In allen
vier Fällen war der Abbruchgrund `budget_exhausted` bei kleiner **Spektrallücke**
(\(6\cdot10^{-4}\) bis \(1{,}0\cdot10^{-2}\)) — und mit 300 000 Schritten erreichten alle
vier den Grundzustand auf \(\le 1{,}8\cdot10^{-12}\), mit Restbindung \(\sim10^{-8}\).

Es gibt also **keinen falschen Fixpunkt** — nur eine lückenabhängige Rate, wie bei jedem
Gradienten-/Potenzverfahren. Genau so und nicht stärker wird es behauptet.

Reproduktion:

```python
# Seed 7, Parameter wie oben; misst rel = |2W - alpha_g h| / max(1, |alpha_g h|)
pl = PlasmoidLift.from_spectrum(spektrum, rng=rng)
res = pl.lift(x0, max_steps=4000)     # -> reason == "budget_exhausted" bei kleiner Lücke
big = pl.lift(x0, max_steps=300_000)  # -> erreicht den Grundzustand
```

**Kein Physik-Claim.** Hier wird kein Plasma simuliert. Gerechnet wird exakt die obige
lineare Algebra. Die Namen *Helizität*, *kraftfrei*, *Taylor-Zustand* sind die korrekten
Termini der diskreten Woltjer-Taylor-Relaxation und werden als Analogie geführt — analog
zur Konvention „kein physisches Higgs im Gehirn" in J_SPACES_HIGGS.

---

## 5. Ausführen

```bash
python -m fusion_hero_os.core.plasmoid_lift --verify   # Sandbox, echte Asserts
python -m fusion_hero_os.core.plasmoid_lift --demo     # eine Hebung als JSON
python -m pytest tests/test_plasmoid_lift.py -q
```

---

## 6. Schluss

Der gebundene fluide Raum ist kein Mangel — er ist der Ort, an dem der Held überhaupt
etwas tun kann. Die Bindung \(r(x)\) ist die Spannung, aus der die Bewegung kommt; die
Invariante \(H\) ist das, was ihm von oben gegeben und nicht zur Disposition gestellt ist.

Erhoben wird nicht *gegen* die Bindung, sondern *in* ihr, bis keine Kraft mehr zieht.
Was dann steht, ist kraftfrei, gequantelt und energetisch minimal:
der plasmoide Zustand.

\[
\Lambda_h:\ \mathfrak{F}_h\ \longrightarrow\ \mathfrak{P},
\qquad
\dot H=0,\quad \dot W\le 0,\quad \dot W=0\iff Sx=\alpha x .
\]

Es beginnt nicht mit einem Abschluss, sondern mit einem Fixed-Point im heroischen Raum:
\(|\Psi\rangle_h \to |\omega\rangle\).

#FusionHeroOS #GottLayering #PlasmoidLift #TopDownPropagation #Eudaimonismus #HeroicCore
