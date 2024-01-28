# WatchTower

WatchTower is a flexable/lightweight system monitoring dashboard.

# Overview

WatchTower functions as a client/server application, enabling numerous clients to access test results from a central API server. The API server is responsible for executing tests and delivering the corresponding results.

## Example Watchtower Console Output

### Overall Status

![WatchTower Console Overall Status](https://raw.githubusercontent.com/metaevolution/watchtower/main/docs/images/Screenshot3.png)

### Table View

![WatchTower Console Table View](https://raw.githubusercontent.com/metaevolution/watchtower/main/docs/images/Screenshot2.png)

### Tree View

![WatchTower Console Tree View](https://raw.githubusercontent.com/metaevolution/watchtower/main/docs/images/Screenshot1.png)

# Monitor Types

- Ping - Check if target is pingable
- TCP - Check if a specific TCP port is open
- DNS - Verify target resolves in DNS
- HTTP Status - Check if remote website returns specific HTTP response codes
- Browser - Loads a remote website using selenium webdriver
- SpeedTest - Tests the upload/download speed from the WatchTower API server to the internet.

## Installation

### Optional: Use Python Virtual Environment

```bash
# python3 -m venv .venv
# source .venv/bin/activate
```

### Installation

```bash
# pip install .
```

## Usage

### Start API server with sample config

```bash
# watchtower-server -c watchtower.conf.sample
```
OR
```bash
# python -m watchtower.server -c watchtower.conf.sample
```

Note: By default WatchTower uses Flask's built-in development web server listening on localhost:5000.

### In another terminal, start the client and connect to the server running on the same machine

```bash
# watchtower-console -u http://127.0.0.1:5000
```
OR 
```bash
# python -m watchtower.console -u http://127.0.0.1:5000
```
