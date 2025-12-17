# Java8 完整开发环境
# 基于 Eclipse Temurin (原 AdoptOpenJDK)，包含 Maven 和开发工具

FROM eclipse-temurin:8-jdk

# 维护者信息
LABEL maintainer="yggdrasil"
LABEL description="Java 8 开发环境，包含 Maven 和 vim"

# 设置环境变量
ENV MAVEN_VERSION=3.9.6 \
    MAVEN_HOME=/usr/share/maven \
    MAVEN_CONFIG=/root/.m2 \
    TZ=Asia/Shanghai

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装必要的工具
RUN apt-get update && \
    apt-get install -y \
    vim \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Maven
RUN mkdir -p /usr/share/maven /usr/share/maven/ref && \
    curl -fsSL https://apache.osuosl.org/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz | \
    tar -xzC /usr/share/maven --strip-components=1 && \
    ln -s /usr/share/maven/bin/mvn /usr/bin/mvn

# 配置 Maven 环境变量
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

# 创建工作目录
WORKDIR /workspace

# 创建 Maven 仓库目录
RUN mkdir -p /root/.m2

# 预热 Maven（可选，下载常用插件）
RUN mvn --version

# 设置默认命令
CMD ["/bin/bash"]

