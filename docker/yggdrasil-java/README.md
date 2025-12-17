# Yggdrasil Java Docker 环境

Java 开发环境的 Docker 配置，支持多个 Java 版本。

## 目录结构

```
yggdrasil-java/
├── docker-compose.yml    # Docker Compose 配置文件
├── java8/               # Java 8 环境
│   └── Dockerfile       # Java 8 Dockerfile
└── README.md           # 本文档
```

## Java 8 环境

### 环境说明

- **基础镜像**: Eclipse Temurin 8 JDK (原 AdoptOpenJDK)
- **构建工具**: Maven 3.9.6
- **开发工具**: vim, git, curl, wget
- **时区**: Asia/Shanghai

### 快速开始

#### 1. 构建镜像

```bash
cd docker/yggdrasil-java
docker-compose build
```

#### 2. 启动容器

```bash
# 启动并进入容器
docker-compose up -d
docker-compose exec java8-dev bash

# 或者直接运行
docker-compose run --rm java8-dev bash
```

#### 3. 验证环境

在容器内执行以下命令验证环境：

```bash
# 检查 Java 版本
java -version

# 检查 Maven 版本
mvn -version

# 检查 Git 版本
git --version
```

### 端口映射

- `8080`: 主应用端口
- `8081`: 备用应用端口
- `5005`: Java 远程调试端口

### 卷挂载

- **Java 代码**: `../../java` 挂载到 `/workspace`
- **Maven 仓库**: 持久化卷 `maven-repo` 挂载到 `/root/.m2`
- **Bash 历史**: 持久化卷 `bash-history` 挂载到 `/root/.bash_history`

### 常用命令

#### 容器管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f java8-dev

# 进入容器
docker-compose exec java8-dev bash

# 重启容器
docker-compose restart java8-dev
```

#### Maven 操作

```bash
# 编译项目
mvn clean compile

# 打包项目
mvn clean package

# 运行测试
mvn test

# 安装到本地仓库
mvn clean install

# 跳过测试打包
mvn clean package -DskipTests
```

#### 运行 Java 应用

```bash
# 运行 Spring Boot 应用
mvn spring-boot:run

# 运行打包后的 jar
java -jar target/your-app.jar

# 带调试模式运行
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005 -jar target/your-app.jar
```

### 远程调试

1. 在容器内以调试模式启动应用（监听 5005 端口）
2. 在 IDE 中配置远程调试：
   - Host: `localhost`
   - Port: `5005`
   - Debugger mode: Attach

### 环境变量

可以通过修改 `docker-compose.yml` 中的环境变量来调整配置：

- `JAVA_OPTS`: JVM 参数（默认：`-Xmx512m -Xms256m`）
- `MAVEN_OPTS`: Maven 运行参数（默认：`-Xmx512m`）
- `TZ`: 时区设置（默认：`Asia/Shanghai`）

### 自定义配置

#### 修改 Maven 镜像源

创建 `settings.xml` 并挂载到容器：

```xml
<!-- settings.xml -->
<settings>
  <mirrors>
    <mirror>
      <id>aliyun</id>
      <mirrorOf>central</mirrorOf>
      <name>Aliyun Maven</name>
      <url>https://maven.aliyun.com/repository/public</url>
    </mirror>
  </mirrors>
</settings>
```

在 `docker-compose.yml` 中添加卷挂载：

```yaml
volumes:
  - ./settings.xml:/root/.m2/settings.xml
```

#### 调整内存限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

### 故障排查

#### 容器无法启动

```bash
# 查看容器日志
docker-compose logs java8-dev

# 检查容器状态
docker-compose ps
```

#### Maven 下载依赖慢

配置国内镜像源（见上文"修改 Maven 镜像源"）

#### 权限问题

如果遇到文件权限问题，可以在 Dockerfile 中添加用户配置，或使用 `--user` 参数运行容器。

## 许可证

本项目遵循 MIT 许可证。

