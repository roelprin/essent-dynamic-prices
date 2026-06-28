# Changelog

## v3.4.0

Energy Intelligence release.

### Added

- New `advisor.py` module.
- New `Energy advisor` sensor.
- New `Energy score` sensor.
- New `Wachttijd advies` sensor.
- New `Potentiële besparing` sensor.
- Advisor attributes:
  - score
  - rating
  - confidence
  - reasons
  - recommended devices
  - current rank
  - difference to average
  - difference to cheapest hour
  - next hour difference
  - cheapest block
  - potential saving

### Notes

This release introduces the first version of the central Energy Advisor logic.


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
