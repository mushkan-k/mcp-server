from typing import Dict, Any
from .clients.splunk_mcp import SplunkMCP
from .clients.k8s_client import K8sClient
from .clients.send_mail_client import SendMailClient
import httpx
import os
import asyncio

# Load environment variables
SPLUNK_BASE = os.getenv('SPLUNK_BASE_URL', '')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '')
SPLUNK_USER = os.getenv('SPLUNK_USERNAME', '')
SPLUNK_PASS = os.getenv('SPLUNK_PASSWORD', '')
KUBECONFIG = os.getenv('KUBECONFIG_PATH', '')
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')

# Initialize SplunkMCP with dual-mode auth
splunk_mcp = SplunkMCP(
    base_url=SPLUNK_BASE,
    token=SPLUNK_TOKEN,
    username=SPLUNK_USER,
    password=SPLUNK_PASS
) if SPLUNK_BASE else None

# Initialize K8s client
if KUBECONFIG:
    try:
        k8s_client = K8sClient(KUBECONFIG)
    except Exception as e:
        print("K8s client failed to initialize:", str(e))
        k8s_client = None
else:
    print("ℹ Skipping K8s client — no config path provided.")
    k8s_client = None

# Initialize email client
email_client = SendMailClient(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS) if SMTP_HOST else None

# Tool handler (only search, no extra tools)
async def tool_splunk_search(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query")
    earliest = params.get("earliest_time", "-1h")
    latest = params.get("latest_time", "now")

    if not splunk_mcp:
        return {"status": "error", "message": "Splunk client not initialized"}

    try:
        data = await splunk_mcp.search(query, earliest, latest)
        return {
            "status": "success",
            "items": data.get("items", []),
            "count": data.get("count", 0),
            "message": data.get("message", "")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def tool_k8s_get_deployment_details(params):
    namespace = params.get("namespace", "default")
    deployment_name = params["deployment_name"]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/deployments/{namespace}/{deployment_name}",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("deployment details:", response.text)
            return data
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def tool_k8s_fetch_deployments(params):
    namespace = params.get("namespace", "default")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/deployments/{namespace}",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("deployment:", response.text)
            return data
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_fetch_pod_logs(params):
    namespace = params.get("namespace", "default")
    podName = params.get("podName")
    tail_lines = params.get("tail_lines")  

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(  
                f"http://localhost:8080/api/k8s/pods/{namespace}/{podName}/logs",
                params={"tailLines": tail_lines} if tail_lines else None,  
                timeout=20
            )
            response.raise_for_status()
            data = response.text
            print("fetch pod logs:", response.text)
            return data
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_fetch_pods(params):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/pods",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("fetch pods:", response.text)
            return data
    except Exception as e:
        return {"status": "error","message": str(e)}
    

async def tool_k8s_get_service_details(params):
    namespace = params.get("namespace", "default")
    serviceName = params.get("serviceName")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/services/{namespace}/{serviceName}",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("fetch service deatils:", response.text)
            return data
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_fetch_services(params):
    namespace = params.get("namespace", "default")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/services/{namespace}",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("K8s connector response:", data)
            return data
    except Exception as e:
        print("Error calling K8s connector:", str(e))
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_fix_service_port(params):
    namespace = params.get("namespace", "default")
    serviceName = params.get("service_name")
    old_port = params.get("old_port")
    new_port = params.get("new_port")

    if not serviceName or old_port is None or new_port is None:
        return {"status": "error", "message": "Missing required parameters"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8080/api/k8s/services/{namespace}/{serviceName}/fix-port",
                params={"oldPort": old_port, "newPort": new_port},
                timeout=15
            )
            response.raise_for_status()
            data = response.text
            print("port details:", data)
            return data
    except Exception as e:
        print("port details:", str(e))
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_get_pod_details(params):
    namespace = params.get("namespace", "default")
    podName = params.get("pod_name")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/pods/{namespace}/{podName}",
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("pod details:", data)
            return data
    except Exception as e:
        print("port details:", str(e))
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_port_check(params):
    namespace = params.get("namespace", "default")
    podName = params.get("pod_name")
    port = params.get("port")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8080/api/k8s/pods/{namespace}/{podName}/port-check",
                params={"port": port},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print("pods port check:",data)
            return data  
    except Exception as e:
        return {"status": "error","message": str(e)}
    

async def tool_k8s_restart_deployment(params):
    namespace = params.get("namespace", "default")
    deploymentName = params.get("deployment_name")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8080/api/k8s/deployments/{namespace}/{deploymentName}/restart",
                timeout=15
            )
            response.raise_for_status()
            data = response.text
            print("deployment:",data)
            return data  
    except Exception as e:
        return {"status": "error","message": str(e)}


async def tool_k8s_restart_pod(params):
    namespace = params.get("namespace", "default")
    podName = params.get("pod_name")

    if not podName:
        return {"status": "error", "message": "Missing required parameter: pod_name"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8080/api/k8s/pods/{namespace}/{podName}/restart",
                timeout=15
            )
            response.raise_for_status()
            try:
                data = response.json()
            except Exception:
                data = {"message": response.text}
            print("restart details:", data)
            return {"status": "success","result": data}

    except Exception as e:
        import traceback
        print("Restart pod error:", traceback.format_exc())
        return {"status": "error", "message": str(e)}
    

async def tool_k8s_scale_deployment(params):
    namespace = params.get("namespace", "default")
    name = params.get("name")
    replicas = params.get("replicas")

    if not name or replicas is None:
        return {"status": "error", "message": "Missing required parameters: 'name' and/or 'replicas'"}

    payload = {
        "name": name,
        "namespace": namespace,
        "replicas": replicas
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/api/k8s/deployments/scale",
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            try:
                data = response.json()
            except Exception:
                data = {"message": response.text}
            print("scale result:", data)
            return data

    except Exception as e:
        import traceback
        print("Scale deployment error:", traceback.format_exc())
        return {"status": "error", "message": str(e)}
    

async def tool_email_send(params: Dict[str, Any]):
    to = params.get('to')
    subject = params.get('subject')
    body = params.get('body', '')
    html = params.get('html')
    if not to or not subject:
        raise ValueError('to and subject required')
    if not email_client:
        raise RuntimeError('Email client not configured')
    # email client is sync
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, email_client.send_email, to, subject, body, html)


# Tool registry
TOOLS = {
'splunk.search': {
'description': 'Run a Splunk search query',
'params': { 'query': 'string',
            'earliest_time': 'string',
            'latest_time': 'string' },
'handler': tool_splunk_search
},
'k8s.get_deployment_details': {
    'description': 'Fetch full details of a specific Kubernetes deployment',
    'params': {
        'namespace': 'string (optional)',
        'deployment_name': 'string (required)'
    },
    'handler': tool_k8s_get_deployment_details
},
'k8s.fetch_deployments': {
    'description': 'Fetch details of a Kubernetes deployment',
    'params': {
        'namespace': 'string (optional)',
        'name': 'string (required)'
    },
    'handler': tool_k8s_fetch_deployments
},
'k8s.fetch_pod_logs': {
    'description': 'Fetch logs from a specific Kubernetes pod.',
    'params': {
        'namespace': 'string (optional)',
        'podName': 'string (required)',
        'tail_lines': 'int (optional)'
    },
    'handler': tool_k8s_fetch_pod_logs
},
'k8s.fetch_pods': {
    'description': 'Fetch all pods across all namespaces.',
    'params': {},  # No params needed
    'handler': tool_k8s_fetch_pods
},
'k8s.get_service_details': {
    'description': 'Get details of a Kubernetes service',
    'params': { 'service_name': 'string', 'namespace': 'string (optional)' },
    'handler': tool_k8s_get_service_details
},
'k8s.fetch_services': {
    'description': 'List Kubernetes services via connector',
    'params': { 'namespace': 'string (optional)',
                'service_name': 'string (optional)'
                },
    'handler': tool_k8s_fetch_services
},
'k8s.fix_service_port': {
    'description': 'Fix the port configuration of a Kubernetes service',
    'params': {
        'namespace': 'string (optional)',
        'service_name': 'string (required)',
        'old_port': 'int (required)',
        'new_port': 'int (required)'
    },
    'handler': tool_k8s_fix_service_port
},
'k8s.get_pod_details': {
    'description': 'Fetch logs for a specific pod',
    'params': {
        'namespace': 'string (optional)',
        'pod_name': 'string (required)'
    },
    'handler': tool_k8s_get_pod_details
},
'k8s.port_check': {
    'description': 'Check exposed ports for all Kubernetes pods.',
    'params': {
        'namespace': 'string (optional)',
        'pod_name': 'string (required)',
        'port': 'int(required)'
    },  
    'handler': tool_k8s_port_check
},
'k8s.restart_deployment': {
    'description': 'Restart a Kubernetes deployment',
    'params': {
        'namespace': 'string (optional)',
        'deployement_name': 'string (required)'
    },
    'handler': tool_k8s_restart_deployment
},
'k8s.restart_pod': {
    'description': 'Restart a Kubernetes pod by deleting it. The controller will recreate it.',
    'params': {
        'namespace': 'string (optional)',
        'pod_name': 'string (required)'
    },
    'handler': tool_k8s_restart_pod
},
'k8s.scale_deployment': {
    'description': 'Scale a deployment to a specific number of replicas',
    'params': {
        'namespace': 'string (optional)',
        'name': 'string (required)',
        'replicas': 'int (required)'
    },
    'handler': tool_k8s_scale_deployment
},
'email.send': {
'description': 'Send an email via SMTP',
'params': { 'to': 'string', 'subject': 'string', 'body': 'string', 'html': 'string (optional)' },
'handler': tool_email_send
}
}