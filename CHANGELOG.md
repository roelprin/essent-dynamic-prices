# Changelog

## v3.3.0

Energy Advice release.

### Added

- New `Energy advies` sensor.
- Simple dynamic advice based on:
  - current electricity price
  - next hour price
  - day average
  - cheapest hour
  - cheapest block
  - negative market price
- Useful attributes for dashboards and automations:
  - difference to average
  - difference to cheapest hour
  - next hour price difference
  - current market price
  - cheapest block


## v3.1.1

Bugfix release.

### Fixed

- Removes obsolete experimental entities from older v1/v2 builds during config-entry migration.
- Prevents removed experimental sensors from staying visible as `Unavailable` after upgrading to the compact v3 entity model.

### Notes

After installing this update through HACS, restart Home Assistant. The migration runs during startup.


## v3.1.0

Professionalization release.

### Added

- Repository logo asset.
- Expanded README with installation and dashboard examples.
- Dutch and English translation files.
- GitHub Actions workflow for Hassfest and HACS validation.
- Improved HACS metadata.
- Better release documentation.

### Notes

- The Home Assistant integration page may still show `icon not available`. For custom integrations, the official integration icon is normally handled through the Home Assistant brands repository. The local logo is used for repository documentation and future HACS presentation.

## v3.0.0

Refactor release.

### Added

- API client module.
- Coordinator module.
- Shared entity base class.
- Data helper module.
- Diagnostics support.
- Compact entity model.
