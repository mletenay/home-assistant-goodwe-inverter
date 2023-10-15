[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## GoodWe solar inverter for Home Assistant (experimental)

Support for Goodwe solar inverters is present as native integration of [Home Assistant](https://www.home-assistant.io/integrations/goodwe/) since its release 2022.2 and is recommended for most users.

This custom component is experimental version with features not (yet) present in standard HA's integration and is intended for users with specific needs and early adopters of new features.
Use at own risk.

### Differences between HACS 0.9.9.9 and HA 2023.10

- Integration configuration parameters `Scan iterval`, `Network retry attempts`, `Network request timeout`.
- Special work modes `Eco charge mode` and `Eco discharge mode` (24/7 with defined power and SoC).
- Switch `Load Control` (for ET+ inverters).
- Services for getting/setting inverter configuration parameters

### Migration from HACS to HA

If you have been using this custom component and want to migrate to standard HA integration, the migration is straightforward. Just remove the integration from HACS (press Ignore and force uninstall despite the warning the integration is still configured). Atrer restart of Home Assistant, the standard Goodwe integration will start and all your existing settings, entity names, history and statistics should be preserved.

(If you uninstall the integration first, then uninstall HACS component and install integration back again, it will also work, but you will probably loose some history and settings since HA integration uses slightly different default entity names.)

### Documentation

Find the full documentation [here](https://github.com/mletenay/home-assistant-goodwe-inverter).
