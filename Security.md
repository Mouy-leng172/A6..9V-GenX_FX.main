# Security Setup and Repository Policy

This document covers two critical areas:
1. **Internal Setup**: Hardening instructions for the development and execution machine.
2. **Public Policy**: The formal vulnerability reporting process for the repository.

---

## Part 1: Internal Infrastructure Setup Guide

Implement these controls across your Linux, macOS, and Windows environments to protect your active trading keys and AI models.

### 1. Network & Remote Monitoring
*   **Zero Port Forwarding**: Never open router ports to the public internet to check your bot.
*   **Encrypted Mesh VPN**: Install **Tailscale** or **WireGuard** on your trading machines and mobile devices for secure, private remote monitoring.
*   **Dedicated VLAN**: Isolate your development machines on a separate network segment away from IoT devices and guest Wi-Fi.

### 2. Operating System Hardening
*   **Linux (Ubuntu/Debian)**: 
    *   Enable the firewall: `sudo ufw default deny incoming`, `sudo ufw default allow outgoing`, and `sudo ufw enable`.
    *   Isolate the bot process under a dedicated, non-root user account.
*   **macOS**: 
    *   Turn on FileVault full-disk encryption via System Settings.
    *   Enable the built-in firewall and set stealth mode to ignore unsolicited network probes.
*   **Windows**: 
    *   Ensure BitLocker drive encryption is active on all development drives.
    *   Run code strictly within **WSL2 (Windows Subsystem for Linux)** to isolate execution from daily web-browsing activities.

### 3. Safe AI Execution & Dependency Auditing
*   **Block Arbitrary Execution**: Never load untrusted `.pkl` (Pickle) files or raw weights. Use **`safetensors`** formats to prevent remote code execution during model loading.
*   **Automate Code Audits**: Run **`pip-audit`** weekly to scan library stacks (PyTorch, TensorFlow, CCXT, Alpaca) for known supply-chain vulnerabilities.
*   **Git Leak Prevention**: Add `.env`, `*.key`, and `config.json` to your global `.gitignore` before initializing a repository.

### 4. Exchange API & Token Guardrails
*   **Restrict Scopes**: Explicitly uncheck **"Withdrawal Allowed"** on all broker or exchange API configurations. Only check **"Read"** and **"Trade"**.
*   **IP Binding**: Bind your API tokens exclusively to your home network's static IP or your designated cloud VPN gateway IP.

---

## Part 2: Public Security Policy

## Supported Versions

The following versions of this project are actively monitored and supported with security patches.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this automated trading and AI infrastructure, please do not log a public GitHub issue. Report it using the private channel detailed below.

### Where to Report
Please email security disclosures directly to: **[INSERT_YOUR_SECURITY_EMAIL]**
If available, encrypt your message using the PGP key found here: **[INSERT_PGP_KEY_LINK_OR_ID]**

### What to Include
To help us patch the issue efficiently, please provide:
1.  A clear description of the vulnerability.
2.  Step-by-step instructions or a proof-of-concept (PoC) script to reproduce it.
3.  The estimated impact (e.g., private key extraction risk, data poisoning, trade injection).

### Our Response Timeline
*   **Initial Acknowledgement**: Within 48 hours of receipt.
*   **Status Updates**: Every 7 days during investigation and patching.
*   **Resolution Goal**: Validated vulnerabilities aim to be patched within 30 days.

### Process & Public Disclosure
1.  **Triage**: The vulnerability will be verified in an isolated environment.
2.  **Notification**: You will receive an official notification detailing if the report was accepted or declined.
3.  **Remediation**: Accepted vulnerabilities will be patched and backported to all supported versions.
4.  **Coordinated Disclosure**: A public security advisory will be issued only after users have had ample time to deploy the fix.

