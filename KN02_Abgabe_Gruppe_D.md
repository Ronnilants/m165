# KN02 – MongoDB: Gruppe D – Das Projektmanagement-Tool

---

## Phase 2: Das relationale Erbe

### Setup

Die drei Collections `projects`, `users` und `tasks` wurden mit den vorgegebenen JSON-Daten befüllt.

### Code: Aggregation-Pipeline

```js
db.projects.aggregate([
  // Schritt 1: Nur Projekt 301 laden
  { $match: { "_id": ObjectId("651d00000000000000000301") } },

  // Schritt 2: Alle Tasks dieses Projekts via $lookup joinen
  {
    $lookup: {
      from: "tasks",
      localField: "_id",
      foreignField: "project_id",
      as: "tasks"
    }
  },

  // Schritt 3: Tasks-Array auffalten, damit der nächste $lookup pro Task funktioniert
  { $unwind: "$tasks" },

  // Schritt 4: Zugewiesenen User (Assignee) via $lookup joinen
  {
    $lookup: {
      from: "users",
      localField: "tasks.assignee_id",
      foreignField: "_id",
      as: "tasks.assignee"
    }
  },

  // Schritt 5: Assignee-Array auffalten (immer 1 User pro Task)
  { $unwind: "$tasks.assignee" },

  // Schritt 6: Dokument wieder zusammenführen – Tasks als Array, Assignee-Name einbetten
  {
    $group: {
      _id: "$_id",
      name: { $first: "$name" },
      status: { $first: "$status" },
      tasks: {
        $push: {
          _id: "$tasks._id",
          title: "$tasks.title",
          status: "$tasks.status",
          assignee_name: "$tasks.assignee.name"
        }
      }
    }
  }
])
```

### Erklärung

Die Pipeline startet mit einem `$match`, das nur das gewünschte Projekt (ID 301) aus der `projects`-Collection lädt. Danach verknüpft ein erster `$lookup` alle Tasks, deren `project_id` mit der Projekt-ID übereinstimmt – das entspricht einem SQL-JOIN. Ein zweiter `$lookup` holt anschliessend für jeden Task den zugehörigen User aus der `users`-Collection anhand der `assignee_id`. Abschliessend fasst `$group` alle einzelnen Task-Zeilen wieder zu einem einzigen Projektdokument mit einem `tasks`-Array zusammen, das den Namen des Assignees direkt enthält.

### Beweis: Ergebnis-Dokument

```json
[
  {
    "_id": "651d00000000000000000301",
    "name": "Backend Refactoring",
    "status": "Active",
    "tasks": [
      {
        "_id": "651d00000000000000007001",
        "title": "API Endpunkte auf GraphQL umstellen",
        "status": "In Progress",
        "assignee_name": "Alice Meyer"
      },
      {
        "_id": "651d00000000000000007002",
        "title": "Datenbank-Indizes prüfen",
        "status": "To Do",
        "assignee_name": "Alice Meyer"
      }
    ]
  }
]
```

---

## Phase 3: Die Performance-Analyse

### Metriken (relationales Design mit `$lookup`)

| Metrik | Wert | Quelle |
|---|---|---|
| `totalDocsExamined` | **1** (projects) + **6** (tasks, 2× full scan) + **3** (users) = **10** | `explain("executionStats")` je Stage |
| `nReturned` | **1** (Enddokument) | `$group`-Stage |
| `executionTimeMillis` | **2 ms** | `$cursor`-Stage |

> **Detailaufschlüsselung aus dem `explain`-Output:**
> - `$cursor` (projects): `totalDocsExamined: 1`, `executionTimeMillis: 2`
> - `$lookup` tasks: `totalDocsExamined: 6`, `collectionScans: 2` (kein Index auf `project_id`!)
> - `$lookup` users: `totalDocsExamined: 3`, nutzt `_id_`-Index

### Beweis: `explain("executionStats")` Output (Auszug)

```json
{
  "stages": [
    {
      "$cursor": {
        "executionStats": {
          "nReturned": 1,
          "executionTimeMillis": 2,
          "totalDocsExamined": 1
        }
      }
    },
    {
      "$lookup": {
        "from": "tasks",
        "totalDocsExamined": 6,
        "collectionScans": 2,
        "indexesUsed": [],
        "nReturned": 2
      }
    },
    {
      "$lookup": {
        "from": "users",
        "totalDocsExamined": 3,
        "indexesUsed": ["_id_"],
        "nReturned": 2
      }
    }
  ]
}
```

### Fazit: Warum ist das relationale Design ein Flaschenhals?

Das kritische Problem liegt im zweiten `$lookup` auf die `tasks`-Collection: Das Feld `project_id` besitzt **keinen Index** (`indexesUsed: []`), weshalb MongoDB bei jeder Anfrage einen vollständigen Collection-Scan (`collectionScans: 2`) durchführen muss. Mit 3 Tasks bedeutet das noch 6 untersuchte Dokumente – kein Problem. Wächst das System jedoch auf 100'000 Tasks an, muss MongoDB bei jeder Dashboard-Anfrage alle 100'000 Dokumente scannen, selbst wenn nur 10 davon zum gesuchten Projekt gehören. Das `totalDocsExamined` steigt also linear mit der Datenmenge, während `nReturned` klein bleibt – ein klassisches Zeichen für einen Bottleneck. Jeder zusätzliche `$lookup` multipliziert dieses Problem. Das relationale Design erzwingt in MongoDB teure Runtime-Joins, die in einer dokumentenorientierten Datenbank ohne optimale Indexstruktur schnell zum Flaschenhals werden.

---

## Phase 4: Der Paradigmenwechsel (Design)

### Neue JSON-Struktur (Embedded Document)

```json
{
  "_id": { "$oid": "651d00000000000000000301" },
  "name": "Backend Refactoring",
  "status": "Active",
  "tasks": [
    {
      "_id": { "$oid": "651d00000000000000007001" },
      "title": "API Endpunkte auf GraphQL umstellen",
      "status": "In Progress",
      "assignee_name": "Alice Meyer"
    },
    {
      "_id": { "$oid": "651d00000000000000007002" },
      "title": "Datenbank-Indizes prüfen",
      "status": "To Do",
      "assignee_name": "Alice Meyer"
    }
  ]
}
```

### Begründung

Im neuen Design werden die Tasks direkt als Array in das Projektdokument **eingebettet** (Embedding). Zusätzlich wird der Name des Assignees (`assignee_name`) als String im Task-Objekt **denormalisiert** – d.h. bewusst dupliziert, anstatt eine Referenz auf die `users`-Collection zu pflegen.

Diese Entscheidung begründet sich mit zwei zentralen Prinzipien:

**1-to-Few / 1-to-Many:** Ein Projekt hat typischerweise eine überschaubare, endliche Anzahl Tasks (1-to-Few). MongoDB-Dokumente haben ein 16-MB-Limit, das hier nie erreicht wird. Das Embedding ist daher sicher und sinnvoll.

**Read-to-Write Ratio:** Ein Projekt-Dashboard wird deutlich häufiger gelesen als Tasks erstellt oder umbenannt werden. Das Read-to-Write Ratio ist sehr hoch, was Embedding stark begünstigt. Der einzige Nachteil der Denormalisierung – wenn sich der Name eines Users ändert, muss er an mehreren Stellen aktualisiert werden – fällt kaum ins Gewicht, da Namenänderungen extrem selten sind (Write-Rate nahe null). Dafür wird jeder Lesevorgang mit einer einzigen `.find()`-Abfrage ohne Join erledigt.

---

## Phase 5: Der Beweis

### Code: `.find()`-Abfrage

```js
db.projects_embedded.find({ "_id": ObjectId("651d00000000000000000301") })
```

### Ergebnis

```json
[
  {
    "_id": "651d00000000000000000301",
    "name": "Backend Refactoring",
    "status": "Active",
    "tasks": [
      {
        "_id": "651d00000000000000007001",
        "title": "API Endpunkte auf GraphQL umstellen",
        "status": "In Progress",
        "assignee_name": "Alice Meyer"
      },
      {
        "_id": "651d00000000000000007002",
        "title": "Datenbank-Indizes prüfen",
        "status": "To Do",
        "assignee_name": "Alice Meyer"
      }
    ]
  }
]
```

### Metriken (neues Embedded Design)

| Metrik | Phase 3 (relational) | Phase 5 (embedded) | Verbesserung |
|---|---|---|---|
| `totalDocsExamined` | 10 (über 3 Collections) | **1** | **10× weniger** |
| `nReturned` | 1 | **1** | gleich |
| `executionTimeMillis` | 2 ms | **0 ms** | **schneller** |

### Beweis: `explain("executionStats")` Output

```json
{
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 1,
    "executionTimeMillis": 0,
    "totalKeysExamined": 1,
    "totalDocsExamined": 1,
    "executionStages": {
      "stage": "IDHACK",
      "nReturned": 1,
      "executionTimeMillisEstimate": 0,
      "keysExamined": 1,
      "docsExamined": 1
    }
  }
}
```

### Vergleich & Interpretation

Das neue Design reduziert `totalDocsExamined` von 10 auf **1** – MongoDB liest exakt das eine benötigte Dokument, ohne einen einzigen Collection-Scan oder Join. Die `executionTimeMillis` fiel von 2 ms auf **0 ms** (unterhalb der Messschwelle). Das Re-Design hat sich klar gelohnt: Statt mehrerer `$lookup`-Stages über drei Collections genügt nun ein einziger Index-Lookup via `IDHACK`. Skaliert das System auf Millionen von Tasks, bleibt das Embedded-Design konstant schnell (O(1)), während das relationale Design linear langsamer würde (O(n)).
