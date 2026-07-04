# Moderation contract

The only coupling between **yachan** (monolith) and **moderation** (stateless
microservice). No shared code, no shared database — both sides hardcode these
strings independently and agree on the JSON shapes below.

## Transport

- **Broker:** one shared Redis, `REDIS_URL` (db 0). It is a message bus, not a
  shared datastore — the moderation service never touches yachan's Postgres.
- **Serialization:** JSON only (matches yachan's `accept_content=["json"]`).
- **No result backend on the moderation path.** Neither side calls
  `AsyncResult.get()`. Return of the verdict is a second one-way task, not a reply.
- Tasks are addressed by **string name** via `celery.send_task(...)`; the sender
  does not import or register the receiver's task.

## Queues

Three queues on the one shared Redis; each side reads only what is addressed to it.

| Queue                | Writes         | Reads          | Carries                                               |
|----------------------|----------------|----------------|-------------------------------------------------------|
| `celery` (default)   | yachan         | yachan         | yachan's own tasks (`process_attachment`, `expire_bans`) |
| `moderation`         | yachan         | moderation svc | `moderate_image`, `moderate_text`                     |
| `moderation_results` | moderation svc | yachan         | `apply_moderation_verdict`, `apply_text_verdict`      |

- `moderation` — transport **to** the microservice: only yachan writes, only the
  moderation worker reads (`-Q moderation`).
- `moderation_results` — transport **back** to the monolith: only the moderation
  worker writes, only yachan reads.
- yachan's worker consumes **two** queues — its own default plus the results
  channel: `-Q celery,moderation_results`. This is the one change to yachan's
  worker command (made in step 2).

## Task 1 — `moderate_image`  (yachan → service)

Producer: yachan `store_uploads`. Consumer: moderation worker (plain sync task,
torch, no DB).

```
name:  "moderate_image"
queue: "moderation"
args:  [attachment_id: int, image_url: str, mode: str]
```

- `attachment_id` — correlation id. The service echoes it back untouched; it does
  not know or care that it is a post attachment.
- `image_url` — absolute, service-reachable media URL built by yachan from
  `MEDIA_INTERNAL_URL` (dev: the in-network minio endpoint; prod: falls back to the
  public bucket url from `public_url`). The service fetches bytes with
  `httpx.get(image_url)` as an external client — it holds no media config of its own.
- `mode` — classification profile. `"nsfw"` for now; grows to `"csam"` etc. as
  later pipelines land. The service selects the model set by this string.

## Task 2 — `apply_moderation_verdict`  (service → yachan)

Producer: moderation worker. Consumer: yachan `apply_moderation_verdict`
(`ScopedTask`, the only side that touches the DB).

```
name:  "apply_moderation_verdict"
queue: "moderation_results"
args:  [attachment_id: int, verdict: object]
```

`verdict`:

```json
{
  "status": "safe" | "flagged" | "blocked",
  "nsfw_score": 0.0,          // float, or null
  "labels": { "porn": 0.9 }   // object of per-class scores, or null
}
```

Two tiers map to status: `blocked` = explicit/hardcore (hidden retroactively),
`flagged` = erotica (kept, surfaced to a human moderator), `safe` = clean.

## Task 3 — `moderate_text`  (yachan → service)

Producer: yachan post-create views (`create_reply`, `create_thread`, `edit_post`),
only when the post has body text. Consumer: moderation worker (onnx toxicity model
+ spam heuristic, no DB).

```
name:  "moderate_text"
queue: "moderation"
args:  [post_id: int, text: str]
```

- `post_id` — correlation id, echoed back untouched.
- `text` — the post's raw body. Small, so it travels inline in the message (no URL
  fetch, unlike images).

## Task 4 — `apply_text_verdict`  (service → yachan)

Producer: moderation worker. Consumer: yachan `apply_text_verdict` (`ScopedTask`).
The text path does **not** hide or delete anything — a flagged post is **auto-reported**
(a `Report` row with `is_auto = true`) for a human moderator to decide.

```
name:  "apply_text_verdict"
queue: "moderation_results"
args:  [post_id: int, verdict: object]
```

`verdict`:

```json
{
  "toxic": true,              // blatant toxicity (death-wishes etc.)
  "spam": false,             // blatant spam
  "scores": { "toxic": 0.98 } // optional per-signal scores, or null
}
```

yachan auto-reports if either `toxic` or `spam` is true (reason lists which),
deduped to one auto-report per post. Neither flag → nothing happens.

## Failure & idempotency

- **Failure fallback.** If the service cannot fetch the URL or the classifier
  errors, it replies with a `flagged` verdict (fail-safe to human review) rather
  than leaving the attachment `pending` forever. A retry policy is still TODO.
- **Idempotency.** `apply_moderation_verdict` is an UPDATE by `attachment_id`, so a
  redelivery is safe to run twice. `apply_text_verdict` is deduped by a one-auto-report-per-post
  check, so a redelivery (or a re-moderated edit) never piles on duplicate reports.
- **Text failure fallback.** A fetch/classifier error on the text path replies with both
  flags false (no report) — text moderation must never itself flood the report queue on error.
