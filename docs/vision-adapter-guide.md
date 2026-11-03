# SceneSignal — Vision Adapter Guide

This guide explains how to implement a concrete `VisualAnalysisPort` adapter for SceneSignal.

## Requirements & Rules
1. **No hidden retries:** Adapters must not retry internally upon provider failures. Application-level retry policies handle transient errors.
2. **Typed exceptions:** Raise typed errors (`ProviderTimeout`, `ProviderRateLimited`, `ProviderUnavailable`, `ProviderResponseInvalid`, `ProviderConfigurationError`) when provider calls fail.
3. **Secrets by reference:** Never log, print, or commit API keys or credentials. Use reference configuration (`provider_config_ref`).
4. **Untrusted responses:** All output from vision providers is treated as untrusted data and validated by `validate_response`.
