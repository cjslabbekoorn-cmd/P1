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
        title="Hero", bg_image=image_key, overlay=("#46211AE6", "#46211A1A"),
        min_height=height, align="stretch", justify="center", tag="section",
        divider_bottom=("curve", "#FFFFFF", 70),
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
                     pad_mobile=dims(80, 20, 64, 20), tag="section", divider_top=("curve", "#FFFFFF", 60))


def stat(icon_key, number, label, suffix="", width=30):
    return container(icon(icon_key, color="cf55c96", px=64), counter(number, label, suffix),
                     title=f"Cijfer · {label}", align="center", gap_px=8, width=width)


def listing(title_note, *cards, cols=3):
    """Container die het Listing Grid voorstelt; inhoud = ontwerp van het listing item."""
    w = {2: 48, 3: 31, 4: 23}[cols]
    for c in cards:
        c["settings"]["width"] = size(w, "%")
        c["settings"]["width_mobile"] = size(100, "%")
        c["settings"]["width_tablet"] = size(48 if cols > 2 else 100, "%")
    return container(*cards, title=f"LISTING · {title_note}", direction="row", wrap=True, gap_px=24,
                     extra={"flex_align_items": "stretch"})


def logo_wall(keys, bg="#FFFFFF"):
    logos = [container(image(k, height=80, radius=0, fit="contain"), title=f"Logo · {k}", bg=bg,
                       radius=999, pad=dims(24), align="center", justify="center",
                       extra={"width": size(140), "width_tablet": size(130), "width_mobile": size(120),
                              "min_height": size(140), "min_height_tablet": size(130),
                              "min_height_mobile": size(120)})
             for k in keys]
    return container(*logos, title="LISTING · sponsors (actief=true, sorteer op niveau + volgorde)",
                     direction="row", wrap=True, justify="center", gap_px=20, mobile_column=False)


def news_cards():
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
                   *[media_card(k, d, t, b, l) for k, d, t, b, l in items])


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


def page(slug, title, *content, parent=None, seo=None):
    PAGES.append({"slug": slug, "title": title, "parent": parent, "seo": seo, "content": list(content)})


# HOME -------------------------------------------------------------------
wine_badge = container(
    widget("icon-box", {
        "selected_icon": {"value": {"url": "{{img:icon_wijn}}", "id": "{{imgid:icon_wijn}}"}, "library": "svg"},
        "position": "left", "position_mobile": "left", "position_tablet": "left", "text_align_mobile": "left", "title_text": "Wijnactie", "description_text": "Rood, wit en alcoholvrij",
        "title_size": "p", "icon_size": size(44), "icon_space": size(14),
        "link": {"url": "/evenementen/wijnactie/"},
        "title_typography_typography": "custom", "title_typography_font_size": size(22),
        # donkerbruin op oranje: wit/crème op #ED7404 haalt geen 4,5:1 contrast
        "__globals__": {"primary_color": g_color("text"), "title_color": g_color("text"),
                        "description_color": g_color("text"), "title_typography_typography": g_type("accent")},
    }),
    title="Campagnebadge (Dynamic Visibility: Options › campagne aan)", bg_global="secondary", radius=999,
    pad=dims(14, 28, 14, 20), extra={"width": size(300), "width_mobile": size(280), "flex_align_self": "center"})

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
         title="Transparantie", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50)),
     section(
         container(section_head("Doe mee", "Steun ons met plezier",
                                "Een dag achter het stuur, een balletje slaan of een glas wijn met vrienden: bij Sampark begint hulp vaak met plezier."),
                   button("Alle evenementen", "/evenementen/", style="outline", icon=True, nowrap=True),
                   direction="row", justify="space-between", align="flex-end", gap_px=24),
         listing("evenementen · status IN (aangekondigd, open, doorlopend) · sorteer datum_start ASC · max 3",
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
         title="Sponsors", bg_global="cf55c96", divider_top=("curve", "#FFFFFF", 50),
         divider_bottom=("curve", "#FFFFFF", 50)),
     section(
         container(section_head("Nieuws", "Het laatste uit India en Nederland"),
                   button("Alle nieuwsberichten", "/nieuws/", style="outline", icon=True, nowrap=True),
                   direction="row", justify="space-between", align="flex-end", gap_px=24),
         news_cards(),
         title="Nieuws"),
     seo=("Stichting Sampark | Help een kind in India naar school",
          "Sinds 2007 geeft Stichting Sampark kinderen in India toegang tot onderwijs. Doneer, sponsor een kind of doe mee aan onze evenementen."))

# ONS WERK ---------------------------------------------------------------


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
         section_head("Scholen in Budaun", "Vier scholen op het platteland",
                      "Rond Budaun maken we vier scholen mogelijk. Door te bouwen, te renoveren en te blijven investeren groeit elke school mee met de kinderen."),
         listing("projecten · projecttype=school · sorteer titel",
                 project_card("proj_khukdi", "407 leerlingen · Nieuwbouw", "Khukdi School", "Van vijf lokalen naar vijftien.", "/ons-werk/khukdi-school/"),
                 project_card("proj_kundanpur", "329 leerlingen · Renovatie", "Kundanpur School", "Waar het begint.", "/ons-werk/kundanpur-school/"),
                 project_card("proj_bilsi", "359 leerlingen · Renovatie", "Bilsi School", "Leren begint bij de leraar.", "/ons-werk/bilsi-school/"),
                 project_card("proj_ghadia", "482 leerlingen · Renovatie", "Ghadia School", "Een school midden op het platteland.", "/ons-werk/ghadia-school/"),
                 cols=4),
         title="Scholen", extra={"_element_id": "scholen"}),
     section(
         section_head("Opleidingen in New Delhi", "Een vak leren in de stad",
                      "Veel jongeren trekken van het platteland naar de stad en belanden zonder werk in de sloppenwijken. Met gerichte opleidingen geven we ze een eerlijke kans op een baan."),
         listing("projecten · projecttype=opleiding",
                 project_card("proj_computer", "20 studenten", "Computerspecialist", "Digitale vaardigheden voor een kantoorbaan.", "/ons-werk/computerspecialist/"),
                 project_card("proj_modinette", "29 studenten", "Modinette", "Kleding maken en een eigen inkomen.", "/ons-werk/modinette/"),
                 project_card("proj_beauty", "24 studenten", "Schoonheidsspecialiste", "Een vak met vraag in de stad.", "/ons-werk/schoonheidsspecialiste/")),
         title="Opleidingen", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50),
         divider_bottom=("curve", "#FFFFFF", 50), extra={"_element_id": "opleidingen"}),
     section(
         section_head("Initiatieven", "Kleine projecten, groot verschil"),
         listing("projecten · projecttype=initiatief",
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

# EVENEMENTEN -------------------------------------------------------------
page("evenementen", "Evenementen",
     page_hero("Evenementen", "Rijd mee in de rally, sla een balletje voor het goede doel of bestel je wijn bij ons. Elke deelname brengt een kind dichter bij de schoolbank.",
               "hero_events", eye="Doe mee"),
     section(
         section_head("Binnenkort", "Schrijf je in"),
         listing("evenementen · status IN (aangekondigd, open, vol) · sorteer datum_start ASC",
                 event_card("padel", "Inschrijving open"), event_card("rally", "Aangekondigd"),
                 event_card("golf", "Aangekondigd")),
         title="Binnenkort"),
     section(
         section_head("Het hele jaar", "Altijd mogelijk"),
         listing("evenementen · status=doorlopend", event_card("wijn", "Het hele jaar"),
                 event_card("reis", "Op aanvraag"), cols=2),
         title="Doorlopend", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50),
         divider_bottom=("curve", "#FFFFFF", 50)),
     section(
         section_head("Terugblikken", "Zo was het vorig jaar"),
         news_cards(),
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
         title="ANBI en vragen", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50)),
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
             card(eyebrow("Superforms · product Eenmalige donatie"), heading("Doneer nu", "h3", size_px=30),
                  text("<p>Op de live site staat hier het Superforms-formulier van het product <strong>Eenmalige donatie</strong> (via een Woo product-shortcode of een knop naar het product met het bedrag als URL-parameter).</p>"),
                  container(button("€ 10", "/product/donatie/?bedrag=10", style="outline"),
                            button("€ 25", "/product/donatie/?bedrag=25", style="outline"),
                            button("€ 50", "/product/donatie/?bedrag=50", style="outline"),
                            button("€ 100", "/product/donatie/?bedrag=100", style="outline"),
                            direction="row", wrap=True, gap_px=10, mobile_column=False),
                  button("Ander bedrag", "/product/donatie/", full=True),
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
         listing("WC Product Query · product_cat=sponsorpakket · sorteer prijs DESC",
                 card(eyebrow("€ 2.500 per jaar"), heading("Sona (Goud)", "h3", size_px=28),
                      icon_list(["Alles uit Peetal", "Deelname golftoernooi én Sampark Rally", "Naamsvermelding bij het gekozen evenement"]),
                      button("Kies Sona", "/product/sona-goud/", full=True), title="Kaart · Sona", bg="e64974d"),
                 card(eyebrow("€ 1.750 per jaar"), heading("Chandee (Zilver)", "h3", size_px=28),
                      icon_list(["Alles uit Peetal", "Deelname golftoernooi óf Sampark Rally", "Naamsvermelding bij dat evenement"]),
                      button("Kies Chandee", "/product/chandee-zilver/", full=True), title="Kaart · Chandee", bg="e64974d"),
                 card(eyebrow("€ 500 per jaar"), heading("Peetal (Brons)", "h3", size_px=28),
                      icon_list(["Naamsvermelding op onze website", "Klikbare Sampark-banner voor je eigen site", "Sampark-uitingen voor je MVO"]),
                      button("Kies Peetal", "/product/peetal-brons/", full=True), title="Kaart · Peetal", bg="e64974d")),
         title="Pakketten", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50), divider_bottom=("curve", "#FFFFFF", 50)),
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
            ("2019", "Nieuwbouw Khukdi", "De nieuwe school met vijftien lokalen opent haar deuren."),
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
         title="Bestuur", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50), divider_bottom=("curve", "#FFFFFF", 50)),
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
         title="Documenten", bg_global="658acb6", divider_top=("curve", "#FFFFFF", 50)),
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

# ---------------------------------------------------------------- schrijven


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for i, p in enumerate(PAGES):
        doc = {"version": "0.4", "title": p["title"], "type": "page", "slug": p["slug"],
               "parent": p["parent"], "menu_order": i, "seo": p["seo"], "content": p["content"],
               "page_settings": {"hide_title": "yes"}}
        (OUT / f"{p['slug']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    print(f"{len(PAGES)} pagina's geschreven naar {OUT}")


if __name__ == "__main__":
    main()
