#!/usr/bin/env python3
import argparse
import json
import sys
import time
import itertools
import requests


def main():
    # Main parser for the default 'run' command and global options
    parser = argparse.ArgumentParser(
        prog="bp",
        description="Bug Bounty Platform CLI. Default command is 'run'.",
        add_help=False,  # We will add it back later to control order
    )

    # Arguments for the 'run' command
    run_group = parser.add_argument_group("Run Command Arguments")
    run_group.add_argument(
        "--api", default="http://localhost:8000", help="Backend API URL"
    )
    run_group.add_argument("--project", help="Project name")
    run_group.add_argument(
        "--type", choices=["attack_surface", "sca", "smart_contract"]
    )
    run_group.add_argument(
        "--url", help="Target URL (attack_surface) or repo path (sca)"
    )
    run_group.add_argument("--source", help="Solidity source file for smart_contract")
    run_group.add_argument(
        "--scope", nargs="*", default=[], help="Allowed domains/repos"
    )
    run_group.add_argument(
        "--no-accept", action="store_true", help="Do not accept terms (will fail)"
    )
    run_group.add_argument(
        "-w",
        "--wait",
        action="store_true",
        help="Wait for the job to complete and show results.",
    )

    # Help argument
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    subparsers = parser.add_subparsers(dest="cmd", title="Available Commands")

    # Parser for the 'status' command
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", help="Job ID to check")
    status_parser.add_argument(
        "--api", default="http://localhost:8000", help="Backend API URL"
    )

    args = parser.parse_args()

    if args.cmd == "status":
        # Handle 'status' command
        r = requests.get(f"{args.api}/jobs/{args.job_id}")
        try:
            r.raise_for_status()
        except Exception:
            print(r.text, file=sys.stderr)
            sys.exit(1)
        data = r.json()
        print("Job Status:")
        print(f"  ID: {data.get('job_id')}")
        print(f"  Project: {data.get('project_name')}")
        print(f"  Type: {data.get('job_type')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Created At: {data.get('created_at')}")
        if data.get("started_at"):
            print(f"  Started At: {data.get('started_at')}")
        if data.get("finished_at"):
            print(f"  Finished At: {data.get('finished_at')}")
    else:
        # Handle default 'run' command
        # Manually check for required arguments for the run command
        if not args.project or not args.type:
            parser.error(
                "the following arguments are required for 'run' command: --project, --type"
            )

        payload = {
            "project_name": args.project,
            "job_type": args.type,
            "accept_terms": not args.no_accept,
        }

        if args.scope:
            payload["scope"] = args.scope

        if args.type == "attack_surface":
            if not args.url:
                parser.error("--url is required for attack_surface")
            payload["target_url"] = args.url

        if args.type == "sca":
            if not args.url:
                parser.error("--url must point to local repo path for SCA")
            payload["target_url"] = args.url

        if args.type == "smart_contract":
            if not args.source:
                parser.error("--source .sol file required for smart_contract")
            payload["contract_source"] = open(args.source, "r", encoding="utf-8").read()

        r = requests.post(f"{args.api}/jobs", json=payload)
        try:
            r.raise_for_status()
        except Exception:
            print(r.text, file=sys.stderr)
            sys.exit(1)

        data = r.json()
        job_id = data.get("job_id")
        project = data.get("project_name")
        print(f"Job submitted successfully for project '{project}'.")
        print(f"Job ID: {job_id}")

        if args.wait:
            spinner = itertools.cycle(["-", "/", "|", "\\"])
            status = "pending"
            print("Waiting for job to complete...", end="", flush=True)
            while status not in ["finished", "failed"]:
                try:
                    time.sleep(1)
                    r_status = requests.get(f"{args.api}/jobs/{job_id}")
                    r_status.raise_for_status()
                    status = r_status.json().get("status")
                    print(f"\rWaiting for job to complete... {next(spinner)}", end="", flush=True)
                except (requests.RequestException, KeyboardInterrupt) as e:
                    print(f"\nAn error occurred: {e}")
                    sys.exit(1)

            print("\nJob finished.")
            # Fetch final status and display
            r_final = requests.get(f"{args.api}/jobs/{job_id}")
            final_data = r_final.json()
            print("Job Status:")
            print(f"  ID: {final_data.get('job_id')}")
            print(f"  Project: {final_data.get('project_name')}")
            print(f"  Type: {final_data.get('job_type')}")
            print(f"  Status: {final_data.get('status')}")
            print(f"  Created At: {final_data.get('created_at')}")
            if final_data.get("started_at"):
                print(f"  Started At: {final_data.get('started_at')}")
            if final_data.get("finished_at"):
                print(f"  Finished At: {final_data.get('finished_at')}")
        else:
            print(f"To check status, run: bp status {job_id}")


if __name__ == "__main__":
    main()
