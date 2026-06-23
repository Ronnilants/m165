# KN05 – Neo4j Graph Database: Szenario B – Fraud Detection (Geldwäsche-Ringe)

---

## Phase 2: Kanten-Attribute erstellen

### Vollständiger CREATE-Code

```cypher
CREATE 
  (acc1:Account {id: '1001', owner: 'Alice'}),
  (acc2:Account {id: '1002', owner: 'Bob'}),
  (acc3:Account {id: '1003', owner: 'Charlie'}),
  (acc4:Account {id: '1004', owner: 'Dave'}),
  (acc1)-[:TRANSFERRED {amount: 5000}]->(acc2),
  (acc2)-[:TRANSFERRED {amount: 4800}]->(acc3),
  (acc3)-[:TRANSFERRED {amount: 4600}]->(acc1),
  (acc3)-[:TRANSFERRED {amount: 2000}]->(acc4)
```

### Erklärung der Struktur

Die vier Überweisungen bilden folgendes Muster:

```
Alice --5000--> Bob --4800--> Charlie --4600--> Alice  (Geldwäsche-Ring!)
                                      --2000--> Dave
```

- `(acc1)-[:TRANSFERRED {amount: 5000}]->(acc2)` → Alice überweist 5000 an Bob
- `(acc2)-[:TRANSFERRED {amount: 4800}]->(acc3)` → Bob überweist 4800 an Charlie
- `(acc3)-[:TRANSFERRED {amount: 4600}]->(acc1)` → Charlie überweist 4600 an Alice **(schliesst den Ring)**
- `(acc3)-[:TRANSFERRED {amount: 2000}]->(acc4)` → Charlie überweist ausserdem 2000 an Dave

Das Attribut `amount` gehört zur **Kante (Relationship)**, nicht zum Knoten.

---

## Phase 3: Die fehlerhafte KI-Query

### Die falsche Query

```cypher
MATCH (charlie:Account {owner: 'Charlie'})<-[:TRANSFERRED]-(recipient:Account)
RETURN recipient.owner, recipient.amount
```

### Resultat der falschen Query

```
recipient.owner | recipient.amount
"Bob"           | NULL
```

### Warum ist das Resultat falsch?

**Fehler 1 – Falsche Pfeilrichtung:**
`<-[:TRANSFERRED]-` bedeutet: *Wer hat an Charlie überwiesen?* Das ist Bob (Bob → Charlie).
Wir wollen aber: *An wen hat Charlie überwiesen?* Das wäre `->`.

**Fehler 2 – `amount` ist auf der Kante, nicht auf dem Knoten:**
`recipient.amount` versucht das Attribut `amount` vom Account-Knoten zu lesen – dort existiert es nicht → `NULL`.
Das Attribut `amount` liegt auf der `[:TRANSFERRED]`-Kante. Um darauf zuzugreifen, muss die Kante mit einer Variable gebunden werden: `[r:TRANSFERRED]`, dann `r.amount`.

---

### Die korrigierte Query

```cypher
MATCH (charlie:Account {owner: 'Charlie'})-[r:TRANSFERRED]->(recipient:Account)
RETURN recipient.owner AS empfaenger, r.amount AS betrag
```

**Änderungen:**
1. `<-[...]-` → `-[r:TRANSFERRED]->` (Pfeil umgekehrt + Kante als Variable `r` gebunden)
2. `recipient.amount` → `r.amount` (amount von der Kante lesen, nicht vom Knoten)

### Resultat der korrigierten Query

```
empfaenger | betrag
"Dave"     | 2000
"Alice"    | 4600
```

Charlie hat an **Alice** (4600) und **Dave** (2000) überwiesen – korrekt und vollständig.

---

## Beweis: Queries im Vergleich

| | Falsche Query | Korrigierte Query |
|---|---|---|
| Pfeilrichtung | `<-` (falsch: wer zahlt *an* Charlie) | `->` (korrekt: wer Charlie *bezahlt*) |
| Amount-Quelle | `recipient.amount` (Knoten, nicht vorhanden) | `r.amount` (Kante, korrekt) |
| Ergebnis | Bob, NULL | Alice (4600), Dave (2000) |
