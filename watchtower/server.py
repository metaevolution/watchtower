import argparse
import signal
import sys
from watchtower.config import AppConfig
from watchtower.testcases import TestSuite

from watchtower.logging_config import logger


from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

test_suite = TestSuite()
logger.info("Tests loaded")

@app.route("/")
def root():
    return ""


@app.route("/api/scoreboard", methods=["GET"])
def get_data():
    return jsonify(test_suite.to_json())


@app.route("/api/statelog", methods=["GET"])
def get_statelog():
    return jsonify(test_suite.state_log.to_json())


def signal_handler(sig, frame):
    print("Shutting down gracefully...")
    sys.exit(0)


def run():
    parser = argparse.ArgumentParser(
        prog="WatchTower API Server",
        description="WatchTower is a flexable/lightweight system monitoring dashboard.",
        epilog="Text at the bottom of help",
    )
    parser.add_argument(
        "-c", "--config", help="Watchtower config file. Default: watchtower.conf"
    )
    args = parser.parse_args()

    logger.info("Started WatchTower server")

    appconfig = AppConfig(args.config) if args.config else AppConfig()

    test_suite.initialize_tests(appconfig.config)

    signal.signal(signal.SIGINT, signal_handler)

    
    test_suite.start()
    logger.info("Scheduler started")

    logger.info("Starting web server...")
    app.run(host="0.0.0.0")


if __name__ == "__main__":
    run()