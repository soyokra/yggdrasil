# k8s

- NodePort: client -> NodePort -> kubeProxy -> Service(ClusterIP) -> Pod
- NodePort: client -> NodePort ->  IngressController -> IngressRules -> Service(ClusterIP) -> Pod

## 集群架构
![cluster.png](cluster.png)