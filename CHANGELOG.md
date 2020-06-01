# Changelog
All notable changes to this project will be documented in this file.

## [1.0.0] - 20202-05-29
### Added
- Added Changelog
- Support for customizations.yaml
- Support for validating SealedSecret exists
- Generic schema validator created to validate more than just one schema type

### Deprecations
- The `--values-path` flag has been deprecated and will be removed in future releases
- The `--charts-path` flag has been deprecated and will be removed in future releases
- Discovering and injecting the latest version into a manifest has been deprecated and will be removed in future releases

### Removed
- [BREAKING] Previously deprecated flags have been removed

## [0.24.0] - 2020-04-20
### Removed
- Deprecated master manifest has been removed
- The `-in` arg is now required
