
## Lern-Mechanismus (autopoietisch)

Das Skript im Projektstamm liest `hero-archive/experiences.csv` ein, in dem jede Zeile eine
binäre Konfiguration (`x_bits`) und einen numerischen Score (`score`) enthält.

- `x_bits` ist ein Binärstring der Länge n (z.B. `11000000`).
- `score` ist ein Reward/Erfolgsmaß (positiv = gut, negativ = schlecht).

Für jede Erfahrung wird die Q-Matrix wie folgt aktualisiert:

- Bildung des äußeren Produkts `x x^T` als Muster für aktive Variablenpaare.
- Update-Regel: `Q := Q - alpha * score * (x x^T)` mit Lernrate `alpha`.
  - Gute Konfigurationen (score > 0) senken die Kosten der beteiligten Paare.
  - Schlechte Konfigurationen (score < 0) erhöhen die Kosten.

Die resultierende Matrix wird als:

- `quantum/qubo_learned.npy`
- `quantum/qubo_learned.csv`

gespeichert und dient als autopoietisch gelernte Quanten-/QUBO-Matrix auf Basis der Archivdaten.
