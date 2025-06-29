import json
import os

from tesla_tou_settings import TimeOfUseSettings


def test_tesla_tou_deserialization_serialization():
    # Define the path to the JSON file
    json_file_path = os.path.join(
        os.path.dirname(__file__), "examples", "tesla_tou.json"
    )

    # Read the JSON file
    with open(json_file_path, "r") as f:
        original_json_data = json.load(f)

    # Deserialize the JSON data into TimeOfUseSettings object
    tou_settings = TimeOfUseSettings.from_dict(original_json_data)

    # Serialize the TimeOfUseSettings object back to JSON
    serialized_json_data = tou_settings.to_dict()

    # Compare the original JSON data with the serialized JSON data
    # We'll compare dictionaries directly as order might not be preserved in JSON
    assert original_json_data == serialized_json_data
