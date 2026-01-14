# Translation Guide for Critical Infrastructure (Bar OS)

This guide explains how translations actually work in the backend.

There are two separate translation systems:
- **Site content** (pages, menus, events, news, etc.) is stored in the database via **modeltranslation** fields and edited in the CMS.
- **Interface text** (buttons, labels, system messages) lives in `.po` files and is edited with **Rosetta**.

## 1) Translating site content (Pages, Menus, Events, News)

**Where:** CMS (not Rosetta)

### How it works
- Content fields have language variants (e.g., `title_en`, `title_de`).
- The CMS language switcher controls which language field you are editing.
- If a translation is missing, the default language is used as a fallback.

### Steps
1. Open the CMS and go to the content you want to edit (Pages, Events, Menu, News).
2. Use the **language switcher** in the top bar to pick a language.
3. Edit the fields or page blocks in that language.
4. Save and publish.

### Slugs
- Each language can have its own slug (recommended for SEO and clarity).
- If a language slug is missing, the default language slug is used.

### Public URLs
- Public pages use language prefixes, e.g. `/en/`, `/es/`, `/de/`, `/fr/`.
- The language switcher on the public site swaps the prefix.

## 2) Translating interface text (CMS/Admin)

**Where:** Rosetta

Rosetta only translates **UI strings** (buttons, labels, system messages). It does **not** translate page content.

Steps:
1. Go to `http://localhost:8000/rosetta/`
2. Pick a language.
3. Edit translations and save.

## Language settings

Language support is controlled in `app/core/settings.py`:

```python
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
    ("de", "Deutsch"),
    ("fr", "Français"),
]

MODELTRANSLATION_LANGUAGES = ("en", "es", "de", "fr")
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
```

You can also limit which languages appear in the UI using **Site Settings → Enabled languages**.

## FAQ

**Q: Do I need to translate everything?**
No. The default language is used as a fallback.

**Q: Where do I translate page builder blocks?**
In the CMS with the language switcher set to the language you want to edit. Blocks are stored per language (`blocks_en`, `blocks_de`, etc.).

**Q: Can different languages have different slugs?**
Yes, and it’s recommended for SEO.

**Q: Does Rosetta translate public page content?**
No. Rosetta is only for interface strings.
