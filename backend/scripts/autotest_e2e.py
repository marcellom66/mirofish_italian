#!/usr/bin/env python3
"""
End-to-End Auto-Test: Validate graph creation and simulation pipeline
Tests: project creation → graph build → simulation → preparation → entity detection
"""

import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5001"
FRONTEND_BASE = "http://127.0.0.1:3000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(msg, level="INFO"):
    prefix = {
        "INFO": f"{Colors.BLUE}ℹ️{Colors.END}",
        "SUCCESS": f"{Colors.GREEN}✓{Colors.END}",
        "ERROR": f"{Colors.RED}✗{Colors.END}",
        "WARN": f"{Colors.YELLOW}⚠️{Colors.END}",
    }.get(level, "→")
    print(f"{prefix} {msg}")

def check_backend():
    """Verify backend is running"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        if r.status_code == 200:
            log("Backend is running", "SUCCESS")
            return True
    except:
        pass
    log("Backend not responding at http://127.0.0.1:5001", "ERROR")
    return False

def create_test_project():
    """Create minimal test project with multipart form data"""
    import io
    try:
        # Prepare multipart form data
        form_data = {
            "project_name": (None, "AutoTest Project"),
            "simulation_requirement": (None, "Test simulation with minimal content focusing on remote work and business scenarios"),
            "additional_context": (None, "")
        }
        
        # Create a test file
        test_content = "Remote work is becoming increasingly important. Companies are adopting flexible working arrangements."
        files = {
            "files": ("test.txt", io.BytesIO(test_content.encode()), "text/plain")
        }
        
        r = requests.post(f"{BASE_URL}/api/graph/ontology/generate", data=form_data, files=files, timeout=30)
        if r.status_code == 200:
            data = r.json().get("data", {})
            project_id = data.get("project_id")
            if project_id:
                log(f"Project created: {project_id}", "SUCCESS")
                return project_id
        else:
            log(f"Create failed ({r.status_code}): {r.text[:100]}", "WARN")
    except Exception as e:
        log(f"Project creation failed: {e}", "ERROR")
    return None

def build_graph(project_id):
    """Build knowledge graph (async task, wait for completion)"""
    try:
        payload = {"project_id": project_id}
        r = requests.post(f"{BASE_URL}/api/graph/build", json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json().get("data", {})
            task_id = data.get("task_id")
            
            if not task_id:
                log(f"No task_id in response", "WARN")
                return None
            
            log(f"Graph build task started: {task_id}", "INFO")
            
            # Poll task status
            for poll_count in range(30):
                time.sleep(2)
                task_r = requests.get(f"{BASE_URL}/api/graph/task/{task_id}", timeout=10)
                if task_r.status_code == 200:
                    task_data = task_r.json().get("data", {})
                    task_status = task_data.get("status")
                    
                    if task_status == "completed":
                        result = task_data.get("result", {})
                        graph_id = result.get("graph_id")
                        if graph_id:
                            log(f"Graph built: {graph_id}", "SUCCESS")
                            return graph_id
                    elif task_status == "failed":
                        error = task_data.get("error", "unknown error")
                        log(f"Build failed: {error}", "ERROR")
                        return None
                    else:
                        print(f"  Poll {poll_count}: status={task_status}")
            
            log("Graph build timed out", "WARN")
    except Exception as e:
        log(f"Graph build failed: {e}", "ERROR")
    return None

def verify_graph_nodes(graph_id):
    """Check if graph has nodes with content"""
    try:
        r = requests.get(f"{BASE_URL}/api/graph/data/{graph_id}", timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            nodes = data.get("nodes", [])
            log(f"Graph has {len(nodes)} nodes", "INFO" if nodes else "WARN")
            
            for i, node in enumerate(nodes[:3]):  # Show first 3
                name = node.get("name", "?")
                labels = node.get("labels", [])
                summary = node.get("summary", "")[:30]
                print(f"  [{i}] name='{name}' labels={labels} summary='{summary}...'")
            
            return len(nodes) > 0
    except Exception as e:
        log(f"Graph data fetch failed: {e}", "ERROR")
    return False

def create_simulation(project_id, graph_id):
    """Create simulation"""
    try:
        payload = {
            "project_id": project_id,
            "graph_id": graph_id,
            "enable_twitter": True,
            "enable_reddit": True
        }
        r = requests.post(f"{BASE_URL}/api/simulation/create", json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            sim_id = data.get("simulation_id")
            if sim_id:
                log(f"Simulation created: {sim_id}", "SUCCESS")
                return sim_id
    except Exception as e:
        log(f"Simulation creation failed: {e}", "ERROR")
    return None

def prepare_simulation(sim_id):
    """Start preparation and poll until complete"""
    try:
        # Start prepare
        payload = {"simulation_id": sim_id, "force_regenerate": True}
        r = requests.post(f"{BASE_URL}/api/simulation/prepare", json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", {})
            task_id = data.get("task_id")
            expected = data.get("expected_entities_count", 0)
            types = data.get("entity_types", [])
            log(f"Prepare started (task={task_id}, expected={expected}, types={types})", "INFO")
            
            # Poll status
            for poll_count in range(15):
                time.sleep(2)
                poll_payload = {"simulation_id": sim_id, "task_id": task_id}
                pr = requests.post(f"{BASE_URL}/api/simulation/prepare/status", json=poll_payload, timeout=10)
                if pr.status_code == 200:
                    pdata = pr.json().get("data", {})
                    status = pdata.get("status", "")
                    progress = pdata.get("progress", 0)
                    
                    if status in ["ready", "completed"]:
                        prepare_info = pdata.get("prepare_info", {})
                        entities = prepare_info.get("entities_count", 0)
                        profiles = prepare_info.get("profiles_count", 0)
                        log(f"Prepare completed: {entities} entities, {profiles} profiles", "SUCCESS")
                        return {"entities": entities, "profiles": profiles}
                    else:
                        print(f"  Poll {poll_count}: {progress}% - {pdata.get('message', '')[:60]}")
        
        log("Prepare didn't complete in time", "WARN")
    except Exception as e:
        log(f"Prepare failed: {e}", "ERROR")
    return None

def run_autotest():
    """Run full pipeline test"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"MiroFish E2E AutoTest")
    print(f"{'='*60}{Colors.END}\n")
    
    # Step 1: Backend check
    if not check_backend():
        return False
    
    # Step 2: Create project
    project_id = create_test_project()
    if not project_id:
        log("Aborting: cannot create project", "ERROR")
        return False
    
    # Step 3: Build graph
    graph_id = build_graph(project_id)
    if not graph_id:
        log("Aborting: cannot build graph", "ERROR")
        return False
    
    # Step 4: Verify graph has nodes
    time.sleep(1)
    if not verify_graph_nodes(graph_id):
        log("⚠️  Graph has NO NODES - this will cause 0 entities", "WARN")
        log("   → Check graph build logic or input data quality", "INFO")
        return False
    
    # Step 5: Create simulation
    sim_id = create_simulation(project_id, graph_id)
    if not sim_id:
        log("Aborting: cannot create simulation", "ERROR")
        return False
    
    # Step 6: Prepare simulation
    prepare_result = prepare_simulation(sim_id)
    if not prepare_result:
        log("Aborting: prepare failed", "ERROR")
        return False
    
    # Step 7: Verify results
    entities = prepare_result.get("entities", 0)
    profiles = prepare_result.get("profiles", 0)
    
    print(f"\n{Colors.BLUE}{'='*60}")
    print("AutoTest Results")
    print(f"{'='*60}{Colors.END}")
    
    if entities > 0 and profiles > 0:
        log(f"✓ Full pipeline works! {entities} entities → {profiles} profiles", "SUCCESS")
        print(f"\n{Colors.GREEN}✓ PASS: System is ready for simulations{Colors.END}\n")
        return True
    elif entities == 0:
        log("✗ FAIL: Zero entities detected", "ERROR")
        log("  Root causes to check:", "INFO")
        log("  1. Graph nodes have empty labels AND no name/summary", "INFO")
        log("  2. Input text too short → insufficient entities extracted", "INFO")
        log("  3. Ontology mismatch → entity types not found", "INFO")
        print()
        return False
    else:
        log(f"✗ FAIL: Entities={entities} but Profiles={profiles} (mismatch)", "ERROR")
        print()
        return False

if __name__ == "__main__":
    success = run_autotest()
    sys.exit(0 if success else 1)
