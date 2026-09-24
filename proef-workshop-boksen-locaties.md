# Proef: Workshop boksen – alleen blok "Locaties"

Doel: nieuw concept (niet post 2055 aanpassen), alleen het blok Locaties plaatsen om te testen of de connector klassieke v3-widgets kan schrijven. Niet publiceren.

## Doel
- Posttype: `aanbod` (zelfde type als 2055), status **draft**
- Titel: `Workshop boksen (concept)` (slug pas bij livegang op `workshop-boksen` zetten; 2055 bestaat al met die slug)
- Categorie `aanbod-categorie`: 62 (workshops), zoals 2055

## Blok Locaties – tekst (bron: Asana-reactie Berend, 21-08-2026, 28 woorden)
> Onze thuisbasis is Zwolle, maar we komen ook naar je toe. De workshop boksen is ook beschikbaar in Amsterdam, Rotterdam, Utrecht, Arnhem en Groningen.

Geen H2 in de briefing. Interne links naar locatiepagina's zijn niet gevraagd; optioneel na akkoord.

## Elementor-data (klassiek v3, zoals de rest van de site)
```json
[
  {
    "elType": "container",
    "settings": { "content_width": "boxed", "_title": "Locaties" },
    "elements": [
      {
        "elType": "widget",
        "widgetType": "text-editor",
        "settings": {
          "editor": "<p>Onze thuisbasis is Zwolle, maar we komen ook naar je toe. De workshop boksen is ook beschikbaar in Amsterdam, Rotterdam, Utrecht, Arnhem en Groningen.</p>"
        }
      }
    ]
  }
]
```

## Controle na plaatsen
1. Post is draft, niet zichtbaar op de front-end.
2. In de editor staat één container met één text-editor widget (geen atomic v4-element).
3. Post 2055 is ongewijzigd.
