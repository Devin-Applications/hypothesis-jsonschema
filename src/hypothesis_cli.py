#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from typing import Dict, Any

from hypothesis import given, settings, strategies as st
from hypothesis_jsonschema import from_schema

def load_schema(schema_input: str) -> Dict[str, Any]:
    """Load schema from a file or parse it as a JSON string."""
    print(f"Attempting to load schema from: {schema_input}")
    try:
        with open(schema_input, 'r') as f:
            schema = json.load(f)
            print(f"Successfully loaded schema from file: {schema_input}")
            return schema
    except FileNotFoundError:
        try:
            schema = json.loads(schema_input)
            print("Successfully parsed inline JSON schema")
            return schema
        except json.JSONDecodeError:
            raise ValueError(f"Invalid schema: {schema_input}")

def limit_complexity(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Limit the complexity of the schema to generate simpler instances."""
    if isinstance(schema, dict):
        for key, value in list(schema.items()):
            if key == "type" and value == "array":
                schema["maxItems"] = min(schema.get("maxItems", 10), 5)
            elif key == "type" and value == "object":
                schema["maxProperties"] = min(schema.get("maxProperties", 10), 5)
            elif key == "type" and value in ["string", "number", "integer"]:
                schema["maxLength"] = min(schema.get("maxLength", 100), 20)
            elif isinstance(value, (dict, list)):
                schema[key] = limit_complexity(value)
    elif isinstance(schema, list):
        return [limit_complexity(item) for item in schema]
    return schema

def generate_json_instances(schema: Dict[str, Any], num: int, seed: int) -> None:
    """Generate and print JSON instances conforming to the schema."""
    print(f"Generating {num} JSON instances with seed {seed}")
    print(f"Using schema: {json.dumps(schema, indent=2)}")
    limited_schema = limit_complexity(schema)
    strategy = from_schema(limited_schema)

    print("Starting instance generation")
    @settings(max_examples=num, deadline=None)
    @given(strategy)
    def print_instance(instance):
        print(f"Generated instance: {json.dumps(instance)}")

    print_instance()
    print("Finished instance generation")

def run_test_script(schema: Dict[str, Any], num: int, script: str) -> None:
    """Generate JSON instances, write to file, and run test script."""
    print(f"Running test script: {script}")
    print(f"Generating {num} test instances")
    limited_schema = limit_complexity(schema)
    strategy = from_schema(limited_schema)

    print("Starting test execution")
    @settings(max_examples=num, deadline=None)
    @given(strategy)
    def test_instance(instance):
        print(f"Generated test instance: {json.dumps(instance)}")
        with open('testcase.json', 'w') as f:
            json.dump(instance, f)

        print(f"Executing test script: {script} testcase.json")
        result = subprocess.run([script, 'testcase.json'], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Test script failed with output:\n{result.stdout}\n{result.stderr}")
            raise AssertionError("Test script failed")
        else:
            print("Test script executed successfully")

    test_instance()
    print("Finished test execution")

def main():
    parser = argparse.ArgumentParser(description="Generate JSON instances from a schema.")
    parser.add_argument("schema", help="JSON schema (file path or inline JSON)")
    parser.add_argument("--num", type=int, default=100, help="Number of instances to generate")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--script", help="Test script to run on generated instances")

    args = parser.parse_args()
    print(f"Received arguments: schema={args.schema}, num={args.num}, seed={args.seed}, script={args.script}")

    try:
        schema = load_schema(args.schema)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.seed is not None:
        print(f"Setting random seed to {args.seed}")
        st.random.seed(args.seed)

    try:
        if args.script:
            run_test_script(schema, args.num, args.script)
        else:
            generate_json_instances(schema, args.num, args.seed)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting CLI execution")
    main()
    print("CLI execution completed")
