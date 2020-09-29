import yaml
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("country_iso3", help="Country ISO3")
    return parser.parse_args()


def parse_yaml(filename):
    with open(filename, "r") as stream:
        config = yaml.safe_load(stream)
    return config
