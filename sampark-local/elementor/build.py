#!/usr/bin/env python3
"""Genereert de Elementor-pagina's voor Sampark als JSON (elementor/pages/*.json).

De JSON wordt door scripts/build-site.php in WordPress gezet en is ook als
template te importeren (Elementor > Templates > Importeren) op staging.

Placeholders die build-site.php invult:
  {{img:sleutel}} / {{imgid:sleutel}}  -> url / id van een geïmporteerde afbeelding
  {{url:/pad/}}                       -> absolute url op de site

Blokken die later een JetEngine Listing Grid worden, hebben in de Navigator een
titel die begint met "LISTING ·". De statische kaarten daarin zijn het ontwerp
van het listing item.
"""
import json
import hashlib
from pathlib import Path
from urllib.parse import quote

OUT = Path(__file__).parent / "pages"

# ---------------------------------------------------------------- basis

_n = 0


def _id(seed=""):
    global _n
    _n += 1
    return hashlib.md5(f"{seed}{_n}".encode()).hexdigest()[:7]


def g_color(name):
    return f"globals/colors?id={name}"


def g_type(name):
    return f"globals/typography?id={name}"


def dims(top, right=None, bottom=None, left=None, unit="px"):
    right = top if right is None else right
    bottom = top if bottom is None else bottom
    left = right if left is None else left
    vals = [str(v) for v in (top, right, bottom, left)]
    return {"unit": unit, "top": vals[0], "right": vals[1], "bottom": vals[2], "left": vals[3],
            "isLinked": len(set(vals)) == 1}


def size(v, unit="px"):
    return {"unit": unit, "size": v, "sizes": []}


def gap(v):
    return {"column": str(v), "row": str(v), "isLinked": True, "unit": "px", "size": v}


# Elementor-vormscheiding "Waves": (breedte %, hoogte px). Smaller en hoger dan op staging, zodat de golf
# duidelijker zichtbaar is.
WAVES = {"top": (150, 80), "bottom": (130, 70)}
WAVES_MOBILE = (260, 44)

# Overlay op hero's: van links (tekst) bijna dekkend naar rechts halfdoorzichtig, voor contrast op elke foto
HERO_OVERLAY = ("#46211AD9", "#46211A59")


def container(*children, title=None, direction="column", boxed=False, width=None, gap_px=24,
              pad=None, pad_mobile=None, bg=None, bg_global=None, bg_image=None, overlay=None,
              radius=None, align=None, justify=None, wrap=False, mobile_column=True,
              divider_bottom=None, divider_top=None, min_height=None, tag=None, css_classes=None,
              extra=None):
    s = {"flex_direction": direction, "flex_gap": gap(gap_px)}
    if boxed:
        s["content_width"] = "boxed"
        s["boxed_width"] = size(1140)
    else:
        s["content_width"] = "full"
    if width is not None:
        s["width"] = size(width, "%")
        s["width_mobile"] = size(100, "%")
    if direction == "row":
        # expliciet zetten: anders neemt een kind de mobiele richting van zijn ouder over
        s["flex_direction_tablet"] = "row"
        s["flex_direction_mobile"] = "column" if mobile_column else "row"
    if wrap:
        s["flex_wrap"] = "wrap"
    if pad is not None:
        s["padding"] = pad
    if pad_mobile is not None:
        s["padding_mobile"] = pad_mobile
    globs = {}
    if bg or bg_global:
        s["background_background"] = "classic"
        if bg:
            s["background_color"] = bg
        if bg_global:
            globs["background_color"] = g_color(bg_global)
    if bg_image:
        s["background_background"] = "classic"
        s["background_image"] = {"url": f"{{{{img:{bg_image}}}}}", "id": f"{{{{imgid:{bg_image}}}}}"}
        s["background_position"] = "center center"
        s["background_size"] = "cover"
    if overlay:
        s["background_overlay_background"] = "gradient"
        s["background_overlay_color"] = overlay[0]
        s["background_overlay_color_b"] = overlay[1]
        s["background_overlay_gradient_angle"] = size(90, "deg")
        s["background_overlay_opacity"] = {"unit": "px", "size": 1, "sizes": []}
    if radius is not None:
        s["border_radius"] = dims(radius)
    if align:
        s["flex_align_items"] = align
    if justify:
        s["flex_justify_content"] = justify
    if min_height:
        s["min_height"] = size(min_height, "px")
    for side, d in (("bottom", divider_bottom), ("top", divider_top)):
        if d:
            shape, color, h = d
            s[f"shape_divider_{side}"] = shape
            s[f"shape_divider_{side}_color"] = color
            if shape == "waves":
                # golfbeweging uit de huisstijl, met de maten van staging: breed uitgerekt, dus rustig
                w, hh = WAVES[side]
                s[f"shape_divider_{side}_width"] = size(w, "%")
                s[f"shape_divider_{side}_height"] = size(hh)
                s[f"shape_divider_{side}_width_mobile"] = size(WAVES_MOBILE[0], "%")
                s[f"shape_divider_{side}_height_mobile"] = size(WAVES_MOBILE[1])
            else:
                s[f"shape_divider_{side}_width"] = size(100, "%")
                s[f"shape_divider_{side}_height"] = size(h)
    if tag:
        s["html_tag"] = tag
    if title:
        s["_title"] = title
    if css_classes:
        s["css_classes"] = css_classes
    if extra:
        s.update(extra)
    if globs:
        s["__globals__"] = globs
    return {"id": _id(title or ""), "elType": "container", "settings": s,
            "elements": [c for c in children if c], "isInner": False}


def section(*children, title, bg_global=None, pad=(96, 24), boxed=True, gap_px=40, **kw):
    """Paginasectie: volle breedte achtergrond, inhoud 1140px."""
    return container(*children, title=title, boxed=boxed, gap_px=gap_px, bg_global=bg_global,
                     pad=dims(pad[0], pad[1]), pad_mobile=dims(min(pad[0], 64), 20), tag="section", **kw)


def widget(kind, settings, title=None):
    if title:
        settings["_title"] = title
    return {"id": _id(kind), "elType": "widget", "widgetType": kind, "settings": settings, "elements": []}


def heading(text, level="h2", align=None, color=None, typo=None, size_px=None, tag=None):
    s = {"title": text, "header_size": tag or level}
    globs = {}
    if align:
        s["align"] = align
    if color:
        globs["title_color"] = g_color(color)
    if typo:
        globs["typography_typography"] = g_type(typo)
    if size_px:
        s["typography_typography"] = "custom"
        s["typography_font_size"] = size(size_px)
        s["typography_font_size_mobile"] = size(round(size_px * 0.72))
    if globs:
        s["__globals__"] = globs
    return widget("heading", s)


def eyebrow(text, color="accent", align=None):
    """Kleine kop boven een titel, Patrick Hand in hoofdletters (globale typografie 'accent')."""
    s = {"title": text, "header_size": "p", "typography_typography": "custom",
         "typography_font_size": size(20), "typography_letter_spacing": size(0.5),
         "__globals__": {"title_color": g_color(color), "typography_typography": g_type("accent")}}
    if align:
        s["align"] = align
    return widget("heading", s)


def text(html, color=None, align=None, size_px=None):
    s = {"editor": html}
    if align:
        s["align"] = align
    if color:
        s["__globals__"] = {"text_color": g_color(color)}
    if size_px:
        s["typography_typography"] = "custom"
        s["typography_font_size"] = size(size_px)
    return widget("text-editor", s)


def button(label, url, style="primary", align=None, full=False, icon=False, nowrap=False):
    s = {"text": label, "link": {"url": url, "is_external": "", "nofollow": ""}}
    if nowrap:
        s["_flex_size"] = "none"
    if align:
        s["align"] = align
    if full:
        s["align"] = "justify"
    if style == "light":
        s["__globals__"] = {"background_color": g_color("658acb6"), "button_text_color": g_color("primary"),
                            "button_background_hover_color": g_color("e64974d"),
                            "hover_color": g_color("primary")}
    elif style == "dark":
        s["__globals__"] = {"background_color": g_color("primary"), "button_text_color": g_color("658acb6"),
                            "button_background_hover_color": g_color("text")}
    elif style == "link-light":
        s.update({"background_color": "#00000000", "button_padding": dims(4, 0), "typography_typography": "custom",
                  "typography_font_family": "aptos", "typography_text_transform": "none", "typography_font_size": size(14),
                  "typography_font_weight": "600"})
        s["__globals__"] = {"button_text_color": g_color("658acb6"), "hover_color": g_color("cf55c96"),
                            "button_background_hover_color": g_color("primary")}
    elif style == "outline-light":
        s["background_color"] = "#00000000"
        s["border_border"] = "solid"
        s["border_width"] = dims(1)
        s["__globals__"] = {"border_color": g_color("658acb6"), "button_text_color": g_color("658acb6"),
                            "button_background_hover_color": g_color("658acb6"), "hover_color": g_color("primary")}
    elif style == "outline":
        s["background_color"] = "#00000000"
        s["border_border"] = "solid"
        s["border_width"] = dims(1)
        s["__globals__"] = {"border_color": g_color("accent"), "button_text_color": g_color("accent"),
                            "button_background_hover_color": g_color("accent"), "hover_color": g_color("658acb6")}
    if icon:
        s["selected_icon"] = {"value": "fas fa-arrow-right", "library": "fa-solid"}
        s["icon_align"] = "row-reverse"
        s["icon_indent"] = size(8)
    return widget("button", s)


def image(key, height=None, radius=20, fit=True, alt=""):
    s = {"image": {"url": f"{{{{img:{key}}}}}", "id": f"{{{{imgid:{key}}}}}", "alt": alt},
         "image_size": "large", "width": size(100, "%"),
         "image_border_radius": dims(radius)}
    if height:
        s["height"] = size(height)
        s["height_mobile"] = size(round(height * 0.75))
        if fit:
            s["object-fit"] = "cover" if fit is True else fit
    return widget("image", s)


def icon(key, color="accent", px=72, align="center"):
    return widget("icon", {
        "selected_icon": {"value": {"url": f"{{{{img:{key}}}}}", "id": f"{{{{imgid:{key}}}}}"}, "library": "svg"},
        "size": size(px), "align": align, "__globals__": {"primary_color": g_color(color)}})


def counter(number, label, suffix="", color="primary"):
    return widget("counter", {
        "starting_number": 0, "ending_number": number, "suffix": suffix,
        "thousand_separator": "yes", "thousand_separator_char": ".", "title": label,
        "__globals__": {"number_color": g_color(color), "title_color": g_color("text"),
                        "typography_number_typography": g_type("primary")},
        "typography_title_typography": "custom", "typography_title_font_family": "aptos",
        "typography_title_font_size": size(16), "typography_title_text_transform": "none",
        "typography_title_line_height": size(1.4, "em"), "typography_title_font_weight": "400",
        "typography_number_typography": "custom", "typography_number_font_size": size(56),
    })


def icon_list(items, icon_value="fas fa-check", color="accent"):
    return widget("icon-list", {
        "icon_list": [{"text": t, "selected_icon": {"value": icon_value, "library": "fa-solid"}, "_id": _id(t)}
                      for t in items],
        "space_between": size(10),
        "__globals__": {"icon_color": g_color(color), "text_color": g_color("text")},
    })


def accordion(items):
    return widget("toggle", {
        "tabs": [{"tab_title": q, "tab_content": a, "_id": _id(q)} for q, a in items],
        "border_width": size(0), "space_between": size(12),
        "__globals__": {"title_color": g_color("text"), "tab_active_color": g_color("primary"),
                        "title_background": g_color("658acb6"), "content_color": g_color("text")},
        "title_padding": dims(18, 24), "content_padding": dims(0, 24, 18, 24),
    })


def spacer(px):
    return widget("spacer", {"space": size(px)})


def html(code, title=None):
    return widget("html", {"html": code}, title=title)


# ---------------------------------------------------------------- componenten


def section_head(eye, title, intro=None, align="left", light=False):
    color = "658acb6" if light else "text"
    items = [eyebrow(eye, color="cf55c96" if light else "accent", align=align),
             heading(title, "h2", align=align, color=color)]
    if intro:
        items.append(text(f"<p>{intro}</p>", color=color, align=align))
    return container(*items, title="Sectiekop", gap_px=8, extra={"width": size(100, "%"),
                     "max_width": size(720)} if align == "left" else {"flex_align_items": "center"})


def hero(title, intro, image_key, eye=None, buttons=(), height=560, badge=None):
    """Hero met foto, donkere gradient links en een gebogen overgang naar de volgende sectie."""
    inner = []
    if eye:
        inner.append(eyebrow(eye, color="cf55c96"))
    inner.append(heading(title, "h1", color="658acb6", typo="accent", size_px=64))
    inner.append(text(f"<p>{intro}</p>", color="658acb6", size_px=19))
    if buttons:
        inner.append(container(*buttons, title="Knoppen", direction="row", gap_px=12, mobile_column=False,
                               wrap=True))
    content = container(*inner, title="Hero tekst", gap_px=16, width=55)
    kids = [content]
    if badge:
        kids.append(badge)
    return container(
        container(*kids, title="Hero inhoud", direction="row", boxed=True, align="center",
                  justify="space-between", gap_px=40, pad=dims(140, 24, 140, 24),
                  pad_mobile=dims(110, 20, 110, 20)),
        title="Hero", bg_image=image_key, overlay=HERO_OVERLAY,
        min_height=height, align="stretch", justify="center", tag="section",
        divider_bottom=("waves", "#FFFFFF", 70),
    )


def page_hero(title, intro, image_key, eye=None):
    return hero(title, intro, image_key, eye=eye, height=440)


def card(*children, title="Kaart", bg="658acb6", pad=28, width=None, gap_px=14):
    return container(*children, title=title, bg_global=bg, radius=20, pad=dims(pad), gap_px=gap_px,
                     width=width, css_classes="sp-card")


def media_card(img, eye, title, body, link, cta="Lees meer", width=None, img_h=220):
    return card(image(img, height=img_h, radius=14), eyebrow(eye, color="accent"),
                heading(title, "h3", color="text", size_px=26), text(f"<p>{body}</p>"),
                button(cta, link, style="outline", icon=True),
                title=f"Kaart · {title}", pad=20, width=width)


def cta_band(title, body, buttons, eye=None):
    inner = []
    if eye:
        inner.append(eyebrow(eye, color="cf55c96", align="center"))
    inner += [heading(title, "h2", color="658acb6", align="center"),
              text(f"<p>{body}</p>", color="658acb6", align="center"),
              container(*buttons, direction="row", justify="center", gap_px=12, wrap=True, mobile_column=False)]
    return container(container(*inner, title="CTA inhoud", boxed=True, gap_px=16, align="center",
                               extra={"boxed_width": size(760)}),
                     title="CTA band", bg_global="primary", pad=dims(110, 24, 96, 24),
                     pad_mobile=dims(80, 20, 64, 20), tag="section", divider_top=("waves", "#FFFFFF", 60))


def stat(icon_key, number, label, suffix="", width=30):
    return container(icon(icon_key, color="cf55c96", px=64), counter(number, label, suffix),
                     title=f"Cijfer · {label}", align="center", gap_px=8, width=width)


def listing(title_note, *cards, cols=3, jet=None):
    # "titel @@listing,query,kolommen" koppelt het blok aan een JetEngine Listing Grid
    if "@@" in title_note:
        title_note, spec = title_note.split(" @@")
        lst, qry, n = spec.split(",")
        jet = (lst, qry, int(n))
    """Container die het Listing Grid voorstelt; inhoud = ontwerp van het listing item."""
    w = {2: 48, 3: 31, 4: 23}[cols]
    for c in cards:
        c["settings"]["width"] = size(w, "%")
        c["settings"]["width_mobile"] = size(100, "%")
        c["settings"]["width_tablet"] = size(48 if cols > 2 else 100, "%")
    extra = {"flex_align_items": "stretch"}
    if jet:
        # build-site.php vervangt dit blok door een JetEngine Listing Grid als JetEngine actief is
        extra["_sp_jet"] = {"listing": jet[0], "query": jet[1], "cols": jet[2] if len(jet) > 2 else cols}
    return container(*cards, title=f"LISTING · {title_note}", direction="row", wrap=True, gap_px=24,
                     extra=extra)


def logo_wall(keys, bg="#FFFFFF", jet=("sponsorlogo", "q_sponsors", 6)):
    logos = [container(image(k, height=80, radius=0, fit="contain"), title=f"Logo · {k}", bg=bg,
                       radius=999, pad=dims(24), align="center", justify="center",
                       extra={"width": size(140), "width_tablet": size(130), "width_mobile": size(120),
                              "min_height": size(140), "min_height_tablet": size(130),
                              "min_height_mobile": size(120)})
             for k in keys]
    return container(*logos, title="LISTING · sponsors (actief=true, sorteer op niveau + volgorde)",
                     direction="row", wrap=True, justify="center", gap_px=20, mobile_column=False,
                     extra={"_sp_jet": {"listing": jet[0], "query": jet[1], "cols": jet[2]}} if jet else None)


def news_cards(query="q_nieuws"):
    items = [
        ("news_golf_2025", "11 november 2025", "Nat, maar onvergetelijk: Golftoernooi 2025!",
         "Het jaarlijkse Samparkgolftoernooi was er weer eentje om niet snel te vergeten.",
         "/nat-maar-onvergetelijk-golftoernooi-2025/"),
        ("news_canada", "25 september 2025", "Scholen krijgen bezoek uit Canada!",
         "Mark en Sharon Jansen van Mores Textiles kwamen op bezoek bij onze scholen in India.",
         "/scholen-krijgen-bezoek-uit-canada/"),
        ("news_abhishek", "25 september 2025", "Afscheid Abhishek Pandey",
         "We namen op bijzondere wijze afscheid van onze gewaardeerde schoolcoördinator.",
         "/afscheid-abhishek-pandey/"),
    ]
    return listing("nieuws (3 nieuwste, of gerelateerd via relatie)",
                   *[media_card(k, d, t, b, l) for k, d, t, b, l in items], jet=("nieuwskaart", query, 3))


EVENTS = {
    "padel": ("event_padel", "21 november 2026 · Zwolle", "Padel toernooi",
              "Een sportieve middag bij Peakz Padel Zwolle. € 89 per team van twee.",
              "/evenementen/padel-toernooi/", "Schrijf je in"),
    "wijn": ("event_wijn", "Het hele jaar", "Wijnactie",
             "Rood, wit en alcoholvrij. € 43,50 per doos van zes flessen, opbrengst naar de scholen.",
             "/evenementen/wijnactie/", "Bestel je wijn"),
    "rally": ("event_rally", "September 2027 · datum volgt", "Sampark Rally",
              "Een dag met je eigen klassieker door Oost-Nederland. € 600 per equipe.",
              "/evenementen/sampark-rally/", "Bekijk de rally"),
    "golf": ("event_golf", "Oktober 2027 · datum volgt", "Golftoernooi",
             "Wedstrijd, clinic of masterclass op Het Rijk van Nunspeet. Vanaf € 300 p.p.",
             "/evenementen/golftoernooi/", "Bekijk het toernooi"),
    "reis": ("event_reis", "Op aanvraag", "Project- en cultuurreis",
             "Reis mee naar India en zie met eigen ogen wat jouw steun doet.",
             "/evenementen/project-en-cultuurreis/", "Meer over de reis"),
}


def event_card(key, status_label=None):
    img, when, title, body, link, cta = EVENTS[key]
    head = [eyebrow(when, color="accent")]
    c = card(image(img, height=200, radius=14), *head, heading(title, "h3", size_px=26),
             text(f"<p>{body}</p>"), button(cta, link, icon=True), title=f"Kaart · {title}", pad=20)
    if status_label:
        c["elements"].insert(1, html(f'<span class="sp-chip">{status_label}</span>', title="Status (dynamic)"))
    return c


# ---------------------------------------------------------------- pagina's

PAGES = []


def page(slug, title, *content, parent=None, seo=None, template="elementor_header_footer", css=None):
    """template: elementor_header_footer (met site-header en -footer) of elementor_canvas (zonder, bv. afrekenen).
    css: bestandsnaam in elementor/css/, komt als Pagina-CSS in Elementor."""
    PAGES.append({"slug": slug, "title": title, "parent": parent, "seo": seo, "content": list(content),
                  "template": template, "css": css})


# HOME -------------------------------------------------------------------
wine_badge = container(
    widget("icon-box", {
        "selected_icon": {"value": {"url": "{{img:icon_wijn}}", "id": "{{imgid:icon_wijn}}"}, "library": "svg"},
        "position": "left", "position_mobile": "left", "position_tablet": "left", "text_align_mobile": "left",
        "title_text": "Wijnactie 2026", "description_text": "Rood, wit en alcoholvrij<br><strong>Bestel nu →</strong>",
        "title_size": "p", "icon_size": size(56), "icon_size_mobile": size(44), "icon_space": size(16),
        "link": {"url": "/evenementen/wijnactie/"},
        "title_typography_typography": "custom", "title_typography_font_size": size(28),
        "title_typography_font_size_mobile": size(24), "title_typography_line_height": size(1.1, "em"),
        "description_typography_typography": "custom", "description_typography_font_size": size(16),
        "description_typography_font_weight": "600",
        # donkerbruin op oranje: wit/crème op #ED7404 haalt geen 4,5:1 contrast
        "__globals__": {"primary_color": g_color("text"), "title_color": g_color("text"),
                        "description_color": g_color("text"), "title_typography_typography": g_type("accent")},
    }),
    title="Campagnebadge (Dynamic Visibility: Options › campagne aan)", bg_global="secondary", radius=999,
    pad=dims(20, 36, 20, 24), css_classes="sp-campagne",
    extra={"width": size(360), "width_mobile": size(300), "flex_align_self": "center"})

page("home", "Home",
     hero("Help een kind naar school",
          "Voor € 5 per maand geef je een kind in India de kans om te leren. Sinds 2007 bouwen we samen met lokale partners aan vier scholen en drie beroepsopleidingen.",
          "hero_home", eye="Stichting Sampark",
          buttons=(button("Doneer nu", "/steun-ons/doneren/"),
                   button("Sponsor een kind", "/product/sponsor-een-kind/", style="light")),
          badge=wine_badge),
     section(
         container(stat("icon_rugtas", 1577, "Leerlingen op onze vier scholen"),
                   stat("icon_computer", 600, "Voltooide cursussen in Delhi", "+"),
                   stat("icon_fiets", 125, "Fietsen per jaar voor geslaagden"),
                   title="Kerncijfers (Options Page › kerncijfers)", direction="row", justify="space-between",
                   gap_px=32),
         title="Impact", pad=(48, 24)),
     section(
         section_head("Ons werk", "Onderwijs als begin van een betere toekomst",
                      "We richten ons op één ding: kinderen en jongvolwassenen in India de kans geven om te leren. Op het platteland rond Budaun en in de stad New Delhi."),
         listing("projecttype (3 termen, met aantal projecten)",
                 media_card("proj_khukdi", "4 scholen · Budaun", "Scholen op het platteland",
                            "Ruim 1.500 kinderen krijgen dagelijks les op de scholen in Khukdi, Kundanpur, Bilsi en Ghadia.",
                            "/ons-werk/#scholen", "Bekijk de scholen"),
                 media_card("proj_computer", "3 opleidingen · New Delhi", "Een vak leren in de stad",
                            "Computerspecialist, modinette en schoonheidsspecialiste: opleidingen die echt tot werk leiden.",
                            "/ons-werk/#opleidingen", "Bekijk de opleidingen"),
                 media_card("proj_fietsen", "Initiatieven", "Fietsen, zon en licht",
                            "Fietsen voor geslaagden, zonnepanelen op Khukdi en solarlampjes om thuis te studeren.",
                            "/ons-werk/#initiatieven", "Bekijk de initiatieven")),
         title="Ons werk"),
     section(
         container(
             container(eyebrow("Waar je geld naartoe gaat"),
                       heading("95% gaat direct naar hulp", "h2"),
                       text("<p>Het bestuur werkt onbezoldigd en Venture Group draagt de organisatiekosten. Daardoor komt vrijwel elke euro terecht bij de scholen en opleidingen.</p>"),
                       icon_list(["Salarissen van docenten", "Lesmateriaal en sportattributen", "Schoolarts en schoolreis",
                                  "Fietsen voor geslaagden", "Computers en naaimachines voor Delhi", "Huur, elektriciteit en onderhoud"]),
                       button("ANBI en jaarverslagen", "/over-ons/anbi/", style="outline", icon=True),
                       title="Tekst", gap_px=16, width=50),
             container(image("proj_khukdi_gebouw", height=520), title="Beeld", width=46),
             title="Twee kolommen", direction="row", gap_px=48, align="center"),
         title="Transparantie", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50)),
     section(
         container(section_head("Doe mee", "Steun ons met plezier",
                                "Een dag achter het stuur, een balletje slaan of een glas wijn met vrienden: bij Sampark begint hulp vaak met plezier."),
                   button("Alle evenementen", "/evenementen/", style="outline", icon=True, nowrap=True),
                   direction="row", justify="space-between", align="flex-end", gap_px=24),
         listing("evenementen · status IN (aangekondigd, open, doorlopend) · sorteer datum_start ASC · max 3 @@eventkaart,q_events_home,3",
                 event_card("padel", "Inschrijving open"), event_card("wijn", "Het hele jaar"),
                 event_card("rally", "Aangekondigd")),
         title="Evenementen"),
     section(
         section_head("Steun ons", "Kies hoe je wilt helpen", align="center"),
         container(
             card(eyebrow("Eenmalig"), heading("Doneer", "h3", size_px=30),
                  text("<p>Elk bedrag helpt. Giften aan Sampark zijn aftrekbaar, want we zijn een ANBI.</p>"),
                  button("Doneer nu", "/steun-ons/doneren/", full=True), title="Kaart · Doneer"),
             card(eyebrow("€ 60 per jaar"), heading("Sponsor een kind", "h3", size_px=30),
                  text("<p>Je betaalt een jaar lesgeld en schoolbenodigdheden voor één kind.</p>"),
                  button("Sponsor een kind", "/product/sponsor-een-kind/", full=True), title="Kaart · Sponsor een kind"),
             card(eyebrow("Vanaf € 500 per jaar"), heading("Voor bedrijven", "h3", size_px=30),
                  text("<p>Een sponsorpakket met naamsvermelding en deelname aan onze evenementen.</p>"),
                  button("Bekijk de pakketten", "/steun-ons/bedrijven/", full=True), title="Kaart · Bedrijven"),
             title="Drie keuzes", direction="row", gap_px=24, extra={"flex_align_items": "stretch"}),
         title="Steun ons"),
     section(
         section_head("Onze sponsors", "Deze bedrijven gingen je voor", align="center", light=False),
         logo_wall(["logo_venture", "logo_groothuis", "logo_schieven", "logo_w4y", "logo_venttri",
                    "logo_rijk", "logo_arcus", "logo_kvs", "logo_pleijsier", "logo_positie1"]),
         container(button("Word sponsor", "/steun-ons/bedrijven/", style="dark"), align="center"),
         title="Sponsors", bg_global="cf55c96", divider_top=("waves", "#FFFFFF", 50),
         divider_bottom=("waves", "#FFFFFF", 50)),
     section(
         container(section_head("Nieuws", "Het laatste uit India en Nederland"),
                   button("Alle nieuwsberichten", "/nieuws/", style="outline", icon=True, nowrap=True),
                   direction="row", justify="space-between", align="flex-end", gap_px=24),
         news_cards(),
         title="Nieuws"),
     seo=("Stichting Sampark | Help een kind in India naar school",
          "Sinds 2007 geeft Stichting Sampark kinderen in India toegang tot onderwijs. Doneer, sponsor een kind of doe mee aan onze evenementen."))

# ONS WERK ---------------------------------------------------------------


# ---------------------------------------------------------------- scholen en kaart

LEAFLET_CSS = (Path(__file__).parent.parent / "assets" / "vendor" / "leaflet-1.9.4.min.css").read_text()

DEFAULT_FUNDS = ["Salarissen van docenten", "Lesmateriaal", "Schoolarts", "Fietsen voor geslaagden"]

# Locaties: Bilsi en Islamnagar komen uit OpenStreetMap (plaatsniveau). Khukdi en Ghadia staan niet
# in OSM; hun positie is bij benadering en moet in het JetEngine Map-veld worden ingevuld.
SCHOOLS = [
    {"slug": "khukdi-school", "name": "Khukdi School", "tagline": "Van vijf lokalen naar vijftien",
     "pupils": 407, "work": "Nieuwbouw", "village": "Khukdi", "lat": 28.07, "lng": 79.02, "approx": True,
     "img": "proj_khukdi", "gallery": ["proj_khukdi", "proj_zon"],
     "intro": "In het oude schoolgebouw van Khukdi waren maar vijf leslokalen beschikbaar. Voor 407 kinderen. Dat betekende dat sommige klassen buiten les kregen, met alles wat het weer daar aan meebrengt: hitte, stof en regen. Wie buiten zit, leert minder.",
     "facts": [("407", "leerlingen"), ("15", "klaslokalen"), ("1", "bibliotheek"), ("Zon", "eigen stroom")],
     "story_title": "Een school die klopt",
     "story": ["Het nieuwe gebouw telt maar liefst vijftien klaslokalen. Op de begane grond zijn zes lokalen, een sportzaal, kantoren en een ruimte voor de schoolzuster. Op de eerste etage nog eens negen lokalen, een bibliotheek en een computerruimte. Er zijn meerdere sanitaire voorzieningen, waardoor kinderen ook het belang van hygiëne meekrijgen.",
               "Voor het eerst kan iedere leerling in Khukdi zijn lessen volgen in een echt klaslokaal, zonder gehinderd te worden door weersinvloeden."],
     "extra_title": "Energie van de zon",
     "extra": "Khukdi is ook onze meest duurzame school. Dankzij een geslaagd zonnepanelenproject wekt de school haar eigen energie op. Dat is belangrijk in een regio waar de stroom regelmatig uitvalt. Zo blijven de computers draaien en de lampen branden, ook als het net het laat afweten.",
     "facilities": ["15 klaslokalen", "Sportzaal", "Bibliotheek", "Computerruimte", "Ruimte voor de schoolzuster", "Sanitaire voorzieningen", "Zonnepanelen"],
     "funds": DEFAULT_FUNDS,
     "moments": [("Vroeger", "Vijf lokalen voor 407 kinderen; sommige klassen kregen buiten les."),
                 ("Nieuwbouw", "Een gebouw met vijftien lokalen, een bibliotheek en een computerruimte."),
                 ("Zonnepanelen", "De school wekt haar eigen stroom op.")],
     "news": [("proj_zon", "Khukdi School", "Zonnepanelen op de school in Khukdi", "Hoe de school haar eigen energie is gaan opwekken.", "/zonnepanelen-sampark-school-khukdi/")]},
    {"slug": "kundanpur-school", "name": "Kundanpur School", "tagline": "Waar het begint",
     "pupils": 329, "work": "Renovatie", "village": "Islamnagar", "lat": 28.3289, "lng": 78.7258, "approx": False,
     "img": "proj_kundanpur", "gallery": ["proj_kundanpur", "hero_contact"],
     "intro": "Voor bezoekers uit Nederland is Kundanpur meestal de eerste school die ze zien. De bus rijdt het dorp Islamnagar binnen en dan gaat het snel: een tikka op het voorhoofd, een bloemenkrans om de nek, en honderden kinderen die in de rij staan om je welkom te heten.",
     "facts": [("329", "leerlingen"), ("Renovatie", "gebouw"), ("Islamnagar", "dorp"), ("VCT", "lokale partner")],
     "story_title": "Opgeknapt door vrijwilligers",
     "story": ["Wie na de ontvangst een rondje door het dorp loopt, begrijpt meteen waarom deze school er staat. De huizen zijn eenvoudig, het werk is zwaar, en voor veel gezinnen is onderwijs geen vanzelfsprekendheid maar een keuze die geld kost. Op de Sampark De Paul school krijgen 329 kinderen die kans wél."],
     "extra_title": "Onderwijs stopt hier niet zomaar",
     "extra": "Toen de scholen tijdens de lockdown gesloten bleven, ging het door: onze leraren trokken de dorpen in en gaven les in kleine groepjes, zo'n vijftig tot zestig leerlingen per dag.",
     "facilities": [],
     "funds": ["Salarissen van docenten", "Lesmateriaal en sportattributen", "Schoolarts", "Vaste lasten zoals elektriciteit", "Fietsen voor geslaagden"],
     "moments": [("Renovatie", "Vrijwilligers knapten de school op."),
                 ("Lockdown", "Leraren gaven les in de dorpen, aan vijftig tot zestig leerlingen per dag."),
                 ("Nu", "329 kinderen gaan elke dag naar school.")],
     "news": []},
    {"slug": "bilsi-school", "name": "Bilsi School", "tagline": "Leren begint bij de leraar",
     "pupils": 359, "work": "Renovatie", "village": "Bilsi", "lat": 28.1277, "lng": 78.9092, "approx": False,
     "img": "proj_bilsi", "gallery": ["proj_bilsi", "over_verhaal"],
     "intro": "Op de school in Bilsi krijgen 359 kinderen les. Wat een school goed maakt, zijn niet alleen de muren. Het zijn de mensen die er voor de klas staan. Juist daar hebben we in Bilsi extra op ingezet.",
     "facts": [("359", "leerlingen"), ("2014", "renovatie"), ("2 weken", "vrijwilligerswerk"), ("VCT", "lokale partner")],
     "story_title": "Twee weken die het verschil maakten",
     "story": ["In januari 2014 reisde een groep Nederlandse vrijwilligers af naar Budaun. Twee weken lang werkten zij aan de scholen in Bilsi en Ghadia. Naast het opknappen van lokalen en meubilair was er nadrukkelijk aandacht voor de kwaliteit van het onderwijs zelf: vrijwilligers gaven de leraren feedback op hun manier van lesgeven, en de docenten konden Engelse lessen volgen. Dat is een vaardigheid die in India deuren opent naar vervolgonderwijs en werk.",
               "Ook de kinderen leerden iets nieuws. De vrijwilligers lieten zien waarom hygiëne telt, van handen wassen vóór het eten tot het schoonhouden van de klas. En er werd volop gelachen: de groep organiseerde een sportdag waar de hele school aan meedeed."],
     "extra_title": "Hoe het nu gaat",
     "extra": "Sinds de renovatie blijft Sampark betrokken bij Bilsi. Samen met onze lokale partner dragen we bij aan de salarissen van docenten, lesmateriaal, de schoolarts en fietsen voor geslaagden.",
     "facilities": [],
     "funds": DEFAULT_FUNDS,
     "moments": [("Januari 2014", "Twee weken renovatie door Nederlandse vrijwilligers, feedback voor leraren en Engelse les."),
                 ("Sportdag", "De hele school deed mee aan de sportdag van de vrijwilligers."),
                 ("Nu", "359 kinderen krijgen les, met steun voor docenten en lesmateriaal.")],
     "news": []},
    {"slug": "ghadia-school", "name": "Ghadia School", "tagline": "Een school midden op het platteland",
     "pupils": 482, "work": "Renovatie", "village": "Ghadia", "lat": 28.20, "lng": 79.06, "approx": True,
     "img": "proj_ghadia", "gallery": ["proj_ghadia", "proj_solar"],
     "intro": "In het dorp Ghadia, in de regio Budaun, krijgen dagelijks 482 kinderen les. Voor veel van hen is deze school de eerste in de familie die ze van binnen zien. Hun ouders werken op het land of in de bouw en hebben zelf nooit leren lezen. Hier begint dat verhaal opnieuw, bij hun kinderen.",
     "facts": [("482", "leerlingen"), ("2014", "renovatie"), ("Moestuin", "en speelplek"), ("Solar", "lampjes")],
     "story_title": "Vrijwilligers die de handen uit de mouwen staken",
     "story": ["Het jaar 2014 stond in het teken van renovatie. In januari reisde een groep Nederlandse vrijwilligers af naar India en werkte twee weken lang aan de scholen in Ghadia en Bilsi. Er werd gestuct en gesausd, meubilair opgeknapt en lokalen versierd. In de tuin verrezen moestuintjes en een speelplek.",
               "Maar het ging om meer dan verf en stenen. De vrijwilligers gaven leraren feedback op hun manier van lesgeven en verzorgden Engelse lessen. Ze lieten kinderen zien waarom handen wassen vóór het eten zo belangrijk is. En er was tijd voor lachen: de week werd afgesloten met een sportdag die niemand snel vergeet."],
     "extra_title": "Hoe het nu gaat",
     "extra": "Sinds de renovatie blijven wij betrokken bij Ghadia. Samen met onze lokale partner zorgen we voor salarissen van docenten, lesmateriaal, gezondheidszorg en fietsen voor geslaagden. Zo blijft de school niet alleen overeind, maar groeit hij mee met de kinderen die er zitten.",
     "facilities": ["Gerenoveerde lokalen", "Moestuintjes", "Speelplek"],
     "funds": ["Salarissen van docenten", "Lesmateriaal", "Gezondheidszorg", "Fietsen voor geslaagden"],
     "moments": [("Januari 2014", "Renovatie: stucwerk, meubilair, moestuintjes en een speelplek."),
                 ("Solarlampjes", "Leerlingen krijgen een lampje om thuis te kunnen studeren."),
                 ("Nu", "482 kinderen krijgen dagelijks les.")],
     "news": []},
]

DELHI = {"slug": "delhi-centre", "name": "Delhi Centre", "type": "centre", "region": "New Delhi",
         "lat": 28.6139, "lng": 77.2090, "approx": True, "img": "proj_computer",
         "meta": "73 studenten · 3 opleidingen", "url": "/ons-werk/#opleidingen",
         "courses": [("Computerspecialist", "/ons-werk/computerspecialist/"), ("Modinette", "/ons-werk/modinette/"),
                     ("Schoonheidsspecialiste", "/ons-werk/schoonheidsspecialiste/")]}

MAP_CSS = """
.sp-map{display:grid;grid-template-columns:300px 1fr;gap:24px;align-items:stretch}
.sp-map--compact{grid-template-columns:1fr}
.sp-map__list{display:flex;flex-direction:column;gap:18px}
.sp-map__group h4{font-family:"Patrick Hand",sans-serif;text-transform:uppercase;color:#BD5C38;font-size:18px;font-weight:400;margin:0 0 8px}
.sp-map__group ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.sp-map .sp-map__btn{width:100%;display:flex;justify-content:space-between;align-items:center;gap:12px;text-align:left;cursor:pointer;
  background:#F5EDE3!important;border:1px solid transparent!important;border-radius:14px!important;padding:12px 16px!important;color:#46211A!important;
  font-family:inherit!important;text-transform:none!important;box-shadow:none!important;transition:border-color .2s,background .2s}
.sp-map .sp-map__btn:hover,.sp-map .sp-map__btn:focus-visible,.sp-map .sp-map__btn[aria-pressed=true]{border-color:#BD5C38!important;background:#fff!important;outline:none}
.sp-map__btn strong{font-family:Spectral,serif;font-weight:500;font-size:19px;display:block;color:#46211A}
.sp-map__btn small{color:#7a5d52;font-size:14px;font-family:aptos,sans-serif}
.sp-map__btn i{width:12px;height:12px;border-radius:50%;flex:none;background:#963322}
.sp-map__btn[data-type=centre] i{background:#ED7404}
.sp-map__canvas{min-height:520px;border-radius:20px;overflow:hidden;background:#F5EDE3;z-index:0}
.sp-map__canvas .leaflet-tile-pane{filter:sepia(.35) saturate(.75) brightness(1.03)}
.sp-pin{background:none;border:0}
.sp-pin b{display:block;width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#963322;border:3px solid #fff;box-shadow:0 2px 6px rgba(70,33,26,.35)}
.sp-pin--centre b{background:#ED7404}
.sp-pin--current b{width:30px;height:30px;background:#BD5C38}
.sp-pin--region{cursor:pointer}
.sp-pin--region .dot{position:absolute;inset:0;border-radius:50%;background:#963322;border:3px solid #fff;box-shadow:0 2px 8px rgba(70,33,26,.4)}
.sp-pin--region.is-centre .dot{background:#ED7404}
.sp-pin--region .lbl{position:absolute;top:50%;transform:translateY(-50%);white-space:nowrap;padding:6px 12px;border-radius:999px;
  background:#963322;color:#F5EDE3;font-family:"Patrick Hand",sans-serif;text-transform:uppercase;font-size:16px;line-height:1.2;box-shadow:0 3px 10px rgba(70,33,26,.3)}
.sp-pin--region.is-centre .lbl{background:#ED7404;color:#46211A}
.sp-pin--region.side-right .lbl{left:26px}
.sp-pin--region.side-left .lbl{right:26px}
.sp-pin--region:focus-visible{outline:none}.sp-pin--region:focus-visible .lbl{outline:2px solid #46211A;outline-offset:2px}
.sp-pop{display:flex;flex-direction:column;gap:6px;font-family:inherit;color:#46211A}
.sp-pop img{width:100%;height:120px;object-fit:cover;border-radius:10px;display:block}
.sp-pop em{font-style:normal;font-family:"Patrick Hand",sans-serif;text-transform:uppercase;color:#BD5C38;font-size:15px}
.sp-pop strong{font-family:Spectral,serif;font-weight:500;font-size:20px;line-height:1.2}
.sp-pop small{color:#7a5d52}
.sp-pop a.sp-pop__btn{display:inline-block;margin-top:4px;background:#BD5C38;color:#F5EDE3!important;text-decoration:none;font-family:"Patrick Hand",sans-serif;text-transform:uppercase;padding:8px 16px;border-radius:4px;text-align:center}
.sp-pop ul{margin:0;padding-left:18px}
.leaflet-popup-content-wrapper{border-radius:16px}
.leaflet-popup-content{margin:12px;width:230px!important}
@media (max-width:900px){.sp-map{grid-template-columns:1fr}.sp-map__list{order:2}.sp-map__canvas{min-height:420px}}
"""

MAP_JS = r"""
(function(){
  function boot(el){
    if(!window.L){return setTimeout(function(){boot(el)},120);}
    if(el.dataset.ready){return;} el.dataset.ready='1';
    var pts=JSON.parse(el.getAttribute('data-points')), focus=el.getAttribute('data-focus');
    var canvas=el.querySelector('.sp-map__canvas');
    var map=L.map(canvas,{scrollWheelZoom:false,minZoom:4,maxZoom:+(el.getAttribute('data-maxzoom')||12),attributionControl:true});
    L.tileLayer(el.getAttribute('data-tiles'),{maxZoom:+(el.getAttribute('data-maxzoom')||12),attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
    function pin(cls){return L.divIcon({className:'sp-pin '+cls,html:'<b></b>',iconSize:[24,24],iconAnchor:[6,22],popupAnchor:[6,-20]});}
    function card(p){
      var h='<div class="sp-pop">'+(p.img?'<img src="'+p.img+'" alt="">':'')+'<em>'+p.meta+'</em><strong>'+p.name+'</strong>';
      if(p.approx){h+='<small>Locatie bij benadering</small>';}
      if(p.courses){h+='<ul>'+p.courses.map(function(c){return '<li><a href="'+c[1]+'">'+c[0]+'</a></li>'}).join('')+'</ul>';}
      return h+'<a class="sp-pop__btn" href="'+p.url+'">'+(p.type==='school'?'Bekijk de school':'Bekijk de opleidingen')+'</a></div>';
    }
    var points=L.layerGroup(), regions=L.layerGroup(), groups={};
    pts.forEach(function(p){
      var cls=p.slug===focus?'sp-pin--current':(p.type==='centre'?'sp-pin--centre':'');
      p.marker=L.marker([p.lat,p.lng],{icon:pin(cls),title:p.name,alt:p.name,keyboard:true}).bindPopup(card(p)).addTo(points);
      (groups[p.region]=groups[p.region]||[]).push(p);
    });
    var meanLng=pts.reduce(function(a,p){return a+p.lng},0)/pts.length;
    Object.keys(groups).forEach(function(name){
      var g=groups[name], lat=0, lng=0; g.forEach(function(p){lat+=p.lat;lng+=p.lng;});
      var side=(lng/g.length)<meanLng?' side-left':' side-right';
      var label=g[0].type==='centre'?name+' · 3 opleidingen':name+' · '+g.length+' scholen';
      L.marker([lat/g.length,lng/g.length],{icon:L.divIcon({className:'sp-pin sp-pin--region'+side+(g[0].type==='centre'?' is-centre':''),html:'<span class="dot"></span><span class="lbl">'+label+'</span>',iconSize:[18,18],iconAnchor:[9,9]}),keyboard:true,title:label})
        .on('click',function(){ if(g.length>1){map.flyToBounds(L.latLngBounds(g.map(function(p){return [p.lat,p.lng]})).pad(.6),{maxZoom:10});} else {map.flyTo([g[0].lat,g[0].lng],9); setTimeout(function(){g[0].marker.openPopup()},900);} })
        .addTo(regions);
    });
    function sync(){ if(map.getZoom()>=8){map.removeLayer(regions);points.addTo(map);} else {map.removeLayer(points);regions.addTo(map);} }
    map.on('zoomend',sync);
    if(focus){ var f=pts.filter(function(p){return p.slug===focus})[0]; map.setView([f.lat,f.lng],9); }
    else { map.fitBounds([[8,68.5],[35.5,97.5]]); }
    sync();
    el.querySelectorAll('[data-goto]').forEach(function(b){
      b.addEventListener('click',function(){
        var p=pts.filter(function(x){return x.slug===b.getAttribute('data-goto')})[0];
        el.querySelectorAll('[data-goto]').forEach(function(o){o.setAttribute('aria-pressed','false')}); b.setAttribute('aria-pressed','true');
        map.flyTo([p.lat,p.lng],p.type==='centre'?11:10);
        map.once('moveend',function(){ p.marker.openPopup(); });
      });
    });
  }
  function all(){document.querySelectorAll('.sp-map').forEach(boot);}
  if(document.readyState!=='loading'){all();} else {document.addEventListener('DOMContentLoaded',all);}
  window.addEventListener('elementor/frontend/init',all);
})();
"""


def map_points():
    pts = [{"slug": s["slug"], "name": s["name"], "type": "school", "region": "Budaun", "lat": s["lat"],
            "lng": s["lng"], "approx": s["approx"], "img": f"{{{{img:{s['img']}}}}}",
            "meta": f"{s['pupils']} leerlingen · {s['work']}", "url": f"/ons-werk/{s['slug']}/"} for s in SCHOOLS]
    d = dict(DELHI)
    d["img"] = f"{{{{img:{d['img']}}}}}"
    return pts + [d]


def india_map(focus=None, with_list=True, height=560):
    import html as _h
    pts = map_points()
    lst = ""
    if with_list:
        rows = "".join(f'<li><button type="button" class="sp-map__btn" data-type="school" data-goto="{p["slug"]}" aria-pressed="false">'
                       f'<span><strong>{p["name"]}</strong><small>{p["meta"]}</small></span><i></i></button></li>'
                       for p in pts if p["type"] == "school")
        lst = (f'<div class="sp-map__list"><div class="sp-map__group"><h4>Budaun · Uttar Pradesh</h4><ul>{rows}</ul></div>'
               f'<div class="sp-map__group"><h4>New Delhi</h4><ul><li><button type="button" class="sp-map__btn" data-type="centre" '
               f'data-goto="delhi-centre" aria-pressed="false"><span><strong>Delhi Centre</strong><small>{DELHI["meta"]}</small></span><i></i></button></li></ul></div></div>')
    data = _h.escape(json.dumps(pts, ensure_ascii=False), quote=True)
    code = (f"<style>{LEAFLET_CSS}{MAP_CSS}</style>"
            f'<div class="sp-map{"" if with_list else " sp-map--compact"}" data-points="{data}" data-focus="{focus or ""}" '
            f'data-maxzoom="12" data-tiles="https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png">{lst}'
            f'<div class="sp-map__canvas" style="min-height:{height}px" role="region" aria-label="Kaart met de scholen van Sampark in India"></div></div>'
            f'<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>'
            f"<script>{MAP_JS}</script>")
    return html(code, title="KAART · JetEngine Map Listing (Leaflet/OSM) · projecten met Map-veld · clustering aan")


def fa_icon(value, color="accent", px=36):
    return widget("icon", {"selected_icon": {"value": value, "library": "fa-solid"}, "size": size(px),
                           "align": "left", "__globals__": {"primary_color": g_color(color)}})


def project_card(img, meta, title, tagline, link):
    return card(image(img, height=220, radius=14), eyebrow(meta), heading(title, "h3", size_px=26),
                text(f"<p>{tagline}</p>"), button("Bekijk dit project", link, style="outline", icon=True),
                title=f"Kaart · {title}", pad=20)


page("ons-werk", "Ons werk",
     page_hero("Ons werk", "Onderwijs is de voorwaarde voor een betere toekomst. Daarom bouwen we aan scholen op het platteland en opleidingen in de stad.",
               "hero_onswerk", eye="Scholen, opleidingen en initiatieven"),
     section(
         container(
             container(eyebrow("Onze aanpak"), heading("Samen met lokale partners", "h2"),
                       text("<p>We werken samen met de Vincentian Charitable Trust uit New Delhi. Zij zorgen ervoor dat de scholen elke dag open zijn. Wij betalen mee aan wat daarvoor nodig is: van docentsalarissen tot fietsen voor geslaagden.</p><p>Doordat het bestuur onbezoldigd werkt, gaat 95% van elke gift direct naar hulp.</p>"),
                       width=55, gap_px=14),
             container(stat("icon_rugtas", 1577, "Leerlingen", width=48), stat("icon_computer", 73, "Studenten in Delhi", width=48),
                       title="Cijfers", direction="row", width=40, gap_px=16, mobile_column=False),
             direction="row", gap_px=48, align="center"),
         title="Aanpak"),
     section(
         section_head("Waar we werken", "Klik op een school",
                      "Vier scholen in het district Budaun en een opleidingscentrum in New Delhi. Klik op een regio om in te zoomen, en op een school voor meer informatie."),
         india_map(),
         title="Kaart", pad=(40, 24)),
     section(
         section_head("Scholen in Budaun", "Vier scholen op het platteland",
                      "Rond Budaun maken we vier scholen mogelijk. Door te bouwen, te renoveren en te blijven investeren groeit elke school mee met de kinderen."),
         listing("projecten · projecttype=school · sorteer titel @@projectkaart,q_scholen,4",
                 project_card("proj_khukdi", "407 leerlingen · Nieuwbouw", "Khukdi School", "Van vijf lokalen naar vijftien.", "/ons-werk/khukdi-school/"),
                 project_card("proj_kundanpur", "329 leerlingen · Renovatie", "Kundanpur School", "Waar het begint.", "/ons-werk/kundanpur-school/"),
                 project_card("proj_bilsi", "359 leerlingen · Renovatie", "Bilsi School", "Leren begint bij de leraar.", "/ons-werk/bilsi-school/"),
                 project_card("proj_ghadia", "482 leerlingen · Renovatie", "Ghadia School", "Een school midden op het platteland.", "/ons-werk/ghadia-school/"),
                 cols=4),
         title="Scholen", extra={"_element_id": "scholen"}),
     section(
         section_head("Opleidingen in New Delhi", "Een vak leren in de stad",
                      "Veel jongeren trekken van het platteland naar de stad en belanden zonder werk in de sloppenwijken. Met gerichte opleidingen geven we ze een eerlijke kans op een baan."),
         listing("projecten · projecttype=opleiding @@projectkaart,q_opleidingen,3",
                 project_card("proj_computer", "20 studenten", "Computerspecialist", "Digitale vaardigheden voor een kantoorbaan.", "/ons-werk/computerspecialist/"),
                 project_card("proj_modinette", "29 studenten", "Modinette", "Kleding maken en een eigen inkomen.", "/ons-werk/modinette/"),
                 project_card("proj_beauty", "24 studenten", "Schoonheidsspecialiste", "Een vak met vraag in de stad.", "/ons-werk/schoonheidsspecialiste/")),
         title="Opleidingen", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50),
         divider_bottom=("waves", "#FFFFFF", 50), extra={"_element_id": "opleidingen"}),
     section(
         section_head("Initiatieven", "Kleine projecten, groot verschil"),
         listing("projecten · projecttype=initiatief @@projectkaart,q_initiatieven,4",
                 project_card("proj_fietsen", "Elk jaar", "Fietsen voor geslaagden", "Zodat het vervolgonderwijs bereikbaar is.", "/ons-werk/fietsen/"),
                 project_card("proj_zon", "Khukdi School", "Zonnepanelen", "Een school die haar eigen energie opwekt.", "/ons-werk/zonnepanelen/"),
                 project_card("proj_solar", "Ghadia", "Solarlampjes", "Licht om thuis te kunnen studeren.", "/ons-werk/solarlampjes/"),
                 project_card("proj_accrete", "Partner", "Stichting Accrete", "Leerlingen in Nederland en India verbonden.", "/ons-werk/stichting-accrete/"),
                 cols=4),
         title="Initiatieven", extra={"_element_id": "initiatieven"}),
     cta_band("Bouw mee aan een school", "Voor € 60 per jaar betaal je het lesgeld en de schoolspullen van één kind.",
              [button("Sponsor een kind", "/product/sponsor-een-kind/", style="light"),
               button("Doneer eenmalig", "/steun-ons/doneren/", style="outline-light")], eye="Steun ons"),
     seo=("Ons werk | Scholen en opleidingen in India | Stichting Sampark",
          "Vier scholen rond Budaun, drie beroepsopleidingen in New Delhi en initiatieven als fietsen en zonnepanelen."))

# De schoolpagina's zijn geen losse pagina's meer: /ons-werk/{school}/ is de projectsingle met de
# Theme Builder-template "Single · Project" (zie onderaan).

# EVENEMENTEN -------------------------------------------------------------
page("evenementen", "Evenementen",
     page_hero("Evenementen", "Rijd mee in de rally, sla een balletje voor het goede doel of bestel je wijn bij ons. Elke deelname brengt een kind dichter bij de schoolbank.",
               "hero_events", eye="Doe mee"),
     section(
         section_head("Binnenkort", "Schrijf je in"),
         listing("evenementen · status IN (aangekondigd, open, vol) · sorteer datum_start ASC @@eventkaart,q_events_binnenkort,3",
                 event_card("padel", "Inschrijving open"), event_card("rally", "Aangekondigd"),
                 event_card("golf", "Aangekondigd")),
         title="Binnenkort"),
     section(
         section_head("Het hele jaar", "Altijd mogelijk"),
         listing("evenementen · status=doorlopend @@eventkaart,q_events_doorlopend,2",event_card("wijn", "Het hele jaar"),
                 event_card("reis", "Op aanvraag"), cols=2),
         title="Doorlopend", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50),
         divider_bottom=("waves", "#FFFFFF", 50)),
     section(
         section_head("Terugblikken", "Zo was het vorig jaar"),
         news_cards("q_nieuws_events"),
         title="Terugblikken (nieuws · categorie=evenementen)"),
     cta_band("Zichtbaar als sponsor bij een evenement?", "Met een Sona- of Chandee-pakket doe je mee én staat je bedrijf bij het evenement vermeld.",
              [button("Bekijk de sponsorpakketten", "/steun-ons/bedrijven/", style="light")], eye="Voor bedrijven"),
     seo=("Evenementen | Sampark Rally, Golftoernooi, Padel en Wijnactie",
          "Doe mee aan de evenementen van Stichting Sampark. De opbrengst gaat naar onderwijs in India."))

# STEUN ONS ---------------------------------------------------------------


def option_card(eye, title, body, cta, link, img):
    return card(image(img, height=200, radius=14), eyebrow(eye), heading(title, "h3", size_px=28),
                text(f"<p>{body}</p>"), button(cta, link, full=True), title=f"Kaart · {title}", pad=20)


page("steun-ons", "Steun ons",
     page_hero("Steun ons", "Of je nu € 10 geeft, een kind een jaar naar school laat gaan of als bedrijf structureel bijdraagt: 95% van je steun gaat direct naar onderwijs in India.",
               "hero_steun", eye="Jouw bijdrage telt"),
     section(
         listing("statisch (4 vaste keuzes)",
                 option_card("Eenmalig", "Doneer", "Kies zelf je bedrag. Je ontvangt direct een bevestiging per mail.", "Doneer nu", "/steun-ons/doneren/", "steun_doneer"),
                 option_card("€ 60 per jaar", "Sponsor een kind", "Een jaar lesgeld en schoolspullen voor één kind.", "Sponsor een kind", "/product/sponsor-een-kind/", "steun_kind"),
                 option_card("Vanaf € 500 per jaar", "Voor bedrijven", "Sponsorpakketten met naamsvermelding en evenementen.", "Bekijk de pakketten", "/steun-ons/bedrijven/", "steun_bedrijf"),
                 option_card("Het hele jaar", "Doe mee", "Rally, golf, padel of de wijnactie.", "Bekijk de evenementen", "/evenementen/", "steun_event"),
                 cols=4),
         title="Keuzes"),
     section(
         container(
             container(eyebrow("ANBI"), heading("Je gift is aftrekbaar", "h2"),
                       text("<p>Stichting Sampark is door de Belastingdienst erkend als Algemeen Nut Beogende Instelling. Giften kun je aftrekken van de inkomsten- of vennootschapsbelasting. Ons RSIN is 818925887.</p>"),
                       button("Bekijk onze ANBI-gegevens", "/over-ons/anbi/", style="outline", icon=True),
                       width=50, gap_px=14),
             container(accordion([
                 ("Waar gaat mijn geld naartoe?", "<p>Naar salarissen van docenten, lesmateriaal, de schoolarts, fietsen voor geslaagden en de vaste lasten van de scholen en opleidingen.</p>"),
                 ("Hoeveel gaat er naar de organisatie?", "<p>Vrijwel niets. Het bestuur werkt onbezoldigd en Venture Group draagt de organisatiekosten. 95% gaat direct naar hulp.</p>"),
                 ("Kan ik ook per bank overmaken?", "<p>Ja, op NL25 ABNA 0578 9231 73 ten name van Stichting Sampark in Genemuiden.</p>"),
                 ("Krijg ik een bevestiging?", "<p>Ja, na je betaling ontvang je direct een bevestiging per mail. Die kun je bewaren voor je belastingaangifte.</p>"),
             ]), width=46),
             direction="row", gap_px=48),
         title="ANBI en vragen", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50)),
     seo=("Steun ons | Doneer of sponsor een kind | Stichting Sampark",
          "Doneer, sponsor een kind voor € 60 per jaar of word bedrijfssponsor. Giften aan Sampark zijn aftrekbaar (ANBI)."))

page("doneren", "Doneren",
     page_hero("Doneer", "Met je gift betaal je mee aan docenten, lesmateriaal en fietsen voor kinderen in India.", "hero_doneer", eye="Eenmalige gift"),
     section(
         container(
             container(eyebrow("Kies je bedrag"), heading("Wat jouw gift betekent", "h2"),
                       icon_list(["€ 10 · lesmateriaal voor een klas", "€ 25 · een schooluniform", "€ 60 · een jaar onderwijs voor één kind", "€ 100 · bijdrage aan een fiets voor een geslaagde"], icon_value="fas fa-heart"),
                       text("<p><em>Bedragen ter illustratie, af te stemmen met het bestuur.</em></p>", size_px=14),
                       width=45, gap_px=14),
             card(eyebrow("Doneer nu"), heading("Kies je bedrag", "h3", size_px=30),
                  text("<p>Kies een bedrag of vul zelf een bedrag in. Je rekent daarna veilig af met iDEAL of op factuur.</p>"),
                  widget("shortcode", {"shortcode": '[super_form id="{{form:donatie_pagina}}"]'},
                         title="Super Forms · Donatieformulier (doneerpagina, vast product Eenmalige donatie)"),
                  title="Donatieblok", bg="#FFFFFF", width=50),
             direction="row", gap_px=48, align="flex-start"),
         title="Doneren"),
     parent="steun-ons",
     seo=("Doneer aan Stichting Sampark | Onderwijs voor kinderen in India",
          "Doe een eenmalige gift. 95% gaat direct naar onderwijs in India en je gift is aftrekbaar."))

page("bedrijven", "Voor bedrijven",
     page_hero("Sponsor als bedrijf", "Een hecht zakelijk netwerk dat structureel bijdraagt aan onderwijs in India. Met naamsvermelding, evenementen en materiaal voor je MVO-verhaal.",
               "hero_bedrijven", eye="Voor bedrijven"),
     section(
         container(
             container(eyebrow("Waarom sponsoren"), heading("Maatschappelijk ondernemen met een gezicht", "h2"),
                       icon_list(["Naamsvermelding op onze website en bij evenementen", "Deelname aan de Sampark Rally en het golftoernooi",
                                  "Materiaal voor je eigen MVO-communicatie", "Een netwerk van ondernemers uit de regio"]), width=55, gap_px=14),
             card(eyebrow("Contact"), heading("Lianne Molhoek", "h3", size_px=26),
                  text("<p>Secretaris van het bestuur<br>038 385 50 00<br>info@sampark.nl</p>"),
                  button("Neem contact op", "/contact/", style="outline", icon=True), width=40, title="Contactpersoon"),
             direction="row", gap_px=48, align="center"),
         title="Waarom"),
     section(
         section_head("Sponsorpakketten", "Kies het pakket dat bij je past", align="center"),
         listing("WC Product Query · product_cat=sponsorpakket · sorteer prijs DESC @@pakketkaart,q_pakketten,3",
                 card(eyebrow("€ 2.500 per jaar"), heading("Sona (Goud)", "h3", size_px=28),
                      icon_list(["Alles uit Peetal", "Deelname golftoernooi én Sampark Rally", "Naamsvermelding bij het gekozen evenement"]),
                      button("Kies Sona", "/product/sona-goud/", full=True), title="Kaart · Sona", bg="e64974d"),
                 card(eyebrow("€ 1.750 per jaar"), heading("Chandee (Zilver)", "h3", size_px=28),
                      icon_list(["Alles uit Peetal", "Deelname golftoernooi óf Sampark Rally", "Naamsvermelding bij dat evenement"]),
                      button("Kies Chandee", "/product/chandee-zilver/", full=True), title="Kaart · Chandee", bg="e64974d"),
                 card(eyebrow("€ 500 per jaar"), heading("Peetal (Brons)", "h3", size_px=28),
                      icon_list(["Naamsvermelding op onze website", "Klikbare Sampark-banner voor je eigen site", "Sampark-uitingen voor je MVO"]),
                      button("Kies Peetal", "/product/peetal-brons/", full=True), title="Kaart · Peetal", bg="e64974d")),
         title="Pakketten", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50), divider_bottom=("waves", "#FFFFFF", 50)),
     section(
         section_head("Onze sponsors", "Zij gingen je voor", align="center"),
         logo_wall(["logo_venture", "logo_groothuis", "logo_schieven", "logo_w4y", "logo_venttri",
                    "logo_rijk", "logo_arcus", "logo_kvs", "logo_pleijsier", "logo_positie1"], bg="#F5EDE3"),
         title="Sponsors"),
     parent="steun-ons",
     seo=("Sponsor worden als bedrijf | Stichting Sampark",
          "Sponsorpakketten vanaf € 500 per jaar met naamsvermelding, deelname aan evenementen en MVO-materiaal."))

# OVER ONS ----------------------------------------------------------------
BOARD = [("Irma van Dalfsen", "Voorzitter", "board_irma"), ("Lianne Molhoek", "Secretaris", "board_lianne"),
         ("Pieter Veuger", "Penningmeester", "board_pieter"), ("Arjen Hoekman", "Projectcommissie", "board_arjen"),
         ("Henk Eilander", "Fondsenwerving", "board_henk"), ("Richard Nijhof", "Fondsenwerving", "board_richard"),
         ("Eric Haasjes", "Fondsenwerving", "board_eric"), ("Margreet van Dalfsen", "Vrijwilligers", "board_margreet")]

TIMELINE = [("2007", "Oprichting", "Venture Group richt Stichting Sampark op om iets terug te doen voor India."),
            ("2014", "Renovaties", "Vrijwilligers knappen in twee weken de scholen in Bilsi en Ghadia op."),
            ("[jaar]", "Nieuwbouw Khukdi", "Een nieuwe school met vijftien lokalen. Jaartal nog te bevestigen."),
            ("2025", "Nieuw bestuur", "Eric Haasjes en Richard Nijhof versterken de fondsenwerving.")]

page("over-ons", "Over ons",
     page_hero("Over ons", "Sinds 2007 zet Stichting Sampark zich in voor kinderen en jongvolwassenen in India. Sampark betekent verbinding.", "hero_over", eye="Wie we zijn"),
     section(
         container(
             container(eyebrow("Ons verhaal"), heading("Educatie is een voorwaarde", "h2"),
                       text("<p>De stichting ontstond doordat Venture Group al jaren actief is in India en iets terug wilde doen voor de lokale bevolking. Vanuit de overtuiging dat onderwijs de basis is voor een betere toekomst, richten we ons daar volledig op.</p>"),
                       width=55, gap_px=14),
             container(image("over_verhaal", height=380), width=40),
             direction="row", gap_px=48, align="center"),
         title="Verhaal"),
     section(
         section_head("Bestuur", "De mensen achter Sampark", "Het bestuur werkt onbezoldigd.", align="center"),
         container(*[container(image(k, height=200, radius=999, fit=True), heading(n, "h4", align="center", size_px=22),
                               eyebrow(r, align="center"), title=f"Bestuurslid · {n}", align="center", gap_px=6, width=22,
                               extra={"width_mobile": size(46, "%"), "width_tablet": size(30, "%")})
                     for n, r, k in BOARD],
                   title="LISTING · Options › bestuur (repeater)", direction="row", wrap=True, justify="center",
                   gap_px=32, mobile_column=False),
         title="Bestuur", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50), divider_bottom=("waves", "#FFFFFF", 50)),
     section(
         section_head("Partners", "Samen met India"),
         text("<p>We werken samen met de Vincentian Charitable Trust (VCT) uit New Delhi en het management van Sampark India. Zij zijn dagelijks bij de scholen en opleidingen betrokken.</p>"),
         title="Partners"),
     section(
         section_head("Tijdlijn", "Bijna twintig jaar Sampark"),
         container(*[card(heading(y, "h3", color="primary", size_px=40), heading(t, "h4", size_px=22), text(f"<p>{b}</p>"),
                           title=f"Tijdlijn · {y}", width=23) for y, t, b in TIMELINE],
                   title="LISTING · Options › tijdlijn (repeater)", direction="row", gap_px=24, wrap=True),
         title="Tijdlijn"),
     cta_band("Transparant over elke euro", "Lees onze jaarverslagen, het beleidsplan en alle gegevens die we als ANBI publiceren.",
              [button("Naar ANBI & financiën", "/over-ons/anbi/", style="light")]),
     seo=("Over Stichting Sampark | Sinds 2007 onderwijs in India", "Wie we zijn, ons bestuur, onze partners in India en onze geschiedenis."))

page("anbi", "ANBI & financiën",
     page_hero("ANBI & financiën", "Alle gegevens die we als Algemeen Nut Beogende Instelling publiceren, op één plek.", "hero_anbi", eye="Transparantie"),
     section(
         container(
             card(heading("Gegevens", "h3", size_px=28),
                  html("<dl class='sp-dl'><dt>Naam</dt><dd>Stichting Sampark</dd><dt>RSIN</dt><dd>818925887</dd><dt>KvK</dt><dd>08169359</dd><dt>Adres</dt><dd>Schering 31-33, 8281 JW Genemuiden</dd><dt>Telefoon</dt><dd>038 385 50 00</dd><dt>E-mail</dt><dd>info@sampark.nl</dd><dt>IBAN</dt><dd>NL25 ABNA 0578 9231 73</dd></dl>", title="Dynamic tags · Options › registratie/contact"),
                  title="Gegevens", width=40),
             container(
                 heading("Doelstelling", "h3", size_px=28),
                 text("<p>Het ondersteunen van projecten en initiatieven in India die zich richten op het bestrijden van analfabetisme en armoede, door het aanbieden van scholing: basisonderwijs, voortgezet onderwijs en beroepsopleidingen.</p>"),
                 heading("Beloningsbeleid", "h3", size_px=28),
                 text("<p>Bestuursleden ontvangen geen beloning. Venture Group stelt medewerkers en middelen beschikbaar.</p>"),
                 heading("Beleidsplan en activiteiten", "h3", size_px=28),
                 text("<p>[Tekst uit Options › anbi_teksten: beleidsplan en verslag van de activiteiten.]</p>"),
                 width=55, gap_px=12),
             direction="row", gap_px=48),
         title="ANBI-gegevens"),
     section(
         section_head("Documenten", "Jaarverslagen en jaarrekeningen"),
         listing("Options › anbi_documenten (repeater) · sorteer jaar DESC",
                 card(heading("2024", "h3", color="primary", size_px=36), text("<p>Jaarrekening</p>"), button("Download (pdf)", "#", style="outline"), title="Document · 2024"),
                 card(heading("2023", "h3", color="primary", size_px=36), text("<p>Jaarrekening</p>"), button("Download (pdf)", "#", style="outline"), title="Document · 2023"),
                 card(heading("2022", "h3", color="primary", size_px=36), text("<p>Jaarrekening</p>"), button("Download (pdf)", "#", style="outline"), title="Document · 2022"),
                 cols=3),
         title="Documenten", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50)),
     parent="over-ons",
     seo=("ANBI-gegevens en jaarverslagen | Stichting Sampark", "RSIN, bestuur, beloningsbeleid, beleidsplan en jaarrekeningen van Stichting Sampark."))

page("contact", "Contact",
     page_hero("Contact", "Vragen over doneren, sponsoren of een evenement? We helpen je graag.", "hero_contact", eye="Neem contact op"),
     section(
         container(
             container(heading("Stichting Sampark", "h3", size_px=28),
                       text("<p>Schering 31-33<br>8281 JW Genemuiden</p><p>038 385 50 00<br>info@sampark.nl</p><p>Telefonisch bereikbaar op kantoordagen tussen 9.00 en 17.00 uur.</p>"),
                       text("<p>KvK 08169359 · RSIN 818925887<br>IBAN NL25 ABNA 0578 9231 73</p>", size_px=15),
                       width=40, gap_px=12),
             card(heading("Stuur ons een bericht", "h3", size_px=28),
                  text("<p>[Elementor Pro Form-widget: naam, e-mail, onderwerp (algemeen / doneren / sponsoring / evenement), bericht, privacy-akkoord. Actie: e-mail naar info@sampark.nl + bevestiging aan afzender.]</p>"),
                  title="Formulier (Elementor Pro Form)", bg="e64974d", width=55),
             direction="row", gap_px=48),
         title="Contact"),
     seo=("Contact | Stichting Sampark", "Neem contact op met Stichting Sampark in Genemuiden."))


# WINKELWAGEN, AFREKENEN, MIJN ACCOUNT -------------------------------------------
# Zoals op staging: winkelwagen en afrekenen zonder site-menu (Elementor Canvas), met een eigen smalle kop en voet,
# de Elementor Pro-widgets en de Pagina-CSS van staging (elementor/css/). Afrekenen blijft de klassieke checkout,
# nodig voor het sponsorpakket-snippet.

def shop_header(back_label, back_url):
    logo = widget("image", {"image": {"url": "{{img:logo_sampark}}", "id": "{{imgid:logo_sampark}}", "alt": "Stichting Sampark"},
                            "width": size(150), "width_mobile": size(120), "image_border_radius": dims(0),
                            "link_to": "custom", "link": {"url": "/"}}, title="Logo (naar home)")
    return container(
        container(logo, button(back_label, back_url, style="outline"),
                  title="Kop inhoud", boxed=True, direction="row", justify="space-between", align="center",
                  mobile_column=False, pad=dims(18, 24), pad_mobile=dims(14, 20)),
        title="Smalle kop (zonder menu)", bg_global="658acb6", tag="header")


def shop_footer():
    return container(
        container(text("<p>© Stichting Sampark · ANBI-erkend · Veilig betalen met iDEAL of op factuur</p>",
                       color="658acb6", size_px=14),
                  title="Voet inhoud", boxed=True, pad=dims(20, 24)),
        title="Smalle voet", bg_global="accent", tag="footer")


def shop_main(*kids):
    return container(*kids, title="Inhoud", boxed=True, pad=dims(56, 24, 80, 24), pad_mobile=dims(32, 16, 56, 16), gap_px=24)


# Teksten van de Elementor Pro-widgets in het Nederlands (Elementor Pro heeft geen Nederlands taalpakket)
CART_TEXTS = {"update_cart_button_text": "Winkelwagen bijwerken", "apply_coupon_button_text": "Toepassen",
              "totals_section_title": "Totaal", "update_shipping_button_text": "Bijwerken",
              "checkout_button_text": "Doorgaan naar afrekenen"}


def checkout_fields(prefix, labels, placeholders=None):
    placeholders = placeholders or {}
    return [{"_id": _id(k), "field_key": f"{prefix}_{k}", "field_label": l, "label": l,
             "placeholder": placeholders.get(k, ""), "repeater_state": "locale" if k in ADDRESS_KEYS else ""}
            for k, l in labels]


ADDRESS_KEYS = {"country", "address_1", "postcode", "city", "state"}
ADDRESS = [("first_name", "Voornaam"), ("last_name", "Achternaam"), ("company", "Bedrijfsnaam"),
           ("country", "Land/regio"), ("address_1", "Straat en huisnummer"), ("postcode", "Postcode"),
           ("city", "Plaats"), ("state", "Provincie")]
CHECKOUT_TEXTS = {
    "billing_details_section_title": "Factuurgegevens", "shipping_details_section_title": "Verzenden naar een ander adres?",
    "additional_information_section_title": "Extra informatie", "order_summary_section_title": "Jouw bestelling",
    "returning_customer_section_title": "Heb je al een account?", "returning_customer_link_text": "Log hier in",
    "create_account_text": "Account aanmaken?", "coupon_section_title_text": "Heb je een kortingscode?",
    "coupon_section_title_link_text": "Klik hier om je code in te voeren",
    "terms_conditions_message_text": "Ik ga akkoord met de", "terms_conditions_link_text": "algemene voorwaarden",
    "billing_details_form_fields": checkout_fields("billing", ADDRESS + [("phone", "Telefoon"), ("email", "E-mailadres")],
                                                   {"address_1": "Straatnaam en huisnummer"}),
    "shipping_details_form_fields": checkout_fields("shipping", ADDRESS, {"address_1": "Straatnaam en huisnummer"}),
    "additional_information_form_fields": [{"_id": _id("notes"), "field_key": "order_comments",
                                            "field_label": "Bestelnotities (optioneel)", "label": "Bestelnotities (optioneel)",
                                            "placeholder": "Bijvoorbeeld een voorkeur voor de bezorging.", "repeater_state": ""}],
}
ACCOUNT_TABS = [("dashboard", "Overzicht"), ("orders", "Bestellingen"), ("downloads", "Downloads"),
                ("edit-address", "Adressen"), ("edit-account", "Accountgegevens"), ("customer-logout", "Uitloggen")]


page("winkelwagen", "Winkelwagen",
     shop_header("Verder kijken", "/steun-ons/"),
     shop_main(widget("woocommerce-cart", {"cart_layout": "two-column", "sticky_right_column": "yes", **CART_TEXTS},
                      title="Winkelwagen (Elementor Pro)")),
     shop_footer(),
     template="elementor_canvas", css="winkelwagen",
     seo=("Winkelwagen | Stichting Sampark", ""))

page("afrekenen", "Afrekenen",
     shop_header("Terug naar winkelwagen", "/winkelwagen/"),
     shop_main(widget("woocommerce-checkout-page", {"checkout_layout": "two-column", "sticky_right_column": "yes", **CHECKOUT_TEXTS},
                      title="Afrekenen (Elementor Pro, klassieke checkout)")),
     shop_footer(),
     template="elementor_canvas", css="afrekenen",
     seo=("Afrekenen | Stichting Sampark", ""))

page("mijn-account", "Mijn account",
     container(
         container(eyebrow("Voor donateurs en sponsors"), heading("Mijn account", "h1", color="primary", typo="accent", size_px=52),
                   text("<p>Bekijk je bestellingen, inschrijvingen en gegevens.</p>", size_px=18),
                   title="Kop", boxed=True, gap_px=10),
         title="Paginakop", bg_global="658acb6", pad=dims(72, 24, 88, 24), pad_mobile=dims(48, 20, 64, 20), tag="header",
         divider_bottom=("waves", "#FFFFFF", 50)),
     shop_main(widget("woocommerce-my-account", {"tabs": [{"_id": _id(k), "field_key": k, "field_label": l, "tab_name": l}
                                                       for k, l in ACCOUNT_TABS]},
                      title="Mijn account (Elementor Pro)")),
     css="mijn-account",
     seo=("Mijn account | Stichting Sampark", ""))


# SITEMAP --------------------------------------------------------------------------
def sitemap_item(title, kind, source, hierarchical=False):
    item = {"_id": _id(source), "sitemap_type_selector": kind, "sitemap_title": title,
            "sitemap_orderby_post_type": "menu_order" if kind == "post_type" else "name", "sitemap_order": "asc"}
    item["sitemap_source_post_type" if kind == "post_type" else "sitemap_source_taxonomy"] = source
    if hierarchical:
        item["sitemap_hierarchical"] = "yes"
    if source == "post":
        item.update({"sitemap_orderby_post_type": "post_date", "sitemap_order": "desc"})
    return item


page("sitemap", "Sitemap",
     container(
         container(eyebrow("Overzicht"), heading("Sitemap", "h1", color="primary", typo="accent", size_px=52),
                   text("<p>Alle pagina's, projecten, evenementen en berichten op één plek.</p>", size_px=18),
                   title="Kop", boxed=True, gap_px=10),
         title="Paginakop", bg_global="658acb6", pad=dims(72, 24, 88, 24), pad_mobile=dims(48, 20, 64, 20), tag="header",
         divider_bottom=("waves", "#FFFFFF", 50)),
     section(widget("sitemap", {
         "sitemap_items": [sitemap_item("Pagina's", "post_type", "page", hierarchical=True) | {"sitemap_orderby_post_type": "post_title"},
                           sitemap_item("Ons werk", "post_type", "projecten"),
                           sitemap_item("Evenementen", "post_type", "evenementen"),
                           sitemap_item("Doneren en sponsoren", "post_type", "product"),
                           sitemap_item("Nieuwscategorieën", "taxonomy", "category"),
                           sitemap_item("Nieuws", "post_type", "post")],
         "sitemap_columns": "3", "sitemap_columns_tablet": "2", "sitemap_columns_mobile": "1",
         "sitemap_exclude": ["current_post", "manual_selection"],
         "sitemap_exclude_ids": "{{pageids:winkelwagen,afrekenen,mijn-account,shop,bedankt,betaling-mislukt}}",
         "sitemap_title_tag": "h3", "sitemap_section_padding": dims(0, 0, 24, 0),
         "sitemap_title_typography_typography": "custom", "sitemap_title_typography_font_size": size(26),
         "__globals__": {"sitemap_title_color": g_color("primary"), "sitemap_title_typography_typography": g_type("primary"),
                         "sitemap_list_item_color": g_color("text")}}, title="Sitemap (Elementor Pro)"),
             title="Sitemap", pad=(48, 24)),
     seo=("Sitemap | Stichting Sampark", "Overzicht van alle pagina's, projecten, evenementen en berichten van Stichting Sampark."))


# ---------------------------------------------------------------- JetEngine listing items
# Ontwerp van de kaarten als JetEngine-listing (Elementor). jetengine-setup.php maakt de listings
# aan en zet deze inhoud erin. Alleen JetEngine Dynamic-widgets, dus geen Elementor Pro nodig.


def dyn_field(source, key, tag="div", typo=None, color="text", size_px=None, fmt=None, hide=True,
              filt=None, upper=False, extra=None):
    st = {"dynamic_field_source": source, "field_tag": tag, "hide_if_empty": "yes" if hide else "",
          "__globals__": {"field_color": g_color(color)}}
    if source == "object":
        st["dynamic_field_post_object"] = key
    else:
        st["dynamic_field_post_meta"] = key
    if fmt:
        st["dynamic_field_custom"] = "yes"
        st["dynamic_field_format"] = fmt
    if typo:
        st["__globals__"]["field_typography_typography"] = g_type(typo)
    if size_px:
        st["field_typography_typography"] = "custom"
        st["field_typography_font_size"] = size(size_px)
    if upper:
        st["field_typography_text_transform"] = "uppercase"
    if filt:
        st["dynamic_field_filter"] = "yes"
        st.update(filt)
    if extra:
        st.update(extra)
    return widget("jet-listing-dynamic-field", st)


def dyn_image(source="post_thumbnail", height=220, fit="cover", radius=14, link=True, link_source="_permalink",
              new_tab=False):
    st = {"dynamic_image_source": source, "dynamic_image_size": "large", "image_width": size(100, "%"),
          "image_height": size(height), "image_object_fit": fit, "image_border_radius": dims(radius),
          "hide_if_empty": "", "lazy_load_image": "yes"}
    if link:
        st.update({"linked_image": "yes", "image_link_source": link_source})
        if new_tab:
            st["open_in_new"] = "yes"
    return widget("jet-listing-dynamic-image", st)


def dyn_link(label, style="outline", source="_permalink", full=False):
    st = {"dynamic_link_source": source, "link_label": label, "link_wrapper_tag": "div",
          "link_padding": dims(10, 22), "link_border_radius": dims(4),
          "link_typography_typography": "custom", "link_typography_font_family": "Patrick Hand",
          "link_typography_text_transform": "uppercase", "link_typography_font_size": size(16)}
    if full:  # grote knop over de volle breedte (inschrijven)
        st.update({"link_padding": dims(18, 28), "link_typography_font_size": size(22), "_css_classes": "sp-cta-full"})
    if style == "outline":
        st.update({"link_border_border": "solid", "link_border_width": dims(1)})
        st["__globals__"] = {"link_color": g_color("accent"), "link_border_color": g_color("accent"),
                             "link_icon_color": g_color("accent")}
    else:
        st.update({"link_bg_background": "classic", "link_bg_hover_background": "classic"})
        st["__globals__"] = {"link_color": g_color("658acb6"), "link_bg_color": g_color("accent"),
                             "link_bg_hover_color": g_color("primary"), "link_icon_color": g_color("658acb6")}
    return widget("jet-listing-dynamic-link", st)


def listing_card(*kids, title, bg="658acb6", pad=20):
    colour = {"bg": bg} if bg.startswith("#") else {"bg_global": bg}
    c = container(*kids, title=title, radius=20, pad=dims(pad), gap_px=12, css_classes="sp-card", **colour,
                  extra={"min_height": size(100, "%")})
    return [c]


CHIP = {"field_bg_background": "classic", "field_bg_color": "#ECC0AE", "field_padding": dims(4, 12),
        "field_border_radius": dims(999), "field_display": "inline",
        "field_typography_typography": "custom", "field_typography_font_family": "Patrick Hand",
        "field_typography_text_transform": "uppercase", "field_typography_font_size": size(15)}

LISTINGS = {
    "projectkaart": ("Projectkaart", "projecten", listing_card(
        dyn_image(),
        container(dyn_field("meta", "aantal", tag="span", typo="accent", color="accent", size_px=18),
                  dyn_field("meta", "eenheid", tag="span", typo="accent", color="accent", size_px=18),
                  dyn_field("meta", "soort_werk", tag="span", typo="accent", color="accent", size_px=18, fmt="· %s"),
                  direction="row", gap_px=6, mobile_column=False, wrap=True, title="Kenmerken"),
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=26),
        dyn_field("meta", "tagline", tag="p"),
        dyn_link("Bekijk dit project"),
        title="Projectkaart")),
    "eventkaart": ("Evenementkaart", "evenementen", listing_card(
        dyn_image(height=200),
        dyn_field("meta", "status", tag="span", color="primary",
                  filt={"filter_callback": "jet_engine_label_by_glossary", "labels_by_glossary": "{{glossary:status}}"},
                  extra=CHIP),
        dyn_field("meta", "datum_start", tag="span", typo="accent", color="accent", size_px=18,
                  filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
        dyn_field("meta", "datum_label", tag="span", typo="accent", color="accent", size_px=18),
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=26),
        dyn_field("object", "post_excerpt", tag="p"),
        dyn_link("Meer informatie", style="primary"),
        title="Evenementkaart")),
    "sponsorlogo": ("Sponsorlogo", "sponsors", [container(
        dyn_image(height=80, fit="contain", radius=0, link=True, link_source="website", new_tab=True),
        title="Logo", bg="#FFFFFF", radius=999, pad=dims(24), align="center", justify="center",
        extra={"width": size(140), "min_height": size(140), "width_mobile": size(120), "min_height_mobile": size(120)})]),
    "nieuwskaart": ("Nieuwskaart", "post", listing_card(
        dyn_image(),
        dyn_field("object", "post_date", tag="span", typo="accent", color="accent", size_px=18,
                  filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=24),
        dyn_field("object", "post_excerpt", tag="p"),
        dyn_link("Lees meer"),
        title="Nieuwskaart")),
    "pakketkaart": ("Sponsorpakket", "product", listing_card(
        dyn_field("meta", "_price", tag="span", typo="accent", color="accent", size_px=18,
                  fmt="€ %s per jaar", filt={"filter_callback": "number_format", "num_dec_point": ",",
                                            "num_thousands_sep": ".", "num_decimals": 0}),
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=28),
        dyn_field("object", "post_excerpt", tag="div"),
        dyn_link("Kies dit pakket", style="primary"),
        title="Pakketkaart", bg="e64974d", pad=28)),
    "inschrijfkaart": ("Inschrijfkaart (product bij evenement)", "product", listing_card(
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=26),
        dyn_field("meta", "_price", tag="span", typo="accent", color="accent", size_px=20,
                  fmt="€ %s", filt={"filter_callback": "number_format", "num_dec_point": ",",
                                    "num_thousands_sep": ".", "num_decimals": 2}),
        dyn_field("object", "post_excerpt", tag="div"),
        dyn_link("Inschrijven of bestellen", style="primary"),
        title="Inschrijfkaart", bg="#FFFFFF", pad=24)),
    # Conversiekaart in de inschrijfsectie van een evenement: één product, groot bedrag, knop over de volle breedte
    "inschrijfkaart-groot": ("Inschrijfkaart groot (evenement)", "product", listing_card(
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=30),
        dyn_field("meta", "_price", tag="p", color="accent", size_px=44,
                  fmt="€ %s", filt={"filter_callback": "number_format", "num_dec_point": ",",
                                    "num_thousands_sep": ".", "num_decimals": 2},
                  extra={"field_typography_font_family": "Patrick Hand", "field_typography_line_height": size(1, "em")}),
        dyn_field("object", "post_excerpt", tag="div"),
        dyn_link("Schrijf je nu in", style="primary", full=True),
        title="Inschrijfkaart groot", bg="#FFFFFF", pad=0)),
    "bestelkaart": ("Bestelkaart (evenement het hele jaar)", "product", listing_card(
        dyn_image(height=220, radius=14, fit="contain"),
        dyn_field("object", "post_title", tag="h3", typo="primary", size_px=24),
        dyn_field("meta", "_price", tag="span", color="accent", size_px=28,
                  fmt="€ %s per doos", filt={"filter_callback": "number_format", "num_dec_point": ",",
                                             "num_thousands_sep": ".", "num_decimals": 2},
                  extra={"field_typography_font_family": "Patrick Hand"}),
        dyn_field("object", "post_excerpt", tag="div"),
        dyn_link("Bestel nu", style="primary", full=True),
        title="Bestelkaart", bg="#FFFFFF", pad=24)),
    "kaartpopup": ("Kaart-popup school", "projecten", [container(
        dyn_image(height=120, radius=10),
        container(dyn_field("meta", "aantal", tag="span", typo="accent", color="accent", size_px=16),
                  dyn_field("meta", "eenheid", tag="span", typo="accent", color="accent", size_px=16),
                  direction="row", gap_px=6, mobile_column=False, title="Aantal"),
        dyn_field("object", "post_title", tag="h4", typo="primary", size_px=20),
        dyn_link("Bekijk de school", style="primary"),
        title="Popup", gap_px=8, pad=dims(4))]),
}


def write_listings():
    out = OUT.parent / "listings"
    out.mkdir(exist_ok=True)
    for key, (title, source, content) in LISTINGS.items():
        (out / f"{key}.json").write_text(json.dumps({"key": key, "title": title, "source": source,
                                                     "content": content}, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- inhoud voor JetEngine (content.json)

FUND_KEYS = [("docent", "docenten"), ("sport", "sport"), ("lesmateriaal", "lesmateriaal"), ("schoolarts", "schoolarts"),
             ("gezondheid", "gezondheidszorg"), ("fiets", "fietsen"), ("elektriciteit", "vaste_lasten")]


def fund_keys(labels):
    keys = []
    for label in labels:
        low = label.lower()
        for k, v in FUND_KEYS:
            if k in low and v not in keys:
                keys.append(v)
    return keys


def content_json():
    projects = []
    for i, sch in enumerate(SCHOOLS):
        body = f"<h2>{sch['story_title']}</h2>" + "".join(f"<p>{p}</p>" for p in sch["story"])
        projects.append({
            "slug": sch["slug"], "title": sch["name"], "type": "school", "regio": "budaun", "order": i,
            "excerpt": sch["intro"], "content": body, "thumb": sch["img"], "gallery": sch["gallery"],
            "meta": {"tagline": sch["tagline"], "aantal": sch["pupils"], "eenheid": "leerlingen",
                     "soort_werk": sch["work"], "dorp": sch["village"], "extra_titel": sch["extra_title"],
                     "extra_tekst": sch["extra"], "we_financieren": fund_keys(sch["funds"]),
                     "feiten": [{"waarde": v, "label": l} for v, l in sch["facts"]],
                     "voorzieningen": [{"voorziening": v} for v in sch["facilities"]],
                     "momenten": [{"moment": m, "tekst": t} for m, t in sch["moments"]]},
            "lat": sch["lat"], "lng": sch["lng"]})
    delhi_intro = ("De trek van het platteland naar de grote steden is groot, maar veel mensen vinden daar geen baan en "
                   "belanden in de sloppenwijken. Om jongvolwassenen meer kans op een betere toekomst te geven, "
                   "biedt Sampark in New Delhi gewilde beroepsopleidingen aan.")
    for i, (slug, title, n, tag, img) in enumerate([
            ("computerspecialist", "Computerspecialist", 20, "Digitale vaardigheden voor een kantoorbaan.", "proj_computer"),
            ("modinette", "Modinette", 29, "Kleding maken en een eigen inkomen.", "proj_modinette"),
            ("schoonheidsspecialiste", "Schoonheidsspecialiste", 24, "Een vak met vraag in de stad.", "proj_beauty")]):
        projects.append({"slug": slug, "title": title, "type": "opleiding", "regio": "new-delhi", "order": 10 + i,
                         "excerpt": delhi_intro, "content": f"<p>{delhi_intro}</p>", "thumb": img, "gallery": [img],
                         "meta": {"tagline": tag, "aantal": n, "eenheid": "studenten", "soort_werk": "Doorlopend",
                                  "dorp": "New Delhi"},
                         "lat": DELHI["lat"], "lng": DELHI["lng"]})
    for i, (slug, title, tag, img, link) in enumerate([
            ("fietsen", "Fietsen voor geslaagden", "Zodat het vervolgonderwijs bereikbaar is.", "proj_fietsen", ""),
            ("zonnepanelen", "Zonnepanelen", "Een school die haar eigen energie opwekt.", "proj_zon", ""),
            ("solarlampjes", "Solarlampjes", "Licht om thuis te kunnen studeren.", "proj_solar", ""),
            ("stichting-accrete", "Stichting Accrete", "Leerlingen in Nederland en India verbonden.", "proj_accrete",
             "https://ichthus.accrete.nl/basisschool/stichtingsampark")]):
        projects.append({"slug": slug, "title": title, "type": "initiatief", "regio": "budaun", "order": 20 + i,
                         "excerpt": tag, "content": f"<p>{tag}</p>", "thumb": img, "gallery": [img],
                         "meta": {"tagline": tag, "soort_werk": "Doorlopend", "externe_link": link}})
    events = [
        {"slug": "padel-toernooi", "order": 1, "title": "Padel toernooi", "thumb": "event_padel",
         "excerpt": "Een sportieve middag bij Peakz Padel Zwolle. € 89 per team van twee.",
         "content": "<p>Of je nu net begint met padel of al aardig wat wedstrijden hebt gespeeld, iedereen is welkom. We spelen in drie categorieën: Starter, Intermediate en Advanced.</p><p>Deelname kost € 89 per team van twee personen, inclusief twee consumptiebonnen per persoon. Inschrijven gaat via Peakz Padel.</p>",
         "meta": {"status": "open", "datum_start": "2026-11-21", "tijd": "12.00 – 17.00 uur",
                  "locatie_tekst": "Peakz Padel Zwolle, Hanzelaan 95, Zwolle", "prijs_label": "€ 89 per team van twee",
                  "externe_inschrijflink": "https://www.peakzpadel.nl/reserveren/kalender-event?id=f450c14a-f944-4996-9f84-fc4d85b76739"}},
        {"slug": "wijnactie", "order": 4, "title": "Wijnactie", "thumb": "event_wijn",
         "excerpt": "Rood, wit en alcoholvrij. € 43,50 per doos van zes flessen, opbrengst naar de scholen.",
         "content": "<p>Ieder jaar stellen we vanuit Stichting Sampark een tweetal wijnen samen, en dit jaar ook een alcoholvrije. Afhalen of laten thuisbezorgen.</p>",
         "meta": {"status": "doorlopend", "datum_label": "Het hele jaar", "prijs_label": "€ 43,50 per doos"},
         "products": ["rode-wijn", "witte-wijn", "alcoholvrij"]},
        {"slug": "sampark-rally", "order": 2, "title": "Sampark Rally", "thumb": "event_rally",
         "excerpt": "Een dag met je eigen klassieker door Oost-Nederland. € 600 per equipe.",
         "content": "<p>Een compleet verzorgde dag voor twee personen in een eigen auto, afgesloten met een diner en de prijsuitreiking.</p>",
         "meta": {"status": "aangekondigd", "datum_label": "September 2027 · datum volgt", "prijs_label": "€ 600 per equipe", "max_deelnemers": 60},
         "products": ["ticket-sampark-rally"]},
        {"slug": "golftoernooi", "order": 3, "title": "Golftoernooi", "thumb": "event_golf",
         "excerpt": "Wedstrijd, clinic of masterclass op Het Rijk van Nunspeet. Vanaf € 300 p.p.",
         "content": "<p>Speel mee in de wedstrijd om de wisselbeker, of doe mee aan een clinic voor beginners of een masterclass voor gevorderden.</p>",
         "meta": {"status": "aangekondigd", "datum_label": "Oktober 2027 · datum volgt", "locatie_tekst": "Het Rijk van Nunspeet",
                  "prijs_label": "€ 300 p.p. of € 1.200 per tafel",
                  "programma": [{"tijd": "09:30 – 11:00", "onderdeel": "Ontvangst wedstrijdspelers"},
                                {"tijd": "11:30 – 16:30", "onderdeel": "Wedstrijd (shotgun)"},
                                {"tijd": "12:00 – 16:30", "onderdeel": "Lunch en clinics"},
                                {"tijd": "18:00 – 21:00", "onderdeel": "Diner en prijsuitreiking"}]},
         "products": ["golftoernooi"]},
        {"slug": "project-en-cultuurreis", "order": 5, "title": "Project- en cultuurreis", "thumb": "event_reis",
         "excerpt": "Reis mee naar India en zie met eigen ogen wat jouw steun doet.",
         "content": "<p>Regelmatig organiseert Stichting Sampark een reis naar India. Deelnemers maken kennis met het kleurrijke leven daar en zien met eigen ogen het verschil dat hulp kan maken.</p>",
         "meta": {"status": "doorlopend", "datum_label": "Op aanvraag"}},
    ]
    sponsors = [("Venture Group", "logo_venture", "https://venture-group.nl/"), ("Groothuis Bouwgroep", "logo_groothuis", "https://www.groothuisbouwgroep.nl/"),
                ("Schieven Keizer", "logo_schieven", "https://schievenkeizer.nl/"), ("We for You", "logo_w4y", ""),
                ("Venttri", "logo_venttri", "https://www.venttri.nl/"), ("Het Rijk van Nunspeet", "logo_rijk", "https://www.golfenophetrijk.nl/nunspeet.html"),
                ("Arcus IT", "logo_arcus", "https://arcusit.nl/"), ("KVS", "logo_kvs", "https://kvsbv.nl/"),
                ("Pleijsier Bouw en Onderhoud", "logo_pleijsier", "https://pleijsierbouwenonderhoud.nl/"), ("Positie1", "logo_positie1", "https://positie1.nl/")]
    news = [
        {"slug": "nat-maar-onvergetelijk-golftoernooi-2025", "title": "Nat, maar onvergetelijk: Golftoernooi 2025!", "date": "2025-11-11 10:00:00",
         "thumb": "news_golf_2025", "cat": "evenementen", "events": ["golftoernooi"],
         "excerpt": "Het jaarlijkse Samparkgolftoernooi was er weer eentje om niet snel te vergeten."},
        {"slug": "scholen-krijgen-bezoek-uit-canada", "title": "Scholen krijgen bezoek uit Canada!", "date": "2025-09-25 11:00:00",
         "thumb": "news_canada", "cat": "scholen-leerlingen", "projects": ["kundanpur-school"],
         "excerpt": "Mark en Sharon Jansen van Mores Textiles kwamen op bezoek bij onze scholen in India."},
        {"slug": "afscheid-abhishek-pandey", "title": "Afscheid Abhishek Pandey", "date": "2025-09-25 10:00:00",
         "thumb": "news_abhishek", "cat": "stichting",
         "excerpt": "We namen op bijzondere wijze afscheid van onze gewaardeerde schoolcoördinator."},
        {"slug": "zonnepanelen-sampark-school-khukdi", "title": "Zonnepanelen op de school in Khukdi", "date": "2020-10-20 10:00:00",
         "thumb": "proj_zon", "cat": "scholen-leerlingen", "projects": ["khukdi-school", "zonnepanelen"],
         "excerpt": "Hoe de school in Khukdi haar eigen energie is gaan opwekken."},
    ]
    options = {"cijfer_leerlingen": 1577, "cijfer_cursussen": 600, "cijfer_fietsen": 125, "cijfer_studenten_delhi": 73,
               "adres": "Schering 31-33\n8281 JW Genemuiden", "telefoon": "038 385 50 00", "email": "info@sampark.nl",
               "bereikbaarheid": "Op kantoordagen tussen 9.00 en 17.00 uur", "kvk": "08169359", "rsin": "818925887",
               "iban": "NL25 ABNA 0578 9231 73", "campagne_aan": "true", "campagne_titel": "Wijnactie",
               "campagne_tekst": "Rood, wit en alcoholvrij", "campagne_link": "/evenementen/wijnactie/",
               "bestuur": [{"naam": n, "functie": f, "foto": k} for n, f, k in BOARD],
               "tijdlijn": [{"jaar": y, "titel": t, "tekst": b} for y, t, b in TIMELINE]}
    return {"projects": projects, "events": events, "sponsors": [{"title": t, "thumb": k, "website": w, "order": i}
                                                                  for i, (t, k, w) in enumerate(sponsors)],
            "news": news, "options": options}


# ---------------------------------------------------------------- Theme Builder: header en footer (Elementor Pro)

TEMPLATES = []


def template(key, title, kind, content, conditions=("include/general",)):
    TEMPLATES.append({"key": key, "title": title, "type": kind, "conditions": list(conditions), "content": content})


def nav_menu(menu, layout="horizontal", align="end", dropdown="tablet", color="text", hover="primary", size_px=16,
             weight="600", pad_h=14, title=None):
    st = {"menu": menu, "layout": layout, "align_items": align, "pointer": "underline" if layout == "horizontal" else "none",
          "submenu_icon": {"value": "fas fa-chevron-down", "library": "fa-solid"}, "dropdown": dropdown, "toggle": "burger",
          "full_width": "stretch", "toggle_align": "right",
          "menu_typography_typography": "custom", "menu_typography_font_family": "aptos",
          "menu_typography_font_weight": weight, "menu_typography_font_size": size(size_px),
          "padding_horizontal_menu_item": size(pad_h), "padding_vertical_menu_item": size(10 if layout == "horizontal" else 4),
          "pointer_width": size(2), "dropdown_border_radius": dims(12), "dropdown_top_distance": size(6),
          "dropdown_typography_typography": "custom", "dropdown_typography_font_family": "aptos",
          "dropdown_typography_font_size": size(15), "dropdown_typography_text_transform": "none", "padding_vertical_dropdown_item": size(10),
          "__globals__": {"color_menu_item": g_color(color), "color_menu_item_hover": g_color(hover),
                          "pointer_color_menu_item_hover": g_color("accent"), "color_menu_item_active": g_color(hover),
                          "pointer_color_menu_item_active": g_color("accent"),
                          "color_dropdown_item": g_color("text"), "background_color_dropdown_item": g_color("658acb6"),
                          "color_dropdown_item_hover": g_color("658acb6"), "background_color_dropdown_item_hover": g_color("accent"),
                          "toggle_color": g_color("text"), "toggle_background_color": g_color("658acb6")}}
    if layout == "vertical":
        st["dropdown"] = "none"
    return widget("nav-menu", st, title=title)


def option_field(field, tag="span", color="658acb6", size_px=15, fmt=None):
    st = {"dynamic_field_source": "options_page", "dynamic_field_option": f"stichting::{field}", "field_tag": tag,
          "hide_if_empty": "yes", "field_typography_typography": "custom", "field_typography_font_size": size(size_px),
          "__globals__": {"field_color": g_color(color)}}
    if fmt:
        st["dynamic_field_custom"] = "yes"
        st["dynamic_field_format"] = fmt
    if field == "adres":
        st["dynamic_field_filter"] = "yes"
        st["filter_callback"] = "wpautop"
    return widget("jet-listing-dynamic-field", st, title=f"Options › {field}")


TOP_LINKS = [("Voor bedrijven", "/steun-ons/bedrijven/"), ("Contact", "/contact/"), ("Mijn account", "/mijn-account/")]

def header_nav():
    w = nav_menu("hoofdmenu", title="Hoofdmenu")
    w["settings"].update({"_flex_size": "grow", "_flex_size_tablet": "none", "_flex_size_mobile": "none",
                          "_flex_order_tablet": "end", "_flex_order_mobile": "end"})
    return w


header_content = [
    container(
        container(
            text("<p>Sinds 2007 onderwijs in India · ANBI-erkend</p>", color="658acb6", size_px=14),
            container(*[button(l, u, style="link-light") for l, u in TOP_LINKS], title="Topbalk links", direction="row",
                      gap_px=18, mobile_column=False, align="center"),
            title="Topbalk inhoud", boxed=True, direction="row", justify="space-between", align="center", gap_px=16,
            pad=dims(6, 24), mobile_column=False),
        title="Topbalk", bg_global="primary", extra={"hide_mobile": "hidden-mobile"}),
    container(
        container(
            widget("image", {"image": {"url": "{{img:logo_sampark}}", "id": "{{imgid:logo_sampark}}", "alt": "Stichting Sampark"},
                             "image_size": "medium", "width": size(170), "width_mobile": size(112),
                             "link_to": "custom", "link": {"url": "/", "is_external": "", "nofollow": ""},
                             "image_border_radius": dims(0), "_flex_size": "none"}, title="Logo"),
            header_nav(),
            button("Doneer", "/steun-ons/doneren/", nowrap=True),
            widget("woocommerce-menu-cart", {"icon": "bag-medium", "items_indicator": "bubble", "hide_empty_indicator": "yes",
                                             "show_subtotal": "", "toggle_icon_size": size(22), "_flex_size": "none",
                                             "toggle_button_border_width": size(0), "toggle_button_padding": dims(8),
                                             "__globals__": {"toggle_button_icon_color": g_color("text"),
                                                             "toggle_button_background_color": g_color("658acb6"),
                                                             "items_indicator_background_color": g_color("accent"),
                                                             "items_indicator_text_color": g_color("658acb6")}},
                   title="Winkelmandje"),
            title="Hoofdbalk inhoud", boxed=True, direction="row", justify="space-between", align="center", gap_px=16,
            pad=dims(10, 24), pad_mobile=dims(8, 16), mobile_column=False,
            extra={"flex_wrap": "nowrap", "flex_wrap_mobile": "nowrap", "flex_gap_mobile": gap(8)}),
        title="Hoofdbalk", bg_global="658acb6",
        extra={"sticky": "top", "sticky_on": ["desktop", "tablet", "mobile"], "sticky_effects_offset": 40,
               "box_shadow_box_shadow_type": "yes",
               "box_shadow_box_shadow": {"horizontal": 0, "vertical": 2, "blur": 12, "spread": 0, "color": "rgba(70,33,26,0.08)"}}),
]
template("header", "Header", "header", header_content)

SOCIALS = [("fab fa-facebook-f", "https://www.facebook.com/StichtingSampark", "Facebook"),
           ("fab fa-instagram", "https://www.instagram.com/stichtingsampark/", "Instagram"),
           ("fab fa-linkedin-in", "https://www.linkedin.com/company/stichting-sampark/", "LinkedIn"),
           ("fab fa-youtube", "https://www.youtube.com/channel/UCAt0_VtY9orOiD4r5Hv_82w", "YouTube")]

footer_col = lambda *kids, title, width=23: container(*kids, title=title, gap_px=10, width=width,
                                                      extra={"width_tablet": size(46, "%")})
foot_head = lambda t: heading(t, "h4", color="658acb6", size_px=22)

footer_content = [
    container(
        container(
            footer_col(
                widget("image", {"image": {"url": "{{img:logo_sampark}}", "id": "{{imgid:logo_sampark}}", "alt": "Stichting Sampark"},
                                 "image_size": "medium", "width": size(170), "align": "left", "_css_classes": "sp-logo-light",
                                 "link_to": "custom", "link": {"url": "/"}, "image_border_radius": dims(0)}, title="Logo"),
                heading("Biedt kinderen een toekomst.", "p", color="cf55c96", typo="accent", size_px=22),
                widget("social-icons", {"social_icon_list": [{"_id": _id(n), "social_icon": {"value": ic, "library": "fa-brands"},
                                                              "link": {"url": u, "is_external": "on"}, "item_icon_color": "custom"}
                                                             for ic, u, n in SOCIALS],
                                        "align": "left", "icon_color": "custom", "icon_size": size(16), "icon_padding": size(0.6, "em"),
                                        "icon_spacing": size(8), "shape": "circle",
                                        "__globals__": {"icon_primary_color": g_color("658acb6"), "icon_secondary_color": g_color("text")}},
                       title="Social"),
                title="Merk", width=24),
            footer_col(foot_head("Contact"), option_field("adres", tag="div"), option_field("telefoon", tag="div"),
                       option_field("email", tag="div"), option_field("bereikbaarheid", tag="div", color="cf55c96", size_px=14),
                       title="Contact (Options Page)", width=21),
            footer_col(foot_head("Direct naar"), nav_menu("footer-direct-naar", layout="vertical", align="start", color="658acb6",
                                                          hover="cf55c96", size_px=15, weight="400", pad_h=0),
                       title="Direct naar", width=18),
            footer_col(foot_head("Nieuwsbrief"),
                       text("<p>Twee keer per jaar nieuws uit India en over onze evenementen.</p>", color="658acb6", size_px=15),
                       widget("form", {"form_name": "Nieuwsbrief", "form_fields": [
                           {"_id": _id("nb-email"), "custom_id": "email", "field_type": "email", "field_label": "E-mailadres",
                            "placeholder": "Je e-mailadres", "required": "true", "width": "100"}],
                           "show_labels": "", "button_text": "Inschrijven", "button_width": "100",
                           "submit_actions": ["email"], "email_to": "info@sampark.nl",
                           "email_subject": "Nieuwe aanmelding nieuwsbrief", "email_content": "[all-fields]",
                           "success_message": "Dank je wel! Je bent aangemeld.",
                           "row_gap": size(10), "field_border_radius": dims(12),
                           "__globals__": {"button_background_color": g_color("accent"), "button_text_color": g_color("658acb6"),
                                           "button_background_hover_color": g_color("primary"),
                                           "field_text_color": g_color("text"), "field_background_color": g_color("658acb6")}},
                              title="Nieuwsbrief (Elementor Form · actie: e-mail; Mailchimp na keuze)"),
                       title="Nieuwsbrief", width=25),
            title="Kolommen", boxed=True, direction="row", gap_px=32, wrap=True, justify="space-between",
            pad=dims(72, 24, 48, 24), pad_mobile=dims(56, 20, 32, 20)),
        container(
            container(
                container(option_field("kvk", fmt="KvK %s", size_px=14, color="cf55c96"),
                          option_field("rsin", fmt="RSIN %s", size_px=14, color="cf55c96"),
                          option_field("iban", fmt="IBAN %s", size_px=14, color="cf55c96"),
                          title="Registratie", direction="row", gap_px=18, wrap=True, mobile_column=False),
                nav_menu("footer-juridisch", align="end", dropdown="none", color="cf55c96", hover="658acb6", size_px=14,
                         weight="400", pad_h=8, title="Juridisch"),
                widget("image", {"image": {"url": "{{img:logo_anbi}}", "id": "{{imgid:logo_anbi}}", "alt": "ANBI"},
                                 "width": size(64), "image_border_radius": dims(0), "_flex_size": "none"}, title="ANBI-logo"),
                title="Onderbalk inhoud", boxed=True, direction="row", justify="space-between", align="center", gap_px=20,
                wrap=True, pad=dims(18, 24)),
            title="Onderbalk", extra={"border_border": "solid", "border_width": {"unit": "px", "top": "1", "right": "0",
                                                                            "bottom": "0", "left": "0", "isLinked": False},
                                      "border_color": "rgba(245,237,227,0.15)"}),
        title="Footer", bg_global="text"),
]
template("footer", "Footer", "footer", footer_content)


# ---------------------------------------------------------------- Theme Builder: singles (Elementor Pro + JetEngine)
# Eén template per posttype in plaats van een losse pagina per school of evenement. Alle inhoud komt uit
# de velden van het bericht (JetEngine Dynamic-widgets en Elementor Pro-thema-widgets). Secties met een
# optioneel veld krijgen Dynamic Visibility ("veld bestaat"); secties met een Listing Grid krijgen de klasse
# sp-hide-empty en verdwijnen als de query leeg is (Listing Grid › Hide widget if › Query is empty).


def etag(name, settings=None):
    """Elementor dynamic tag, zoals de editor die opslaat."""
    return (f'[elementor-tag id="{_id(name)}" name="{name}" '
            f'settings="{quote(json.dumps(settings or {}, separators=(",", ":")))}"]')


def visible_if(el, *fields, relation="AND"):
    """JetEngine Dynamic Visibility: alleen tonen als de meta-velden een waarde hebben.
    Een veld met een @ ervoor is een eigenschap van het bericht zelf, bv. "@post_content"."""
    def tag(f):
        if f.startswith("@"):
            return etag("jet-object-property", {"object_prop": f[1:]})
        return etag("jet-post-custom-field", {"meta_field": f})
    el["settings"].update({
        "jedv_enabled": "yes", "jedv_type": "show", "jedv_relation": relation,
        "jedv_conditions": [{"_id": _id(f), "jedv_condition": "exists", "__dynamic__": {"jedv_field": tag(f)}}
                            for f in fields]})
    return el


def jet_grid(listing_key, query_key, cols=3, note=None):
    """Plek voor een JetEngine Listing Grid; build-site.php zet hier de echte grid neer."""
    return container(title=f"LISTING · {note or query_key}",
                     extra={"_sp_jet": {"listing": listing_key, "query": query_key, "cols": cols, "hide_empty": True}})


def post_title(size_px=64, color="658acb6", level="h1"):
    w = heading("", level, color=color, typo="accent", size_px=size_px)
    w["widgetType"] = "theme-post-title"
    w["settings"]["title"] = ""
    w["settings"]["__dynamic__"] = {"title": etag("post-title")}
    w["settings"]["_title"] = "Titel (post title)"
    return w


def post_content(title="Inhoud (post content)"):
    return widget("theme-post-content", {"__globals__": {"text_color": g_color("text")}}, title=title)


def single_hero(*inner, height=520):
    """Hero zoals op de pagina's, met de uitgelichte afbeelding als achtergrond."""
    c = container(
        container(container(*inner, title="Hero tekst", gap_px=16, width=60),
                  title="Hero inhoud", direction="row", boxed=True, align="center", gap_px=40,
                  pad=dims(140, 24, 140, 24), pad_mobile=dims(110, 20, 110, 20)),
        title="Hero (uitgelichte afbeelding)", overlay=HERO_OVERLAY, min_height=height,
        align="stretch", justify="center", tag="section", divider_bottom=("waves", "#FFFFFF", 70))
    c["settings"].update({"background_background": "classic", "background_position": "center center",
                          "background_size": "cover",
                          "__dynamic__": {"background_image": etag("post-featured-image")}})
    return c


def hide_empty(sec):
    sec["settings"]["css_classes"] = (sec["settings"].get("css_classes", "") + " sp-hide-empty").strip()
    return sec


def repeater(field, fmt, css, title, tag="div"):
    return widget("jet-listing-dynamic-repeater", {
        "dynamic_field_source": field, "dynamic_field_format": fmt, "item_tag": tag, "items_delimiter": "",
        "hide_if_empty": "yes", "_css_classes": css}, title=title)


def gallery_field(cols=2):
    w = dyn_field("meta", "galerij", hide=True,
                  filt={"filter_callback": "jet_engine_img_gallery_grid", "img_columns": cols,
                        "img_gallery_size": "large", "img_gallery_lightbox": "yes"})
    w["settings"]["img_gallery_gap"] = size(20)
    w["settings"]["_title"] = "Galerij (gallery-veld)"
    return w


steun_cta = cta_band("Help een kind naar school",
                     "Voor € 60 per jaar betaal je het lesgeld en de schoolspullen van één kind.",
                     [button("Sponsor een kind", "/product/sponsor-een-kind/", style="light"),
                      button("Doneer eenmalig", "/steun-ons/doneren/", style="outline-light")], eye="Steun ons werk")

# Project (school, opleiding, initiatief) --------------------------------------------------------
project_single = [
    single_hero(
        dyn_field("meta", "dorp", tag="p", typo="accent", color="cf55c96", size_px=20, upper=True),
        post_title(),
        dyn_field("object", "post_excerpt", tag="p", color="658acb6", size_px=19),
        container(button("Sponsor een kind", "/product/sponsor-een-kind/"),
                  button("Doneer voor dit project", "/steun-ons/doneren/", style="light"),
                  title="Knoppen", direction="row", gap_px=12, mobile_column=False, wrap=True)),
    visible_if(section(repeater("feiten", '<div class="sp-fact"><strong>%waarde%</strong><span>%label%</span></div>',
                                "sp-facts", "Feiten (repeater feiten)"),
                       title="Feiten", pad=(40, 24)), "feiten"),
    section(
        container(
            container(eyebrow("Het verhaal"), post_content(),
                      dyn_field("meta", "extra_titel", tag="h3", typo="primary", size_px=26),
                      dyn_field("meta", "extra_tekst", tag="p", filt={"filter_callback": "wpautop"}),
                      visible_if(container(dyn_link("Bezoek de website", source="externe_link"), title="Externe link"),
                                 "externe_link"),
                      title="Verhaal", width=55, gap_px=14),
            container(dyn_image(height=420, radius=20, link=False),
                      visible_if(container(eyebrow("Voorzieningen"),
                                           repeater("voorzieningen", '<span class="sp-check">%voorziening%</span>',
                                                    "sp-checks", "Voorzieningen (repeater)"),
                                           title="Voorzieningen", gap_px=8), "voorzieningen"),
                      title="Beeld en voorzieningen", width=40, gap_px=24),
            direction="row", gap_px=48, align="flex-start"),
        title="Verhaal"),
    visible_if(section(
        section_head("Jouw steun", "Wat Sampark hier betaalt",
                     "Samen met de Vincentian Charitable Trust houden we de school elke dag open."),
        dyn_field("meta", "we_financieren", tag="div",
                  filt={"filter_callback": "jet_engine_render_checklist", "checklist_cols_num": 3,
                        "labels_by_glossary": "{{glossary:financiering}}",
                        "selected_field_icon": {"value": "fas fa-check-circle", "library": "fa-solid"}},
                  extra={"_css_classes": "sp-checklist", "checklist_cols_num_mobile": 1}),
        title="Wat we betalen", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50),
        divider_bottom=("waves", "#FFFFFF", 50)), "we_financieren"),
    visible_if(section(
        section_head("Door de jaren heen", "Zo is het gegaan"),
        repeater("momenten", '<div class="sp-moment"><span class="sp-moment__when">%moment%</span><p>%tekst%</p></div>',
                 "sp-moments", "Momenten (repeater)"),
        title="Tijdlijn"), "momenten"),
    visible_if(section(
        section_head("Waar we zijn", "Op de kaart",
                     "Budaun ligt ongeveer 200 kilometer (hemelsbreed) ten oosten van New Delhi, in de deelstaat Uttar Pradesh."),
        html('<div class="sp-map__canvas" style="min-height:420px"></div>',
             title="KAART · JetEngine Map Listing · q_dit_project · zoom 9"),
        title="Locatie"), "locatie"),
    visible_if(section(section_head("In beeld", "Foto's"), gallery_field(), title="Galerij", pad=(40, 24)), "galerij"),
    hide_empty(section(section_head("Nieuws", "Nieuws over dit project"),
                       jet_grid("nieuwskaart", "q_project_nieuws", 3, "nieuws via relatie Project ↔ Bericht"),
                       title="Nieuws")),
    steun_cta,
    hide_empty(section(section_head("Bekijk ook", "Andere projecten"),
                       jet_grid("projectkaart", "q_andere_projecten", 3, "zelfde projecttype, zonder dit project"),
                       title="Andere projecten")),
]
template("single-project", "Single · Project", "single-post", project_single, conditions=("include/singular/projecten",))

# Evenement ----------------------------------------------------------------------------------
def visible_when(el, field, value, equal=True):
    """JetEngine Dynamic Visibility: tonen als een meta-veld wel (of juist niet) deze waarde heeft."""
    el["settings"].update({
        "jedv_enabled": "yes", "jedv_type": "show", "jedv_relation": "AND",
        "jedv_conditions": [{"_id": _id(field), "jedv_condition": "equal" if equal else "not-equal",
                             "jedv_value": value, "jedv_data_type": "chars",
                             "__dynamic__": {"jedv_field": etag("jet-post-custom-field", {"meta_field": field})}}]})
    return el


def info_row(fa, label, *fields_w, fields=()):
    """Praktische informatie als vlak in de rechterkolom: icoon links, label en waarde rechts."""
    c = container(fa_icon(fa, px=24),
                  container(eyebrow(label), *fields_w, title="Label en waarde", gap_px=2),
                  title=f"Info · {label}", direction="row", gap_px=16, mobile_column=False, align="flex-start",
                  css_classes="sp-info", extra={"width": size(100, "%")})
    return visible_if(c, *fields, relation="OR") if fields else c


def not_if(el, field):
    """JetEngine Dynamic Visibility: alleen tonen als het meta-veld leeg is."""
    el["settings"].update({
        "jedv_enabled": "yes", "jedv_type": "show", "jedv_relation": "AND",
        "jedv_conditions": [{"_id": _id(field), "jedv_condition": "not-exists",
                             "__dynamic__": {"jedv_field": etag("jet-post-custom-field", {"meta_field": field})}}]})
    return el


def css(el, classes):
    """Extra CSS-klasse op een widget of container."""
    key = "css_classes" if el.get("elType") == "container" else "_css_classes"
    el["settings"][key] = (el["settings"].get(key, "") + " " + classes).strip()
    return el


def fact(fa, *fields_w, fields=()):
    """Kerngegeven in de inschrijfsectie: klein icoon en waarde op één regel."""
    c = container(fa_icon(fa, px=18), *fields_w, title="Kerngegeven", direction="row", gap_px=10, mobile_column=False,
                  align="center", css_classes="sp-fact")
    return visible_if(c, *fields, relation="OR") if fields else c


def inschrijf_knop(**kw):
    """Knop naar de inschrijfsectie: "Schrijf je in", of "Bestel nu" als er producten te bestellen zijn (wijnactie)."""
    return container(css(button("Schrijf je in", "#inschrijven", **kw), "sp-als-inschrijf"),
                     css(button("Bestel nu", "#inschrijven", **kw), "sp-als-bestel"),
                     title="Knop naar inschrijven", gap_px=0,
                     css_classes="sp-knop-inschrijven" + ("" if kw.get("full") else " sp-knop-auto"))


event_single = [
    single_hero(
        dyn_field("meta", "status", tag="span", color="primary",
                  filt={"filter_callback": "jet_engine_label_by_glossary", "labels_by_glossary": "{{glossary:status}}"},
                  extra=dict(CHIP, _flex_size="none")),
        post_title(),
        dyn_field("object", "post_excerpt", tag="p", color="658acb6", size_px=19),
        container(visible_when(inschrijf_knop(), "status", "afgelopen", equal=False),
                  button("Alle evenementen", "/evenementen/", style="light"),
                  title="Knoppen", direction="row", gap_px=12, mobile_column=False, wrap=True)),
    section(
        container(
            container(eyebrow("Over dit evenement"), post_content(),
                      visible_if(container(eyebrow("Programma"),
                                           repeater("programma", '<div class="sp-prog"><span>%tijd%</span><strong>%onderdeel%</strong></div>',
                                                    "sp-programma", "Programma (repeater)"),
                                           title="Programma", gap_px=12, bg_global="658acb6", radius=20, pad=dims(28),
                                           extra={"margin": dims(16, 0, 0, 0)}),
                                 "programma"),
                      title="Beschrijving en programma", width=60, gap_px=14),
            container(
                info_row("far fa-calendar-alt", "Wanneer",
                         dyn_field("meta", "datum_start", tag="p", filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
                         dyn_field("meta", "datum_label", tag="p"), fields=("datum_start", "datum_label")),
                info_row("far fa-clock", "Tijd", dyn_field("meta", "tijd", tag="p"), fields=("tijd",)),
                info_row("fas fa-map-marker-alt", "Waar", dyn_field("meta", "locatie_tekst", tag="p"), fields=("locatie_tekst",)),
                info_row("fas fa-euro-sign", "Kosten", dyn_field("meta", "prijs_label", tag="p"), fields=("prijs_label",)),
                info_row("fas fa-hourglass-half", "Inschrijven tot",
                         dyn_field("meta", "inschrijving_tot", tag="p", filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
                         fields=("inschrijving_tot",)),
                info_row("fas fa-users", "Deelnemers",
                         dyn_field("meta", "max_deelnemers", tag="p", fmt="Maximaal %s"), fields=("max_deelnemers",)),
                visible_when(inschrijf_knop(full=True), "status", "afgelopen", equal=False),
                title="Praktische informatie (rechts, onder elkaar)", width=34, gap_px=14),
            direction="row", gap_px=48, align="flex-start", justify="space-between"),
        title="Over"),
    # Inschrijven: alleen dit evenement, gericht op aanmelden. Links waarom en wanneer, rechts de inschrijfkaart.
    # Evenementen die het hele jaar lopen (wijnactie) tonen "Bestel nu" met de producten in drie kolommen; zonder product of
    # link (cultuurreis op aanvraag) vraagt de kaart om contact. Het wisselen gebeurt met CSS (sampark-styles.php).
    visible_when(section(
        container(
            container(eyebrow("Doe mee"),
                      css(heading("Schrijf je nu in", "h2", color="primary", typo="accent", size_px=56), "sp-als-inschrijf"),
                      css(heading("Bestel nu", "h2", color="primary", typo="accent", size_px=56), "sp-als-bestel"),
                      dyn_field("object", "post_title", tag="p", typo="primary", color="accent", size_px=28),
                      css(text("<p>Je hebt een mooie dag en je helpt een kind in India naar school: "
                               "de opbrengst gaat naar de scholen van Sampark.</p>", size_px=18), "sp-als-inschrijf"),
                      css(text("<p>Met elke bestelling help je een kind in India naar school: "
                               "de opbrengst gaat naar de scholen van Sampark.</p>", size_px=18), "sp-als-bestel"),
                      container(
                          fact("far fa-calendar-alt",
                               dyn_field("meta", "datum_start", tag="span", filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
                               dyn_field("meta", "datum_label", tag="span"), fields=("datum_start", "datum_label")),
                          fact("fas fa-map-marker-alt", dyn_field("meta", "locatie_tekst", tag="span"), fields=("locatie_tekst",)),
                          fact("fas fa-euro-sign", dyn_field("meta", "prijs_label", tag="span"), fields=("prijs_label",)),
                          title="Kerngegevens", gap_px=4, css_classes="sp-kerngegevens"),
                      visible_if(container(
                          fa_icon("fas fa-hourglass-half", px=18),
                          dyn_field("meta", "inschrijving_tot", tag="span", color="primary", fmt="<strong>Inschrijven kan tot %s</strong>",
                                    filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
                          title="Deadline", direction="row", gap_px=10, mobile_column=False, align="center",
                          css_classes="sp-urgent"), "inschrijving_tot"),
                      visible_if(container(
                          fa_icon("fas fa-users", px=18),
                          dyn_field("meta", "max_deelnemers", tag="span", color="primary", fmt="<strong>Maximaal %s deelnemers: vol is vol</strong>"),
                          title="Maximum", direction="row", gap_px=10, mobile_column=False, align="center",
                          css_classes="sp-urgent"), "max_deelnemers"),
                      not_if(html('<ul class="sp-voordelen"><li>Direct een bevestiging per e-mail</li>'
                                  '<li>Veilig betalen met iDEAL of op factuur</li></ul>',
                                  title="Zekerheden (niet bij inschrijven via de organisator)"), "externe_inschrijflink"),
                      title="Waarom meedoen (links)", width=50, gap_px=14, css_classes="sp-waarom"),
            container(
                visible_when(container(visible_when(container(
                    jet_grid("inschrijfkaart-groot", "q_event_producten", 1, "product(en) van dit evenement"),
                    title="Inschrijfkaart"), "status", "doorlopend", equal=False), title="Niet vol"),
                    "status", "vol", equal=False),
                visible_when(container(
                    heading("Dit evenement is vol", "h3", color="primary", size_px=26),
                    text("<p>Neem contact met ons op: we zetten je graag op de wachtlijst.</p>"),
                    button("Zet me op de wachtlijst", "/contact/", full=True),
                    title="Vol", gap_px=12, css_classes="sp-keep sp-vol"), "status", "vol"),
                visible_if(container(
                    text("<p>Inschrijven voor dit evenement gaat via de organisator.</p>"),
                    dyn_link("Schrijf je nu in", style="primary", source="externe_inschrijflink", full=True),
                    title="Externe inschrijving", gap_px=12, css_classes="sp-keep sp-extern"), "externe_inschrijflink"),
                container(
                    heading("Interesse?", "h3", color="primary", size_px=26),
                    text("<p>Laat het ons weten, dan nemen we contact met je op over de mogelijkheden en de data.</p>"),
                    button("Neem contact op", "/contact/", full=True),
                    title="Nog geen inschrijving (alleen zonder product of link)", gap_px=12, css_classes="sp-keep sp-inschrijf-later"),
                container(text("<p>Vragen over inschrijven?</p>", size_px=14),
                          option_field("telefoon", tag="span", color="text", size_px=14),
                          title="Vragen", direction="row", gap_px=6, wrap=True, mobile_column=False,
                          css_classes="sp-keep sp-vragen"),
                title="Inschrijfkaart (rechts)", width=42, bg="#FFFFFF", radius=20, pad=dims(36), pad_mobile=dims(24),
                gap_px=16, css_classes="sp-inschrijfkaart"),
            title="Inschrijven: tekst en kaart", direction="row", gap_px=48, align="center", justify="space-between"),
        visible_when(container(jet_grid("bestelkaart", "q_event_producten", 3, "producten van dit evenement"),
                               title="Bestellen (het hele jaar)", css_classes="sp-bestellen"), "status", "doorlopend"),
        title="Inschrijven", bg_global="658acb6", pad=(72, 24), divider_top=("waves", "#FFFFFF", 50),
        divider_bottom=("waves", "#FFFFFF", 50), gap_px=40, extra={"_element_id": "inschrijven", "css_classes": "sp-inschrijven"}),
        "status", "afgelopen", equal=False),
    visible_if(section(section_head("In beeld", "Foto's"), gallery_field(3), title="Galerij", pad=(40, 24)), "galerij"),
    hide_empty(section(section_head("Met dank aan", "Sponsors van dit evenement", align="center"),
                       jet_grid("sponsorlogo", "q_event_sponsors", 6, "sponsors via relatie Sponsor ↔ Evenement"),
                       title="Sponsors", align="center")),
    hide_empty(section(section_head("Terugblik", "Nieuws over dit evenement"),
                       jet_grid("nieuwskaart", "q_event_nieuws", 3, "nieuws via relatie Evenement ↔ Bericht"),
                       title="Nieuws")),
    section(
        section_head("Ook interessant", "Andere manieren om Sampark te steunen"),
        container(eyebrow("Andere evenementen"),
                  jet_grid("eventkaart", "q_andere_events", 3, "andere evenementen (niet afgelopen), zonder dit evenement"),
                  title="Andere evenementen", gap_px=16, css_classes="sp-hide-empty"),
        container(eyebrow("Sponsorpakketten"),
                  jet_grid("pakketkaart", "q_pakketten", 3, "sponsorpakketten"),
                  title="Sponsorpakketten", gap_px=16, css_classes="sp-hide-empty", bg_global="658acb6", radius=20,
                  pad=dims(32), pad_mobile=dims(20)),
        title="Ook interessant (ondergeschikt)", gap_px=40, pad=(64, 24)),
    cta_band("Kun je er niet bij zijn?", "Met een donatie help je net zo goed: elke euro gaat naar de scholen in India.",
             [button("Doneer", "/steun-ons/doneren/", style="light"),
              button("Andere evenementen", "/evenementen/", style="outline-light")], eye="Steun ons werk"),
]
template("single-event", "Single · Evenement", "single-post", event_single, conditions=("include/singular/evenementen",))

# Nieuwsbericht -----------------------------------------------------------------------------
narrow = {"boxed_width": size(800)}
post_single = [
    container(
        container(
            dyn_field("object", "post_date", tag="p", typo="accent", color="accent", size_px=20,
                      filt={"filter_callback": "jet_engine_date", "date_format": "j F Y"}),
            post_title(size_px=52, color="text"),
            dyn_field("object", "post_excerpt", tag="p", size_px=20),
            title="Kop", boxed=True, gap_px=12, extra=narrow),
        title="Berichtkop", pad=dims(72, 24, 32, 24), pad_mobile=dims(48, 20, 24, 20), tag="header"),
    container(
        widget("theme-post-featured-image", {"image_size": "full", "width": size(100, "%"), "height": size(520),
                                             "height_mobile": size(260), "object-fit": "cover",
                                             "image_border_radius": dims(20),
                                             "__dynamic__": {"image": etag("post-featured-image")}},
               title="Uitgelichte afbeelding"),
        title="Beeld", boxed=True, pad=dims(0, 24), extra={"boxed_width": size(1000)}),
    container(post_content("Bericht (post content)"), title="Tekst", boxed=True, pad=dims(48, 24, 72, 24), extra=narrow),
    hide_empty(section(section_head("Over dit project", "Lees meer over het project"),
                       jet_grid("projectkaart", "q_bericht_projecten", 3, "projecten via relatie Project ↔ Bericht"),
                       title="Gekoppelde projecten", bg_global="658acb6", divider_top=("waves", "#FFFFFF", 50))),
    hide_empty(section(section_head("Evenement", "Doe volgende keer mee"),
                       jet_grid("eventkaart", "q_bericht_events", 3, "evenementen via relatie Evenement ↔ Bericht"),
                       title="Gekoppelde evenementen")),
    hide_empty(section(section_head("Nieuws", "Meer nieuws"),
                       jet_grid("nieuwskaart", "q_nieuws_meer", 3, "3 nieuwste, zonder dit bericht"),
                       title="Meer nieuws")),
    steun_cta,
]
template("single-post", "Single · Nieuwsbericht", "single-post", post_single, conditions=("include/singular/post",))

# Nieuwsarchief: de berichtenpagina /nieuws/ en de categoriepagina's. De Listing Grid gebruikt de query van het
# archief zelf ("Use as Archive Template"), met een knop "Meer nieuws" die via JetEngine Load more werkt.
NEWS_CATS = [("Alles", "/nieuws/"), ("Scholen & leerlingen", "/category/scholen-leerlingen/"),
             ("Evenementen", "/category/evenementen/"), ("Sponsors & partners", "/category/sponsors-partners/"),
             ("Stichting", "/category/stichting/")]


def archive_title():
    w = heading("", "h1", color="primary", typo="accent", size_px=56)
    w["widgetType"] = "theme-archive-title"
    w["settings"]["title"] = ""
    w["settings"]["__dynamic__"] = {"title": etag("archive-title", {"include_context": "", "fallback": "Nieuws"})}
    w["settings"]["_title"] = "Titel (archieftitel: Nieuws of de categorie)"
    return w


more = button("Meer nieuws", "#", style="outline", align="center")
more["settings"]["_element_id"] = "sp-meer-nieuws"
more["settings"]["_title"] = "Load more-knop (ID sp-meer-nieuws)"
news_archive = [
    container(
        container(
            eyebrow("Uit India en Nederland"),
            archive_title(),
            text("<p>Verhalen van de scholen, terugblikken op onze evenementen en nieuws over de stichting.</p>", size_px=19),
            container(*[button(l, u, style="outline") for l, u in NEWS_CATS], title="Categorieën", direction="row",
                      gap_px=10, wrap=True, mobile_column=False, css_classes="sp-cats"),
            title="Kop", boxed=True, gap_px=14, extra={"boxed_width": size(1140)}),
        title="Archiefkop", bg_global="658acb6", pad=dims(80, 24, 96, 24), pad_mobile=dims(56, 20, 72, 20), tag="header",
        divider_bottom=("waves", "#FFFFFF", 50)),
    section(jet_grid("nieuwskaart", "archive", 3, "berichten van dit archief, 9 per keer"),
            more, title="Berichten", pad=(48, 24), gap_px=32),
    steun_cta,
]
template("archive-news", "Archief · Nieuws", "archive", news_archive,
         conditions=("include/archive/post_archive", "include/archive/category"))


# Product ---------------------------------------------------------------------------------
# Eén basis-template met de winkelwagenknop (sponsorpakketten, sponsor een kind) en per categorie een
# variant met het Super Forms-formulier. De categorie-voorwaarde gaat in Elementor Pro voor op "alle producten".

def product_template(key, title, order_widget, cat=None, price=True, note=None):
    info = [widget("woocommerce-breadcrumb", {}, title="Kruimelpad"),
            widget("woocommerce-product-title", {"header_size": "h1", "typography_typography": "custom",
                                                 "typography_font_size": size(48), "typography_font_size_mobile": size(34),
                                                 "__globals__": {"title_color": g_color("primary"),
                                                                 "typography_typography": g_type("accent")},
                                                 "__dynamic__": {"title": etag("woocommerce-product-title-tag")}},
                   title="Producttitel")]
    if price:
        info.append(widget("woocommerce-product-price", {"price_typography_typography": "custom",
                                                         "price_typography_font_size": size(26),
                                                         "__globals__": {"price_color": g_color("accent"),
                                                                         "price_typography_typography": g_type("accent")}},
                           title="Prijs"))
    info.append(widget("woocommerce-product-short-description", {"__globals__": {"text_color": g_color("text")}},
                       title="Korte omschrijving"))
    if note:
        info.append(text(f"<p>{note}</p>", size_px=15))
    info.append(order_widget)
    content = [
        section(
            container(
                container(widget("woocommerce-product-images", {"image_border_radius": dims(20), "spacing": size(16)},
                                 title="Productbeeld"), title="Beeld", width=45),
                container(*info, title="Product en bestellen", width=50, gap_px=16, css_classes="sp-product"),
                direction="row", gap_px=48, align="flex-start"),
            title="Product", pad=(64, 24)),
        # de beschrijving alleen als er een lange tekst is
        visible_if(section(
            container(eyebrow("Over dit product"),
                      widget("woocommerce-product-content", {"text_typography_typography": "custom",
                                                             "text_typography_font_size": size(17),
                                                             "text_typography_line_height": size(1.7, "em"),
                                                             "__globals__": {"text_color": g_color("text")}},
                             title="Beschrijving (lange omschrijving)"),
                      title="Beschrijving", bg_global="658acb6", radius=20, pad=dims(48, 56), pad_mobile=dims(28, 22),
                      gap_px=10, css_classes="sp-product-desc", extra={"max_width": size(900)}),
            title="Beschrijving", pad=(24, 24), gap_px=0), "@post_content"),
        container(
            container(
                container(fa_icon("fas fa-hand-holding-heart", color="primary", px=30),
                          text("<p><strong>ANBI-erkend</strong><br>Je gift is fiscaal aftrekbaar.</p>"),
                          title="ANBI", direction="row", gap_px=14, mobile_column=False, width=31),
                container(fa_icon("fas fa-school", color="primary", px=30),
                          text("<p><strong>Naar de scholen</strong><br>Opbrengsten gaan naar onderwijs in India.</p>"),
                          title="Bestemming", direction="row", gap_px=14, mobile_column=False, width=31),
                container(fa_icon("fas fa-lock", color="primary", px=30),
                          text("<p><strong>Veilig betalen</strong><br>iDEAL of op factuur.</p>"),
                          title="Betalen", direction="row", gap_px=14, mobile_column=False, width=31),
                title="Vertrouwen inhoud", boxed=True, direction="row", gap_px=24, justify="space-between",
                pad=dims(40, 24)),
            title="Vertrouwen", bg_global="658acb6", tag="section"),
    ]
    conditions = (f"include/product/in_product_cat/{{{{pcat:{cat}}}}}",) if cat else ("include/product",)
    template(key, title, "product", content, conditions=conditions)


def super_form(key):
    return widget("shortcode", {"shortcode": f'[super_form id="{{{{form:{key}}}}}"]'}, title=f"Super Forms · {key}")


product_template("product", "Product · winkelwagenknop",
                 widget("woocommerce-product-add-to-cart", {"show_quantity": "", "button_text": "In winkelmand"},
                        title="Bestelknop"))
product_template("product-wijn", "Product · wijnactie (Super Forms)", super_form("wijn"), cat="wijnactie",
                 note="Per doos van 6 flessen. Afhalen in Genemuiden of laten bezorgen.")
product_template("product-rally", "Product · Sampark Rally (Super Forms)", super_form("rally"), cat="samparkrally")
product_template("product-golf", "Product · golftoernooi (Super Forms)", super_form("golf"), cat="golftoernooi")
product_template("product-donatie", "Product · donatie (Super Forms)", super_form("donatie"), cat="donatie", price=False)


# BEDANKPAGINA NA EEN BESTELLING ----------------------------------------------------
# Elementor Pro › Site-instellingen › WooCommerce › Purchase Summary-pagina wijst naar deze pagina (shop-settings.php):
# na elke bestelling toont WooCommerce hier de bestelling, met daarnaast wat er nu gebeurt.
SUMMARY_TEXTS = {
    "confirmation_message_active": "", "payment_details_number": "Bestelnummer:", "payment_details_date": "Datum:",
    "payment_details_email": "E-mailadres:", "payment_details_total": "Totaal:", "payment_details_payment": "Betaalmethode:",
    "bank_details_text": "Onze bankgegevens", "downloads_text": "Downloads", "order_summary_text": "Je bestelling",
    "billing_details_text": "Factuurgegevens", "shipping_details_text": "Bezorgadres",
    "sections_background_color": "#F6F6F6", "sections_border_type": "none", "sections_border_radius": dims(10),
    "sections_padding": dims(24), "sections_spacing": size(20),
    "__globals__": {"titles_color": g_color("primary"), "general_text_color": g_color("text"),
                    "payment_details_titles_color": g_color("text"), "payment_details_items_color": g_color("primary")},
}


def next_step(fa, title, *body, key):
    return container(fa_icon(fa, px=22),
                     container(heading(title, "h3", size_px=19, color="text"), *body, title="Stap tekst", gap_px=2),
                     title=f"Stap · {key}", direction="row", gap_px=14, mobile_column=False, align="flex-start",
                     css_classes=f"sp-stap sp-stap-{key}")


def small(html_text):
    return text(html_text, size_px=15)


page("bedankt", "Bedankt",
     container(
         container(eyebrow("Bestelling ontvangen"),
                   heading("Bedankt voor jouw steun!", "h1", color="primary", typo="accent", size_px=52),
                   text("<p>Fijn dat je ons helpt kinderen in India een betere toekomst te geven. Hieronder zie je je "
                        "bestelling; dezelfde gegevens staan in de bevestiging in je mailbox.</p>", size_px=18),
                   title="Kop", boxed=True, gap_px=10, extra={"boxed_width": size(1140)}),
         title="Paginakop", bg_global="658acb6", pad=dims(72, 24, 88, 24), pad_mobile=dims(48, 20, 64, 20), tag="header",
         divider_bottom=("waves", "#FFFFFF", 50)),
     shop_main(container(
         container(widget("woocommerce-purchase-summary", SUMMARY_TEXTS, title="Bestelling (Elementor Pro Purchase Summary)"),
                   title="Bestelling", width=60),
         container(
             card(eyebrow("Wat gebeurt er nu?"),
                  next_step("far fa-envelope", "Bevestiging per e-mail",
                            small("<p>Je krijgt binnen een paar minuten een e-mail met je bestelling en de factuur.</p>"), key="mail"),
                  next_step("fas fa-file-invoice", "Betaal je op factuur?",
                            small("<p>Maak het bedrag binnen 14 dagen over, met je bestelnummer erbij, naar:</p>"),
                            option_field("iban", tag="p", color="text", size_px=15, fmt="<strong>%s</strong> t.n.v. Stichting Sampark"),
                            key="factuur"),
                  next_step("far fa-calendar-check", "Ingeschreven voor een evenement?",
                            small("<p>Vlak voor het evenement sturen we je de praktische informatie.</p>"), key="evenement"),
                  next_step("fas fa-wine-bottle", "Wijn besteld?",
                            small("<p>Kies je voor afhalen, dan maken we een afspraak. Bij bezorgen hoor je van ons wanneer de wijn komt.</p>"),
                            key="wijn"),
                  title="Wat gebeurt er nu", pad=28, gap_px=14),
             card(eyebrow("Goed om te weten"),
                  small("<p>Stichting Sampark is een ANBI. Je gift is daardoor fiscaal aftrekbaar.</p>"),
                  option_field("rsin", tag="p", color="text", size_px=14, fmt="RSIN %s"),
                  heading("Vragen over je bestelling?", "h3", size_px=19, color="text"),
                  option_field("telefoon", tag="p", color="text", size_px=15),
                  option_field("email", tag="p", color="text", size_px=15),
                  title="Goed om te weten", pad=28, gap_px=8),
             title="Wat nu (rechts)", width=36, gap_px=20),
         title="Bestelling en vervolg", direction="row", gap_px=40, align="flex-start", justify="space-between")),
     section(
         section_head("Nog meer doen?", "Steun Sampark het hele jaar",
                      "Met een sponsorpakket of een vaste gift help je de scholen structureel."),
         container(jet_grid("pakketkaart", "q_pakketten", 3, "sponsorpakketten"),
                   title="Sponsorpakketten", bg_global="658acb6", radius=20, pad=dims(32), pad_mobile=dims(20),
                   css_classes="sp-hide-empty"),
         container(button("Doneer", "/steun-ons/doneren/"), button("Bekijk de evenementen", "/evenementen/", style="outline"),
                   title="Knoppen", direction="row", gap_px=12, wrap=True, mobile_column=False),
         title="Nog meer doen", gap_px=28),
     css="bedankt",
     seo=("Bedankt voor je bestelling | Stichting Sampark", ""))


# BETALING MISLUKT ------------------------------------------------------------------
# De snippet betaling-mislukt.php stuurt de bedankpagina hierheen als de bestelling mislukt of geannuleerd is;
# de shortcode toont de bestelling met de knop "Opnieuw betalen".
page("betaling-mislukt", "Betaling mislukt",
     container(
         container(eyebrow("Betaling niet gelukt"),
                   heading("Je betaling is niet gelukt", "h1", color="primary", typo="accent", size_px=52),
                   text("<p>Geen zorgen: er is niets afgeschreven en je bestelling is bewaard. "
                        "Je kunt het meteen nog een keer proberen.</p>", size_px=18),
                   title="Kop", boxed=True, gap_px=10, extra={"boxed_width": size(1140)}),
         title="Paginakop", bg_global="658acb6", pad=dims(72, 24, 88, 24), pad_mobile=dims(48, 20, 64, 20), tag="header",
         divider_bottom=("waves", "#FFFFFF", 50)),
     shop_main(container(
         container(heading("Je bestelling", "h2", color="primary", size_px=28),
                   widget("shortcode", {"shortcode": "[sampark_betaling_mislukt]"}, title="Bestelling (snippet betaling-mislukt)"),
                   title="Bestelling", width=60, bg="#F6F6F6", radius=10, pad=dims(28), gap_px=16),
         container(
             card(eyebrow("Hoe kan dat?"),
                  next_step("fas fa-ban", "Betaling afgebroken",
                            small("<p>Je hebt in de bank-app of bij iDEAL op annuleren of terug gedrukt.</p>"), key="afgebroken"),
                  next_step("far fa-clock", "Te lang gewacht",
                            small("<p>Na een paar minuten verloopt een betaling vanzelf.</p>"), key="verlopen"),
                  next_step("fas fa-university", "Geweigerd door de bank",
                            small("<p>Bijvoorbeeld door een limiet of onvoldoende saldo. Probeer een andere rekening "
                                  "of kies voor betalen op factuur.</p>"), key="geweigerd"),
                  title="Hoe kan dat", pad=28, gap_px=14),
             card(eyebrow("Lukt het niet?"),
                  small("<p>Neem contact met ons op, dan helpen we je verder.</p>"),
                  option_field("telefoon", tag="p", color="text", size_px=15),
                  option_field("email", tag="p", color="text", size_px=15),
                  title="Hulp", pad=28, gap_px=8),
             title="Uitleg (rechts)", width=36, gap_px=20),
         title="Bestelling en uitleg", direction="row", gap_px=40, align="flex-start", justify="space-between")),
     css="betaling-mislukt",
     seo=("Betaling mislukt | Stichting Sampark", ""))


def write_templates():
    out = OUT.parent / "templates"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    for t in TEMPLATES:
        doc = {"version": "0.4", "title": t["title"], "type": t["type"], "key": t["key"],
               "conditions": t["conditions"], "content": t["content"], "page_settings": {}}
        (out / f"{t['key']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

# ---------------------------------------------------------------- schrijven


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for i, p in enumerate(PAGES):
        doc = {"version": "0.4", "title": p["title"], "type": "page", "slug": p["slug"],
               "parent": p["parent"], "menu_order": i, "seo": p["seo"], "content": p["content"],
               "page_settings": {"hide_title": "yes"}, "template": p["template"]}
        if p["css"]:
            doc["page_settings"]["custom_css"] = (OUT.parent / "css" / f"{p['css']}.css").read_text()
        (OUT / f"{p['slug']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    write_listings()
    write_templates()
    (OUT.parent / "content.json").write_text(json.dumps(content_json(), ensure_ascii=False, indent=1))
    print(f"{len(PAGES)} pagina's en {len(LISTINGS)} listings geschreven naar {OUT.parent}")


if __name__ == "__main__":
    main()
