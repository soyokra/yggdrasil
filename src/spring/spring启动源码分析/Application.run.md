## 简述
SpringBoot的SpringApplication.run()方法是应用的启动入口，本质是**创建并初始化一个ApplicationContext**。

整个启动流程可以分为三个阶段：
1. **SpringApplication构造**：推断应用类型、加载初始化器和监听器
2. **环境准备**：配置环境、打印Banner
3. **Context初始化**：创建、准备、刷新ApplicationContext

## 启动流程概览

```
main方法
  └─> SpringApplication.run(主类, 参数)
       ├─> new SpringApplication(主类) ────────── 构造阶段
       │    ├─> 推断应用类型（SERVLET/REACTIVE/NONE）
       │    ├─> 加载ApplicationContextInitializer
       │    ├─> 加载ApplicationListener
       │    └─> 推断主类
       │
       └─> run(参数) ────────────────────────── 运行阶段
            ├─> 启动计时器
            ├─> 配置Headless属性
            ├─> 获取并启动SpringApplicationRunListeners
            ├─> 准备Environment
            ├─> 打印Banner
            ├─> createApplicationContext() ────── 创建Context
            ├─> prepareContext() ───────────── 准备Context
            ├─> refreshContext() ────────────── 刷新Context（核心）
            ├─> afterRefresh()
            ├─> 停止计时器并打印启动信息
            ├─> 发布ApplicationStartedEvent
            └─> 调用ApplicationRunner和CommandLineRunner
```

## 构造方法
```java
public SpringApplication(ResourceLoader resourceLoader, Class<?>... primarySources) {
    this.resourceLoader = resourceLoader;
    Assert.notNull(primarySources, "PrimarySources must not be null");
    this.primarySources = new LinkedHashSet<>(Arrays.asList(primarySources));
    this.webApplicationType = WebApplicationType.deduceFromClasspath();
    setInitializers((Collection) getSpringFactoriesInstances(ApplicationContextInitializer.class));
    setListeners((Collection) getSpringFactoriesInstances(ApplicationListener.class));
    this.mainApplicationClass = deduceMainApplicationClass();
}
```

## run方法详解

### 源码分析

```java
public ConfigurableApplicationContext run(String... args) {
    // 1. 启动计时器，用于记录启动耗时
    StopWatch stopWatch = new StopWatch();
    stopWatch.start();
    
    ConfigurableApplicationContext context = null;
    
    // 2. 配置Headless模式（java.awt.headless）
    // 默认为true，表示在没有显示器、键盘等外设的服务器环境中运行
    configureHeadlessProperty();
    
    // 3. 获取SpringApplicationRunListeners，并发布starting事件
    // 这是SpringBoot的事件机制，用于在启动过程中发布各种事件
    SpringApplicationRunListeners listeners = getRunListeners(args);
    listeners.starting();
    
    try {
       // 4. 封装命令行参数
       ApplicationArguments applicationArguments = new DefaultApplicationArguments(args);
       
       // 5. 准备环境（Environment）
       // 包括：系统属性、环境变量、配置文件（application.properties/yml）等
       ConfigurableEnvironment environment = prepareEnvironment(listeners, applicationArguments);
       configureIgnoreBeanInfo(environment);
       
       // 6. 打印Banner（启动时的那个Spring图标）
       Banner printedBanner = printBanner(environment);
       
       // 7. 创建ApplicationContext
       // 根据应用类型创建：AnnotationConfigServletWebServerApplicationContext（Web应用）
       context = createApplicationContext();
       
       // 8. 准备Context
       // 设置environment、应用初始化器、注册主类为Bean等
       prepareContext(context, environment, listeners, applicationArguments, printedBanner);
       
       // 9. 刷新Context（最核心的步骤）
       // 执行AbstractApplicationContext.refresh()的13个步骤
       refreshContext(context);
       
       // 10. 刷新后的处理（空方法，留给子类扩展）
       afterRefresh(context, applicationArguments);
       
       // 11. 停止计时器，打印启动日志
       stopWatch.stop();
       if (this.logStartupInfo) {
          new StartupInfoLogger(this.mainApplicationClass).logStarted(getApplicationLog(), stopWatch);
       }
       
       // 12. 发布ApplicationStartedEvent事件
       listeners.started(context);
       
       // 13. 调用ApplicationRunner和CommandLineRunner
       // 执行用户自定义的启动逻辑
       callRunners(context, applicationArguments);
    }
    catch (Throwable ex) {
       // 异常处理：发布ApplicationFailedEvent事件
       handleRunFailure(context, ex, listeners);
       throw new IllegalStateException(ex);
    }

    try {
       // 14. 发布ApplicationReadyEvent事件，表示应用已准备好接受请求
       listeners.running(context);
    }
    catch (Throwable ex) {
       handleRunFailure(context, ex, null);
       throw new IllegalStateException(ex);
    }
    
    // 15. 返回ApplicationContext
    return context;
}
```

### 关键步骤详解

#### 1. 获取SpringApplicationRunListeners

```java
SpringApplicationRunListeners listeners = getRunListeners(args);

private SpringApplicationRunListeners getRunListeners(String[] args) {
    Class<?>[] types = new Class<?>[] { SpringApplication.class, String[].class };
    return new SpringApplicationRunListeners(logger,
            getSpringFactoriesInstances(SpringApplicationRunListener.class, types, this, args));
}
```

SpringApplicationRunListener是SpringBoot的事件发布机制，默认实现是`EventPublishingRunListener`，它会在启动的各个阶段发布事件：

| 事件 | 时机 | 说明 |
|------|------|------|
| ApplicationStartingEvent | starting() | 应用开始启动 |
| ApplicationEnvironmentPreparedEvent | environmentPrepared() | 环境准备完成 |
| ApplicationContextInitializedEvent | contextPrepared() | Context创建完成 |
| ApplicationPreparedEvent | contextLoaded() | Context准备完成 |
| ApplicationStartedEvent | started() | Context刷新完成 |
| ApplicationReadyEvent | running() | 应用已就绪 |
| ApplicationFailedEvent | failed() | 启动失败 |

#### 2. 准备Environment

```java
private ConfigurableEnvironment prepareEnvironment(
        SpringApplicationRunListeners listeners,
        ApplicationArguments applicationArguments) {
    
    // 创建Environment
    ConfigurableEnvironment environment = getOrCreateEnvironment();
    
    // 配置Environment：添加命令行参数等
    configureEnvironment(environment, applicationArguments.getSourceArgs());
    
    // 附加额外的PropertySource
    ConfigurationPropertySources.attach(environment);
    
    // 发布environmentPrepared事件
    // ConfigFileApplicationListener会在这时加载application.properties/yml
    listeners.environmentPrepared(environment);
    
    // 将Environment绑定到SpringApplication
    bindToSpringApplication(environment);
    
    return environment;
}
```

Environment的PropertySource层次结构：
```
ConfigurableEnvironment
  └── MutablePropertySources
        ├── commandLineArgs (命令行参数，优先级最高)
        ├── systemProperties (System.getProperties())
        ├── systemEnvironment (System.getenv())
        ├── random (random.*)
        ├── applicationConfig: [classpath:/application.properties]
        ├── applicationConfig: [classpath:/application-{profile}.properties]
        └── defaultProperties (默认属性，优先级最低)
```

#### 3. 创建ApplicationContext

详见：[Application.createApplicationContext](Application.createApplicationContext.md)

根据`webApplicationType`创建不同类型的Context：
- **SERVLET**: `AnnotationConfigServletWebServerApplicationContext`（Web应用）
- **REACTIVE**: `AnnotationConfigReactiveWebServerApplicationContext`（响应式应用）
- **NONE**: `AnnotationConfigApplicationContext`（非Web应用）

#### 4. 准备Context

```java
private void prepareContext(ConfigurableApplicationContext context,
        ConfigurableEnvironment environment,
        SpringApplicationRunListeners listeners,
        ApplicationArguments applicationArguments,
        Banner printedBanner) {
    
    // 设置环境
    context.setEnvironment(environment);
    
    // 后处理Context：设置BeanNameGenerator、ResourceLoader等
    postProcessApplicationContext(context);
    
    // 应用所有ApplicationContextInitializer
    applyInitializers(context);
    
    // 发布contextPrepared事件
    listeners.contextPrepared(context);
    
    // 打印启动和Profile信息
    if (this.logStartupInfo) {
        logStartupInfo(context.getParent() == null);
        logStartupProfileInfo(context);
    }
    
    // 注册特殊的单例Bean
    ConfigurableListableBeanFactory beanFactory = context.getBeanFactory();
    beanFactory.registerSingleton("springApplicationArguments", applicationArguments);
    if (printedBanner != null) {
        beanFactory.registerSingleton("springBootBanner", printedBanner);
    }
    
    // 设置是否允许Bean定义覆盖
    if (beanFactory instanceof DefaultListableBeanFactory) {
        ((DefaultListableBeanFactory) beanFactory)
                .setAllowBeanDefinitionOverriding(this.allowBeanDefinitionOverriding);
    }
    
    // 加载Bean源（通常是主类）
    Set<Object> sources = getAllSources();
    Assert.notEmpty(sources, "Sources must not be empty");
    load(context, sources.toArray(new Object[0]));
    
    // 发布contextLoaded事件
    listeners.contextLoaded(context);
}
```

#### 5. 刷新Context

详见：[Application.refreshContext](Application.refreshContext.md)

这是最核心的步骤，执行`AbstractApplicationContext.refresh()`的13个步骤，完成：
- BeanDefinition注册
- Bean实例化
- WebServer创建和启动
- 等等

#### 6. 调用Runners

```java
private void callRunners(ApplicationContext context, ApplicationArguments args) {
    List<Object> runners = new ArrayList<>();
    runners.addAll(context.getBeansOfType(ApplicationRunner.class).values());
    runners.addAll(context.getBeansOfType(CommandLineRunner.class).values());
    AnnotationAwareOrderComparator.sort(runners);
    
    for (Object runner : new LinkedHashSet<>(runners)) {
        if (runner instanceof ApplicationRunner) {
            callRunner((ApplicationRunner) runner, args);
        }
        if (runner instanceof CommandLineRunner) {
            callRunner((CommandLineRunner) runner, args);
        }
    }
}
```

ApplicationRunner和CommandLineRunner用于在应用启动完成后执行自定义逻辑：

```java
@Component
@Order(1)
public class MyApplicationRunner implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) throws Exception {
        System.out.println("ApplicationRunner executed");
        // 执行启动后的初始化逻辑
    }
}

@Component
@Order(2)
public class MyCommandLineRunner implements CommandLineRunner {
    @Override
    public void run(String... args) throws Exception {
        System.out.println("CommandLineRunner executed");
        // 执行启动后的初始化逻辑
    }
}
```

### SpringApplicationRunListeners的作用

SpringApplicationRunListeners是SpringBoot的事件发布机制的核心，它在启动的各个关键节点发布事件，允许监听器响应这些事件。

#### 事件发布时间线

```
应用启动
  ↓
listeners.starting()          → ApplicationStartingEvent
  ↓
准备Environment
  ↓
listeners.environmentPrepared() → ApplicationEnvironmentPreparedEvent
  ↓                               (ConfigFileApplicationListener加载配置文件)
创建Context
  ↓
listeners.contextPrepared()    → ApplicationContextInitializedEvent
  ↓
加载Bean定义
  ↓
listeners.contextLoaded()      → ApplicationPreparedEvent
  ↓
refresh Context（13步）
  ↓
listeners.started()            → ApplicationStartedEvent
  ↓
调用Runners
  ↓
listeners.running()            → ApplicationReadyEvent
  ↓
应用就绪，可接受请求
```

#### 监听事件示例

```java
@Component
public class MyApplicationListener implements ApplicationListener<ApplicationReadyEvent> {
    
    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("应用已就绪，可以开始接受请求");
        // 执行一些初始化工作
    }
}

// 或者使用@EventListener
@Component
public class MyEventListener {
    
    @EventListener
    public void handleApplicationReady(ApplicationReadyEvent event) {
        System.out.println("应用已就绪");
    }
    
    @EventListener
    public void handleApplicationStarted(ApplicationStartedEvent event) {
        System.out.println("应用已启动");
    }
}
```

## 总结

SpringApplication.run()方法的执行流程：

1. **初始化阶段**：创建SpringApplication，加载配置
2. **环境准备**：创建和配置Environment
3. **Context创建**：创建ApplicationContext实例
4. **Context准备**：应用初始化器、注册特殊Bean
5. **Context刷新**：执行refresh()的13个步骤（核心）
6. **启动完成**：调用Runners，发布Ready事件

整个过程通过SpringApplicationRunListeners发布事件，各个组件可以通过监听事件来参与启动过程。