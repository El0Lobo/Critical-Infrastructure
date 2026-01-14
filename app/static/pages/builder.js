const BOOT_DATA = (() => {
  const el = document.getElementById("page-builder-config");
  if (!el) {
    return {};
  }
  try {
    return JSON.parse(el.textContent || "{}");
  } catch (error) {
    console.error("Failed to parse page builder config", error);
    return {};
  }
})();

if (!window.__PAGE_BUILDER__) {
  window.__PAGE_BUILDER__ = BOOT_DATA;
}

const DEFAULT_BLOCK_LIBRARY = [
  {
    type: "hero",
    icon: "🌄",
    label: "Hero banner",
    category: "story",
    description: "Large hero with background image and primary call-to-actions.",
    defaults: {
      kicker: "",
      title: "Welcome to our space",
      subtitle: "Introduce the vibe of your venue or collective here.",
      background_image: "",
      overlay: 0.45,
      alignment: "center",
      actions: [],
    },
    fields: [
      { key: "kicker", type: "text", label: "Kicker" },
      { key: "title", type: "text", label: "Headline" },
      { key: "subtitle", type: "textarea", label: "Subheadline", rows: 3 },
      {
        key: "background_image",
        type: "url",
        label: "Background image URL",
        help: "Paste an image URL from the media library.",
        assetKinds: ["image"],
      },
      {
        key: "overlay",
        type: "range",
        label: "Overlay strength",
        min: 0,
        max: 0.85,
        step: 0.05,
      },
      {
        key: "alignment",
        type: "select",
        label: "Text alignment",
        options: [
          { value: "left", label: "Left" },
          { value: "center", label: "Center" },
          { value: "right", label: "Right" },
        ],
      },
      {
        key: "actions",
        type: "list",
        label: "Buttons",
        itemLabel: "Button",
        itemDefaults: { label: "Learn more", href: "#", style: "primary", new_tab: false },
        itemFields: [
          { key: "label", type: "text", label: "Label" },
          { key: "href", type: "url", label: "Link" },
          {
            key: "style",
            type: "select",
            label: "Style",
            options: [
              { value: "primary", label: "Primary" },
              { value: "ghost", label: "Outline" },
              { value: "link", label: "Link" },
            ],
          },
          { key: "new_tab", type: "toggle", label: "Open in new tab" },
        ],
      },
    ],
    styleTargets: [
      { key: "kicker", label: "Kicker" },
      { key: "title", label: "Headline" },
      { key: "subtitle", label: "Subheadline" },
    ],
  },
  {
    type: "navigation",
    icon: "🧭",
    label: "Navigation bar",
    category: "navigation",
    description: "Configure the main site navigation (brand link + menu).",
    defaults: {
      enabled: true,
      show_logo: true,
      logo_text: "",
      logo_text_auto: true,
      logo_image: "",
      logo_width: null,
      show_language_switcher: true,
      show_theme_switcher: false,
      layout: "center",
      links: [],
    },
    fields: [
      { key: "enabled", type: "toggle", label: "Show navigation bar" },
      { key: "show_logo", type: "toggle", label: "Show logo image if available" },
      {
        key: "logo_image",
        type: "url",
        label: "Logo image",
        help: "Override the Site Settings logo for this page.",
        assetKinds: ["image"],
        allowUpload: true,
      },
      {
        key: "logo_width",
        type: "number",
        label: "Logo width (px)",
        min: 40,
        max: 600,
        help: "Optional fixed width. Leave blank to use the original image size.",
      },
      {
        key: "logo_text_auto",
        type: "toggle",
        label: "Use Site Settings brand text",
        help: "Keeps this in sync with the setup page.",
      },
      {
        key: "logo_text",
        type: "text",
        label: "Brand text",
        help: "Override the default when automation is off.",
        disabledWhen: { key: "logo_text_auto", value: true },
      },
      {
        key: "layout",
        type: "select",
        label: "Alignment",
        options: [
          { value: "center", label: "Centered" },
          { value: "left", label: "Left" },
        ],
      },
      { key: "show_language_switcher", type: "toggle", label: "Show language switcher" },
      {
        key: "show_theme_switcher",
        type: "toggle",
        label: "Show theme switcher",
        help: "Adds a visitor theme selector (Standard look, 80s, Neobrutalism).",
      },
      {
        key: "links",
        type: "navlinks",
        label: "Navigation links",
        help: "Pick and order the page links for this navigation bar.",
      },
    ],
    styleTargets: [
      { key: "logo_text", label: "Brand text" },
      { key: "links", label: "Navigation pills" },
    ],
  },
  {
    type: "rich_text",
    icon: "✍️",
    label: "Rich text",
    category: "content",
    description: "Free-form HTML section for detailed copy.",
    defaults: {
      html: "<p>Write your story here. This block accepts standard HTML.</p>",
    },
    fields: [
      {
        key: "html",
        type: "textarea",
        label: "Content",
        rows: 8,
        help: "Supports HTML markup. Use paragraphs, headings, lists, etc.",
      },
    ],
  },
  {
    type: "events",
    icon: "🎟️",
    label: "Events",
    category: "data",
    description: "Showcase upcoming events pulled from the CMS schedule.",
    defaults: {
      title: "Upcoming events",
      subtitle: "",
      limit: 4,
      include_internal: false,
      layout: "grid",
      show_actions: true,
      open_mode: "link",
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Number of events", min: 1, max: 16 },
      { key: "include_internal", type: "toggle", label: "Include internal events" },
      {
        key: "layout",
        type: "select",
        label: "Layout",
        options: [
          { value: "grid", label: "Grid" },
          { value: "list", label: "List" },
        ],
      },
      {
        key: "open_mode",
        type: "select",
        label: "Click action",
        options: [
          { value: "link", label: "Go to event page" },
          { value: "modal", label: "Open quick view modal" },
          { value: "none", label: "No action" },
        ],
      },
      { key: "show_actions", type: "toggle", label: "Show “Details” buttons" },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "events_compact",
    icon: "📅",
    label: "Events (compact)",
    category: "data",
    description: "Small list of the next events without full cards.",
    defaults: {
      title: "Next up",
      subtitle: "",
      limit: 3,
      include_internal: false,
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Number of events", min: 1, max: 12 },
      { key: "include_internal", type: "toggle", label: "Include internal events" },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "events_archive",
    icon: "🗂️",
    label: "Events (archive)",
    category: "data",
    description: "Full event grid with optional filters and past events.",
    defaults: {
      title: "Event archive",
      subtitle: "",
      limit: 12,
      include_internal: false,
      include_past: false,
      show_filters: true,
      show_search: false,
      show_past_toggle: true,
      category_slugs: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Items to show", min: 1, max: 50 },
      { key: "include_internal", type: "toggle", label: "Include internal events" },
      { key: "include_past", type: "toggle", label: "Include past events" },
      { key: "show_filters", type: "toggle", label: "Show filter buttons" },
      { key: "show_search", type: "toggle", label: "Show search box" },
      { key: "show_past_toggle", type: "toggle", label: "Allow past toggle" },
      {
        key: "category_slugs",
        type: "sluglist",
        label: "Category filter",
        help: "Optional: restrict to these category slugs.",
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "recurring_events",
    icon: "🔁",
    label: "Recurring series",
    category: "data",
    description: "Highlight recurring events with a modal series view.",
    defaults: {
      title: "Recurring series",
      subtitle: "",
      limit: 6,
      occurrence_limit: 6,
      include_internal: false,
      include_past: true,
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Series to show", min: 1, max: 20 },
      { key: "occurrence_limit", type: "number", label: "Dates per series", min: 1, max: 20 },
      { key: "include_internal", type: "toggle", label: "Include internal events" },
      { key: "include_past", type: "toggle", label: "Include past dates" },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "news_latest",
    icon: "📰",
    label: "Latest news",
    category: "data",
    description: "Compact teaser of recent public news posts.",
    defaults: {
      title: "Latest news",
      subtitle: "",
      limit: 3,
      category: "",
      link_label: "View all news",
      link_href: "/news/",
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Items to show", min: 1, max: 6 },
      {
        key: "category",
        type: "text",
        label: "Category filter",
        help: "Optional category name to filter posts.",
      },
      { key: "link_label", type: "text", label: "CTA label" },
      { key: "link_href", type: "url", label: "CTA link" },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Subtitle" },
    ],
  },
  {
    type: "news_archive",
    icon: "🗂️",
    label: "News archive",
    category: "data",
    description: "Large module listing public news with filters and search.",
    defaults: {
      title: "News & updates",
      subtitle: "",
      show_search: true,
      show_filters: true,
      category: "",
      limit: 6,
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "limit", type: "number", label: "Initial items", min: 3, max: 12 },
      { key: "show_search", type: "toggle", label: "Enable search input" },
      { key: "show_filters", type: "toggle", label: "Show category filters" },
      {
        key: "category",
        type: "text",
        label: "Restrict to category",
        help: "Leave blank to include all categories.",
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Subtitle" },
    ],
  },
  {
    type: "menu",
    icon: "🍹",
    label: "Menu",
    category: "data",
    description: "Highlight menu categories or dishes from the POS menu.",
    defaults: {
      title: "Menu highlights",
      subtitle: "",
      category_slugs: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      {
        key: "category_slugs",
        type: "sluglist",
        label: "Limit to categories",
        help: "Optional. Enter category slugs separated by commas. Leave empty to show all top-level categories.",
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "opening_hours",
    icon: "⏰",
    label: "Opening hours",
    category: "contact",
    description: "Display the structured opening hours from site settings.",
    defaults: {
      title: "Opening hours",
      subtitle: "",
      show_contact: true,
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "show_contact", type: "toggle", label: "Show contact details" },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "contact",
    icon: "☎️",
    label: "Contact",
    category: "contact",
    description: "Contact details and social links sourced from site settings.",
    defaults: {
      contact_fields: null,
      social_fields: null,
      show_social: true,
    },
    fields: [
      {
        key: "contact_fields",
        type: "checkboxes",
        label: "Contact details to show",
        optionsSource: "contact",
        defaultAll: true,
        help: "Select which address, phone, email, or website info from Site Settings appears.",
      },
      {
        key: "social_fields",
        type: "checkboxes",
        label: "Social profiles",
        optionsSource: "social",
        defaultAll: true,
        help: "Toggle which social links to render. Leave everything unchecked to hide socials.",
      },
    ],
  },
  {
    type: "inventory",
    icon: "📦",
    label: "Inventory list",
    category: "data",
    description: "List publicly visible inventory items such as board games or gear.",
    defaults: {
      title: "Available gear",
      subtitle: "",
      category_slugs: "",
    },
    fields: [
      { key: "title", type: "text", label: "Title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      {
        key: "category_slugs",
        type: "sluglist",
        label: "Limit to categories",
        help: "Optional comma-separated inventory category slugs. Leave empty to show all public items.",
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "map",
    icon: "🗺️",
    label: "OpenStreetMap",
    category: "contact",
    description: "Embed an interactive OpenStreetMap with directions and nearby options.",
    defaults: {
      title: "Find us",
      subtitle: "Plan your visit or share directions.",
      latitude: null,
      longitude: null,
      zoom: 15,
      auto_location: true,
      address_override: "",
      show_transport: true,
      transport_heading: "Public transport",
      transport_items: [
        { label: "Bus 5 — Stadtgarten", details: "2 min walk" },
        { label: "Train — Hauptbahnhof", details: "10 min walk" },
      ],
      show_parking: true,
      parking_heading: "Parking",
      parking_items: [
        { label: "City Garage", details: "24/7 · first hour free" },
        { label: "Harbour lot", details: "Evenings / weekends" },
      ],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      {
        key: "auto_location",
        type: "toggle",
        label: "Use address from Site Settings",
        help: "Automatically geocode the venue address to place the marker.",
      },
      {
        key: "address_override",
        type: "textarea",
        label: "Custom address",
        rows: 2,
        help: "Optional override when the venue has a different public-facing address.",
      },
      {
        key: "latitude",
        type: "number",
        label: "Latitude",
        step: 0.0001,
        help: "Use decimal degrees (e.g. 47.6593). Leave blank to keep using the geocoded address.",
        disabledWhen: { key: "auto_location", value: true },
      },
      {
        key: "longitude",
        type: "number",
        label: "Longitude",
        step: 0.0001,
        help: "Use decimal degrees (e.g. 9.1749). Leave blank to keep using the geocoded address.",
        disabledWhen: { key: "auto_location", value: true },
      },
      {
        key: "zoom",
        type: "number",
        label: "Zoom level",
        min: 2,
        max: 19,
        help: "Higher values zoom in further. Default: 15.",
      },
      { key: "show_transport", type: "toggle", label: "Show public transport options" },
      {
        key: "transport_heading",
        type: "text",
        label: "Transport heading",
        disabledWhen: { key: "show_transport", value: false },
      },
      {
        key: "transport_items",
        type: "list",
        label: "Transport entries",
        disabledWhen: { key: "show_transport", value: false },
        itemLabel: "Stop",
        itemDefaults: { label: "", details: "" },
        itemFields: [
          { key: "label", type: "text", label: "Name" },
          { key: "details", type: "text", label: "Details" },
        ],
      },
      { key: "show_parking", type: "toggle", label: "Show parking options" },
      {
        key: "parking_heading",
        type: "text",
        label: "Parking heading",
        disabledWhen: { key: "show_parking", value: false },
      },
      {
        key: "parking_items",
        type: "list",
        label: "Parking entries",
        disabledWhen: { key: "show_parking", value: false },
        itemLabel: "Parking spot",
        itemDefaults: { label: "", details: "" },
        itemFields: [
          { key: "label", type: "text", label: "Name" },
          { key: "details", type: "text", label: "Details" },
        ],
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Subtitle" },
    ],
  },
  {
    type: "gallery",
    icon: "🖼️",
    label: "Gallery",
    category: "media",
    description: "Grid of images with optional captions.",
    defaults: {
      title: "Gallery",
      subtitle: "",
      columns: 3,
      items: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "columns", type: "number", label: "Columns", min: 1, max: 4 },
      {
        key: "items",
        type: "list",
        label: "Images",
        itemLabel: "Image",
        itemDefaults: { image: "", caption: "", alt: "" },
        itemFields: [
          { key: "image", type: "url", label: "Image URL", assetKinds: ["image"] },
          { key: "caption", type: "text", label: "Caption" },
          { key: "alt", type: "text", label: "Alt text" },
        ],
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "media_carousel",
    icon: "📽️",
    label: "Media carousel",
    category: "media",
    description: "Full-bleed carousel for images or videos from digital assets.",
    defaults: {
      title: "Featured media",
      subtitle: "",
      autoplay: false,
      autoplay_interval: 6,
      show_thumbnails: true,
      items: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "autoplay", type: "toggle", label: "Autoplay slides" },
      {
        key: "autoplay_interval",
        type: "number",
        label: "Autoplay interval (seconds)",
        min: 3,
        max: 30,
        step: 1,
        disabledWhen: { key: "autoplay", value: false },
      },
      { key: "show_thumbnails", type: "toggle", label: "Show thumbnails" },
      {
        key: "items",
        type: "list",
        label: "Slides",
        itemLabel: "Slide",
        itemDefaults: {
          asset: null,
          caption: "",
          description: "",
          cta_label: "",
          cta_url: "",
        },
        itemFields: [
          {
            key: "asset",
            type: "asset",
            label: "Media asset",
            assetKinds: ["image", "video"],
            allowUpload: true,
          },
          { key: "caption", type: "text", label: "Caption" },
          { key: "description", type: "textarea", label: "Description", rows: 2 },
          { key: "cta_label", type: "text", label: "Button label" },
          { key: "cta_url", type: "url", label: "Button link" },
        ],
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "media_player",
    icon: "🎧",
    label: "Media player",
    category: "media",
    description: "Playlist of uploaded audio or video assets with inline players.",
    defaults: {
      title: "Listen & watch",
      subtitle: "",
      layout: "list",
      show_downloads: false,
      items: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      {
        key: "layout",
        type: "select",
        label: "Layout",
        options: [
          { value: "list", label: "Stacked list" },
          { value: "grid", label: "Grid" },
        ],
      },
      { key: "show_downloads", type: "toggle", label: "Show download links" },
      {
        key: "items",
        type: "list",
        label: "Tracks",
        itemLabel: "Track",
        itemDefaults: {
          asset: null,
          title: "",
          description: "",
        },
        itemFields: [
          {
            key: "asset",
            type: "asset",
            label: "Audio or video asset",
            assetKinds: ["audio", "video"],
            allowUpload: true,
          },
          { key: "title", type: "text", label: "Display title" },
          { key: "description", type: "textarea", label: "Description", rows: 2 },
        ],
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "download_list",
    icon: "⬇️",
    label: "Download list",
    category: "media",
    description: "Curated list of downloadable assets with optional previews.",
    defaults: {
      title: "Downloads",
      subtitle: "",
      show_icons: true,
      items: [],
    },
    fields: [
      { key: "title", type: "text", label: "Section title" },
      { key: "subtitle", type: "textarea", label: "Subtitle", rows: 2 },
      { key: "show_icons", type: "toggle", label: "Show file type icons" },
      {
        key: "items",
        type: "list",
        label: "Downloads",
        itemLabel: "Asset",
        itemDefaults: {
          asset: null,
          label: "",
          description: "",
          button_label: "Download",
        },
        itemFields: [
          {
            key: "asset",
            type: "asset",
            label: "Asset",
            assetKinds: [],
            allowUpload: true,
          },
          { key: "label", type: "text", label: "Title override" },
          { key: "description", type: "textarea", label: "Description", rows: 2 },
          { key: "button_label", type: "text", label: "Button label" },
        ],
      },
    ],
    styleTargets: [
      { key: "title", label: "Section title" },
      { key: "subtitle", label: "Section subtitle" },
    ],
  },
  {
    type: "footer",
    icon: "🦶",
    label: "Footer",
    category: "navigation",
    description: "Layered footer with brand story, navigation, legal, and social links.",
    defaults: {
      brand_name: "",
      brand_tagline: "",
      brand_logo: "",
      brand_logo_width: null,
      address_html: "",
      links_heading: "Explore",
      legal_heading: "Legal",
      social_heading: "Connect",
      links: [],
      legal: [],
      social_links: [],
      show_language_switcher: true,
    },
    fields: [
      { key: "brand_name", type: "text", label: "Brand name" },
      { key: "brand_tagline", type: "text", label: "Tagline", help: "Optional short line that appears under the brand." },
      {
        key: "brand_logo",
        type: "url",
        label: "Logo URL",
        help: "Paste an image URL from the media library.",
        assetKinds: ["image"],
      },
      {
        key: "brand_logo_width",
        type: "number",
        label: "Logo width (px)",
        min: 40,
        max: 800,
        help: "Optional fixed width for the footer logo.",
      },
      {
        key: "address_html",
        type: "textarea",
        label: "About / contact text",
        rows: 3,
        help: "Supports line breaks to highlight address, office hours, or other notes.",
      },
      {
        key: "links_heading",
        type: "text",
        label: "Primary links heading",
        help: "Optional title shown above the primary link column.",
      },
      {
        key: "links",
        type: "list",
        label: "Primary links",
        itemLabel: "Link",
        itemDefaults: { label: "About", href: "#", new_tab: false },
        modal: {
          title: "Footer navigation links",
          description: "Add and reorder the primary footer links.",
        },
        itemFields: [
          { key: "label", type: "text", label: "Label" },
          { key: "href", type: "url", label: "URL" },
          { key: "new_tab", type: "toggle", label: "Open in new tab" },
        ],
      },
      {
        key: "legal_heading",
        type: "text",
        label: "Legal links heading",
        help: "Optional title shown above the legal / utility links.",
      },
      {
        key: "legal",
        type: "list",
        label: "Legal links",
        itemLabel: "Link",
        itemDefaults: { label: "Imprint", href: "#", new_tab: false },
        modal: {
          title: "Footer legal links",
          description: "Add legal and policy links displayed in the footer.",
        },
        itemFields: [
          { key: "label", type: "text", label: "Label" },
          { key: "href", type: "url", label: "URL" },
          { key: "new_tab", type: "toggle", label: "Open in new tab" },
        ],
      },
      {
        key: "social_heading",
        type: "text",
        label: "Social heading",
        help: "Optional title shown above social link chips.",
      },
      {
        key: "social_links",
        type: "list",
        label: "Social links",
        itemLabel: "Profile",
        itemDefaults: { label: "Instagram", href: "#", new_tab: true },
        modal: {
          title: "Footer social links",
          description: "Add social profiles to display as chips in the footer.",
        },
        itemFields: [
          { key: "label", type: "text", label: "Platform" },
          { key: "href", type: "url", label: "URL" },
          { key: "new_tab", type: "toggle", label: "Open in new tab" },
        ],
      },
      {
        key: "show_language_switcher",
        type: "toggle",
        label: "Show language switcher",
      },
    ],
  },
];

const STYLE_DEFAULTS = Object.freeze({
  font_family: "",
  font_size: "",
  text_color: "",
  background_color: "",
  font_asset: null,
});

const STYLE_FONT_OPTIONS = [
  { value: "", label: "Match site theme" },
  { value: "sans", label: "Sans serif" },
  { value: "serif", label: "Serif" },
  { value: "mono", label: "Monospace" },
  { value: "display", label: "Display / All caps" },
  { value: "press_start", label: "Press Start 2P" },
  { value: "archivo_black", label: "Archivo Black" },
  { value: "glass_antiqua", label: "Glass Antiqua" },
  { value: "im_fell", label: "IM Fell DW Pica" },
  { value: "orbitron", label: "Orbitron" },
  { value: "pathway_extreme", label: "Pathway Extreme" },
  { value: "raleway", label: "Raleway" },
  { value: "special_elite", label: "Special Elite" },
  { value: "staatliches", label: "Staatliches" },
];

const STYLE_FONT_SIZE_OPTIONS = [
  { value: "", label: "Theme default" },
  { value: "xs", label: "XS" },
  { value: "sm", label: "Small" },
  { value: "base", label: "Base" },
  { value: "lg", label: "Large" },
  { value: "xl", label: "Extra large" },
  { value: "xxl", label: "Hero" },
];

const CONTACT_FIELD_BLUEPRINT = [
  { value: "address", label: "Address" },
  { value: "phone", label: "Phone" },
  { value: "email", label: "Email" },
  { value: "website", label: "Website" },
];

const SOCIAL_FIELD_BLUEPRINT = [
  { value: "facebook", label: "Facebook" },
  { value: "instagram", label: "Instagram" },
  { value: "twitter", label: "Twitter" },
  { value: "tiktok", label: "TikTok" },
  { value: "youtube", label: "YouTube" },
  { value: "spotify", label: "Spotify" },
  { value: "soundcloud", label: "SoundCloud" },
  { value: "bandcamp", label: "Bandcamp" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "mastodon", label: "Mastodon" },
];

const state = {
  blocks: [],
  selectedId: null,
  dirty: false,
  siteContext: null,
  siteLoading: false,
  theme: normaliseTheme({}),
  themeSnapshot: {
    body: {},
    sections: {},
  },
};

function escapeHtml(value = "") {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function rgbToHex(value) {
  if (!value) {
    return "";
  }
  const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
  if (!match) {
    return "";
  }
  const toHex = (num) => Number(num).toString(16).padStart(2, "0");
  return `#${toHex(match[1])}${toHex(match[2])}${toHex(match[3])}`.toUpperCase();
}

function updateThemeSnapshotFromFrame(frame) {
  if (!frame || !frame.contentDocument) {
    return;
  }
  const doc = frame.contentDocument;
  const body = doc.body;
  if (!body) {
    return;
  }
  const bodyStyles = frame.contentWindow?.getComputedStyle(body);
  const sectionTarget =
    doc.querySelector(".page-block") ||
    doc.querySelector(".page-block__container") ||
    body;
  const sectionStyles = frame.contentWindow?.getComputedStyle(sectionTarget);
  state.themeSnapshot = {
    body: {
      font_family: bodyStyles?.fontFamily || "",
      font_size: bodyStyles?.fontSize || "",
      text_color: rgbToHex(bodyStyles?.color || ""),
      background_color: rgbToHex(bodyStyles?.backgroundColor || ""),
    },
    sections: {
      font_family: sectionStyles?.fontFamily || "",
      font_size: sectionStyles?.fontSize || "",
      text_color: rgbToHex(sectionStyles?.color || ""),
      background_color: rgbToHex(sectionStyles?.backgroundColor || ""),
    },
  };
  renderThemeCard();
}

function cssUrl(value = "") {
  return String(value).replace(/"/g, '\\"');
}

function formatAddressPreview(address = {}) {
  if (!address) return "";
  const line1 = [address.street, address.number].filter(Boolean).join(" ").trim();
  const line2 = [address.postal_code, address.city].filter(Boolean).join(" ").trim();
  const parts = [line1, line2, address.country].filter(Boolean);
  return parts.join(", ");
}

function buildContactOptions() {
  const site = state.siteContext;
  if (!site) {
    return CONTACT_FIELD_BLUEPRINT;
  }
  const contact = site.contact || {};
  const options = [];
  const addressPreview = formatAddressPreview(site.address || {});
  options.push({
    value: "address",
    label: addressPreview ? `Address - ${addressPreview}` : "Address (not set)",
    disabled: !addressPreview,
  });
  options.push({
    value: "phone",
    label: contact.phone ? `Phone - ${contact.phone}` : "Phone (not set)",
    disabled: !contact.phone,
  });
  options.push({
    value: "email",
    label: contact.email ? `Email - ${contact.email}` : "Email (not set)",
    disabled: !contact.email,
  });
  options.push({
    value: "website",
    label: contact.website ? `Website - ${contact.website}` : "Website (not set)",
    disabled: !contact.website,
  });
  return options;
}

function buildSocialOptions() {
  const site = state.siteContext;
  if (!site) {
    return SOCIAL_FIELD_BLUEPRINT;
  }
  const social = site.social || {};
  return SOCIAL_FIELD_BLUEPRINT.map((option) => {
    const value = social[option.value];
    return {
      value: option.value,
      label: value ? `${option.label} - ${value}` : `${option.label} (not set)`,
      disabled: !value,
    };
  });
}

function getCheckboxOptions(field) {
  if (Array.isArray(field.options)) {
    return field.options;
  }
  if (field.optionsSource === "contact") {
    return buildContactOptions();
  }
  if (field.optionsSource === "social") {
    return buildSocialOptions();
  }
  if (typeof field.getOptions === "function") {
    return field.getOptions(state, field);
  }
  return [];
}

function hashString(value) {
  let hash = 0;
  const str = String(value || "");
  for (let i = 0; i < str.length; i += 1) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

function guessFontFormat(url, mime) {
  const mimeMap = {
    "font/woff2": "woff2",
    "font/woff": "woff",
    "font/otf": "opentype",
    "font/ttf": "truetype",
    "application/font-woff": "woff",
  };
  if (mime && typeof mime === "string") {
    const lower = mime.toLowerCase();
    if (mimeMap[lower]) {
      return mimeMap[lower];
    }
  }
  const base = (url || "").split("?", 1)[0];
  const ext = (base.split(".").pop() || "").toLowerCase();
  return (
    {
      woff2: "woff2",
      woff: "woff",
      otf: "opentype",
      ttf: "truetype",
    }[ext] || "truetype"
  );
}

function normaliseFontAsset(asset, index = 0) {
  if (!asset || !asset.url) {
    return null;
  }
  const rawTitle =
    (asset.title || asset.slug || `Font ${index + 1}`).trim() || `Font ${index + 1}`;
  const label = rawTitle.replace(/;/g, ",");
  const idPart =
    asset.id != null ? String(asset.id) : `${label}-${index}-${asset.url.slice(-6)}`;
  const family = `CMSInlineFont-${hashString(`${idPart}`)}`;
  return {
    id: asset.id,
    title: rawTitle,
    label,
    url: asset.url,
    family,
    format: guessFontFormat(asset.url, asset.mime_type),
  };
}

function toStyleFontAsset(asset) {
  if (!asset || !asset.url) {
    return null;
  }
  return {
    id: asset.id ?? null,
    title: asset.title || asset.label || "Custom font",
    url: asset.url,
    format: asset.format,
  };
}

function buildFontAssetControls(options = {}) {
  const {
    placeholder = "Use theme font",
    currentAsset = null,
    context = "popover",
    onChange = () => {},
  } = options;
  const fonts = fontState.assets || [];
  const controls = document.createElement("div");
  controls.className =
    context === "popover" ? "builder-style-popover__font-asset" : "builder-font-asset-controls";
  const select = document.createElement("select");
  const placeholderOption = document.createElement("option");
  placeholderOption.value = "";
  placeholderOption.textContent = fonts.length ? placeholder : "No fonts available";
  select.appendChild(placeholderOption);
  let selectedFamily = "";
  fonts.forEach((asset) => {
    const opt = document.createElement("option");
    opt.value = asset.family;
    opt.textContent = asset.label;
    if (
      currentAsset &&
      (currentAsset.url === asset.url || (currentAsset.id != null && currentAsset.id === asset.id))
    ) {
      selectedFamily = asset.family;
    }
    select.appendChild(opt);
  });
  select.value = selectedFamily;
  select.disabled = !fonts.length;
  select.addEventListener("change", (event) => {
    const family = event.target.value;
    if (!family) {
      onChange(null);
      return;
    }
    const asset = fonts.find((item) => item.family === family);
    if (asset) {
      onChange(toStyleFontAsset(asset));
    }
  });
  controls.appendChild(select);

  const browseFonts = document.createElement("button");
  browseFonts.type = "button";
  browseFonts.className = "btn btn-xs btn-outline-secondary";
  browseFonts.textContent = "Browse fonts";
  browseFonts.addEventListener("click", () => {
    openAssetBrowser({
      kinds: ["font"],
      onSelect(asset) {
        const normalized = normaliseFontAsset(asset, fonts.length);
        if (!normalized) {
          alert("Could not use that font asset.");
          return;
        }
        const payload = toStyleFontAsset(normalized);
        onChange(payload);
        fetchFontAssets(true).finally(() => {
          if (context === "popover") {
            if (isStylePopoverOpen()) {
              refreshStylePopover();
            }
          } else if (dom.settings) {
            renderSettings();
          }
        });
      },
    });
  });
  controls.appendChild(browseFonts);

  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "btn btn-xs btn-outline-secondary";
  clearBtn.textContent = "Clear";
  clearBtn.disabled = !currentAsset;
  clearBtn.addEventListener("click", () => {
    onChange(null);
    if (context !== "popover") {
      clearBtn.disabled = true;
      select.value = "";
    }
  });
  controls.appendChild(clearBtn);
  return controls;
}

function formatFileSize(bytes) {
  const size = Number(bytes);
  if (!Number.isFinite(size) || size <= 0) {
    return "";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  const units = ["KB", "MB", "GB", "TB"];
  let value = size / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatDuration(seconds) {
  const total = Number(seconds);
  if (!Number.isFinite(total) || total <= 0) {
    return "";
  }
  const hrs = Math.floor(total / 3600);
  const mins = Math.floor((total % 3600) / 60);
  const secs = Math.floor(total % 60);
  const parts = [];
  if (hrs) {
    parts.push(String(hrs).padStart(2, "0"));
  }
  parts.push(String(hrs ? mins : mins).padStart(2, "0"));
  parts.push(String(secs).padStart(2, "0"));
  return parts.join(":");
}

function normaliseBuilderAsset(asset) {
  if (!asset || (!asset.id && !asset.url)) {
    return null;
  }
  return {
    id: asset.id ?? null,
    title: asset.title || asset.slug || "Asset",
    slug: asset.slug || "",
    kind: asset.kind || "other",
    description: asset.description || "",
    url: asset.url || "",
    mime_type: asset.mime_type || "",
    size_bytes: Number.isFinite(asset.size_bytes) ? asset.size_bytes : null,
    width: Number.isFinite(asset.width) ? asset.width : null,
    height: Number.isFinite(asset.height) ? asset.height : null,
    duration_seconds: Number.isFinite(asset.duration_seconds) ? asset.duration_seconds : null,
    collection: asset.collection || null,
    is_external: Boolean(asset.is_external),
    external_domain: asset.external_domain || "",
  };
}

function buildAssetPreviewCard(asset) {
  const card = document.createElement("div");
  card.className = "builder-asset-card";
  const thumb = document.createElement("div");
  thumb.className = `builder-asset-card__thumb builder-asset-card__thumb--${asset.kind || "other"}`;
  if (asset.kind === "image" && asset.url) {
    thumb.style.backgroundImage = `url(\"${cssUrl(asset.url)}\")`;
  } else {
    const icon = document.createElement("span");
    icon.textContent =
      {
        video: "▶",
        audio: "♫",
        pdf: "📄",
        doc: "📑",
        archive: "🗂",
        font: "𝐀",
      }[asset.kind] || "⬇";
    thumb.appendChild(icon);
  }
  card.appendChild(thumb);

  const meta = document.createElement("div");
  meta.className = "builder-asset-card__meta";
  const title = document.createElement("strong");
  title.textContent = asset.title || "Selected asset";
  meta.appendChild(title);
  const details = document.createElement("span");
  const bits = [];
  if (asset.kind) {
    bits.push(asset.kind.toUpperCase());
  }
  const sizeLabel = formatFileSize(asset.size_bytes);
  if (sizeLabel) {
    bits.push(sizeLabel);
  }
  const durationLabel = formatDuration(asset.duration_seconds);
  if (durationLabel) {
    bits.push(durationLabel);
  }
  details.textContent = bits.join(" · ");
  meta.appendChild(details);
  card.appendChild(meta);

  return card;
}

function getDefaultBrandText() {
  return (state.siteContext && state.siteContext.name) || "";
}

function applySiteBrandTextDefaults(options = {}) {
  const defaultText = getDefaultBrandText();
  if (!defaultText || !state.blocks.length) {
    return false;
  }
  let changed = false;
  state.blocks.forEach((block) => {
    if (block.type !== "navigation") {
      return;
    }
    if (block.props && block.props.logo_text_auto === false) {
      return;
    }
    if (block.props) {
      block.props.logo_text_auto = true;
      if (block.props.logo_text !== defaultText) {
        block.props.logo_text = defaultText;
        changed = true;
      }
    }
  });
  if (changed && !options.silent) {
    persistBlocks();
    renderSettings();
    schedulePreview();
  }
  return changed;
}

function fetchFontAssets(force = false) {
  if (!config.urls || !config.urls.assets) {
    return Promise.resolve([]);
  }
  if (fontState.promise && !force) {
    return fontState.promise;
  }
  const params = new URLSearchParams();
  params.append("kind", "font");
  const url = `${config.urls.assets}?${params.toString()}`;
  fontState.promise = fetch(url, {
    headers: { "X-Requested-With": "XMLHttpRequest" },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to load fonts (${response.status})`);
      }
      return response.json();
    })
    .then((data) => {
      const assets = (data.assets || []).map(normaliseFontAsset).filter(Boolean);
      fontState.assets = assets;
      fontState.byFamily = new Map(assets.map((asset) => [asset.family, asset]));
      return assets;
    })
    .catch((error) => {
      console.error(error);
      fontState.assets = [];
      fontState.byFamily = new Map();
      return [];
    });
  return fontState.promise;
}

function buildFontFamilyFormats(fonts) {
  const extra = (fonts || []).map((font) => `${font.label}=${font.family}`).join(";");
  return [DEFAULT_FONT_FORMATS, extra].filter(Boolean).join(";");
}

const INLINE_EDITOR_SRC = "https://cdn.jsdelivr.net/npm/tinymce@7.1.2/tinymce.min.js";
const INLINE_IMAGE_STYLE_ID = "inline-image-resize-style";
const INLINE_FONT_STYLE_ID = "inline-font-assets-style";
const INLINE_IMAGE_STYLE = `
  .inline-image-resize-target {
    outline: 1px dashed rgba(59, 130, 246, 0.8);
    outline-offset: 2px;
    position: relative;
  }
  .inline-image-resize-handle {
    position: fixed;
    width: 16px;
    height: 16px;
    border-radius: 999px;
    border: 2px solid rgba(59, 130, 246, 1);
    background: rgba(15, 23, 42, 0.95);
    box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.6);
    z-index: 999999;
    cursor: nwse-resize;
    padding: 0;
    display: none;
  }
  .inline-image-resize-handle::after {
    content: "";
    position: absolute;
    inset: 3px;
    border-right: 2px solid rgba(59, 130, 246, 0.8);
    border-bottom: 2px solid rgba(59, 130, 246, 0.8);
    transform: rotate(0deg);
  }
`;

const DEFAULT_FONT_FORMATS = [
  "Andale Mono=andale mono,times",
  "Arial=arial,helvetica,sans-serif",
  "Arial Black=arial black,avant garde",
  "Book Antiqua=book antiqua,palatino",
  "Comic Sans MS=comic sans ms,sans-serif",
  "Courier New=courier new,courier",
  "Georgia=georgia,palatino",
  "Helvetica=helvetica",
  "Impact=impact,chicago",
  "Symbol=symbol",
  "Tahoma=tahoma,arial,helvetica,sans-serif",
  "Terminal=terminal,monaco",
  "Times New Roman=times new roman,times",
  "Trebuchet MS=trebuchet ms,geneva",
  "Verdana=verdana,geneva",
  "Webdings=webdings",
  "Wingdings=wingdings,zapf dingbats",
  "Archivo Black='Archivo Black','Arial Black',sans-serif",
  "Glass Antiqua='Glass Antiqua','Comic Sans MS',cursive",
  "IM Fell DW Pica='IM Fell DW Pica',Georgia,serif",
  "Orbitron='Orbitron','Segoe UI',sans-serif",
  "Pathway Extreme='Pathway Extreme','Raleway',sans-serif",
  "Press Start 2P='Press Start 2P',cursive",
  "Raleway='Raleway','Helvetica Neue',sans-serif",
  "Special Elite='Special Elite','Courier New',monospace",
  "Staatliches='Staatliches','Archivo Black',sans-serif",
].join(";");

const dom = {};
let config = {};
let previewTimer = null;
let previewInflight = null;
let siteContextRequest = null;
const inlineState = {
  enabled: false,
  editors: new Map(),
  imageResizers: new Map(),
};

const fontState = {
  assets: [],
  byFamily: new Map(),
  promise: null,
};

const assetState = {
  modal: null,
  panel: null,
  overlay: null,
  closeButtons: [],
  list: null,
  subtitle: null,
  kinds: [],
  cache: {},
  onSelect: null,
};

const listEditorState = {
  modal: null,
  panel: null,
  title: null,
  description: null,
  body: null,
};

const stylePopoverState = {
  panel: null,
  header: null,
  title: null,
  body: null,
  current: null,
  anchorRect: null,
};

function isAssetBrowserOpen() {
  return assetState.modal && !assetState.modal.classList.contains("is-hidden");
}

function closeAssetBrowser() {
  if (!assetState.modal) {
    return;
  }
  assetState.modal.classList.add("is-hidden");
  assetState.modal.setAttribute("aria-hidden", "true");
  assetState.onSelect = null;
  assetState.kinds = [];
}

function ensureListEditorModal() {
  if (listEditorState.modal) {
    return;
  }
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.hidden = true;
  const card = document.createElement("div");
  card.className = "modal-card dark";
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-modal", "true");

  const header = document.createElement("header");
  header.className = "modal-header";
  const title = document.createElement("h2");
  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn btn-xs btn-outline-secondary";
  closeBtn.textContent = "Close";
  closeBtn.addEventListener("click", () => closeListEditor());
  header.appendChild(title);
  header.appendChild(closeBtn);

  const description = document.createElement("p");
  description.className = "muted";
  const body = document.createElement("div");
  body.className = "modal-form";

  card.appendChild(header);
  card.appendChild(description);
  card.appendChild(body);
  overlay.appendChild(card);
  overlay.addEventListener("click", (event) => {
    if (!event.target.closest(".modal-card")) {
      closeListEditor();
    }
  });

  document.body.appendChild(overlay);
  listEditorState.modal = overlay;
  listEditorState.panel = card;
  listEditorState.title = title;
  listEditorState.description = description;
  listEditorState.body = body;
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeListEditor();
    }
  });
}

function openListEditor(block, field) {
  ensureListEditorModal();
  if (!listEditorState.modal || !listEditorState.body) {
    return;
  }
  listEditorState.title.textContent = field.modal?.title || field.label || "Edit items";
  listEditorState.description.textContent = field.modal?.description || "";
  listEditorState.body.innerHTML = "";
  listEditorState.body.appendChild(renderListField(block, field));
  listEditorState.modal.hidden = false;
  document.body.classList.add("modal-open");
}

function closeListEditor() {
  if (!listEditorState.modal) {
    return;
  }
  listEditorState.modal.hidden = true;
  document.body.classList.remove("modal-open");
  renderSettings();
}

function openAdvancedStyleFromPreview(blockId) {
  if (!blockId) {
    return;
  }
  selectBlock(blockId);
  window.requestAnimationFrame(() => {
    const section = dom.settings?.querySelector("[data-advanced-style]");
    if (!section) {
      return;
    }
    section.classList.add("is-highlighted");
    section.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => {
      section.classList.remove("is-highlighted");
    }, 1200);
  });
}

function renderAssetCards(assets) {
  if (!assetState.list) {
    return;
  }
  assetState.list.innerHTML = "";
  if (!assets.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No assets available yet.";
    assetState.list.appendChild(empty);
    return;
  }

  assets.forEach((asset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `asset-card asset-card--${asset.kind}`;
    const title = escapeHtml(asset.title || asset.slug || asset.kind);
    let thumb = "";
    if (asset.kind === "image" && asset.url) {
      thumb = `<div class="asset-card__thumbnail" style="background-image:url(&quot;${cssUrl(asset.url)}&quot;);"></div>`;
    } else {
      const icon = asset.kind ? escapeHtml(asset.kind.slice(0, 1).toUpperCase()) : "•";
      thumb = `<div class="asset-card__thumbnail asset-card__thumbnail--icon">${icon}</div>`;
    }
    const kindLabel = escapeHtml((asset.kind || "").toUpperCase());
    const mimeLabel = asset.mime_type ? ` · ${escapeHtml(asset.mime_type)}` : "";
    const meta = `
      <div class="asset-card__meta">
        <strong>${title}</strong>
        <span>${kindLabel}${mimeLabel}</span>
      </div>
    `;
    button.innerHTML = `${thumb}${meta}`;
    button.addEventListener("click", () => {
      if (typeof assetState.onSelect === "function") {
        assetState.onSelect(asset);
      }
      closeAssetBrowser();
    });
    assetState.list.appendChild(button);
  });
}

function uploadBuilderAsset(file, { kind } = {}) {
  if (!config.urls || !config.urls.asset_upload) {
    return Promise.reject(new Error("Asset upload unavailable"));
  }
  const formData = new FormData();
  formData.append("file", file);
  if (kind) {
    formData.append("kind", kind);
  }
  const title = file.name || "Upload";
  formData.append("title", title);
  return fetch(config.urls.asset_upload, {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "XMLHttpRequest" },
    credentials: "same-origin",
    body: formData,
  }).then((response) => {
    if (!response.ok) {
      return response.text().then((text) => {
        throw new Error(text || "Failed to upload asset");
      });
    }
    return response.json();
  });
}

function promptAssetUpload({ accept = "", kind = null } = {}, callback) {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = accept;
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) {
        resolve();
        return;
      }
      uploadBuilderAsset(file, { kind })
        .then((payload) => {
          if (typeof callback === "function" && payload && payload.asset) {
            callback(payload.asset);
          }
        })
        .catch((error) => {
          console.error(error);
          alert(error.message || "Could not upload asset.");
        })
        .finally(resolve);
    });
    input.click();
  });
}

async function loadAssets(kinds) {
  if (!assetState.list) {
    return;
  }
  const key = kinds && kinds.length ? kinds.slice().sort().join(",") : "all";
  if (!assetState.cache[key]) {
    if (!config.urls || !config.urls.assets) {
      assetState.list.innerHTML = "<p class=\"muted\">Asset library unavailable.</p>";
      return;
    }
    const params = new URLSearchParams();
    (kinds || []).forEach((kind) => params.append("kind", kind));
    const url = `${config.urls.assets}${params.toString() ? `?${params.toString()}` : ""}`;
    assetState.list.innerHTML = "<p class=\"muted\">Loading assets…</p>";
    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (!response.ok) {
        throw new Error(`Failed to load assets (${response.status})`);
      }
      const data = await response.json();
      assetState.cache[key] = data.assets || [];
    } catch (error) {
      console.error(error);
      assetState.list.innerHTML = "<p class=\"muted\">Could not load assets.</p>";
      return;
    }
  }
  renderAssetCards(assetState.cache[key]);
}

const HEX_COLOR_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

function normaliseStyleValue(value) {
  const textColor =
    typeof value?.text_color === "string" && HEX_COLOR_RE.test(value.text_color)
      ? normalizeHex(value.text_color)
      : "";
  const backgroundColor =
    typeof value?.background_color === "string" && HEX_COLOR_RE.test(value.background_color)
      ? normalizeHex(value.background_color)
      : "";
  return {
    font_family: typeof value?.font_family === "string" ? value.font_family : "",
    font_size: typeof value?.font_size === "string" ? value.font_size : "",
    text_color: textColor,
    background_color: backgroundColor,
    font_asset: value && typeof value.font_asset === "object" ? { ...value.font_asset } : null,
  };
}

function normalizeHex(value) {
  if (typeof value !== "string") {
    return "";
  }
  const trimmed = value.trim();
  if (!HEX_COLOR_RE.test(trimmed)) {
    return "";
  }
  if (trimmed.length === 4) {
    return `#${trimmed[1]}${trimmed[1]}${trimmed[2]}${trimmed[2]}${trimmed[3]}${trimmed[3]}`.toLowerCase();
  }
  return trimmed.toLowerCase();
}

function normaliseTheme(value) {
  const payload = value && typeof value === "object" ? value : {};
  return {
    body: normaliseStyleValue(payload.body),
    sections: normaliseStyleValue(payload.sections),
  };
}

function getPageTheme() {
  state.theme = normaliseTheme(state.theme);
  return state.theme;
}

function updateThemeSection(sectionKey, patch) {
  const theme = getPageTheme();
  if (!theme[sectionKey]) {
    theme[sectionKey] = normaliseStyleValue({});
  }
  const next = normaliseStyleValue({ ...theme[sectionKey], ...patch });
  state.theme = { ...theme, [sectionKey]: next };
  state.dirty = true;
  persistTheme();
  schedulePreview();
  renderThemeCard();
}

function getBlockBaseStyle(block) {
  if (!block.props) {
    block.props = {};
  }
  const current = normaliseStyleValue(block.props.style);
  block.props.style = current;
  return current;
}

function updateBaseStyle(blockId, patch) {
  const block = state.blocks.find((item) => item.id === blockId);
  if (!block) {
    return;
  }
  const current = getBlockBaseStyle(block);
  const next = normaliseStyleValue({ ...current, ...patch });
  block.props = { ...block.props, style: next };
  state.dirty = true;
  persistBlocks();
  schedulePreview();
  refreshStylePopover();
}

function ensureStyleTargets(block) {
  if (!block.props) {
    block.props = {};
  }
  if (!block.props.style_targets || typeof block.props.style_targets !== "object") {
    block.props.style_targets = {};
  }
  return block.props.style_targets;
}

function getStyleTarget(block, key) {
  const targets = ensureStyleTargets(block);
  const current = normaliseStyleValue(targets[key]);
  targets[key] = current;
  return targets[key];
}

function updateStyleTarget(blockId, key, patch) {
  const block = state.blocks.find((item) => item.id === blockId);
  if (!block) {
    return;
  }
  const targets = ensureStyleTargets(block);
  const current = getStyleTarget(block, key);
  targets[key] = normaliseStyleValue({ ...current, ...patch });
  state.dirty = true;
  persistBlocks();
  schedulePreview();
  refreshStylePopover();
}

function resetStyleTarget(blockId, key) {
  updateStyleTarget(blockId, key, { ...STYLE_DEFAULTS });
}

function isStylePopoverOpen() {
  return stylePopoverState.panel && !stylePopoverState.panel.classList.contains("is-hidden");
}

function closeStylePopover() {
  if (!stylePopoverState.panel) {
    return;
  }
  stylePopoverState.panel.classList.add("is-hidden");
  stylePopoverState.panel.style.top = "";
  stylePopoverState.panel.style.left = "";
  stylePopoverState.current = null;
  stylePopoverState.anchorRect = null;
}

function renderStylePopover(block, config) {
  if (!stylePopoverState.body || !config) {
    return;
  }
  const style = getStyleTarget(block, config.targetKey);
  stylePopoverState.title.textContent = `${config.label || "Text"} style`;
  stylePopoverState.body.innerHTML = "";

  const fontField = document.createElement("div");
  fontField.className = "builder-field";
  const fontLabel = document.createElement("label");
  fontLabel.textContent = "Font family";
  const fontSelect = document.createElement("select");
  STYLE_FONT_OPTIONS.forEach((option) => {
    const opt = document.createElement("option");
    opt.value = option.value;
    opt.textContent = option.label;
    fontSelect.appendChild(opt);
  });
  fontSelect.value = style.font_family || "";
  fontSelect.addEventListener("change", (event) => {
    updateStyleTarget(block.id, config.targetKey, { font_family: event.target.value });
  });
  fontField.appendChild(fontLabel);
  fontField.appendChild(fontSelect);
  stylePopoverState.body.appendChild(fontField);

  const assetField = document.createElement("div");
  assetField.className = "builder-field";
  const assetLabel = document.createElement("label");
  assetLabel.textContent = "Uploaded font";
  const assetHint = document.createElement("small");
  assetHint.className = "muted";
  assetHint.textContent = fontState.assets.length
    ? "Fonts synced from Assets → Fonts."
    : "Upload fonts in Assets → Fonts to use them here.";
  const assetControls = buildFontAssetControls({
    context: "popover",
    currentAsset: style.font_asset,
    placeholder: "Use theme font",
    onChange(payload) {
      updateStyleTarget(block.id, config.targetKey, { font_asset: payload, font_family: "" });
    },
  });
  assetField.appendChild(assetLabel);
  assetField.appendChild(assetHint);
  assetField.appendChild(assetControls);
  stylePopoverState.body.appendChild(assetField);

  const sizeField = document.createElement("div");
  sizeField.className = "builder-field";
  const sizeLabel = document.createElement("label");
  sizeLabel.textContent = "Font size";
  const sizeSelect = document.createElement("select");
  STYLE_FONT_SIZE_OPTIONS.forEach((option) => {
    const opt = document.createElement("option");
    opt.value = option.value;
    opt.textContent = option.label;
    sizeSelect.appendChild(opt);
  });
  sizeSelect.value = style.font_size || "";
  sizeSelect.addEventListener("change", (event) => {
    updateStyleTarget(block.id, config.targetKey, { font_size: event.target.value });
  });
  sizeField.appendChild(sizeLabel);
  sizeField.appendChild(sizeSelect);
  stylePopoverState.body.appendChild(sizeField);

  const colorField = document.createElement("div");
  colorField.className = "builder-field";
  const colorLabel = document.createElement("label");
  colorLabel.textContent = "Text color";
  const colorHint = document.createElement("small");
  colorHint.className = "muted";
  colorHint.textContent = style.text_color ? style.text_color.toUpperCase() : "Using theme default";
  const colorControls = document.createElement("div");
  colorControls.className = "builder-style-popover__color";
  const colorInput = document.createElement("input");
  colorInput.type = "color";
  colorInput.value = style.text_color || "#ffffff";
  colorInput.addEventListener("input", (event) => {
    updateStyleTarget(block.id, config.targetKey, { text_color: event.target.value });
  });
  const clearColor = document.createElement("button");
  clearColor.type = "button";
  clearColor.className = "btn btn-xs btn-outline-secondary";
  clearColor.textContent = "Clear";
  clearColor.disabled = !style.text_color;
  clearColor.addEventListener("click", () => {
    updateStyleTarget(block.id, config.targetKey, { text_color: "" });
  });
  colorControls.appendChild(colorInput);
  colorControls.appendChild(clearColor);
  colorField.appendChild(colorLabel);
  colorField.appendChild(colorHint);
  colorField.appendChild(colorControls);
  stylePopoverState.body.appendChild(colorField);

  const actions = document.createElement("div");
  actions.className = "builder-style-popover__actions";
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.className = "btn btn-xs btn-outline-secondary";
  resetBtn.textContent = "Reset styles";
  resetBtn.addEventListener("click", () => {
    resetStyleTarget(block.id, config.targetKey);
  });
  actions.appendChild(resetBtn);
  stylePopoverState.body.appendChild(actions);
}

function positionStylePopover(anchorRect) {
  if (!stylePopoverState.panel) {
    return;
  }
  const rect = anchorRect || stylePopoverState.anchorRect;
  if (!rect) {
    return;
  }
  const panel = stylePopoverState.panel;
  panel.style.top = "0px";
  panel.style.left = "0px";
  const padding = 12;
  const { width, height } = panel.getBoundingClientRect();
  let top = rect.bottom + 8;
  let left = rect.left;
  if (top + height > window.innerHeight - padding) {
    const above = rect.top - height - 8;
    if (above >= padding) {
      top = above;
    } else {
      top = Math.max(padding, window.innerHeight - height - padding);
    }
  }
  if (top < padding) {
    top = padding;
  }
  if (left + width > window.innerWidth - padding) {
    const shiftLeft = rect.right - width;
    if (shiftLeft >= padding) {
      left = shiftLeft;
    } else {
      left = window.innerWidth - width - padding;
    }
  }
  if (left < padding) {
    left = padding;
  }
  panel.style.top = `${top}px`;
  panel.style.left = `${left}px`;
}

function refreshStylePopover() {
  if (!isStylePopoverOpen() || !stylePopoverState.current) {
    return;
  }
  const block = state.blocks.find((item) => item.id === stylePopoverState.current.blockId);
  if (!block) {
    closeStylePopover();
    return;
  }
  renderStylePopover(block, stylePopoverState.current);
  positionStylePopover();
}

function openStylePopover(config) {
  initStylePopover();
  const block = state.blocks.find((item) => item.id === config.blockId);
  if (!block || !stylePopoverState.panel) {
    return;
  }
  stylePopoverState.current = {
    blockId: block.id,
    targetKey: config.targetKey,
    label: config.label || "Text",
  };
  stylePopoverState.anchorRect = config.anchor
    ? {
        top: config.anchor.top,
        left: config.anchor.left,
        bottom: config.anchor.bottom,
        width: config.anchor.width,
        height: config.anchor.height,
      }
    : null;
  stylePopoverState.panel.classList.remove("is-hidden");
  renderStylePopover(block, stylePopoverState.current);
  positionStylePopover(stylePopoverState.anchorRect);
  fetchFontAssets()
    .catch(() => [])
    .then(() => {
      if (!isStylePopoverOpen()) {
        return;
      }
      if (
        !stylePopoverState.current ||
        stylePopoverState.current.blockId !== block.id ||
        stylePopoverState.current.targetKey !== config.targetKey
      ) {
        return;
      }
      const refreshedBlock = state.blocks.find((item) => item.id === block.id);
      if (!refreshedBlock) {
        return;
      }
      renderStylePopover(refreshedBlock, stylePopoverState.current);
      positionStylePopover(stylePopoverState.anchorRect);
    });
}

function initStylePopover() {
  if (stylePopoverState.panel) {
    return;
  }
  const panel = document.createElement("div");
  panel.id = "builder-style-popover";
  panel.className = "builder-style-popover is-hidden";
  const header = document.createElement("div");
  header.className = "builder-style-popover__header";
  const title = document.createElement("strong");
  title.textContent = "Text style";
  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn btn-xs btn-outline-secondary";
  closeBtn.textContent = "Close";
  closeBtn.addEventListener("click", closeStylePopover);
  header.appendChild(title);
  header.appendChild(closeBtn);
  const body = document.createElement("div");
  body.className = "builder-style-popover__body";
  panel.appendChild(header);
  panel.appendChild(body);
  document.body.appendChild(panel);
  stylePopoverState.panel = panel;
  stylePopoverState.header = header;
  stylePopoverState.title = title;
  stylePopoverState.body = body;

  document.addEventListener("click", (event) => {
    if (!isStylePopoverOpen()) {
      return;
    }
    if (stylePopoverState.panel.contains(event.target)) {
      return;
    }
    if (event.target.closest(".builder-style-chip")) {
      return;
    }
    closeStylePopover();
  });
  window.addEventListener("scroll", () => {
    if (isStylePopoverOpen()) {
      closeStylePopover();
    }
  });
  window.addEventListener("resize", () => {
    if (isStylePopoverOpen()) {
      closeStylePopover();
    }
  });
}

const INLINE_ALLOWED_TAGS = new Set([
  "B",
  "STRONG",
  "I",
  "EM",
  "U",
  "S",
  "DEL",
  "BR",
  "A",
  "UL",
  "OL",
  "LI",
  "SPAN",
  "P",
  "H1",
  "H2",
  "H3",
  "H4",
  "H5",
  "H6",
  "IMG",
]);
const INLINE_STYLE_TAGS = new Set(["SPAN", "P", "H1", "H2", "H3", "H4", "H5", "H6", "IMG"]);
const ALLOWED_TEXT_STYLE_PROPS = [
  "font-size",
  "color",
  "background-color",
  "text-decoration",
  "font-family",
];
const IMAGE_STYLE_PROPS = ["width", "height", "max-width", "max-height"];
const COLOR_VALUE =
  /^(#([0-9a-f]{3}|[0-9a-f]{6})|rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)|rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*(0|0?\.\d+|1)\s*\))$/i;
const FONT_SIZE_VALUE =
  /^(\d+(\.\d+)?(px|rem|em|pt|vw|vh|vmin|vmax|%)|xx-small|x-small|small|medium|large|x-large|xx-large|smaller|larger)$/i;
const LENGTH_VALUE = /^(auto|\d+(\.\d+)?(px|rem|em|pt|vw|vh|vmin|vmax|%)?)$/i;
const TEXT_DECORATION_VALUE = /^(none|underline|line-through|overline)$/i;
const FONT_FAMILY_VALUE =
  /^("[^"]+"|'[^']+'|[a-z0-9 _-]+)(\s*,\s*("[^"]+"|'[^']+'|[a-z0-9 _-]+))*$/i;
const INLINE_FONT_FAMILY_RE = /font-family\s*:\s*['"]?(CMSInlineFont-[a-z0-9]+)['"]?/gi;

function filterStyleValue(value, tagName = "") {
  if (!value) {
    return "";
  }
  const pieces = value.split(";").map((part) => part.trim()).filter(Boolean);
  const allowed = [];
  const tag = (tagName || "").toUpperCase();
  pieces.forEach((part) => {
    const [rawProp, ...rest] = part.split(":");
    const prop = (rawProp || "").trim().toLowerCase();
    const value = rest.join(":").trim();
    if (!value) {
      return;
    }
    if (ALLOWED_TEXT_STYLE_PROPS.includes(prop) && tag !== "IMG") {
      if (prop === "font-size" && FONT_SIZE_VALUE.test(value)) {
        allowed.push(`${prop}: ${value}`);
      } else if ((prop === "color" || prop === "background-color") && COLOR_VALUE.test(value)) {
        allowed.push(`${prop}: ${value}`);
      } else if (prop === "text-decoration" && TEXT_DECORATION_VALUE.test(value)) {
        allowed.push(`${prop}: ${value}`);
      } else if (prop === "font-family") {
        const clean = value.replace(/\\+/g, "").trim();
        if (FONT_FAMILY_VALUE.test(clean)) {
          allowed.push(`${prop}: ${clean}`);
        }
      }
    } else if (tag === "IMG" && IMAGE_STYLE_PROPS.includes(prop)) {
      if (LENGTH_VALUE.test(value)) {
        allowed.push(`${prop}: ${value}`);
      }
    }
  });
  return allowed.join("; ");
}

function isSafeHref(value) {
  return /^(https?:|mailto:|\/|#)/i.test(value || "");
}

function isSafeImageSrc(value) {
  return /^(https?:|\/|data:image\/)/i.test(value || "");
}

function cleanDimension(value) {
  if (!value) {
    return "";
  }
  const trimmed = value.trim();
  if (LENGTH_VALUE.test(trimmed)) {
    return trimmed;
  }
  return "";
}

function collectInlineFonts(html) {
  if (!fontState.byFamily.size) {
    return null;
  }
  const source = html || "";
  INLINE_FONT_FAMILY_RE.lastIndex = 0;
  const families = new Set();
  let match;
  while ((match = INLINE_FONT_FAMILY_RE.exec(source))) {
    if (match[1]) {
      families.add(match[1]);
    }
  }
  const fonts = [];
  families.forEach((family) => {
    const asset = fontState.byFamily.get(family);
    if (asset) {
      fonts.push({ family: asset.family, url: asset.url, format: asset.format });
    }
  });
  return fonts;
}

function updateBlockInlineFonts(block, fieldKey, html) {
  if (!block) {
    return;
  }
  if (!block._inlineFontUsage) {
    block._inlineFontUsage = {};
  }
  const fonts = collectInlineFonts(html);
  if (fonts === null) {
    return;
  }
  if (fonts.length) {
    block._inlineFontUsage[fieldKey] = fonts;
  } else {
    delete block._inlineFontUsage[fieldKey];
  }
  const union = [];
  const seen = new Set();
  Object.values(block._inlineFontUsage).forEach((list) => {
    list.forEach((font) => {
      if (!seen.has(font.family)) {
        seen.add(font.family);
        union.push(font);
      }
    });
  });
  if (union.length) {
    block.props.inline_fonts = union;
  } else {
    delete block.props.inline_fonts;
  }
}

function sanitizeInlineHTML(html) {
  const template = document.createElement("template");
  template.innerHTML = html || "";
  function clean(node) {
    Array.from(node.childNodes).forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        return;
      }
      if (child.nodeType === Node.ELEMENT_NODE) {
        if (!INLINE_ALLOWED_TAGS.has(child.tagName)) {
          child.replaceWith(...Array.from(child.childNodes));
        } else {
          let removed = false;
          Array.from(child.attributes).forEach((attr) => {
            if (removed) {
              return;
            }
            const name = attr.name.toLowerCase();
            if (child.tagName === "A" && name === "href") {
              const val = attr.value || "";
              if (isSafeHref(val)) {
                child.setAttribute("href", val);
              } else {
                child.removeAttribute("href");
              }
            } else if (child.tagName === "A" && name === "target") {
              if (attr.value === "_blank") {
                child.setAttribute("target", "_blank");
                child.setAttribute("rel", "noopener");
              } else {
                child.removeAttribute("target");
              }
            } else if (child.tagName === "IMG" && name === "src") {
              const val = attr.value || "";
              if (isSafeImageSrc(val)) {
                child.setAttribute("src", val);
              } else {
                child.remove();
                removed = true;
              }
            } else if (child.tagName === "IMG" && (name === "alt" || name === "title")) {
              child.setAttribute(name, attr.value || "");
            } else if (child.tagName === "IMG" && (name === "width" || name === "height")) {
              const clean = cleanDimension(attr.value || "");
              if (clean) {
                child.setAttribute(name, clean);
              } else {
                child.removeAttribute(name);
              }
            } else if (INLINE_STYLE_TAGS.has(child.tagName) && name === "style") {
              const safe = filterStyleValue(attr.value || "", child.tagName);
              if (safe) {
                child.setAttribute("style", safe);
              } else {
                child.removeAttribute("style");
              }
            } else {
              child.removeAttribute(attr.name);
            }
          });
          if (!removed) {
            clean(child);
          }
        }
      } else {
        child.remove();
      }
    });
  }
  clean(template.content);
  return template.innerHTML;
}

function applyInlineEditValue(blockId, key, value) {
  const block = state.blocks.find((item) => item.id === blockId);
  if (!block) {
    return;
  }
  if (!block.props) {
    block.props = {};
  }
  if (block.props[key] === value) {
    return;
  }
  if (typeof value === "string") {
    updateBlockInlineFonts(block, key, value);
  }
  updateBlockProp(blockId, key, value, {
    skipPreview: inlineState.enabled,
    forceRenderSettings: inlineState.enabled,
  });
}

function loadTinyMCE(frame, callback) {
  const doc = frame.contentDocument;
  if (!doc) {
    return;
  }
  const existing = doc.defaultView && doc.defaultView.tinymce;
  if (existing) {
    callback(existing);
    return;
  }
  if (doc._tinymceLoading) {
    doc._tinymceLoading.push(callback);
    return;
  }
  doc._tinymceLoading = [callback];
  const script = doc.createElement("script");
  script.src = INLINE_EDITOR_SRC;
  script.referrerPolicy = "origin";
  script.addEventListener("load", () => {
    const tiny = doc.defaultView?.tinymce;
    (doc._tinymceLoading || []).forEach((cb) => cb(tiny));
    doc._tinymceLoading = null;
  });
  script.addEventListener("error", () => {
    console.error("Could not load TinyMCE for inline editing.");
    doc._tinymceLoading = null;
  });
  doc.head.appendChild(script);
}

function ensureInlineImageStyles(doc) {
  if (!doc) {
    return;
  }
  if (doc.getElementById(INLINE_IMAGE_STYLE_ID)) {
    return;
  }
  const style = doc.createElement("style");
  style.id = INLINE_IMAGE_STYLE_ID;
  style.textContent = INLINE_IMAGE_STYLE;
  (doc.head || doc.documentElement || doc.body || doc).appendChild(style);
}

function attachImageResizer(frame, img, blockId, fieldKey) {
  const doc = frame.contentDocument;
  const win = frame.contentWindow;
  if (!doc || !img || !blockId || !fieldKey) {
    return () => {};
  }
  ensureInlineImageStyles(doc);
  img.classList.add("inline-image-resize-target");
  const handle = doc.createElement("button");
  handle.type = "button";
  handle.className = "inline-image-resize-handle";
  handle.setAttribute("aria-label", "Drag to resize image");
  handle.tabIndex = -1;
  doc.body.appendChild(handle);
  handle.style.left = "0px";
  handle.style.top = "0px";

  const minAttr = Number(img.getAttribute("data-inline-image-min"));
  const maxAttr = Number(img.getAttribute("data-inline-image-max"));
  const minWidth = Number.isFinite(minAttr) && minAttr > 0 ? minAttr : 40;
  const maxWidth = Number.isFinite(maxAttr) && maxAttr > 0 ? maxAttr : null;

  const updateHandlePosition = () => {
    if (!doc.body.contains(img)) {
      handle.style.display = "none";
      return;
    }
    const rect = img.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      handle.style.display = "none";
      return;
    }
    handle.style.display = "block";
    handle.style.left = `${Math.round(rect.right - 8)}px`;
    handle.style.top = `${Math.round(rect.bottom - 8)}px`;
  };

  const resizeObserver = typeof ResizeObserver === "function" ? new ResizeObserver(updateHandlePosition) : null;
  resizeObserver?.observe(img);
  const scrollListener = () => updateHandlePosition();
  doc.addEventListener("scroll", scrollListener, true);
  win?.addEventListener("resize", updateHandlePosition);
  img.addEventListener("load", updateHandlePosition);
  updateHandlePosition();

  const dragState = {
    startX: 0,
    baseWidth: null,
  };

  function dragMove(event) {
    event.preventDefault();
    if (dragState.baseWidth == null) {
      dragState.baseWidth = img.getBoundingClientRect().width || img.width || minWidth;
    }
    let next = dragState.baseWidth + (event.clientX - dragState.startX);
    next = Math.max(minWidth, Math.round(next));
    if (maxWidth) {
      next = Math.min(maxWidth, next);
    }
    img.style.width = `${next}px`;
    img.style.height = "auto";
    updateHandlePosition();
  }

  function stopDrag() {
    doc.removeEventListener("pointermove", dragMove);
    doc.removeEventListener("pointerup", dragEnd);
  }

  function dragEnd() {
    stopDrag();
    const width = Math.round(img.getBoundingClientRect().width);
    const natural = img.naturalWidth || 0;
    if (natural && Math.abs(width - natural) <= 2) {
      img.style.removeProperty("width");
      img.style.removeProperty("height");
      applyInlineEditValue(blockId, fieldKey, null);
    } else {
      applyInlineEditValue(blockId, fieldKey, width);
    }
    dragState.baseWidth = null;
    updateHandlePosition();
  }

  const onPointerDown = (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragState.startX = event.clientX;
    dragState.baseWidth = img.getBoundingClientRect().width || img.width || minWidth;
    doc.addEventListener("pointermove", dragMove);
    doc.addEventListener("pointerup", dragEnd);
  };

  handle.addEventListener("pointerdown", onPointerDown);
  handle.addEventListener("dblclick", (event) => {
    event.preventDefault();
    event.stopPropagation();
    img.style.removeProperty("width");
    img.style.removeProperty("height");
    applyInlineEditValue(blockId, fieldKey, null);
    updateHandlePosition();
  });

  return () => {
    stopDrag();
    handle.removeEventListener("pointerdown", onPointerDown);
    handle.remove();
    resizeObserver?.disconnect();
    doc.removeEventListener("scroll", scrollListener, true);
    win?.removeEventListener("resize", updateHandlePosition);
    img.removeEventListener("load", updateHandlePosition);
    img.classList.remove("inline-image-resize-target");
  };
}

function destroyInlineImageResizers(frame) {
  const cleanups = inlineState.imageResizers.get(frame) || [];
  cleanups.forEach((cleanup) => {
    try {
      cleanup();
    } catch (error) {
      /* ignore */
    }
  });
  inlineState.imageResizers.delete(frame);
}

function activateInlineImageResizers(frame) {
  const doc = frame.contentDocument;
  if (!doc || !inlineState.enabled) {
    destroyInlineImageResizers(frame);
    return;
  }
  const targets = Array.from(doc.querySelectorAll("[data-inline-block][data-inline-image]"));
  if (!targets.length) {
    destroyInlineImageResizers(frame);
    return;
  }
  destroyInlineImageResizers(frame);
  const cleanups = [];
  targets.forEach((img) => {
    const blockId = img.getAttribute("data-inline-block");
    const fieldKey = img.getAttribute("data-inline-image");
    if (!blockId || !fieldKey) {
      return;
    }
    cleanups.push(attachImageResizer(frame, img, blockId, fieldKey));
  });
  inlineState.imageResizers.set(frame, cleanups);
}

function applyFontFacesToDoc(doc, fonts) {
  if (!doc) {
    return;
  }
  const css = (fonts || [])
    .map((font) => {
      const safeUrl = String(font.url || "").replace(/'/g, "\\'");
      return `@font-face{font-family:'${font.family}';src:url('${safeUrl}') format('${
        font.format || "truetype"
      }');font-display:swap;}`;
    })
    .join("");
  let style = doc.getElementById(INLINE_FONT_STYLE_ID);
  if (!style) {
    style = doc.createElement("style");
    style.id = INLINE_FONT_STYLE_ID;
    (doc.head || doc.documentElement || doc.body || doc).appendChild(style);
  }
  style.textContent = css;
}

function destroyInlineEditors(frame) {
  const doc = frame.contentDocument;
  const tiny = doc && doc.defaultView && doc.defaultView.tinymce;
  const editors = inlineState.editors.get(frame) || [];
  editors.forEach((editor) => {
    try {
      editor.remove();
    } catch (error) {
      try {
        editor.destroy?.();
      } catch (e) {}
    }
  });
  inlineState.editors.delete(frame);
  if (tiny && tiny.EditorManager) {
    Object.values(tiny.EditorManager.editors || {}).forEach((editor) => {
      if (editor && editor.remove) editor.remove();
    });
  }
}

function activateInlineEditors(frame) {
  const doc = frame.contentDocument;
  if (!doc) {
    return;
  }
  const existingToolbar = doc.querySelector(".tox-editor-header");
  if (existingToolbar) {
    existingToolbar.remove();
  }
  const targets = Array.from(doc.querySelectorAll("[data-inline-block][data-inline-field]"));
  if (!targets.length) {
    destroyInlineEditors(frame);
    return;
  }
  loadTinyMCE(frame, (tinymce) => {
    if (!tinymce || !inlineState.enabled) {
      return;
    }
    fetchFontAssets()
      .catch(() => [])
      .then((fonts) => {
        if (!inlineState.enabled) {
          return;
        }
        destroyInlineEditors(frame);
        applyFontFacesToDoc(doc, fonts);
        const fontFormats = buildFontFamilyFormats(fonts);
        const editorList = [];
        targets.forEach((node) => {
          const blockId = node.getAttribute("data-inline-block");
          const fieldKey = node.getAttribute("data-inline-field");
          const existingId = node.getAttribute("data-inline-editor-id");
          const blockData = state.blocks.find((item) => item.id === blockId);
          if (blockData) {
            updateBlockInlineFonts(blockData, fieldKey, node.innerHTML || "");
          }
          if (!node.id) {
            node.id = `inline-${blockId}-${fieldKey}-${Math.random().toString(16).slice(2)}`;
          }
          const initConfig = {
            target: node,
            inline: true,
            menubar: false,
            license_key: "gpl",
            plugins: "link lists image fontfamily fontsize",
            toolbar:
              "undo redo | fontfamily fontsize | bold italic underline strikethrough superscript subscript forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | hr link image removeformat",
            toolbar_mode: "wrap",
            toolbar_persist: false,
            quickbars_selection_toolbar: false,
            quickbars_insert_toolbar: false,
            quickbars_image_toolbar: false,
            image_dimensions: true,
            image_advtab: true,
            automatic_uploads: false,
            object_resizing: true,
            fontsize_formats: "10px 12px 14px 16px 18px 24px 32px 48px",
            font_family_formats: fontFormats,
            setup(editor) {
              const pushValue = () => {
                const html = sanitizeInlineHTML(editor.getContent({ format: "raw" }));
                if (html !== editor.getContent({ format: "raw" })) {
                  editor.setContent(html, { format: "raw" });
                }
                applyInlineEditValue(blockId, fieldKey, html);
              };
              editor.on("Change KeyUp Undo Redo", pushValue);
              editor.on("Blur", pushValue);
            },
          };
          if (window.cmsTinyMCEAssets) {
            Object.assign(initConfig, window.cmsTinyMCEAssets());
          }
          tinymce.init(initConfig).then((editors) => {
            if (!Array.isArray(editors)) {
              return;
            }
            editors.forEach((editor) => {
              editorList.push(editor);
            });
            inlineState.editors.set(frame, editorList);
          });
          if (existingId) {
            tinymce.get(existingId)?.remove();
          }
          node.setAttribute("data-inline-editor-id", node.id);
        });
      });
  });
}

function syncInlineForFrame(frame) {
  if (inlineState.enabled) {
    activateInlineImageResizers(frame);
    activateInlineEditors(frame);
  } else {
    destroyInlineImageResizers(frame);
    destroyInlineEditors(frame);
  }
}

function syncInlineEditState() {
  if (!dom.previewFrames || !dom.previewFrames.length) {
    return;
  }
  dom.previewFrames.forEach((frame) => {
    syncInlineForFrame(frame);
  });
}

function bindInlineFrame(frame) {
  if (!frame || frame._inlineBound) {
    return;
  }
  frame._inlineBound = true;
  frame.addEventListener("load", () => {
    const doc = frame.contentDocument;
    if (doc && !doc._builderClickBound) {
      doc.addEventListener(
        "click",
        (event) => {
          if (!inlineState.enabled) {
            return;
          }
          const target = event.target.closest("[data-inline-block]");
          if (!target) {
            return;
          }
          const blockId = target.getAttribute("data-inline-block");
          if (blockId) {
            selectBlock(blockId);
          }
        },
        true
      );
      doc._builderClickBound = true;
    }
    if (doc && !doc._builderContextBound) {
      doc.addEventListener(
        "contextmenu",
        (event) => {
          const target = event.target.closest("[data-inline-block]");
          if (!target) {
            return;
          }
          const blockId = target.getAttribute("data-inline-block");
          if (!blockId) {
            return;
          }
          event.preventDefault();
          openAdvancedStyleFromPreview(blockId);
        },
        true
      );
      doc._builderContextBound = true;
    }
    updateThemeSnapshotFromFrame(frame);
    syncInlineForFrame(frame);
  });
}



function setInlineEditMode(enabled) {
  const wasEnabled = inlineState.enabled;
  inlineState.enabled = enabled;
  if (dom.inlineEditButton) {
    dom.inlineEditButton.classList.toggle("is-active", enabled);
    dom.inlineEditButton.setAttribute("aria-pressed", enabled ? "true" : "false");
    dom.inlineEditButton.textContent = enabled ? "Stop inline edit" : "Inline edit";
  }
  if (enabled) {
    if (previewTimer) {
      window.clearTimeout(previewTimer);
      previewTimer = null;
    }
    if (previewInflight) {
      previewInflight.abort();
      previewInflight = null;
    }
  }
  syncInlineEditState();
  if (wasEnabled && !enabled) {
    schedulePreview(true);
  }
}

function openAssetBrowser({ kinds = [], onSelect }) {
  if (!assetState.modal) {
    return;
  }
  assetState.kinds = kinds;
  assetState.onSelect = onSelect;
  if (assetState.subtitle) {
    assetState.subtitle.textContent = kinds.length
      ? `Showing ${kinds.join(", ")} assets`
      : "Showing all public assets";
  }
  assetState.modal.classList.remove("is-hidden");
  assetState.modal.setAttribute("aria-hidden", "false");
  if (assetState.panel) {
    assetState.panel.focus();
  }
  loadAssets(kinds);
}

function uuid() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `blk_${Math.random().toString(16).slice(2)}${Date.now()}`;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function getBlueprint(type) {
  return DEFAULT_BLOCK_LIBRARY.find((b) => b.type === type);
}

function normaliseListItemValues(item, blueprintFields = []) {
  const clean = { ...item };
  blueprintFields.forEach((subField) => {
    if (!(subField.key in clean)) {
      return;
    }
    if (subField.type === "asset") {
      clean[subField.key] = normaliseBuilderAsset(clean[subField.key]);
    }
  });
  return clean;
}

function normaliseBlock(block) {
  const blueprint = getBlueprint(block.type);
  if (!blueprint) {
    return block;
  }
  const props = { ...clone(blueprint.defaults), ...clone(block.props || {}) };

  // Type conversions
  blueprint.fields.forEach((field) => {
    const key = field.key;
    if (!(key in props)) {
      return;
    }
    const value = props[key];
    switch (field.type) {
      case "number":
      case "range":
        props[key] = value === "" || value === null ? null : Number(value);
        break;
      case "toggle":
        props[key] = Boolean(value);
        break;
      case "sluglist":
        if (Array.isArray(value)) {
          props[key] = value;
        } else if (typeof value === "string") {
          props[key] = value
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
        } else {
          props[key] = [];
        }
        break;
      case "checkboxes":
        if (value === null || value === undefined) {
          props[key] = null;
        } else if (Array.isArray(value)) {
          props[key] = value.filter((item) => typeof item === "string");
        } else {
          props[key] = [];
        }
        break;
      case "list":
        if (!Array.isArray(value)) {
          props[key] = [];
        } else {
          props[key] = value.map((item) => ({
            ...clone(field.itemDefaults || {}),
            ...item,
          }));
        }
        if (Array.isArray(props[key]) && Array.isArray(field.itemFields)) {
          props[key] = props[key].map((item) => normaliseListItemValues(item, field.itemFields));
        }
        break;
      default:
        break;
    }
  });

  props.style = normaliseStyleValue(block.props ? block.props.style : undefined);

  const rawTargets =
    block.props && typeof block.props.style_targets === "object" ? block.props.style_targets : {};
  props.style_targets = {};
  Object.entries(rawTargets || {}).forEach(([targetKey, targetValue]) => {
    props.style_targets[targetKey] = normaliseStyleValue(targetValue);
  });

  if (block.type === "navigation") {
    if (typeof props.logo_text_auto !== "boolean") {
      props.logo_text_auto = !props.logo_text;
    }
  }

  return {
    id: block.id || uuid(),
    type: block.type,
    props,
  };
}

function normaliseBlocks(blocks) {
  return (blocks || []).map(normaliseBlock);
}

function getSelectedBlock() {
  return state.blocks.find((b) => b.id === state.selectedId) || null;
}

function serialiseBlocks(blocks) {
  return blocks.map((block) => {
    const props = { ...(block.props || {}) };
    Object.keys(props).forEach((key) => {
      if (key.startsWith("__")) {
        delete props[key];
      }
    });
    const clean = { ...block, props };
    Object.keys(clean).forEach((key) => {
      if (key.startsWith("_")) {
        delete clean[key];
      }
    });
    return clean;
  });
}

function persistBlocks() {
  if (!dom.blocksInput) {
    return;
  }
  dom.blocksInput.value = JSON.stringify(serialiseBlocks(state.blocks));
}

function persistTheme() {
  if (!dom.themeInput) {
    return;
  }
  try {
    dom.themeInput.value = JSON.stringify(getPageTheme());
  } catch (error) {
    console.error("Failed to persist theme", error);
  }
}

function schedulePreview(immediate = false) {
  persistBlocks();
  persistTheme();
  if (!config.urls || !config.urls.preview) {
    return;
  }
  if (inlineState.enabled && !immediate) {
    return;
  }
  if (immediate) {
    return fetchPreview();
  }
  if (previewTimer) {
    window.clearTimeout(previewTimer);
  }
  previewTimer = window.setTimeout(fetchPreview, 450);
}

function setPreviewHTML(html) {
  if (!dom.previewFrames || !dom.previewFrames.length) {
    return;
  }
  const content =
    html && html.trim()
      ? html
      : "<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;padding:2rem;font-family:system-ui;background:#0b1118;color:#f0f4f8;} .muted{color:rgba(255,255,255,0.6);}</style></head><body><p class='muted'>Preview will appear here once you add blocks.</p></body></html>";
  dom.previewFrames.forEach((frame) => {
    bindInlineFrame(frame);
    if (frame.srcdoc !== content) {
      frame.srcdoc = content;
    }
  });
}


function getCsrfToken() {
  const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return input ? input.value : "";
}

async function fetchPreview() {
  if (!config.urls || !config.urls.preview) {
    return;
  }
  const navField = document.getElementById("id_custom_nav_items");
  const showNavField = document.getElementById("id_show_navigation_bar");
  let navItems = [];
  if (navField) {
    try {
      navItems = JSON.parse(navField.value || "[]");
    } catch (error) {
      navItems = [];
    }
  }
  let showNav = false;
  const navBlock = state.blocks.find((block) => block.type === "navigation");
  if (navBlock) {
    showNav = navBlock.props.enabled !== false;
    if (Array.isArray(navBlock.props.links)) {
      navItems = navBlock.props.links.slice();
    }
  } else if (showNavField) {
    showNav = false;
  }
  const bodyField = document.getElementById("id_body");
  const cssField = document.getElementById("id_custom_css");
  const jsField = document.getElementById("id_custom_js");
  const renderRawField = document.getElementById("id_render_body_only");
  const payload = {
    blocks: serialiseBlocks(state.blocks),
    custom_nav_items: navItems,
    show_navigation_bar: showNav,
    render_body_only: renderRawField ? !!renderRawField.checked : false,
    body: bodyField ? bodyField.value : "",
    custom_css: cssField ? cssField.value : "",
    custom_js: jsField ? jsField.value : "",
    theme: getPageTheme(),
  };
  if (previewInflight) {
    previewInflight.abort();
  }
  const controller = new AbortController();
  previewInflight = controller;
  try {
    const response = await fetch(config.urls.preview, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`Preview failed with status ${response.status}`);
    }
    const data = await response.json();
    setPreviewHTML(data.html || "");
  } catch (error) {
    if (error.name === "AbortError") {
      return;
    }
    console.error(error);
  } finally {
    previewInflight = null;
  }
}

function renderLibraryFilters(container, categories, selected, onSelect) {
  if (!container) {
    return;
  }
  container.className = "builder-library-filters";
  container.innerHTML = "";
  const allBtn = document.createElement("button");
  allBtn.type = "button";
  allBtn.className = `builder-library-filter${selected === "all" ? " is-active" : ""}`;
  allBtn.textContent = "All";
  allBtn.addEventListener("click", () => onSelect("all"));
  container.appendChild(allBtn);
  categories.forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `builder-library-filter${selected === category ? " is-active" : ""}`;
    button.dataset.category = category;
    button.textContent = category.replace(/_/g, " ");
    button.addEventListener("click", () => onSelect(category));
    container.appendChild(button);
  });
}

function renderLibraryList(container, blocks, selectedCategory) {
  if (!container) {
    return;
  }
  container.innerHTML = "";
  blocks
    .filter((block) => selectedCategory === "all" || block.category === selectedCategory)
    .forEach((block) => {
      const button = document.createElement("button");
      button.className = "builder-library-item";
      button.type = "button";
      button.dataset.blockType = block.type;
      button.innerHTML = `
        <span class="builder-library-item__icon">${block.icon}</span>
        <span>
          <strong>${block.label}</strong>
          <small class="muted">${block.description}</small>
        </span>
      `;
      button.addEventListener("click", () => addBlock(block.type));
      container.appendChild(button);
    });
}

function renderLibrary() {
  if (!dom.library) {
    return;
  }
  dom.library.innerHTML = "";
  const categories = Array.from(
    new Set(DEFAULT_BLOCK_LIBRARY.map((block) => block.category).filter(Boolean))
  );
  const filters = document.createElement("div");
  const listContainer = document.createElement("div");
  listContainer.className = "builder-library-list";
  let selectedCategory = "all";

  const handleSelect = (category) => {
    selectedCategory = category;
    renderLibraryFilters(filters, categories, selectedCategory, handleSelect);
    renderLibraryList(listContainer, DEFAULT_BLOCK_LIBRARY, selectedCategory);
  };

  dom.library.appendChild(filters);
  dom.library.appendChild(listContainer);
  handleSelect(selectedCategory);
}

function renderBlockList() {
  if (!dom.blockList) {
    return;
  }
  dom.blockList.innerHTML = "";
  if (!state.blocks.length) {
    const empty = document.createElement("li");
    empty.className = "builder-empty";
    empty.textContent = "No blocks yet. Add one from the sidebar.";
    dom.blockList.appendChild(empty);
    return;
  }

  state.blocks.forEach((block, index) => {
    const blueprint = getBlueprint(block.type);
    const item = document.createElement("li");
    item.className = `builder-block${block.id === state.selectedId ? " is-selected" : ""}`;
    item.dataset.blockId = block.id;
    item.innerHTML = `
      <div class="builder-block__title">
        <strong>${blueprint ? blueprint.label : block.type}</strong>
        <span class="muted">#${index + 1}</span>
      </div>
      <div class="builder-block__controls">
        <button type="button" class="builder-block__btn" data-action="select">Edit</button>
        <button type="button" class="builder-block__btn" data-action="up">↑</button>
        <button type="button" class="builder-block__btn" data-action="down">↓</button>
        <button type="button" class="builder-block__btn builder-block__btn--danger" data-action="delete">✕</button>
      </div>
    `;
    item.addEventListener("click", (event) => {
      event.preventDefault();
      const action = event.target.dataset.action;
      if (action === "up") {
        event.stopPropagation();
        moveBlock(block.id, -1);
      } else if (action === "down") {
        event.stopPropagation();
        moveBlock(block.id, 1);
      } else if (action === "delete") {
        event.stopPropagation();
        removeBlock(block.id);
      } else {
        selectBlock(block.id);
      }
    });
    dom.blockList.appendChild(item);
  });
}

function renderSettings() {
  if (!dom.settings) {
    return;
  }
  dom.settings.innerHTML = "";
  if (!fontState.assets.length) {
    fetchFontAssets().then((fonts) => {
      if (fonts && fonts.length && dom.settings) {
        renderSettings();
      }
    });
  }
  closeStylePopover();
  const block = getSelectedBlock();
  if (!block) {
    const message = document.createElement("p");
    message.className = "muted builder-settings__empty";
    message.textContent = "Select a block to configure it.";
    dom.settings.appendChild(message);
    return;
  }
  const blueprint = getBlueprint(block.type);
  if (!blueprint) {
    dom.settings.textContent = "Unknown block type.";
    return;
  }

  const form = document.createElement("div");
  form.className = "builder-settings__panel";

  blueprint.fields.forEach((field) => {
    form.appendChild(renderField(block, field, blueprint));
  });

  form.appendChild(renderAdvancedStyleSection(block));

  dom.settings.appendChild(form);
  renderThemeCard();
}

function renderAdvancedStyleSection(block) {
  const style = getBlockBaseStyle(block);
  const wrapper = document.createElement("div");
  wrapper.className = "builder-advanced-style";
  wrapper.dataset.advancedStyle = "true";
  const title = document.createElement("h3");
  title.textContent = "Advanced styling";
  wrapper.appendChild(title);

  const grid = document.createElement("div");
  grid.className = "builder-advanced-style__grid";

  // Font family
  const fontField = document.createElement("div");
  fontField.className = "builder-field";
  const fontLabel = document.createElement("label");
  fontLabel.textContent = "Font";
  const fontSelect = document.createElement("select");
  STYLE_FONT_OPTIONS.forEach((option) => {
    const opt = document.createElement("option");
    opt.value = option.value;
    opt.textContent = option.label;
    fontSelect.appendChild(opt);
  });
  fontSelect.value = style.font_family || "";
  fontSelect.addEventListener("change", (event) => {
    updateBaseStyle(block.id, { font_family: event.target.value });
  });
  fontField.appendChild(fontLabel);
  fontField.appendChild(fontSelect);
  grid.appendChild(fontField);

  const fontAssetField = document.createElement("div");
  fontAssetField.className = "builder-field";
  const fontAssetLabel = document.createElement("label");
  fontAssetLabel.textContent = "Uploaded font";
  const fontAssetHint = document.createElement("small");
  fontAssetHint.className = "muted";
  fontAssetHint.textContent = "Pick a custom font from Assets → Fonts.";
  const fontAssetControls = buildFontAssetControls({
    context: "panel",
    currentAsset: style.font_asset,
    placeholder: "Use theme font",
    onChange(payload) {
      updateBaseStyle(block.id, { font_asset: payload, font_family: "" });
      renderSettings();
    },
  });
  fontAssetField.appendChild(fontAssetLabel);
  fontAssetField.appendChild(fontAssetHint);
  fontAssetField.appendChild(fontAssetControls);
  grid.appendChild(fontAssetField);

  // Font size
  const sizeField = document.createElement("div");
  sizeField.className = "builder-field";
  const sizeLabel = document.createElement("label");
  sizeLabel.textContent = "Font size";
  const sizeSelect = document.createElement("select");
  STYLE_FONT_SIZE_OPTIONS.forEach((option) => {
    const opt = document.createElement("option");
    opt.value = option.value;
    opt.textContent = option.label;
    sizeSelect.appendChild(opt);
  });
  sizeSelect.value = style.font_size || "";
  sizeSelect.addEventListener("change", (event) => {
    updateBaseStyle(block.id, { font_size: event.target.value });
  });
  sizeField.appendChild(sizeLabel);
  sizeField.appendChild(sizeSelect);
  grid.appendChild(sizeField);

  // Text color
  const textColorField = document.createElement("div");
  textColorField.className = "builder-field";
  const textColorLabel = document.createElement("label");
  textColorLabel.textContent = "Text color";
  const textColorInput = document.createElement("input");
  textColorInput.type = "color";
  textColorInput.value = style.text_color || "#ffffff";
  textColorInput.addEventListener("input", (event) => {
    updateBaseStyle(block.id, { text_color: event.target.value });
  });
  const textClear = document.createElement("button");
  textClear.type = "button";
  textClear.className = "btn btn-xs btn-outline-secondary";
  textClear.textContent = "Reset";
  textClear.addEventListener("click", () => {
    updateBaseStyle(block.id, { text_color: "" });
    textColorInput.value = "#ffffff";
  });
  textColorField.appendChild(textColorLabel);
  textColorField.appendChild(textColorInput);
  textColorField.appendChild(textClear);
  grid.appendChild(textColorField);

  // Background color
  const bgField = document.createElement("div");
  bgField.className = "builder-field";
  const bgLabel = document.createElement("label");
  bgLabel.textContent = "Background";
  const bgInput = document.createElement("input");
  bgInput.type = "color";
  bgInput.value = style.background_color || "#000000";
  bgInput.addEventListener("input", (event) => {
    updateBaseStyle(block.id, { background_color: event.target.value });
  });
  const bgClear = document.createElement("button");
  bgClear.type = "button";
  bgClear.className = "btn btn-xs btn-outline-secondary";
  bgClear.textContent = "Reset";
  bgClear.addEventListener("click", () => {
    updateBaseStyle(block.id, { background_color: "" });
    bgInput.value = "#000000";
  });
  bgField.appendChild(bgLabel);
  bgField.appendChild(bgInput);
  bgField.appendChild(bgClear);
  grid.appendChild(bgField);

  wrapper.appendChild(grid);

  const actions = document.createElement("div");
  actions.className = "builder-advanced-style__actions";
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.className = "btn btn-xs btn-outline-secondary";
  resetBtn.textContent = "Reset all";
  resetBtn.addEventListener("click", () => {
    updateBaseStyle(block.id, {
      font_family: "",
      font_size: "",
      text_color: "",
      background_color: "",
      font_asset: null,
    });
    renderSettings();
  });
  actions.appendChild(resetBtn);
  wrapper.appendChild(actions);

  return wrapper;
}

function renderThemePanel() {
  const panel = document.createElement("div");
  panel.className = "builder-theme-panel";
  const snapshot = state.themeSnapshot || {};
  panel.appendChild(
    renderThemeSection(
      "body",
      "Body & navigation",
      "Applies to the page background, base font, and navigation.",
      snapshot.body || {}
    )
  );
  panel.appendChild(
    renderThemeSection(
      "sections",
      "Sections & cards",
      "Applies to block containers (the visible DIVs on the page).",
      snapshot.sections || {}
    )
  );
  return panel;
}

function renderThemeSection(sectionKey, label, hint, snapshot) {
  const wrapper = document.createElement("div");
  wrapper.className = "builder-theme-section";
  const header = document.createElement("div");
  header.className = "builder-theme-section__header";
  const heading = document.createElement("h4");
  heading.textContent = label;
  header.appendChild(heading);
  if (hint) {
    const helper = document.createElement("p");
    helper.className = "muted";
    helper.textContent = hint;
    header.appendChild(helper);
  }
  wrapper.appendChild(header);

  const values = getPageTheme()[sectionKey] || normaliseStyleValue({});
  const grid = document.createElement("div");
  grid.className = "builder-theme-grid";
  grid.appendChild(
    renderThemeSelectField(
      sectionKey,
      "font_family",
      "Font family",
      values,
      false,
      snapshot.font_family
    )
  );
  grid.appendChild(
    renderThemeSelectField(
      sectionKey,
      "font_size",
      "Font size",
      values,
      true,
      snapshot.font_size
    )
  );
  grid.appendChild(
    renderThemeFontAssetField(
      sectionKey,
      "font_asset",
      "Uploaded font",
      values.font_asset,
      snapshot.font_family
    )
  );
  grid.appendChild(
    renderThemeColorField(
      sectionKey,
      "text_color",
      "Text color",
      values,
      snapshot.text_color
    )
  );
  grid.appendChild(
    renderThemeColorField(
      sectionKey,
      "background_color",
      "Background",
      values,
      snapshot.background_color
    )
  );
  wrapper.appendChild(grid);

  const actions = document.createElement("div");
  actions.className = "builder-theme-section__actions";
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.className = "btn btn-xs btn-outline-secondary";
  resetBtn.textContent = "Reset section";
  resetBtn.addEventListener("click", () => {
    updateThemeSection(sectionKey, {
      font_family: "",
      font_size: "",
      text_color: "",
      background_color: "",
      font_asset: null,
    });
    renderSettings();
  });
  actions.appendChild(resetBtn);
  wrapper.appendChild(actions);
  return wrapper;
}

function renderThemeSelectField(sectionKey, prop, label, values, isSize = false, actualValue = "") {
  const field = document.createElement("div");
  field.className = "builder-field";
  const fieldLabel = document.createElement("label");
  fieldLabel.textContent = label;
  const select = document.createElement("select");
  const source = isSize ? STYLE_FONT_SIZE_OPTIONS : STYLE_FONT_OPTIONS;
  source.forEach((option) => {
    const opt = document.createElement("option");
    opt.value = option.value;
    opt.textContent = option.label;
    select.appendChild(opt);
  });
  select.value = values[prop] || "";
  if (!values[prop] && actualValue) {
    const placeholderOption = select.querySelector('option[value=""]');
    if (placeholderOption) {
      placeholderOption.textContent = actualValue;
    }
  }
  select.addEventListener("change", (event) => {
    updateThemeSection(sectionKey, { [prop]: event.target.value });
  });
  field.appendChild(fieldLabel);
  field.appendChild(select);
  return field;
}

function renderThemeColorField(sectionKey, prop, label, values, actualValue = "") {
  const current = values[prop] || "";
  const field = document.createElement("div");
  field.className = "builder-field builder-field--color";
  const fieldLabel = document.createElement("label");
  fieldLabel.textContent = label;
  const controls = document.createElement("div");
  controls.className = "builder-color-control";
  const colorInput = document.createElement("input");
  colorInput.type = "color";
  const effective = current || normalizeHex(actualValue) || "";
  colorInput.value = effective || "#000000";
  const hexInput = document.createElement("input");
  hexInput.type = "text";
  hexInput.inputMode = "text";
  hexInput.placeholder = "#000000";
  hexInput.value = effective || "";
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "btn btn-xs btn-outline-secondary";
  clearBtn.textContent = "Clear";

  const emitValue = (value) => {
    const next = normalizeHex(value);
    updateThemeSection(sectionKey, { [prop]: next });
  };

  colorInput.addEventListener("input", (event) => {
    const next = normalizeHex(event.target.value);
    hexInput.value = next;
    emitValue(next);
  });

  hexInput.addEventListener("change", (event) => {
    const raw = event.target.value.trim();
    if (!raw) {
      colorInput.value = "#000000";
      hexInput.value = "";
      emitValue("");
      return;
    }
    const normalised = normalizeHex(raw.startsWith("#") ? raw : `#${raw}`);
    if (!normalised) {
      const latest = getPageTheme()[sectionKey]?.[prop] || "";
      event.target.value = latest;
      return;
    }
    colorInput.value = normalised;
    hexInput.value = normalised;
    emitValue(normalised);
  });

  clearBtn.addEventListener("click", () => {
    colorInput.value = "#000000";
    hexInput.value = "";
    emitValue("");
    renderSettings();
  });

  controls.appendChild(colorInput);
  controls.appendChild(hexInput);
  controls.appendChild(clearBtn);
  field.appendChild(fieldLabel);
  field.appendChild(controls);
  return field;
}

function renderThemeFontAssetField(sectionKey, prop, label, current, actualValue = "") {
  const field = document.createElement("div");
  field.className = "builder-field";
  const fieldLabel = document.createElement("label");
  fieldLabel.textContent = label;
  const hint = document.createElement("small");
  hint.className = "muted";
  if (!actualValue) {
    hint.textContent = "Apply a custom font from Assets → Fonts.";
  } else {
    hint.textContent = "";
  }
  const controls = buildFontAssetControls({
    context: "panel",
    currentAsset: current,
    placeholder: actualValue || "Use theme font",
    onChange(payload) {
      updateThemeSection(sectionKey, { [prop]: payload });
      renderSettings();
    },
  });
  field.appendChild(fieldLabel);
  if (hint.textContent) {
    field.appendChild(hint);
  }
  field.appendChild(controls);
  return field;
}

function renderThemeCard() {
  if (!dom.themePanel) {
    return;
  }
  dom.themePanel.innerHTML = "";
  dom.themePanel.appendChild(renderThemePanel());
}

function renderField(block, field, blueprint = null) {
  const container = document.createElement("div");
  container.className = "builder-field";
  const isToggle = field.type === "toggle";
  if (isToggle) {
    container.classList.add("builder-field--toggle");
  }

  const label = document.createElement("label");
  label.textContent = field.label;
  const styleTarget =
    blueprint && Array.isArray(blueprint.styleTargets)
      ? blueprint.styleTargets.find((target) => target.key === field.key)
      : null;
  let hintNode = null;
  if (field.help) {
    hintNode = document.createElement("small");
    hintNode.className = "muted";
    hintNode.textContent = field.help;
  }
  if (styleTarget) {
    const header = document.createElement("div");
    header.className = "builder-field__header";
    header.appendChild(label);
    const styleBtn = document.createElement("button");
    styleBtn.type = "button";
    styleBtn.className = "builder-style-chip btn btn-xs btn-outline-secondary";
    styleBtn.textContent = "Text style";
    styleBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openStylePopover({
        blockId: block.id,
        targetKey: styleTarget.key,
        label: styleTarget.label || field.label,
        anchor: styleBtn.getBoundingClientRect(),
      });
    });
    header.appendChild(styleBtn);
    container.appendChild(header);
  } else {
    container.appendChild(label);
  }
  if (hintNode && !isToggle) {
    container.appendChild(hintNode);
  }

  const value = block.props[field.key];
  let input;

  switch (field.type) {
    case "text":
    case "url":
      input = document.createElement("input");
      input.type = field.type === "url" ? "url" : "text";
      input.value = value || "";
      input.addEventListener("input", (event) => {
        updateBlockProp(block.id, field.key, event.target.value);
      });
      break;
    case "number":
      input = document.createElement("input");
      input.type = "number";
      if (field.min !== undefined) input.min = field.min;
      if (field.max !== undefined) input.max = field.max;
      if (field.step !== undefined) input.step = field.step;
      input.value = value ?? "";
      input.addEventListener("input", (event) => {
        const val = event.target.value;
        updateBlockProp(block.id, field.key, val === "" ? null : Number(val));
      });
      break;
    case "range":
      input = document.createElement("input");
      input.type = "range";
      input.min = field.min ?? 0;
      input.max = field.max ?? 1;
      input.step = field.step ?? 0.05;
      input.value = value ?? field.min ?? 0;
      const rangeValue = document.createElement("span");
      rangeValue.className = "muted";
      rangeValue.textContent = Number(input.value).toFixed(2);
      input.addEventListener("input", (event) => {
        const val = Number(event.target.value);
        rangeValue.textContent = val.toFixed(2);
        updateBlockProp(block.id, field.key, val);
      });
      container.appendChild(rangeValue);
      break;
    case "textarea":
      input = document.createElement("textarea");
      input.rows = field.rows || 4;
      input.value = value || "";
      input.addEventListener("input", (event) => {
        updateBlockProp(block.id, field.key, event.target.value);
      });
      break;
    case "select":
      input = document.createElement("select");
      (field.options || []).forEach((option) => {
        const opt = document.createElement("option");
        opt.value = option.value;
        opt.textContent = option.label;
        input.appendChild(opt);
      });
      input.value = value || (field.options && field.options[0] && field.options[0].value) || "";
      input.addEventListener("change", (event) => {
        updateBlockProp(block.id, field.key, event.target.value);
      });
      break;
    case "toggle":
      input = document.createElement("input");
      input.type = "checkbox";
      input.checked = Boolean(value);
      input.addEventListener("change", (event) => {
        updateBlockProp(block.id, field.key, event.target.checked);
      });
      break;
    case "navlinks":
      return renderNavLinksField(block, field, container);
    case "sluglist":
      input = document.createElement("input");
      input.type = "text";
      input.value = Array.isArray(value) ? value.join(", ") : value || "";
      input.placeholder = "category-one, category-two";
      input.addEventListener("input", (event) => {
        const raw = event.target.value;
        const items = raw
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
        updateBlockProp(block.id, field.key, items);
      });
      break;
    case "list":
      if (field.modal) {
        return renderListModalTrigger(block, field);
      }
      return renderListField(block, field);
    case "checkboxes":
      return renderCheckboxField(block, field, container);
    default:
      input = document.createElement("input");
      input.type = "text";
      input.value = value || "";
      input.addEventListener("input", (event) => {
        updateBlockProp(block.id, field.key, event.target.value);
      });
  }

  if (input) {
    container.appendChild(input);
    if (field.assetKinds && field.assetKinds.length) {
      const picker = document.createElement("button");
      picker.type = "button";
      picker.className = "btn btn-sm builder-field__asset-btn";
      picker.textContent = "Choose from library";
      picker.addEventListener("click", (event) => {
        event.preventDefault();
        openAssetBrowser({
          kinds: field.assetKinds,
          onSelect: (asset) => {
            const url = asset.url || "";
            input.value = url;
            updateBlockProp(block.id, field.key, url);
            schedulePreview(true);
          },
        });
      });
      container.appendChild(picker);
      if (field.allowUpload && config.urls && config.urls.asset_upload) {
        const uploadBtn = document.createElement("button");
        uploadBtn.type = "button";
        uploadBtn.className = "btn btn-sm builder-field__asset-btn btn-outline-secondary";
        uploadBtn.textContent = "Upload";
        uploadBtn.addEventListener("click", (event) => {
          event.preventDefault();
          if (uploadBtn.disabled) {
            return;
          }
          const accept = field.assetKinds.includes("image") ? "image/*" : "";
          uploadBtn.disabled = true;
          uploadBtn.textContent = "Uploading...";
          promptAssetUpload({ accept, kind: field.assetKinds[0] || null }, (asset) => {
            const url = asset.url || "";
            input.value = url;
            updateBlockProp(block.id, field.key, url);
            schedulePreview(true);
          }).finally(() => {
            uploadBtn.disabled = false;
            uploadBtn.textContent = "Upload";
          });
        });
        container.appendChild(uploadBtn);
      }
    }
    if (field.disabledWhen && block.props) {
      const condition = field.disabledWhen;
      const disableValue =
        typeof condition.value === "undefined" ? true : condition.value;
      const shouldDisable = block.props[condition.key] === disableValue;
      input.disabled = shouldDisable;
      input.classList.toggle("is-disabled", shouldDisable);
    }
    if (hintNode && isToggle) {
      container.appendChild(hintNode);
    }
  }

  return container;
}

function renderCheckboxField(block, field, container) {
  const options = getCheckboxOptions(field);
  const wrapper = document.createElement("div");
  wrapper.className = "builder-checkboxes";

  if (!options.length) {
    const message = document.createElement("p");
    message.className = "muted";
    message.textContent = state.siteLoading
      ? "Loading site details..."
      : "No options available. Update Site Settings first.";
    wrapper.appendChild(message);
    container.appendChild(wrapper);
    return container;
  }

  const enabledValues = options.filter((opt) => !opt.disabled).map((opt) => opt.value);
  const stored = block.props[field.key];
  const defaultSelection = field.defaultAll === false ? [] : enabledValues;
  const initialSelection =
    Array.isArray(stored) && stored.length ? stored.filter((val) => enabledValues.includes(val)) : defaultSelection;
  const selected = new Set(initialSelection);
  const checkboxes = [];

  options.forEach((option) => {
    const item = document.createElement("label");
    item.className = "builder-checkboxes__item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = option.value;
    checkbox.disabled = Boolean(option.disabled);
    checkbox.checked = selected.has(option.value) && !checkbox.disabled;
    checkbox.addEventListener("change", () => {
      if (checkbox.disabled) {
        return;
      }
      if (checkbox.checked) {
        selected.add(option.value);
      } else {
        selected.delete(option.value);
      }
      updateBlockProp(block.id, field.key, Array.from(selected));
    });

    const text = document.createElement("span");
    text.textContent = option.label || option.value;

    item.appendChild(checkbox);
    item.appendChild(text);
    wrapper.appendChild(item);
    checkboxes.push({ checkbox, option });
  });

  container.appendChild(wrapper);

  const actions = document.createElement("div");
  actions.className = "builder-checkboxes__actions";

  const selectAll = document.createElement("button");
  selectAll.type = "button";
  selectAll.className = "btn btn-xs";
  selectAll.textContent = "Select all";
  selectAll.addEventListener("click", () => {
    selected.clear();
    checkboxes.forEach(({ checkbox, option }) => {
      if (option.disabled) {
        checkbox.checked = false;
        return;
      }
      checkbox.checked = true;
      selected.add(option.value);
    });
    updateBlockProp(block.id, field.key, Array.from(selected));
  });
  actions.appendChild(selectAll);

  const clearAll = document.createElement("button");
  clearAll.type = "button";
  clearAll.className = "btn btn-xs btn-outline-secondary";
  clearAll.textContent = "Clear";
  clearAll.addEventListener("click", () => {
    selected.clear();
    checkboxes.forEach(({ checkbox }) => {
      checkbox.checked = false;
    });
    updateBlockProp(block.id, field.key, []);
  });
  actions.appendChild(clearAll);

  const refreshBtn = document.createElement("button");
  refreshBtn.type = "button";
  refreshBtn.className = "btn btn-xs";
  refreshBtn.textContent = "Refresh site info";
  refreshBtn.addEventListener("click", () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Refreshing…";
    fetchSiteContext(true).finally(() => {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "Refresh site info";
    });
  });
  actions.appendChild(refreshBtn);

  container.appendChild(actions);
  return container;
}

function renderAssetSelector({ value, kinds = [], allowUpload = false, onChange }) {
  const wrapper = document.createElement("div");
  wrapper.className = "builder-asset-field";
  const preview = document.createElement("div");
  preview.className = "builder-asset-field__preview";
  if (value && value.url) {
    preview.appendChild(buildAssetPreviewCard(value));
  } else {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No asset selected.";
    preview.appendChild(empty);
  }
  wrapper.appendChild(preview);

  const actions = document.createElement("div");
  actions.className = "builder-asset-field__actions";
  const chooseBtn = document.createElement("button");
  chooseBtn.type = "button";
  chooseBtn.className = "btn btn-sm";
  chooseBtn.textContent = value ? "Replace asset" : "Choose asset";
  chooseBtn.addEventListener("click", () => {
    openAssetBrowser({
      kinds,
      onSelect(asset) {
        const normalised = normaliseBuilderAsset(asset);
        if (!normalised) {
          alert("Could not use that asset.");
          return;
        }
        onChange(normalised);
      },
    });
  });
  actions.appendChild(chooseBtn);

  if (allowUpload && config.urls && config.urls.asset_upload) {
    const uploadBtn = document.createElement("button");
    uploadBtn.type = "button";
    uploadBtn.className = "btn btn-sm btn-outline-secondary";
    uploadBtn.textContent = "Upload";
    uploadBtn.addEventListener("click", () => {
      uploadBtn.disabled = true;
      uploadBtn.textContent = "Uploading…";
      const accept =
        kinds.length === 1 && kinds[0] === "image"
          ? "image/*"
          : kinds.length === 1 && kinds[0] === "audio"
          ? "audio/*"
          : kinds.length === 1 && kinds[0] === "video"
          ? "video/*"
          : "";
      promptAssetUpload({ accept, kind: kinds[0] || null }, (asset) => {
        const normalised = normaliseBuilderAsset(asset);
        if (normalised) {
          onChange(normalised);
        }
      }).finally(() => {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Upload";
      });
    });
    actions.appendChild(uploadBtn);
  }

  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "btn btn-sm btn-outline-secondary";
  clearBtn.textContent = "Clear";
  clearBtn.disabled = !value;
  clearBtn.addEventListener("click", () => {
    onChange(null);
  });
  actions.appendChild(clearBtn);

  wrapper.appendChild(actions);
  return wrapper;
}

function renderListModalTrigger(block, field) {
  const container = document.createElement("div");
  container.className = "builder-actions builder-actions--modal";

  const summary = document.createElement("div");
  summary.className = "builder-actions__summary";
  const items = Array.isArray(block.props[field.key]) ? block.props[field.key] : [];
  summary.textContent = items.length
    ? `${items.length} ${field.itemLabel || "items"} configured`
    : "No items configured yet.";

  const openBtn = document.createElement("button");
  openBtn.type = "button";
  openBtn.className = "btn btn-sm";
  openBtn.textContent = "Edit list";
  openBtn.addEventListener("click", () => {
    openListEditor(block, field);
  });

  container.appendChild(summary);
  container.appendChild(openBtn);
  return container;
}

function renderListField(block, field) {
  const container = document.createElement("div");
  container.className = "builder-actions";
  const items = Array.isArray(block.props[field.key]) ? block.props[field.key] : [];

  const list = document.createElement("div");
  list.className = "builder-actions-list";

  items.forEach((item, index) => {
    const itemCard = document.createElement("div");
    itemCard.className = "builder-actions-item";

    const header = document.createElement("header");
    header.innerHTML = `<strong>${field.itemLabel || "Item"} #${index + 1}</strong>`;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "builder-block__btn builder-block__btn--danger";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      const nextItems = items.slice(0, index).concat(items.slice(index + 1));
      updateBlockProp(block.id, field.key, nextItems);
      renderSettings();
      schedulePreview();
    });

    header.appendChild(remove);
    itemCard.appendChild(header);

    (field.itemFields || []).forEach((subField) => {
      const subContainer = document.createElement("div");
      subContainer.className = "builder-field";
      const label = document.createElement("label");
      label.textContent = subField.label;
      subContainer.appendChild(label);

      const currentValue = item[subField.key];
      if (subField.type === "asset") {
        const selector = renderAssetSelector({
          value: currentValue,
          kinds: subField.assetKinds || [],
          allowUpload: Boolean(subField.allowUpload),
          onChange(nextAsset) {
            const next = clone(items);
            next[index][subField.key] = nextAsset;
            updateBlockProp(block.id, field.key, next);
            renderSettings();
            schedulePreview(true);
          },
        });
        subContainer.appendChild(selector);
        itemCard.appendChild(subContainer);
        return;
      }

      let input;
      if (subField.type === "toggle") {
        input = document.createElement("input");
        input.type = "checkbox";
        input.checked = Boolean(currentValue);
        input.addEventListener("change", (event) => {
          const next = clone(items);
          next[index][subField.key] = event.target.checked;
          updateBlockProp(block.id, field.key, next);
          schedulePreview();
        });
      } else if (subField.type === "select") {
        input = document.createElement("select");
        (subField.options || []).forEach((option) => {
          const opt = document.createElement("option");
          opt.value = option.value;
          opt.textContent = option.label;
          input.appendChild(opt);
        });
        input.value =
          currentValue || (subField.options && subField.options[0] && subField.options[0].value) || "";
        input.addEventListener("change", (event) => {
          const next = clone(items);
          next[index][subField.key] = event.target.value;
          updateBlockProp(block.id, field.key, next);
          schedulePreview();
        });
      } else if (subField.type === "textarea") {
        input = document.createElement("textarea");
        input.rows = subField.rows || 3;
        input.value = currentValue || "";
        input.addEventListener("input", (event) => {
          const next = clone(items);
          next[index][subField.key] = event.target.value;
          updateBlockProp(block.id, field.key, next);
          schedulePreview();
        });
      } else if (subField.type === "number") {
        input = document.createElement("input");
        input.type = "number";
        if (subField.min !== undefined) input.min = subField.min;
        if (subField.max !== undefined) input.max = subField.max;
        if (subField.step !== undefined) input.step = subField.step;
        input.value = currentValue ?? "";
        input.addEventListener("input", (event) => {
          const next = clone(items);
          const raw = event.target.value;
          next[index][subField.key] = raw === "" ? null : Number(raw);
          updateBlockProp(block.id, field.key, next);
          schedulePreview();
        });
      } else {
        input = document.createElement("input");
        input.type = subField.type === "url" ? "url" : "text";
        input.value = currentValue || "";
        input.addEventListener("input", (event) => {
          const next = clone(items);
          next[index][subField.key] = event.target.value;
          updateBlockProp(block.id, field.key, next);
          schedulePreview();
        });
      }
      subContainer.appendChild(input);
      itemCard.appendChild(subContainer);
    });

    list.appendChild(itemCard);
  });

  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "btn btn-sm";
  addButton.textContent = `Add ${field.itemLabel || "item"}`;
  addButton.addEventListener("click", () => {
    const next = clone(items);
    next.push(clone(field.itemDefaults || {}));
    updateBlockProp(block.id, field.key, next);
    renderSettings();
    schedulePreview(true);
  });

  container.appendChild(list);
  container.appendChild(addButton);
  return container;
}

function renderNavLinksField(block, field, container) {
  const items = config.nav_items || [];
  if (!items.length) {
    const message = document.createElement("p");
    message.className = "muted";
    message.textContent = "Add more pages to configure navigation links.";
    container.appendChild(message);
    return container;
  }

  const legacyField = document.getElementById("id_custom_nav_items");
  const legacyToggle = document.getElementById("id_show_navigation_bar");
  if (legacyToggle) legacyToggle.value = "True";

  const rawStored = Array.isArray(block.props[field.key]) ? block.props[field.key].slice() : null;
  const stored = Array.isArray(rawStored)
    ? rawStored
        .map((entry) => {
          if (typeof entry === "string") {
            return entry;
          }
          if (entry && typeof entry === "object") {
            if (typeof entry.slug === "string") {
              return entry.slug;
            }
            if (typeof entry.value === "string") {
              return entry.value;
            }
          }
          return null;
        })
        .filter(Boolean)
    : null;
  const hasExplicitSelection = Array.isArray(rawStored);
  let selectedOrder = hasExplicitSelection
    ? (stored ? stored.slice() : [])
    : items.filter((item) => item.checked).map((item) => item.slug);
  if (!hasExplicitSelection && !selectedOrder.length) {
    selectedOrder = items.map((item) => item.slug);
  }
  selectedOrder = Array.from(new Set(selectedOrder));
  const allOrder = selectedOrder.concat(
    items.map((item) => item.slug).filter((slug) => !selectedOrder.includes(slug))
  );

  const list = document.createElement("div");
  list.className = "builder-navlinks__list";
  container.appendChild(list);

  function updateSelection() {
    const checked = [];
    Array.from(list.children).forEach((row) => {
      const slug = row.dataset.slug;
      const checkbox = row.querySelector("input[type='checkbox']");
      if (checkbox && checkbox.checked) {
        checked.push(slug);
      }
    });
    if (legacyField) legacyField.value = JSON.stringify(checked);
    updateBlockProp(block.id, field.key, checked);
  }

  function moveRow(row, direction) {
    if (!row) return;
    if (direction === -1 && row.previousElementSibling) {
      list.insertBefore(row, row.previousElementSibling);
    } else if (direction === 1 && row.nextElementSibling) {
      list.insertBefore(row.nextElementSibling, row);
    }
    updateSelection();
  }

  const selectedSet = new Set(selectedOrder);

  allOrder.forEach((slug) => {
    const meta = items.find((item) => item.slug === slug) || { slug, title: slug };
    const row = document.createElement("div");
    row.className = "builder-navlinks__item";
    row.dataset.slug = slug;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = selectedSet.has(slug);
    checkbox.addEventListener("change", updateSelection);

    const name = document.createElement("span");
    name.textContent = meta.title || slug;

    const actions = document.createElement("div");
    actions.className = "builder-navlinks__actions";
    const upBtn = document.createElement("button");
    upBtn.type = "button";
    upBtn.className = "btn btn-xs";
    upBtn.textContent = "▲";
    upBtn.addEventListener("click", () => moveRow(row, -1));
    const downBtn = document.createElement("button");
    downBtn.type = "button";
    downBtn.className = "btn btn-xs";
    downBtn.textContent = "▼";
    downBtn.addEventListener("click", () => moveRow(row, 1));
    actions.appendChild(upBtn);
    actions.appendChild(downBtn);

    row.appendChild(checkbox);
    row.appendChild(name);
    row.appendChild(actions);
    list.appendChild(row);
  });

  const bulk = document.createElement("div");
  bulk.className = "builder-navlinks__bulk";
  const selectAll = document.createElement("button");
  selectAll.type = "button";
  selectAll.className = "btn btn-xs";
  selectAll.textContent = "Select all";
  selectAll.addEventListener("click", () => {
    list.querySelectorAll("input[type='checkbox']").forEach((box) => {
      box.checked = true;
    });
    updateSelection();
  });
  const clearAll = document.createElement("button");
  clearAll.type = "button";
  clearAll.className = "btn btn-xs btn-outline-secondary";
  clearAll.textContent = "Clear";
  clearAll.addEventListener("click", () => {
    list.querySelectorAll("input[type='checkbox']").forEach((box) => {
      box.checked = false;
    });
    updateSelection();
  });
  bulk.appendChild(selectAll);
  bulk.appendChild(clearAll);
  container.appendChild(bulk);

  updateSelection();
  return container;
}

function updateBlockProp(blockId, key, value, options = {}) {
  const block = state.blocks.find((item) => item.id === blockId);
  if (!block) {
    return;
  }
  const skipPreview = Boolean(options.skipPreview);
  const forceRenderSettings = Boolean(options.forceRenderSettings);
  let needsRefresh = false;
  if (block.type === "navigation" && block.props) {
    if (key === "logo_text" && block.props.logo_text_auto) {
      block.props.logo_text_auto = false;
      needsRefresh = true;
    } else if (key === "logo_text_auto") {
      block.props.logo_text_auto = Boolean(value);
      if (block.props.logo_text_auto) {
        block.props.logo_text = getDefaultBrandText() || block.props.logo_text || "";
      } else {
        block.props.logo_text = "";
      }
      needsRefresh = true;
    }
  }
  block.props = { ...block.props, [key]: value };
  state.dirty = true;
  persistBlocks();
  if (!skipPreview) {
    schedulePreview();
  }
  if (needsRefresh || forceRenderSettings) {
    renderSettings();
  }
}

function addBlock(type) {
  const blueprint = getBlueprint(type);
  if (!blueprint) {
    return;
  }
  const block = normaliseBlock({
    id: uuid(),
    type,
    props: clone(blueprint.defaults),
  });
  if (type === "navigation" && Array.isArray(config.nav_items)) {
    const defaultLinks = config.nav_items.filter((item) => item.checked).map((item) => item.slug);
    if (defaultLinks.length) {
      block.props.links = defaultLinks;
    }
  }
  if (type === "navigation") {
    block.props.logo_text_auto = block.props.logo_text_auto !== false;
    if (block.props.logo_text_auto) {
      block.props.logo_text = getDefaultBrandText() || block.props.logo_text || "";
    }
  }
  let nextBlocks = state.blocks.slice();
  if (type === "navigation") {
    nextBlocks.unshift(block);
  } else if (type === "footer") {
    nextBlocks.push(block);
  } else {
    nextBlocks.push(block);
  }
  state.blocks = nextBlocks;
  state.selectedId = block.id;
  state.dirty = true;
  renderBlockList();
  renderSettings();
  persistBlocks();
  schedulePreview(true);
}

function selectBlock(blockId) {
  state.selectedId = blockId;
  renderBlockList();
  renderSettings();
}

function moveBlock(blockId, direction) {
  const index = state.blocks.findIndex((block) => block.id === blockId);
  if (index === -1) {
    return;
  }
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= state.blocks.length) {
    return;
  }
  const updated = state.blocks.slice();
  const [removed] = updated.splice(index, 1);
  updated.splice(targetIndex, 0, removed);
  state.blocks = updated;
  state.dirty = true;
  renderBlockList();
  renderSettings();
  persistBlocks();
  schedulePreview();
}

function removeBlock(blockId) {
  const next = state.blocks.filter((block) => block.id !== blockId);
  state.blocks = next;
  if (state.selectedId === blockId) {
    state.selectedId = next.length ? next[0].id : null;
  }
  state.dirty = true;
  renderBlockList();
  renderSettings();
  persistBlocks();
  schedulePreview();
}

function handleFormSubmit(event) {
  persistBlocks();
  if (!config.urls || !config.urls.save) {
    return;
  }
  // Default form submission handles hero image uploads, keep behaviour.
}

function handlePreviewButton(event) {
  event.preventDefault();
  schedulePreview(true);
}

function fetchSiteContext(force = false) {
  if (!config.urls || !config.urls.site) {
    return Promise.resolve(null);
  }
  if (!force && state.siteContext && !state.siteLoading) {
    return Promise.resolve(state.siteContext);
  }
  if (state.siteLoading && siteContextRequest) {
    return siteContextRequest;
  }
  state.siteLoading = true;
  siteContextRequest = fetch(config.urls.site, { headers: { Accept: "application/json" } })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to load site context");
      }
      return response.json();
    })
    .then((data) => {
      state.siteContext = data;
      applySiteBrandTextDefaults();
      return data;
    })
    .catch(() => {
      state.siteContext = null;
      return null;
    })
    .finally(() => {
      state.siteLoading = false;
      renderSettings();
    });
  return siteContextRequest;
}

function bootstrap() {
  const root = document.getElementById("page-builder");
  if (!root) {
    return;
  }
  config = window.__PAGE_BUILDER__ || {};
  config.nav_items = config.nav_items || [];
  state.siteContext = config.site_context || state.siteContext;
  state.theme = normaliseTheme((config.page && config.page.theme) || {});

  dom.form = document.getElementById("page-form");
  dom.blocksInput = document.getElementById("id_blocks");
  dom.themeInput = document.getElementById("id_theme");
  dom.themePanel = document.getElementById("builder-theme-panel");
  dom.library = document.getElementById("builder-library");
  dom.blockList = document.getElementById("builder-block-list");
  dom.settings = document.getElementById("builder-settings");
  dom.previewFrames = Array.from(document.querySelectorAll("[data-preview-frame]"));
  dom.previewFrames.forEach((frame) => bindInlineFrame(frame));
  dom.previewCanvas = document.getElementById("builder-preview-canvas");
  dom.previewToggle = document.getElementById("builder-preview-toggle");
  dom.previewModeButtons = dom.previewToggle
    ? Array.from(dom.previewToggle.querySelectorAll(".preview-toggle__btn"))
    : [];
  dom.saveButton = document.getElementById("builder-save-btn");
  dom.previewButton = document.getElementById("builder-preview-btn");
  dom.inlineEditButton = document.getElementById("builder-inline-edit-btn");

  assetState.modal = document.getElementById("asset-browser");
  if (assetState.modal) {
    assetState.overlay = assetState.modal.querySelector(".asset-browser__overlay");
    assetState.panel = assetState.modal.querySelector(".asset-browser__panel");
    assetState.list = document.getElementById("asset-browser-list");
    assetState.subtitle = document.getElementById("asset-browser-subtitle");
    assetState.closeButtons = Array.from(assetState.modal.querySelectorAll("[data-asset-close]"));
    assetState.closeButtons.forEach((btn) => btn.addEventListener("click", closeAssetBrowser));
    if (assetState.overlay) {
      assetState.overlay.addEventListener("click", closeAssetBrowser);
    }
  }
  initStylePopover();

  const initialBlocks = normaliseBlocks((config.page && config.page.blocks) || []);
  if (!initialBlocks.length && config.page && config.page.body) {
    const fallback = getBlueprint("rich_text");
    if (fallback) {
      initialBlocks.push({
        id: uuid(),
        type: "rich_text",
        props: { ...clone(fallback.defaults), html: config.page.body },
      });
    }
  }

  state.blocks = initialBlocks;
  applySiteBrandTextDefaults({ silent: true });
  if (state.blocks.length) {
    state.selectedId = state.blocks[0].id;
  }
  persistBlocks();
  persistTheme();

  renderLibrary();
  renderBlockList();
  renderSettings();
  renderThemeCard();

  if (dom.form) {
    dom.form.addEventListener("submit", handleFormSubmit);
  }
  if (dom.previewButton) {
    dom.previewButton.addEventListener("click", handlePreviewButton);
  }
  if (dom.saveButton) {
    dom.saveButton.addEventListener("click", persistBlocks);
  }
  if (dom.inlineEditButton) {
    dom.inlineEditButton.addEventListener("click", () => {
      setInlineEditMode(!inlineState.enabled);
    });
  }

  function setPreviewMode(mode) {
    if (!dom.previewCanvas) {
      return;
    }
    dom.previewCanvas.setAttribute("data-preview-mode", mode);
    dom.previewModeButtons.forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.mode === mode);
    });
  }

  if (dom.previewModeButtons.length) {
    dom.previewModeButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        setPreviewMode(btn.dataset.mode || "desktop");
      });
    });
    setPreviewMode("desktop");
  }

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    if (isAssetBrowserOpen()) {
      event.preventDefault();
      closeAssetBrowser();
    } else if (isStylePopoverOpen()) {
      event.preventDefault();
      closeStylePopover();
    }
  });

  setPreviewHTML(config.preview_html || "");

  if (state.blocks.length) {
    schedulePreview(true);
  }
  fetchSiteContext(!state.siteContext);
  fetchFontAssets();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
