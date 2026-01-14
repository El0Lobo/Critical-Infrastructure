Public Templates Pack
=====================

Place the `public/` folder into your Django templates path:

    app/templates/public/

All templates extend: `public/base_public.html`

They read data from the `SiteSettings` context processor:
- `site_settings`: your global config (name, address, socials, currency, etc.)
- `public_pages`: navigation-ready list of published `app.pages.Page` entries

Suggested URL mapping (adjust to your apps):
- /               -> public/home.html
- /events/        -> public/events.html   (expects `events` in context)
- /news/          -> news/public_index.html     (expects `page_obj` in context)
- /about/         -> public/about.html
- /contact/       -> public/contact.html
- /menu/          -> public/menu.html     (expects `menu_sections`)
- /gallery/       -> public/gallery.html  (expects `images`)
- /shows/         -> public/shows.html    (expects `shows`)
- /music/         -> public/music.html
- /videos/        -> public/videos.html   (expects `videos`)
- /store/         -> public/store.html    (expects `products`)
- /posts/         -> public/posts.html    (expects `posts`)
- /archive/       -> public/archive.html  (expects `archive` structure)
- /<slug>/        -> public/page_detail.html (expects `page`)

These pages are "headless-friendly" and will render gracefully even if certain
optional context variables are missing. Populate them from your respective apps.
