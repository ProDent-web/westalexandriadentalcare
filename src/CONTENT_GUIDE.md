# Content Guide — how every page is written

Read FACTS.md first. Then write in this voice, in this JSON shape.

## Voice
Plain, warm, direct, specific. The dentist explaining it to you across the chair, not a brochure. Second person ("you"), first person plural ("we"). Short paragraphs (1–3 sentences). Sentence-case headings. American English.

Good: "A root canal relieves the pain. The pain was the infection, not the treatment."
Good: "If something can reasonably wait, we will tell you so."
Bad: "Our state-of-the-art facility offers world-class care tailored to your unique needs."

**Banned words/phrases:** state-of-the-art, cutting-edge, world-class, top-rated, best-in-class, unparalleled, utilize, leverage, passionate, dedicated to excellence, nestled, seamless, journey (as in "smile journey"), transform your smile, dream smile, "we understand that", "look no further", "rest assured", "don't hesitate", "comprehensive solution", "holistic".
**Avoid:** exclamation marks, em dashes (use a period or comma instead), rhetorical questions in body text, more than one "Alexandria" per 150 words (mention the location naturally 2–4 times per page, including once in the H1 or intro).

Be honest and specific. Explain what happens, in what order, what it feels like, how long it takes, what it depends on. Say what the office will not do (no pressure, no surprise bills). Name the alternatives, including "do nothing for now." Hedge clinical claims that vary ("often", "for many people", "depending on").

Link generously but naturally with inline Markdown links to other pages of this site (only slugs that exist in the registry). Use link text that is the page topic, not "click here".

## Inline formatting allowed in body text
`**bold**`, `[link text](/slug/)`, and the special tokens `{{phone}}` (renders the phone number as a tel: link), `{{book}}` (renders "book online" linked to the booking system), `{{forms}}` (renders "patient registration page" linked to Denticon). Nothing else: no raw HTML, no headings inside body strings.

## JSON shape (all page types unless noted)
```json
{
  "slug": "/restorative-dentistry/dental-crowns/",
  "type": "service",
  "title": "Dental Crowns",
  "meta_title": "Dental Crowns in Alexandria, VA | West Alexandria Dental Care",
  "meta_description": "140–160 characters, specific, includes the topic and West Alexandria, no hype.",
  "eyebrow": "Restore your smile",
  "h1": "Dental crowns in West Alexandria",
  "intro": "2–3 sentences. What this is, who it is for, the plain version of why. Appears under the H1.",
  "icon": "crown",
  "facts": [
    {"label": "Visits", "value": "Usually two"},
    {"label": "Numbing", "value": "Local anesthetic"},
    {"label": "Back to normal", "value": "Same day"}
  ],
  "sections": [
    {"type": "prose", "heading": "Why a tooth needs a crown", "body": ["Paragraph.", "Paragraph."]},
    {"type": "steps", "heading": "How it goes", "intro": "optional one line", "items": [{"title": "Planning", "body": "..."}, {"title": "Preparation", "body": "..."}]},
    {"type": "list", "heading": "Signs you may need one", "intro": "optional", "style": "check", "items": ["...", "..."]},
    {"type": "cards", "heading": "Your options", "items": [{"title": "Crown", "body": "...", "href": "/optional/"}]},
    {"type": "compare", "heading": "Crown or filling?", "columns": ["Crown", "Filling"], "rows": [["Best for", "Large breakdown", "Small to medium cavities"], ["Visits", "Two", "One"]]},
    {"type": "callout", "tone": "urgent", "heading": "Call today if", "body": "...", "cta": {"label": "Call 703-560-7200", "href": "tel"}}
  ],
  "faqs": [{"q": "Does it hurt?", "a": "2–4 sentences."}],
  "related": ["/restorative-dentistry/tooth-colored-fillings/", "/restorative-dentistry/root-canal-therapy/"],
  "cta": {"heading": "Not sure whether a filling will do?", "body": "One or two sentences inviting a visit or call."}
}
```

### Field rules
- `type`: one of service, symptom, hub, info, area, article, faq, dictionary, dentist.
- `facts`: 3–4 chips for service/symptom pages. Values are short (1–4 words). Omit for info/area/hub pages if nothing sensible fits.
- `icon`: one of: tooth, shield, sparkle, clock, pin, phone, calendar, implant, aligner, crown, drop, moon, alert, child, senior, xray, heart, smile, gum, star, check, family, language, card, wallet, book, map, chat, sun, hand, pulse, wave, gear, leaf, braces, bridge, denture, root, shield-check, repair.
- `sections`: 5–9 sections for service/symptom pages, 4–7 for info/area pages, 3–5 for hubs. Mix the types. Every page has at least one `steps` or `list` section. Section headings are specific ("What a deep cleaning feels like afterward"), never generic ("Overview", "Benefits").
- `callout` tones: `info` (blue), `note` (cream). Do not use red warning boxes; the client does not want them. `cta.href` may be a slug, `tel`, `book`, or `forms`.
- `faqs`: 4–7 on service/symptom pages, 3–5 on info/area pages. Real questions people ask, answered directly.
- `related`: 3–6 existing slugs. Hubs omit `related` (children are auto-listed).
- `cta`: always present. Specific to the page, not generic.
- Word count targets (body text total): service 650–1000; symptom 550–850; info 600–1000; area 450–700; hub 400–650; article 900–1400.

### Hub pages (`type: hub`)
Same shape. Children are listed automatically from the registry, so do NOT list them in a cards section. Sections explain the category, how decisions are made here, what to expect, and who to see. Include one `callout` pointing to emergencies or booking where sensible.

### Symptom pages (`type: symptom`)
Must include, in this order somewhere in sections: a `list` titled like "What is usually behind it" (causes), a `steps` or `list` titled "What to do right now", a `prose` on "What happens at the visit", and a `cards` or `prose` on "How it is treated" linking to the relevant service pages.

### Area pages (`type: area`)
Real geography only (major roads and well-known landmarks that are certain). Drive times hedged ("about ten minutes, depending on traffic"). Explain why the seven-day hours, free parking, languages and insurance matter for that neighborhood. Do not invent neighborhood statistics, school names you are not sure of, or events. Sections: who we see from here, getting to the office (roads, parking, I-395 King Street exit), what a first visit looks like, services people from here commonly need, hours. Include an `faqs` block with 3–4 location-specific questions.

### Article pages (`type: article`)
Add top-level fields: `"date": "2026-08-21"`, `"category": "Urgent dental care"`, `"read_time": "7 min read"`, `"summary": "one or two sentences"`. Sections use the same block types. End with a `callout` (tone note) headed "A note about online dental information" with the standard disclaimer that the article is educational and cannot replace an examination. Then the usual `cta`.

### FAQ page (`type: faq`)
Top-level `"groups": [{"heading": "Appointments and hours", "items": [{"q": "", "a": ""}]}]` (6–8 groups, 30–45 questions total). Also include `intro`, `h1`, `meta_*`, `cta`. No `sections` needed.

### Dictionary page (`type: dictionary`)
Top-level `"terms": [{"term": "Abscess", "definition": "1–3 sentences.", "href": "/emergency-dentistry/dental-abscess/"}]` (70–90 terms, alphabetical, `href` optional and must exist in the registry). Also `intro`, `h1`, `meta_*`, `cta`.

### Info pages (`type: info`)
Same shape as service. `facts` optional.

## Quality bar
Each page must be able to stand alone as the best page on the internet for that topic for a patient in Alexandria: concrete, honest, well-sequenced, with no filler sentence that could be deleted without loss. No two pages may share a paragraph. Do not pad. Do not repeat the intro in the first section.
