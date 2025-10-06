import os, json, argparse, pandas as pd
from dotenv import load_dotenv

OPENFLOW_TITLE = "OpenFlow (Native CDC via Log)"

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Generate F.01 metadata files aligned to Confluence and OpenFlow CDC correction.")
    ap.add_argument("--subcomponents", default="data/F01_subcomponents.json")
    ap.add_argument("--out-dir", default="data")
    args = ap.parse_args()

    with open(args.subcomponents) as f:
        subs = json.load(f)
    # Build options set per discovered subcomponent code
    def options_for(sc_code):
        if sc_code.endswith(".1"):  # CDC
            return [
                ("A", "SaaS CDC Connector", "Medium", "✅","✅","✅", "Managed CDC (e.g., Fivetran/HVR) capturing source changes into Snowflake."),
                ("B", OPENFLOW_TITLE,       "High",   "❌","✅","✅", "Native Snowflake CDC via log using OpenFlow."),
                ("C", "Custom CDC Pipeline (Non-Native)", "High", "❌","⚙️","✅", "External/custom log-shipping & apply; higher control & complexity.")
            ]
        if sc_code.endswith(".2"):  # API Ingestion
            return [
                ("A", "External Functions (Pull APIs)",  "Medium", "❌","✅","✅", "Call external REST APIs to ingest data directly into Snowflake."),
                ("B", "API Gateway → Stage → Load",      "High",   "❌","⚙️","✅", "Receive pushes; land to cloud storage; load via Snowflake."),
                ("C", "No/Minimal API (MVP)",            "Low",    "✅","❌","❌", "Defer API-based ingestion at MVP; use file/SaaS connectors initially.")
            ]
        if sc_code.endswith(".3"):  # Batch
            return [
                ("A", "Snowpipe (Auto-ingest Files)",    "Low",    "✅","✅","✅", "Auto-load files from cloud storage using notifications."),
                ("B", "COPY INTO (Scheduled Batch)",     "Low",    "✅","✅","✅", "Scheduled COPY INTO for predictable loads."),
                ("C", "Snowpipe Streaming (Files→Rows)", "Medium", "❌","⚙️","✅", "Stream rows when file latency is unacceptable.")
            ]
        if sc_code.endswith(".4"):  # Streaming
            return [
                ("A", "Kafka/Kinesis → Snowflake",       "Medium", "❌","✅","✅", "Use connectors/ingest services to push events."),
                ("B", "Snowpipe Streaming",              "Medium", "❌","✅","✅", "Direct row streaming to Snowflake with low latency."),
                ("C", "Event Hub / PubSub → Stage → Load","High",  "❌","⚙️","✅", "Cloud queues → durable stage → micro-batch load.")
            ]
        if sc_code.endswith(".5"):  # SaaS/ELT
            return [
                ("A", "SaaS ELT Connector",              "Low",    "✅","✅","✅", "Managed ELT for common SaaS sources."),
                ("B", "External ETL/ELT Tool",           "Medium", "❌","✅","✅", "Matillion/ADF/dbt jobs; richer scheduling/transform."),
                ("C", "Custom Ingestion Service",        "High",   "❌","⚙️","✅", "Bespoke microservice for niche sources or constraints.")
            ]
        # Default: empty
        return []

    def tasks_for(option_ref):
        t = []
        if option_ref.endswith(".1.A"):
            t += [("Initial CDC Connector Setup","Configure source/target connections and schemas in SaaS CDC.","Low","✅","✅","✅","Data Engineer",""),
                  ("Incremental Load Validation","Validate change capture and latency.","Medium","❌","✅","✅","Data Engineer",""),
                  ("Monitoring & Alerts","Set pipeline health and lag alerts.","Medium","❌","✅","✅","Data Ops","")]
        if option_ref.endswith(".1.B"):  # OpenFlow
            t += [("OpenFlow Setup","Provision OpenFlow CDC for source → Snowflake.","High","❌","✅","✅","Data Engineer",""),
                  ("Idempotent Apply","Design idempotent MERGE/UPSERT apply.","High","❌","✅","✅","Data Engineer",""),
                  ("Runbook & SLOs","Define runbooks and SLOs for CDC.","High","❌","⚙️","✅","Data Ops","")]
        if option_ref.endswith(".1.C"):
            t += [("Log Reader Service","Implement external log reader and durable delivery.","High","❌","⚙️","✅","Software Engineer",""),
                  ("Replay / Recovery","Implement replay and recovery patterns.","High","❌","⚙️","✅","Data Ops","")]
        if option_ref.endswith(".2.A"):
            t += [("Create API Integration","Set up external access integration.","Medium","❌","✅","✅","Data Engineer",""),
                  ("Define External Functions","Implement parameterised external functions.","Medium","❌","✅","✅","Data Engineer","")]
        if option_ref.endswith(".2.B"):
            t += [("Ingress Endpoint","Provision API gateway endpoint with auth.","High","❌","⚙️","✅","Security/Platform",""),
                  ("Landing to Stage","Write payloads to stage with partitioning.","Medium","❌","✅","✅","Data Engineer","")]
        if option_ref.endswith(".2.C"):
            t += [("Defer API Ingestion","Document rationale and alternate path for MVP.","Low","✅","❌","❌","Product/Data Lead","")]
        if option_ref.endswith(".3.A"):
            t += [("Create Stage & Notifications","Define stage & event notifications.","Low","✅","✅","✅","Data Engineer",""),
                  ("Snowpipe Definition","Create pipe with auto-ingest.","Low","✅","✅","✅","Data Engineer","")]
        if option_ref.endswith(".3.B"):
            t += [("Schedule COPY Jobs","Create scheduled COPY INTO jobs.","Low","✅","✅","✅","Data Engineer","")]
        if option_ref.endswith(".3.C"):
            t += [("Streaming Client","Implement streaming client to push rows.","Medium","❌","⚙️","✅","Software Engineer","")]
        if option_ref.endswith(".4.A"):
            t += [("Connector Setup","Configure connector with schema mapping.","Medium","❌","✅","✅","Data Engineer","")]
        if option_ref.endswith(".4.B"):
            t += [("Stream Writer","Implement producer to publish events.","Medium","❌","✅","✅","Software Engineer","")]
        if option_ref.endswith(".4.C"):
            t += [("Queue Binding","Bind Pub/Sub or Event Hub to storage.","High","❌","⚙️","✅","Platform/DevOps","")]
        if option_ref.endswith(".5.A"):
            t += [("Connector Config","Authorize and configure connectors.","Low","✅","✅","✅","Data Engineer","")]
        if option_ref.endswith(".5.B"):
            t += [("Job Orchestration","Define jobs, dependencies, and alerts.","Medium","❌","✅","✅","Data Ops","")]
        if option_ref.endswith(".5.C"):
            t += [("Service Scaffolding","Provision repo and CI/CD.","High","❌","⚙️","✅","Software Engineer","")]
        return t

    # Compose files
    plan = []
    opt_rows = []
    task_rows = []

    for sc in subs:
        sc_code = sc["code"]
        sc_title = sc["title"]  # exact title from Confluence
        plan.append({
            "Parent Page": "F.01 – Ingest",
            "Page Title": sc_title,
            "Page Type": "Subcomponent",
            "Code / Ref": sc_code,
            "Description / Notes": "Auto-synced from Confluence as source of truth.",
            "Complexity": "",
            "Mode Applicability": "",
            "Validation / Cleanup Flag": "Viable",
            "Labels": "blueprint;subcomponent;F.01",
            "Recommended Action": "Create if missing"
        })

        # options
        for letter, title, cx, mvp, prod, ent, notes in options_for(sc_code):
            opt_ref = f"{sc_code}.{letter}"
            opt_rows.append({
                "Component": "F.01 – Ingest",
                "Subcomponent": sc_title,
                "Subcomponent Code": sc_code,
                "OptionRef": opt_ref,
                "Option Title": title,
                "Complexity": cx,
                "MVP": mvp,
                "Production": prod,
                "Enterprise": ent,
                "Option Notes": notes,
                "Viable": "Yes" if not (sc_code.endswith(".1") and title.lower().find("streams")>=0) else "No",
                "DuplicateOf": "F.01.1.B" if (sc_code.endswith(".1") and "Streams" in title) else "",
                "Cleanup Recommendation": "Remove or merge into OpenFlow native CDC" if (sc_code.endswith(".1") and "Streams" in title) else ""
            })
            # option page
            plan.append({
                "Parent Page": sc_title,
                "Page Title": f"{opt_ref} – {title}",
                "Page Type": "Option",
                "Code / Ref": opt_ref,
                "Description / Notes": notes,
                "Complexity": cx,
                "Mode Applicability": f"MVP:{mvp} Prod:{prod} Ent:{ent}",
                "Validation / Cleanup Flag": "Viable",
                "Labels": "blueprint;option;F.01",
                "Recommended Action": "Create"
            })
            # tasks page
            plan.append({
                "Parent Page": f"{opt_ref} – {title}",
                "Page Title": f"Tasks – {opt_ref}",
                "Page Type": "Tasks",
                "Code / Ref": opt_ref,
                "Description / Notes": f"Tasks filtered by OptionRef={opt_ref}.",
                "Complexity": "",
                "Mode Applicability": "",
                "Validation / Cleanup Flag": "",
                "Labels": "blueprint;tasks;F.01",
                "Recommended Action": "Create"
            })
            # tasks rows
            for i, row in enumerate(tasks_for(opt_ref), start=1):
                t_title, t_desc, t_cx, t_mvp, t_prod, t_ent, t_role, t_notes = row
                task_rows.append({
                    "OptionRef": opt_ref,
                    "Task ID": f"{opt_ref}.T{i}",
                    "Task Title": t_title,
                    "Task Description": t_desc,
                    "Complexity": t_cx,
                    "MVP": t_mvp,
                    "Production": t_prod,
                    "Enterprise": t_ent,
                    "Primary Role": t_role,
                    "Notes": t_notes
                })

    # Write files
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "Confluence_Page_Creation_Plan.json"), "w") as f:
        json.dump(plan, f, indent=2)
    pd.DataFrame(plan).to_csv(os.path.join(args.out_dir, "Confluence_Page_Creation_Plan.csv"), index=False)
    pd.DataFrame(opt_rows).to_csv(os.path.join(args.out_dir, "Blueprint_Options_With_Refs.csv"), index=False)
    pd.DataFrame(task_rows).to_csv(os.path.join(args.out_dir, "Blueprint_Tasks_Mapped_To_OptionRefs.csv"), index=False)

    print("Generated:")
    print(" - data/Confluence_Page_Creation_Plan.json")
    print(" - data/Confluence_Page_Creation_Plan.csv")
    print(" - data/Blueprint_Options_With_Refs.csv")
    print(" - data/Blueprint_Tasks_Mapped_To_OptionRefs.csv")

if __name__ == "__main__":
    main()
