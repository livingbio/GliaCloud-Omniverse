# Changelog

Graph Editor Example

## [1.0.22] - 2023-06-23
### Changed
- Copied preview texture images local to the ext and updated their paths in nodes.py.

## [1.0.21] - 2023-06-12
### Added
- Added example for OmniNote, to help with tests.

## [1.0.20] - 2023-02-02
### Fixed
- Ensure application editor menu exists before attempting to add an entry to this extension to it.

## [1.0.19] - 2022-12-07
### Fixed
- The window turns to black when it is closed when it's moved to become an external window

## [1.0.18] - 2022-10-20
### Fixed
- Increase the golden image comparison threshold for the test to fix ETM failure (OM-66335)

## [1.0.17] - 2022-10-19
### Changed
- Increased golden image threshold

## [1.0.16] - 2022-09-28
### Fixed
- Test golden images due to kit update

## [1.0.15] - 2022-07-27
### Fixed
- description check before calling

## [1.0.14] - 2022-06-28
### Added
- zoom_min and zoom_max for the GraphView so that the zoom is not infinite

## [1.0.13] - 2022-05-17
### Changed
- Update test images

## [1.0.12] - 2022-05-06
### Fixed
- Make sure DescendantGetter only works for Node or Port type input, but not backdrop

## [1.0.11] - 2022-04-07
### Fixed
- Compound node deletion when changed compound node with breadcrumbs selection
### Added
- tests

## [1.0.10] - 2022-03-30
### Changed
- update repo_build and repo-licensing

## [1.0.9] - 2022-03-24
### Fixed
- fixed the compound connection issue due to the port name

## [1.0.8] - 2022-02-23
### Changed
- change the simple model to use preview property overriding base GraphModel API instead of creating cutomized preview_data

## [1.0.7] - 2022-02-22
### Changed
- Add subscription for QuickSearch, so to reflect changes when `omni.kit.window.quicksearch` is loaded or unloaded

## [1.0.6] - 2022-01-05
### Changed
- Dependency to QuickSearch is optional because it depends on USD. We don't need
  the dependency to USD here.

## [1.0.5] - 2021-12-22
### Changed
- Added serialization for node expansion states, backdrop nodes color and size
- Fixed issue that ports are created twice from default and json file
- Fixed default subports are not cached
- Fixed default subports has the wrong path
- Fixed pop up dialog window is not updated
- Cleaned up examples with mode data and nodes
- Fixed the issue while deleting the Input/Output node will delete the entire compound node
- Fixed get_next_free_name method

## [1.0.4] - 2021-12-20
### Changed
- Fix backdrop deletion

## [1.0.3] - 2021-12-15
### Changed
- Remove irrelevant tests

## [1.0.2] - 2021-12-15
### Changed
- Minor changes

## [1.0.1] - 2021-12-14
### Added
- Used connection on top for the GraphView
- Add selection deletion for context menu
- Fixed quick search enter action
- Enabled ui_name save/load for label renaming
- Fixed connected_ports return value

## [1.0.0] - 2021-12-10
### Added
- initial commit for a graph editor example using omni.kit.graph.editor.core
- a graph example which allows switching among different graph delegates: omni.kit.graph.delegate.modern, omni.kit.graph.delegate.default and omni.kit.graph.delegate.neo
