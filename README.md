# West Alexandria Dental Care — website

Static, dependency-free website for West Alexandria Dental Care (Dr. Sameer Atrash and Dr. Fadi Alhrashi), 3543 W. Braddock Road, Suite E1, Alexandria, VA 22302.

- **`site/`** — the finished website. Upload this folder as-is to any host (Netlify, Vercel, Cloudflare Pages, GoDaddy, cPanel, S3…). No server code, no database.
- **`src/`** — the source: content, design and the build script that generates `site/`.

## Quick start

```bash
python3 src/build.py --check     # regenerate site/ and verify every internal link
node src/serve.js                # preview at http://localhost:8765
```

Both commands use only what ships with macOS (Python 3) and Node. Nothing to install.

## How the site is organized

| Path | What it is |
|---|---|
| `src/site.json` | **Everything about the practice in one place**: name, phone, address, hours, booking and paperwork URLs, insurance list, languages, the announcement bar text, the navigation menus, the footer columns, and the registry of every page (slug, type, parent, and the content brief it was written from). |
| `src/content/**.json` | One file per page. Plain JSON with headings, paragraphs, steps, lists, comparison tables, callouts, FAQs and related links. No HTML. |
| `src/FACTS.md` | The facts sheet every page was written against. If something about the practice changes, change it here and in `site.json`, then search the content for the old value. |
| `src/CONTENT_GUIDE.md` | The voice and the JSON shape for content pages. Give this to anyone writing new pages. |
| `src/validate.py` | Checks content files for broken links, banned phrases, forbidden claims (prices, reviews, unlisted equipment), wrong phone numbers, missing fields. `python3 src/validate.py --all` |
| `src/build.py` | Renders everything into `site/` (also writes `sitemap.xml`, `robots.txt`, `404.html`, the web manifest and JSON-LD structured data). |
| `src/assets/css/main.css` | The design system. Colors and type are CSS variables at the top. |
| `src/assets/js/main.js` | Interactions: live "Open now / Opens at" status, mega menu, mobile drawer, scroll reveals, FAQ accordions, on-this-page highlighting. The site works fully with JavaScript off. |
| `src/assets/img/` | Logo mark, favicons, social-share image, the two dentist photos and the office render. `python3 src/make_images.py` regenerates the favicons and the share image from the logo mark (needs Pillow). |
| `src/serve.js` | Tiny local preview server with clean URLs. |

## Common edits

**Hours, phone, address, announcement bar, insurance list** → `src/site.json`, then rebuild. The live "Open now" status, the hours tables, the footer, the structured data and the contact page all read from it.

**Turn off the "Opening October 2026" bar** → change `"announcement"` in `site.json` to e.g. `"Now open · Welcoming new patients"`.

**Edit a page's words** → open its JSON in `src/content/`, edit, run `python3 src/validate.py path/to/file.json`, rebuild.

**Add a page** → add an entry to `"pages"` in `site.json` (slug, type, title, parent, hint), create the JSON file at the matching path (`/general-dentistry/example/` → `src/content/general-dentistry/example.json`), rebuild. Hub pages list their children automatically; the mega menu reads from the hubs.

**Add a blog post** → `src/content/blog/<slug>.json` with `type: "article"`, plus a registry entry. The blog index and home page pick the newest three by date.

**Change the domain** → `"domain"` in `site.json` (used for canonical URLs, sitemap and structured data).

## Things to confirm with the client before launch

These came from the client's existing site or were inferred; none are invented, but each is worth a yes from the office.

1. **Contact-form inbox.** The form on `/contact/` prepares an email to `info@merrifielddentist.com` (the address the client's current site used). Change `"email"` in `site.json` if a different inbox should receive inquiries, or connect a form service (Netlify Forms, Formspree) and the form will post there instead.
2. **Domain.** `site.json` assumes `www.westalexandriadentalcare.com`. Update before launch.
3. **Invisalign®.** The clear-aligner pages say "clear aligners, including Invisalign". Dr. Atrash lists Invisalign among his interests; confirm the office will offer that brand or change the wording to "clear aligners".
4. **3D imaging (cone-beam CT) and magnification** are described as used "when they meaningfully improve care", as on the client's existing site. Confirm the equipment is on site.
5. **Virginia Medicaid.** The Medicaid page describes the state's adult and child dental benefit in general, hedged terms. Confirm which Medicaid plans the office is credentialed with.
6. **Sedation.** Pages say "nitrous oxide, and other sedation options after an individual review", matching the client's wording. No specific sedation method is promised.
7. **Photos.** The hero uses the office render from the client's current site, and the dentist photos are the ones they supplied. Higher-resolution portraits and real office photography will lift the site further; drop them into `src/assets/img/` with the same filenames.
8. **Google Business Profile.** Once the office has reviews, a reviews section can be added; the site intentionally has no testimonials now because none exist yet.

## Replacing the placeholder photos

The photos are stock placeholders from Unsplash. Every photo on the site is loaded through a named **slot** in `src/photos.json`, so swapping in real office photography is a file swap, not a code change.

| Slot | Where it appears | Suggested real photo |
|---|---|---|
| `hero-office` | Home page hero (full width, text sits on the left third) | Reception or main treatment room, wide shot, daylight |
| `home-approach` | Home page "Modern tools. Clear decisions." section | A dentist with a patient, or a treatment room detail |
| `home-hours` | Home page hours card, and the evening-hours article | The building entrance or the suite door |
| `contact-exterior` | Contact page hero | The Bradlee Office Building from the parking lot |
| `cat-about` | About, Our approach, Technology | The team, or the office interior |
| `cat-new-patients` | New-patient pages, FAQ, Book Online, first-visit article | The front desk |
| `cat-general`, `cat-restorative`, `cat-cosmetic`, `cat-implants`, `cat-aligners`, `cat-emergency`, `cat-sedation` | Each service hub and all of its pages | A photo that fits that category |
| `cat-children`, `cat-seniors`, `cat-teens`, `cat-family` | Children's, seniors', teens' aligner and family pages | Patients of that age group (with consent) |
| `cat-symptoms` | Symptom guide index and all 13 guides | A calm, natural smile |
| `cat-areas` | Areas index and the 8 neighborhood pages | An Alexandria street scene |
| `cat-blog` | Blog index, dictionary, remaining articles | A quiet clinic detail |

**To replace one:** export the real photo as a JPEG about 1600 px wide (2400 px for `hero-office`), name it exactly as the slot's `"file"` in `src/photos.json` (for example `cat-general.jpg`), and a half-size copy named as `"file_sm"` (`cat-general-sm.jpg`). Drop both into `src/assets/img/photos/`, update the `"alt"` text to describe the real picture, adjust `"position"` if the subject needs to sit higher or lower in the crop, then run `python3 src/build.py`. The `width`/`height` fields are refreshed by `python3 src/photos_fetch.py` (which also re-downloads any placeholder still missing a file). Delete `CREDITS.md` from the photos folder once no Unsplash images remain.

## Hosting: Hostinger via GitHub

The source lives at https://github.com/ProDent-web/westalexandriadentalcare. Every push to `main` runs a GitHub Action ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)) that validates the content, rebuilds `site/`, and publishes the finished files to the `deploy` branch. Hostinger pulls that branch into `public_html`, so the live site updates by itself a minute or two after each push.

**One-time setup in Hostinger hPanel** (Websites → Manage → Advanced → Git):

1. Make sure `public_html` is empty (delete Hostinger's default placeholder files in File Manager if any exist), or the Git tool will refuse to clone.
2. Create a repository with: Repository `https://github.com/ProDent-web/westalexandriadentalcare.git`, Branch `deploy`, Install path left blank (that means `public_html`). Click Create, then Deploy.
3. Under Auto Deployment, copy the webhook URL. In GitHub, open the repo → Settings → Webhooks → Add webhook, paste it, content type `application/json`, event "Just the push event". From then on every publish to `deploy` pulls automatically. (Without the webhook, click Deploy in hPanel after each change.)
4. In hPanel → Security → SSL, make sure the free SSL is active for westalexandriadentalcare.com; `.htaccess` then redirects http and www to `https://westalexandriadentalcare.com`.

If the repository is ever made private, use the SSH address instead (`git@github.com:ProDent-web/westalexandriadentalcare.git`) and add the SSH key hPanel generates as a deploy key in GitHub → Settings → Deploy keys.

**Day to day:** edit content or settings, run `python3 src/build.py --check` to preview locally, commit and push to `main`. The Action does the rest. If an Action run fails (red X on the commit), the validator or the link check found a problem; open the run to see which page.

**Manual fallback:** `site/` can also be uploaded by hand to `public_html` (File Manager or FTP). Include the hidden `.htaccess` file.

**After the first deploy:** submit `https://westalexandriadentalcare.com/sitemap.xml` in Google Search Console, and set the Google Business Profile website link to the home page.

## Pages

116 pages: home, all-services index, contact, book online, 2 dentist profiles + index, about, approach, technology, new-patient section (10), general dentistry (13), restorative (16), cosmetic (5), implants (8), clear aligners (8), emergency (8), sedation (4), symptom guides (14), areas served (9), FAQ, dental dictionary, blog (6 posts + index), privacy, accessibility, 404. See `site/sitemap.xml` for the full list.
