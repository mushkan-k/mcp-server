from kubernetes import client, config
from typing import List, Optional
import os

class K8sClient:
    def __init__(self, kubeconfig_path: Optional[str] = None):
        # load config
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            # try kubeconfig from env or in-cluster
            try:
                config.load_kube_config()
            except Exception:
                config.load_incluster_config()
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()

    def list_pods(self, namespace: str = 'default') -> List[dict]:
        pods = self.core.list_namespaced_pod(namespace)
        return [ { 'name': p.metadata.name, 'namespace': p.metadata.namespace, 'status': p.status.phase } for p in pods.items ]

    def get_pod_logs(self, pod_name: str, namespace: str = 'default', container: Optional[str] = None, tail_lines: int = 200) -> str:
        return self.core.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=container, tail_lines=tail_lines)

    def scale_deployment(self, name: str, namespace: str = 'default', replicas: int = 1) -> dict:
        body = { 'spec': { 'replicas': replicas } }
        resp = self.apps.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=body)
        return { 'name': name, 'namespace': namespace, 'replicas': resp.spec.replicas }
