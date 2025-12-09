# Spring Boot 启动源码分析

## 概述

本文档深入分析Spring Boot应用的启动过程，从`SpringApplication.run()`方法开始，到ApplicationContext完全初始化完成。

Spring Boot的启动过程本质上是**创建并初始化一个ApplicationContext**的过程，这个过程可以分为三个主要阶段：

### 三大阶段

1. **准备阶段**：创建SpringApplication实例，加载配置
2. **创建阶段**：创建ApplicationContext实例
3. **刷新阶段**：初始化ApplicationContext（refresh方法的13个步骤）

### 核心职责

| 阶段 | 核心职责 | 关键步骤 |
|------|----------|----------|
| **准备阶段** | 环境准备、监听器初始化 | 推断应用类型、加载初始化器和监听器 |
| **创建阶段** | 创建Context实例 | 根据应用类型创建对应的ApplicationContext |
| **刷新阶段** | Bean定义注册和实例化 | 13个步骤完成容器初始化 |

## refresh方法的13个步骤

refresh()是ApplicationContext初始化的核心方法，包含13个步骤：

| 步骤 | 方法 | 重要性 | 主要职责 |
|------|------|--------|----------|
| 1 | prepareRefresh | ⭐ | 准备刷新，初始化环境 |
| 2 | obtainFreshBeanFactory | ⭐⭐ | 获取BeanFactory |
| 3 | prepareBeanFactory | ⭐⭐ | 配置BeanFactory的标准特性 |
| 4 | postProcessBeanFactory | ⭐ | 子类扩展点（Web应用添加作用域） |
| 5 | invokeBeanFactoryPostProcessors | ⭐⭐⭐ | **处理配置类，注册BeanDefinition** |
| 6 | registerBeanPostProcessors | ⭐⭐⭐ | **注册Bean后置处理器** |
| 7 | initMessageSource | ⭐ | 初始化国际化消息源 |
| 8 | initApplicationEventMulticaster | ⭐⭐ | 初始化事件多播器 |
| 9 | onRefresh | ⭐⭐ | 子类扩展点（**创建WebServer**） |
| 10 | registerListeners | ⭐⭐ | 注册监听器 |
| 11 | finishBeanFactoryInitialization | ⭐⭐⭐ | **实例化所有单例Bean** |
| 12 | finishRefresh | ⭐⭐⭐ | 完成刷新（**启动WebServer**） |
| 13 | resetCommonCaches | ⭐ | 清理缓存 |

**注**：标记⭐⭐⭐的步骤是最核心的步骤，建议优先阅读。

## 关键概念

### BeanDefinition注册（步骤5）
在invokeBeanFactoryPostProcessors阶段，Spring会：
- 扫描包路径，查找@Component等注解的类
- 处理@Configuration配置类
- 处理@Import和@ImportResource
- 执行SpringBoot自动配置（AutoConfiguration）
- 将所有Bean定义注册到BeanFactory

### Bean实例化（步骤11）
在finishBeanFactoryInitialization阶段，Spring会：
- 按依赖关系顺序实例化Bean
- 处理Bean的生命周期回调
- 执行依赖注入
- 应用AOP代理

### WebServer启动（步骤9和12）
- **步骤9 (onRefresh)**：创建WebServer实例（Tomcat/Jetty/Undertow）
- **步骤12 (finishRefresh)**：启动WebServer，开始接受请求

## 阅读建议

### 按重要性阅读（推荐）

**核心流程（必读）**：
1. [Application.run](Application.run.md) - 启动入口
2. [Application.refreshContext](Application.refreshContext.md) - refresh方法总览
3. [invokeBeanFactoryPostProcessors](AbstractApplicationContext.invokeBeanFactoryPostProcessors.md) - BeanDefinition注册
4. [finishBeanFactoryInitialization](AbstractApplicationContext.finishBeanFactoryInitialization.md) - Bean实例化
5. [finishRefresh](AbstractApplicationContext.finishRefresh.md) - 完成刷新和WebServer启动

**重要扩展点**：
- [ConfigurationClassPostProcessor](ConfigurationClassPostProcessor.processConfigBeanDefinitions.md) - 配置类处理
- [ConfigurationClassParser](ConfigurationClassParser.parse.md) - 注解解析
- [ServletWebServerApplicationContext.onRefresh](ServletWebServerApplicationContext.onRefresh.md) - WebServer创建

**基础设施**：
- [prepareBeanFactory](AbstractApplicationContext.prepareBeanFactory.md) - BeanFactory配置
- [registerBeanPostProcessors](AbstractApplicationContext.registerBeanPostProcessors.md) - 后置处理器
- [initApplicationEventMulticaster](AbstractApplicationContext.initApplicationEventMulticaster.md) - 事件机制

**其他步骤**：
- [prepareRefresh](AbstractApplicationContext.prepareRefresh.md)
- [obtainFreshBeanFactory](AbstractApplicationContext.obtainFreshBeanFactory.md)
- [postProcessBeanFactory](AbstractApplicationContext.postProcessBeanFactory.md)
- [initMessageSource](AbstractApplicationContext.initMessageSource.md)
- [onRefresh](AbstractApplicationContext.onRefresh.md)
- [registerListeners](AbstractApplicationContext.registerListeners.md)

**异常处理**：
- [destroyBeans](AbstractApplicationContext.destroyBeans.md)
- [cancelRefresh](AbstractApplicationContext.cancelRefresh.md)
- [resetCommonCaches](AbstractApplicationContext.resetCommonCaches.md)

### 按流程顺序阅读

如果想完整了解启动流程，可以按照以下顺序阅读：

# 目录
- [Application.run](Application.run.md)
  - [Application.createApplicationContext](Application.createApplicationContext.md)
  - [Application.refreshContext](Application.refreshContext.md)
    - [AbstractApplicationContext.prepareRefresh](AbstractApplicationContext.prepareRefresh.md)
    - [AbstractApplicationContext.obtainFreshBeanFactory](AbstractApplicationContext.obtainFreshBeanFactory.md)
    - [AbstractApplicationContext.prepareBeanFactory](AbstractApplicationContext.prepareBeanFactory.md)
    - [AbstractApplicationContext.postProcessBeanFactory](AbstractApplicationContext.postProcessBeanFactory.md)
    - [AbstractApplicationContext.invokeBeanFactoryPostProcessors](AbstractApplicationContext.invokeBeanFactoryPostProcessors.md)
      - [ConfigurationClassPostProcessor.processConfigBeanDefinitions](ConfigurationClassPostProcessor.processConfigBeanDefinitions.md)
        - [ConfigurationClassParser.parse](ConfigurationClassParser.parse.md)
          - [AutoConfigurationImportSelector.getAutoConfigurationEntry](AutoConfigurationImportSelector.getAutoConfigurationEntry.md)
      - [MapperScannerConfigurer.postProcessBeanDefinitionRegistry](MapperScannerConfigurer.postProcessBeanDefinitionRegistry.md)
        - [ClassPathMapperScanner.scan](ClassPathMapperScanner.scan.md)
    - [AbstractApplicationContext.registerBeanPostProcessors](AbstractApplicationContext.registerBeanPostProcessors.md)
    - [AbstractApplicationContext.initMessageSource](AbstractApplicationContext.initMessageSource.md)
    - [AbstractApplicationContext.initApplicationEventMulticaster](AbstractApplicationContext.initApplicationEventMulticaster.md)
    - [AbstractApplicationContext.onRefresh](AbstractApplicationContext.onRefresh.md)
      - [ServletWebServerApplicationContext.onRefresh](ServletWebServerApplicationContext.onRefresh.md)
    - [AbstractApplicationContext.registerListeners](AbstractApplicationContext.registerListeners.md)
    - [AbstractApplicationContext.finishBeanFactoryInitialization](AbstractApplicationContext.finishBeanFactoryInitialization.md)
    - [AbstractApplicationContext.finishRefresh](AbstractApplicationContext.finishRefresh.md)
    - [AbstractApplicationContext.destroyBeans](AbstractApplicationContext.destroyBeans.md)
    - [AbstractApplicationContext.cancelRefresh](AbstractApplicationContext.cancelRefresh.md)
    - [AbstractApplicationContext.resetCommonCaches](AbstractApplicationContext.resetCommonCaches.md)

## 流程图

- [Spring Boot启动流程图](spring-boot-startup-flow.md)
- [refresh方法时序图](refresh-sequence-diagram.md)

## 辅助图片

- [Bean生命周期图（简化版）](bean_lifecycle_001.png)
- [Bean生命周期图（详细版）](bean_lifecycle_002.png)
