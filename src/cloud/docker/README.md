# docker

## 服务架构
![docker-client-server](./docker-client-server.png)

## 镜像架构
![docker-image](./docker-image.png)

## 基础技术
- 隔离技术（Namespace）：实现进程、网络、文件系统等资源的隔离
  - PID Namespace：进程隔离，独立的进程树
  - Network Namespace：网络隔离，独立的网络栈
  - IPC Namespace：进程间通信隔离
  - Mount Namespace：文件系统挂载点隔离
  - UTS Namespace：主机名和域名隔离
- 资源限制（CGroup）：限制和监控容器资源使用
  - CPU：CPU 使用率和核心数限制
  - Memory：内存使用限制
  - I/O：磁盘读写带宽限制
- 文件系统（UnionFS）：实现镜像分层和共享机制
  - OverlayFS：推荐使用的存储驱动，高性能
  - AUFS：早期使用的联合文件系统
  - btrfs：基于 Btrfs 文件系统的驱动
  - DeviceMapper：基于设备映射的存储驱动
  - VFS：虚拟文件系统驱动（用于测试）

## 容器生命周期
![docker-lifecycle](./docker-lifecycle.png)

## Dockerfile
```dockerfile
# ============ 构建阶段 ============
# ARG 定义构建参数，可在构建时通过 --build-arg 传入
ARG NODE_VERSION=18
ARG BUILD_ENV=production

# 第一阶段：构建阶段，包含完整的构建工具
FROM node:${NODE_VERSION} AS builder

# LABEL 添加元数据标签，用于镜像管理
LABEL maintainer="dev@example.com"
LABEL description="Web application with multi-stage build"
LABEL version="1.0.0"
LABEL build.env="${BUILD_ENV}"

# WORKDIR 设置工作目录，如果目录不存在会自动创建
WORKDIR /build

# 设置环境变量，ENV 在整个构建过程和运行期都有效
ENV NODE_ENV=${BUILD_ENV}
ENV NPM_CONFIG_LOGLEVEL=warn

# COPY 复制本地文件到镜像，支持通配符和多个源
COPY package*.json ./
COPY tsconfig.json ./
COPY src ./src

# RUN 执行命令，&& 连接多个命令，\ 用于换行
RUN npm ci && \
    npm run build && \
    npm prune --production && \
    rm -rf /build/node_modules/.cache

# ============ 运行时阶段 ============
# 第二阶段：运行阶段，使用轻量级基础镜像
FROM node:${NODE_VERSION}-alpine AS runtime

# 添加元数据标签
LABEL stage="runtime"

# 安装系统依赖和运行时工具
RUN apk add --no-cache \
    curl \
    tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

# 创建非 root 用户（安全最佳实践）
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

WORKDIR /app

# 从构建阶段复制文件（多阶段构建的关键）
COPY --from=builder --chown=appuser:appgroup /build/dist ./dist
COPY --from=builder --chown=appuser:appgroup /build/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /build/package*.json ./

# ADD 类似 COPY，但可以自动解压 tar 文件或从 URL 下载
# 这里演示复制本地压缩包（如果有的话）
# ADD app-config.tar.gz /app/config/

# VOLUME 创建挂载点，用于数据持久化
VOLUME ["/app/logs", "/app/data"]

# EXPOSE 声明容器监听端口（TCP 默认，可指定 UDP）
EXPOSE 3000
EXPOSE 8080/udp

# HEALTHCHECK 定义健康检查命令
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# STOPSIGNAL 设置停止容器的信号，默认是 SIGTERM
STOPSIGNAL SIGTERM

# 切换到非 root 用户
USER appuser

# ENTRYPOINT 设置入口点，与 CMD 结合使用
# ENTRYPOINT 不会被 docker run 的参数覆盖，CMD 可以作为 ENTRYPOINT 的参数
ENTRYPOINT ["node"]

# CMD 提供默认命令，如果 docker run 指定了命令则会被覆盖
# 使用 exec 形式（JSON 数组）避免 shell 解释，提高效率
CMD ["dist/server.js"]

# ONBUILD 延迟执行指令，当此镜像被其他 Dockerfile 作为基础镜像时触发
ONBUILD COPY . /app
ONBUILD RUN npm install
```

## 镜像管理/仓库（Registry）
- 公共仓库：提供公开的镜像存储和分发服务
  - Docker Hub：Docker 官方公共仓库，包含大量官方和社区镜像
  - 第三方公共仓库：Quay.io、GitHub Container Registry (ghcr.io)
- 私有仓库：企业内部或组织内部的镜像存储解决方案
  - Harbor：VMware 开源的企业级镜像仓库，支持镜像扫描、RBAC、复制
  - Nexus Repository：Sonatype 提供的仓库管理工具，支持多种包格式
  - GitLab Container Registry：GitLab 集成的容器镜像仓库
  - Docker Registry：Docker 官方的轻量级私有仓库实现
- 镜像标签和版本管理
  - 标签类型：latest（默认）、语义化版本（v1.0.0）、Git 提交哈希、构建号
  - 版本策略：建议使用具体版本号，避免在生产环境使用 latest 标签

## 网络
- 原生网络：Docker 内置的网络驱动和模式
  - 默认网络：Docker 自动创建的三种默认网络模式
    - none网络：禁用容器网络，容器完全隔离
    - host网络：容器直接使用宿主机网络栈，无隔离
    - bridge网络：默认模式，通过虚拟网桥连接容器，NAT 转换
  - 自定义网络：用户自定义的网络配置
    - 自定义bridge网络：创建独立的网桥网络，支持自定义子网和网关
    - 自定义overlay网络：跨主机的网络，用于 Docker Swarm 集群
    - 自定义macvlan网络：为容器分配 MAC 地址，直接连接到物理网络
- 第三方网络：通过插件扩展的网络解决方案
  - flannel网络：CNCF 项目，基于 VXLAN 的覆盖网络
  - weave网络：Weaveworks 开发，自动发现和路由的容器网络
  - calico网络：基于 BGP 的网络和网络安全策略解决方案

## 存储/数据卷（Storage/Volumes）
- 数据卷类型：Docker 提供的数据持久化方案
  - Named Volumes（命名卷）：Docker 管理的持久化存储，生命周期独立于容器
  - Bind Mounts（绑定挂载）：将宿主机目录或文件直接挂载到容器，完全控制路径
  - tmpfs 挂载：将数据存储在内存中，容器停止后数据消失
- 使用场景
  - Named Volumes：数据库数据、配置文件、应用数据持久化
  - Bind Mounts：开发环境代码挂载、配置文件挂载、日志收集
  - tmpfs：临时文件、缓存数据、敏感数据（不落盘）
- 数据卷管理
  - 创建和管理：`docker volume create`、`docker volume ls`、`docker volume inspect`
  - 备份和恢复：通过容器挂载卷进行数据备份
  - 卷驱动：支持本地驱动和第三方驱动（如 NFS、Ceph）

## Docker Compose
- 核心概念：使用 YAML 文件定义和运行多容器 Docker 应用的工具
  - 服务定义：在 docker-compose.yml 中定义多个服务及其配置
  - 网络管理：自动创建网络，服务间可通过服务名通信
  - 数据卷管理：统一管理服务所需的数据卷
- docker-compose.yml 核心配置项
  - services：定义服务列表（镜像、端口、环境变量、依赖关系）
  - networks：定义网络配置
  - volumes：定义数据卷配置
  - environment：环境变量配置
  - depends_on：服务依赖关系定义
- 常用命令
  - `docker-compose up`：启动所有服务（-d 后台运行）
  - `docker-compose down`：停止并删除容器、网络
  - `docker-compose ps`：查看服务状态
  - `docker-compose logs`：查看服务日志（-f 跟随输出）
  - `docker-compose exec`：在运行中的容器内执行命令

## 厂商
- Google Cloud Platform
- Amazon Web Services
- Microsoft Azure
- 阿里云，ACK&ACS
- 腾讯云，TKE
- 百度云，容器引擎CCE和容器实例BCI