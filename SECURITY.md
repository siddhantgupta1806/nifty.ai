# Security Policy

## Supported Versions

This repository is pre-1.0. Security fixes are applied to the latest mainline version.

## Reporting a Vulnerability

Open a private security advisory or contact the maintainers without posting credentials or exploit details publicly.

## Secrets

Never commit `.env`, broker API keys, OpenAlgo API keys, LLM provider keys, account identifiers, or order logs containing personal information.

## Trading Risk

Any issue that could accidentally route Analyzer/paper orders to live broker orders should be treated as security-sensitive.
