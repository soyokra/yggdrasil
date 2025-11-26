# rabbitmq

## 集群架构
- Clustering
- Federation
- Shovels

### Clustering
rabbitmq集群的节点都是平等的，没有所谓的主从节点。主从是在队列层面，早期版本的classic queue需要设置队列为Durable和HA mode，队列才会在不同的节点
形成主从副本和持久化。新版本的Quorum Queues基于Raft协议，默认就是durable, replicated, highly available queue

![clustering.png](clustering.png)