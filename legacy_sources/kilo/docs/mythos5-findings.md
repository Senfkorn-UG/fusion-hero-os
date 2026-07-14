# Claude Mythos 5 & Fable 5 – Recherche-Findings

> **TL;DR** – Mythos 5 und Fable 5 sind dasselbe zugrunde liegende Modell
> (Anthropic, angekündigt am **9. Juni 2026**). **Fable 5** ist die für die
> Allgemeinheit freigegebene Variante *mit* zusätzlichen Sicherheits-Klassifikatoren;
> **Mythos 5** ist dieselbe Basis, aber mit *aufgehobenen* Safeguards in
> bestimmten Bereichen – nur für **freigegebene Organisationen** (v. a. über
> „Project Glasswing" mit der US-Regierung). Alle belastbaren Erkenntnisse unten
> stammen aus **öffentlichen** Quellen; siehe [Methodik](#methodik--quellenlage).

---

## Methodik & Quellenlage

Gesucht wurde „analog ergänzend" über verfügbare Konnektoren, intern wie extern:

- **Extern (Web):** Anthropic-Newsroom, Anthropic Platform Docs, CNBC,
  TechCrunch, MacRumors, AWS-Blog. → Reichhaltige, konsistente öffentliche
  Faktenlage (unten).
- **Intern (deine verbundenen Dienste):** Google Drive (`fullText contains 'Mythos'`)
  und Notion (samt dessen Konnektoren zu Slack/GitHub/Jira/Teams/SharePoint/Linear).
  → **Nichts Relevantes.** Treffer waren ausschließlich False Positives: dein
  Dissertationsmanuskript „Der heroische Mensch" (das Wort „selbst-*mytholog*isierend"
  matcht auf „Mythos") und eine unverbundene Notiz „Computer Science: Vorlesung 5".
- **Wichtige Einordnung:** Ich habe **keinen** privilegierten Zugriff auf
  Anthropic-interne Daten und erfinde nichts. Dieses Dokument fasst
  ausschließlich öffentlich verfügbare Informationen zusammen. Es enthält keine
  Zugangs-, Umgehungs- oder Betriebsanleitungen für Mythos 5.

---

## 1. Was Fable 5 und Mythos 5 sind

- **Claude Fable 5:** ein „Mythos-class"-Modell, das Anthropic „für den
  allgemeinen Gebrauch sicher gemacht" hat. Übertrifft nach eigener Angabe alle
  bisher allgemein verfügbaren Modelle, mit State-of-the-Art-Ergebnissen auf
  nahezu allen getesteten Benchmarks. Je länger/komplexer die Aufgabe, desto
  größer der Vorsprung.
- **Claude Mythos 5:** **dasselbe** zugrunde liegende Modell wie Fable 5 – aber
  mit in bestimmten Domänen **aufgehobenen** Safeguards, nur für vertrauenswürdige
  Partner/Organisationen. Laut Anthropic „die stärksten Cybersecurity-Fähigkeiten
  aller Modelle weltweit".

## 2. Der Kernunterschied: die Safeguards

Fable 5 setzt drei klassifikatorbasierte Schutzmechanismen ein, die sensible
Anfragen an **Claude Opus 4.8** umleiten:

1. **Cybersecurity** – blockiert offensive Cyber-Aufgaben und Exploit-/Schwachstellen-Ausnutzung.
2. **Biologie & Chemie** – verhindert Antworten zu Dual-Use-Bioforschung.
3. **Distillation** – blockiert Versuche, Modellfähigkeiten für konkurrierende
   Systeme abzuziehen.

Weitere öffentlich genannte Punkte:

- Safeguards greifen „in weniger als 5 % der Sessions" (Durchschnitt).
- Externes Bug-Bounty über 1.000+ Stunden ohne „universellen Contributor" (Stand Launch).
- **30-Tage-Datenaufbewahrung** für Mythos-class-Modelle, um neuartige Angriffe
  zu erkennen.
- Mythos 5 = genau diese Safeguards in bestimmten Bereichen entfernt, deshalb
  Beschränkung auf freigegebene Organisationen.

## 3. Fähigkeiten (öffentlich genannte Beispiele)

- Verdichtete „Monate an Engineering in Tage" bei der Migration von Stripes
  Ruby-Codebasis.
- Höchster Score in Cognitions „FrontierCode"-Evaluation für produktionsreifen Code.
- State-of-the-Art-Vision, u. a. Rekonstruktion von Web-Apps aus Screenshots.
- Fokus über Millionen von Tokens (Long-Context-Memory).
- Forschungsnahes Reasoning in Molekularbiologie und Genomik.

## 4. Verfügbarkeit & Zugang

- **Fable 5:** allgemein verfügbar seit **9. Juni 2026** – über Claude API und
  Consumer-Abos (gestaffelter Rollout für Abo-Pläne bis 22. Juni).
- **Mythos 5:** beschränkt auf **Project-Glasswing-Partner** (Cybersecurity) und
  Infrastruktur-Anbieter; zunächst „in Zusammenarbeit mit der US-Regierung" als
  Upgrade zu „Claude Mythos Preview" ausgerollt. Soll bei der Absicherung
  kritischer Software geholfen haben.
- **Bio-Forschende:** sollen über ein geplantes „trusted access program" Zugang
  zu Fable 5 mit *entfernten* Bio-Safeguards erhalten.
- Ein breiteres „trusted access program" ist für die Zukunft angekündigt.

## 5. Preise

- **10 USD / Mio. Input-Tokens** und **50 USD / Mio. Output-Tokens** – laut
  Anthropic „weniger als die Hälfte" des Preises von Claude Mythos Preview.
  (Gilt für beide Modelle.)

## 6. Regulatorik & die Redeployment-Geschichte

Kurze, gut belegte Chronologie um Export-Kontrollen und Wiederfreigabe:

| Datum | Ereignis |
|---|---|
| **9. Juni 2026** | Fable 5 und Mythos 5 veröffentlicht. |
| **12. Juni 2026** | US-Regierung verhängt Exportkontrollen auf beide Modelle; Zugang für alle Nutzer ausgesetzt – nachdem Amazon-Forschende eine Technik fanden, mit der sich Fable 5s Schutz umgehen und Software-Schwachstellen identifizieren ließen. |
| **30. Juni 2026** | Kontrollen aufgehoben (laut CNBC durch die Trump-Administration); Redeployment angekündigt. |
| **1. Juli 2026** | Fable 5 weltweit wieder vollständig verfügbar. |

Weitere öffentlich genannte Punkte zur Wiederfreigabe:

- Anthropic argumentierte, auch schwächere Modelle könnten ähnliche
  Schwachstellen-Identifikation leisten – was die Schwere des Contributors relativiere.
- Ein verbesserter Safety-Klassifikator blockiere die gemeldete Umgehung „in
  über 99 % der Fälle".
- Fable 5 biete „keine solchen einzigartigen offensiven Fähigkeiten" – im
  Unterschied zu **Mythos 5**, das auf **defensive** Cybersecurity-Partner
  beschränkt bleibt.
- Mythos 5 wurde nur für freigegebene US-Organisationen unter Project Glasswing
  wiederhergestellt, mit laufender Ausweitung auf weitere Partner.

---

## 7. Fazit in einem Satz

Fable 5 und Mythos 5 sind technisch identisch; der einzige praktische
Unterschied ist die **Sicherheitsschicht** (drei Klassifikatoren → Umleitung an
Opus 4.8), die bei Mythos 5 für freigegebene Organisationen entfällt – der Rest
ist eine Frage von Zugangsberechtigung, Preis und Regulatorik.

---

## Quellen

- Anthropic – „Claude Fable 5 and Claude Mythos 5": https://www.anthropic.com/news/claude-fable-5-mythos-5
- Anthropic – „Redeploying Claude Fable 5": https://www.anthropic.com/news/redeploying-fable-5
- Anthropic Platform Docs – „Introducing Claude Fable 5 and Claude Mythos 5": https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
- CNBC – „Anthropic releases Mythos-like AI model to the public, Claude Fable 5": https://www.cnbc.com/2026/06/09/anthropic-mythos-claude-fable-5.html
- CNBC – „Trump admin has lifted export controls on Claude Fable 5 and Mythos 5": https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html
- TechCrunch – „Anthropic's Claude Fable 5 is a version of Mythos the public can access today": https://techcrunch.com/2026/06/09/anthropic-released-claude-fable-5-its-most-powerful-model-publicly-days-after-warning-ai-is-getting-too-dangerous/
- MacRumors – „Anthropic Launches Claude Fable 5, Its First Public Mythos-Class Model": https://www.macrumors.com/2026/06/09/anthropic-fable-5/
- AWS Blog – „Anthropic Claude Fable 5 on AWS: Mythos-class capabilities with built-in safeguards now available": https://aws.amazon.com/blogs/aws/anthropic-claude-fable-5-on-aws-mythos-class-capabilities-with-built-in-safeguards-now-available/

*Stand der Recherche: 9. Juli 2026. Zusammenfassung öffentlich verfügbarer Informationen; keine internen oder vertraulichen Anthropic-Daten.*
