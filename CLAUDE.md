# P1: klantwerk van Positie1

Deze repository bevat ontwikkelwerk voor klanten van Positie1. Elke klant heeft een eigen map onder `klanten/`, met een eigen `CLAUDE.md` die voor die klant voorgaat.

## Werkafspraken

- Voer gesprekken, commitberichten en documentatie in het Nederlands.
- Werk altijd binnen één klantmap per taak. Is niet duidelijk voor welke klant een taak is, vraag het dan.
- Wijzig nooit rechtstreeks iets op een live site zonder expliciete opdracht. Laat eerst zien wat er verandert.
- Geheimen (FTP, API-sleutels, wachtwoorden) komen nooit in Git. Zet ze per klant in `klanten/<klant>/.env.deploy` (staat in `.gitignore`).

## Structuur

```
klanten/<klant>/
  CLAUDE.md      klantspecifieke context: site, platform, hosting, wat wel/niet mag
  code/          eigen code die naar de site gaat (bv. child-thema, eigen plugin)
  docs/          voorstellen, audits en notities
```

## Deployen

De Claude Code-cloud laat alleen HTTPS naar buiten toe, dus FTP/SFTP werkt daar niet. Deployen gebeurt vanaf de Mac (Claude Code lokaal) of via een HTTPS-route zoals de WordPress REST API, als de klant die heeft opengezet.
