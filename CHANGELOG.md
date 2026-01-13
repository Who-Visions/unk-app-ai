# Changelog

All notable changes to the **Unk Agent** project will be documented in this file.

## [Unreleased]

## [3.1.0] - 2026-01-13
### Added
- **Gemini 3.0 Integration**: Switched core agent to `gemini-3-flash-preview` and `gemini-3-pro-preview` for "Future Systems" capability.
- **Enterprise Voice UI**: Implemented `ChatUI` class using `rich.live` for smooth, streaming text responses in the terminal.
- **Natural Voice Persona**: Removed robotic digit formatting rules; tuned heuristic prompting to ensure natural pronunciation of years ("Twenty Twenty-Six") and Roman Numerals ("Super Bowl Sixty").
- **Voice Profile**: Standardized on `Sadachbia` voice profile in `UnkVoiceService`.

### Changed
- **Architecture Refactor**: Modularized `chat_with_unk.py` into `UnkAgentApp`, `AudioEngine`, and `ChatUI` classes for better maintainability and testability.
- **Code Quality**: Achieved Pylint score of **8.54/10** by resolving linting errors, cyclic dependencies, and global variable misuse.
- **Latency Optimization**: Optimized `agent_stream_wrapper` to properly handle asynchronous generators, reducing TTS latency.

### Fixed
- **Audio Device Setup**: Resolved `NameError` in `setup_devices` by correctly initializing and returning device indices.
- **Stream Iteration**: Fixed `TypeError: 'async_generator' object is not iterable` in the main chat loop.
- **Roman Numeral Pronunciation**: Added explicit rule to `unk_prompt` to read "LX" as "Sixty".

## [2.5.0] - 2026-01-12
### Added
- **LoreDB Triple Sync**: Implemented "Triple Sync" architecture for `LoreDB`, synchronizing memories to SQLite (local), Firestore (real-time), and BigQuery (analytics).
- **Notion Integration**: Added bi-directional sync with Notion for "Metrics Log" and human-readable memory storage.

### Changed
- **Service Deployment**: Migrated deployment scripts (`deploy.py`) to support Cloud Run with `gemini-2.0-flash` defaults.

## [2.0.0] - 2026-01-05
### Added
- **Cognitive Tiering**: Introduced tiered model architecture (`Flash`, `Pro`, `Thinking`).
- **Firebase Integration**: Full integration with Firebase Auth and Firestore for user management and secure data storage.
- **Web Tools**: Built `skills/web_tools.py` for real-time web search and intelligence gathering.

## [1.0.0] - 2025-11-30
### Added
- **Unk App AI Inception**: Initial repository creation and core architecture planning.
- **Basic Chat**: Simple CLI chat interface (v1.0).
- **Skills System**: Initial framework for pluggable skills.
