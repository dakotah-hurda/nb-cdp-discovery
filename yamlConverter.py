import yaml
from dict2xml import dict2xml
import json
import pprint

def convert_yaml_output():

    yaml_input_file = './output/cdp-dump.yaml'
    xml_output_file = './output/cdp-dump.xml'
    json_output_file = './output/cdp-dump.json'

    with open(yaml_input_file, "r") as f:
        yaml_output = yaml.safe_load(f)

    xml_output = dict2xml(yaml_output)
    json_output = json.dumps(yaml_output)

    with open(xml_output_file, "w+") as f:
        f.write(xml_output)

    with open(json_output_file, "w+") as f:
        f.write(json_output)

