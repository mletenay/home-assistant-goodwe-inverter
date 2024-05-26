[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mletenay)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
![GitHub Release](https://img.shields.io/github/v/release/mletenay/home-assistant-goodwe-inverter)

## GoodWe solar inverter for Home Assistant (experimental)

Support for Goodwe solar inverters is present as native integration of [Home Assistant](https://www.home-assistant.io/integrations/goodwe/) since its release 2022.2 and is recommended for most users.

This custom component is experimental version with features not (yet) present in standard HA's integration and is intended for users with specific needs and early adopters of new features.
Use at own risk.

### Differences between this HACS and native HA integration

- Support for Modbus/TCP
- Special work modes `Eco charge mode` and `Eco discharge mode` (24/7 with defined power and SoC).
- Network configuration parameters `Scan iterval`, `Network retry attempts`, `Network request timeout`.
- Switch `Export Limit Switch`.
- Switch `Load Control` (for ET+ inverters).
- Switch and SoC/Power inputs for `Fast Charging` functionality.
- `Start inverter` and `Stop inverter` buttons for grid-only inverters.
- Services for getting/setting inverter configuration parameters

### Migration from HACS to HA

If you have been using this custom component and want to migrate to standard HA integration, the migration is straightforward. Just remove the integration from HACS (press Ignore and force uninstall despite the warning the integration is still configured). Afrer restart of Home Assistant, the standard Goodwe integration will start and all your existing settings, entity names, history and statistics should be preserved.

(If you uninstall the integration first, then uninstall HACS component and install integration back again, it will also work, but you will probably loose some history and settings since HA integration uses slightly different default entity names.)

### Documentation

Find the full documentation [here](https://github.com/mletenay/home-assistant-goodwe-inverter).
