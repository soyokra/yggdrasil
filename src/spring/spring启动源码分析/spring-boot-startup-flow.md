# Spring Boot 启动流程图

## 整体启动流程

```mermaid
flowchart TD
    Start[main方法] --> CreateApp[创建SpringApplication]
    CreateApp --> DeduceType[推断应用类型<br/>SERVLET/REACTIVE/NONE]
    DeduceType --> LoadInitializers[加载ApplicationContextInitializer]
    LoadInitializers --> LoadListeners[加载ApplicationListener]
    LoadListeners --> DeduceMain[推断主类]
    
    DeduceMain --> Run[调用run方法]
    
    Run --> StartTimer[启动计时器]
    StartTimer --> ConfigHeadless[配置Headless属性]
    ConfigHeadless --> GetRunListeners[获取SpringApplicationRunListeners]
    GetRunListeners --> Starting[发布ApplicationStartingEvent]
    
    Starting --> PrepareEnv[准备Environment]
    PrepareEnv --> EnvPrepared[发布EnvironmentPreparedEvent]
    EnvPrepared --> PrintBanner[打印Banner]
    
    PrintBanner --> CreateContext[创建ApplicationContext]
    CreateContext --> PrepareContext[准备Context]
    PrepareContext --> ContextPrepared[发布ContextInitializedEvent]
    ContextPrepared --> LoadSources[加载Bean源<br/>注册主类为BeanDefinition]
    LoadSources --> ContextLoaded[发布ApplicationPreparedEvent]
    
    ContextLoaded --> RefreshContext[刷新Context<br/>13个步骤]
    RefreshContext --> AfterRefresh[afterRefresh<br/>空方法,子类扩展]
    AfterRefresh --> StopTimer[停止计时器]
    StopTimer --> Started[发布ApplicationStartedEvent]
    
    Started --> CallRunners[调用ApplicationRunner<br/>和CommandLineRunner]
    CallRunners --> Running[发布ApplicationReadyEvent]
    Running --> End[应用就绪,可接受请求]
    
    style CreateContext fill:#e1f5ff
    style RefreshContext fill:#ffe1e1
    style End fill:#e1ffe1
```

## SpringApplication构造过程

```mermaid
flowchart LR
    Start[new SpringApplication] --> SetSources[设置primarySources<br/>主配置类]
    SetSources --> DeduceType[推断应用类型]
    DeduceType --> CheckServlet{检查Servlet类<br/>是否存在?}
    CheckServlet -->|是| Servlet[SERVLET类型]
    CheckServlet -->|否| CheckReactive{检查Reactive类<br/>是否存在?}
    CheckReactive -->|是| Reactive[REACTIVE类型]
    CheckReactive -->|否| None[NONE类型]
    
    Servlet --> LoadInit[加载初始化器]
    Reactive --> LoadInit
    None --> LoadInit
    
    LoadInit --> ScanInit[扫描META-INF/spring.factories]
    ScanInit --> CreateInit[实例化ApplicationContextInitializer]
    CreateInit --> LoadListener[加载监听器]
    LoadListener --> ScanListener[扫描META-INF/spring.factories]
    ScanListener --> CreateListener[实例化ApplicationListener]
    CreateListener --> DeduceMain[推断主类<br/>查找main方法]
    DeduceMain --> End[构造完成]
```

## Environment准备过程

```mermaid
flowchart TD
    Start[prepareEnvironment] --> GetOrCreate[获取或创建Environment]
    GetOrCreate --> ConfigEnv[配置Environment]
    ConfigEnv --> AddCommandLine[添加命令行参数PropertySource]
    AddCommandLine --> Attach[附加ConfigurationPropertySources]
    
    Attach --> Publish[发布EnvironmentPreparedEvent]
    Publish --> Listener1[ConfigFileApplicationListener监听]
    Listener1 --> LoadProps[加载application.properties/yml]
    LoadProps --> LoadProfile[加载profile配置文件]
    LoadProfile --> BindEnv[绑定Environment到SpringApplication]
    BindEnv --> End[Environment准备完成]
    
    style LoadProps fill:#e1f5ff
    style LoadProfile fill:#e1f5ff
```

## Context创建和准备

```mermaid
flowchart TD
    Start[createApplicationContext] --> CheckType{应用类型?}
    CheckType -->|SERVLET| CreateServlet[创建AnnotationConfig<br/>ServletWebServerApplicationContext]
    CheckType -->|REACTIVE| CreateReactive[创建AnnotationConfig<br/>ReactiveWebServerApplicationContext]
    CheckType -->|NONE| CreateDefault[创建AnnotationConfig<br/>ApplicationContext]
    
    CreateServlet --> ContextCreated[Context实例已创建]
    CreateReactive --> ContextCreated
    CreateDefault --> ContextCreated
    
    ContextCreated --> SetEnv[设置Environment]
    SetEnv --> PostProcess[后处理Context<br/>设置BeanNameGenerator等]
    PostProcess --> ApplyInit[应用ApplicationContextInitializer]
    ApplyInit --> Prepared[发布ContextPreparedEvent]
    
    Prepared --> RegSingleton[注册特殊单例Bean<br/>springApplicationArguments<br/>springBootBanner]
    RegSingleton --> LoadDef[加载BeanDefinition<br/>注册主类]
    LoadDef --> Loaded[发布ApplicationPreparedEvent]
    Loaded --> Ready[Context准备完成,等待refresh]
    
    style CreateServlet fill:#ffe1e1
    style LoadDef fill:#e1f5ff
```

## Refresh过程（13步）

```mermaid
flowchart TD
    Start[refreshContext] --> Step1[1. prepareRefresh<br/>准备刷新]
    Step1 --> Step2[2. obtainFreshBeanFactory<br/>获取BeanFactory]
    Step2 --> Step3[3. prepareBeanFactory<br/>配置BeanFactory]
    Step3 --> Step4[4. postProcessBeanFactory<br/>子类扩展点]
    
    Step4 --> Step5[5. invokeBeanFactoryPostProcessors<br/>处理配置类,注册BeanDefinition]
    Step5 --> Step6[6. registerBeanPostProcessors<br/>注册Bean后置处理器]
    Step6 --> Step7[7. initMessageSource<br/>初始化国际化消息源]
    Step7 --> Step8[8. initApplicationEventMulticaster<br/>初始化事件多播器]
    
    Step8 --> Step9[9. onRefresh<br/>创建WebServer]
    Step9 --> Step10[10. registerListeners<br/>注册监听器]
    Step10 --> Step11[11. finishBeanFactoryInitialization<br/>实例化所有单例Bean]
    Step11 --> Step12[12. finishRefresh<br/>启动WebServer,发布事件]
    
    Step12 --> Step13[13. resetCommonCaches<br/>清理缓存]
    Step13 --> End[Refresh完成]
    
    style Step5 fill:#ffe1e1
    style Step6 fill:#ffe1e1
    style Step9 fill:#e1f5ff
    style Step11 fill:#ffe1e1
    style Step12 fill:#e1f5ff
```

## 关键步骤说明

### 核心步骤（必须关注）

1. **invokeBeanFactoryPostProcessors（步骤5）**
   - 扫描包路径，查找@Component等注解
   - 处理@Configuration配置类
   - 执行SpringBoot自动配置
   - 将所有BeanDefinition注册到BeanFactory

2. **registerBeanPostProcessors（步骤6）**
   - 注册各种BeanPostProcessor
   - 为后续的Bean实例化做准备

3. **onRefresh（步骤9）**
   - Web应用创建WebServer实例（Tomcat/Jetty/Undertow）
   - 但此时还未启动

4. **finishBeanFactoryInitialization（步骤11）**
   - 实例化所有非懒加载的单例Bean
   - 执行依赖注入
   - 应用AOP代理

5. **finishRefresh（步骤12）**
   - 启动WebServer
   - 发布ContextRefreshedEvent事件
   - 应用开始可以接受请求

### 事件发布时间线

```mermaid
timeline
    title Spring Boot启动事件时间线
    section 启动前
        starting : ApplicationStartingEvent
        环境准备 : ApplicationEnvironmentPreparedEvent
    section Context创建
        Context准备 : ApplicationContextInitializedEvent
        加载完成 : ApplicationPreparedEvent
    section Refresh
        刷新开始 : ContextRefreshedEvent
    section 启动后
        启动完成 : ApplicationStartedEvent
        应用就绪 : ApplicationReadyEvent
```

## 启动性能分析

典型的Spring Boot应用启动时间分布：

| 阶段 | 耗时占比 | 说明 |
|------|----------|------|
| 准备阶段 | 5% | 创建SpringApplication、加载配置 |
| 创建Context | 5% | 创建ApplicationContext实例 |
| 注册BeanDefinition | 15% | 扫描类、处理注解 |
| 实例化Bean | 60% | 创建Bean实例、依赖注入 |
| 启动WebServer | 10% | 启动Tomcat等 |
| 其他 | 5% | 发布事件、调用Runner等 |

**优化建议**：
- 减少Bean的数量（懒加载）
- 优化依赖关系（避免循环依赖）
- 使用Spring Boot DevTools（开发环境）
- 考虑使用Spring Native（生产环境）

## 相关文档链接

- [Application.run详解](Application.run.md)
- [Application.createApplicationContext](Application.createApplicationContext.md)
- [Application.refreshContext](Application.refreshContext.md)
- [refresh方法时序图](refresh-sequence-diagram.md)

