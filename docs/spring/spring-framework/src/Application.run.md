## 简述
spring boot的SpringApplication类的启动流程，本质是初始化一个ApplicationContext


new Application，加载spring.factories
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

```java
public ConfigurableApplicationContext run(String... args) {
    StopWatch stopWatch = new StopWatch();
    stopWatch.start();
    
    ConfigurableApplicationContext context = null;
    configureHeadlessProperty();
    
    SpringApplicationRunListeners listeners = getRunListeners(args);
    listeners.starting();
    
    try {
       ApplicationArguments applicationArguments = new DefaultApplicationArguments(args);
       
       ConfigurableEnvironment environment = prepareEnvironment(listeners, applicationArguments);
       configureIgnoreBeanInfo(environment);
       
       Banner printedBanner = printBanner(environment);
       
       context = createApplicationContext();
       
       prepareContext(context, environment, listeners, applicationArguments, printedBanner);
       
       refreshContext(context);
       
       afterRefresh(context, applicationArguments);
       
       stopWatch.stop();
       if (this.logStartupInfo) {
          new StartupInfoLogger(this.mainApplicationClass).logStarted(getApplicationLog(), stopWatch);
       }
       
       listeners.started(context);
       
       callRunners(context, applicationArguments);
    }
    catch (Throwable ex) {
       handleRunFailure(context, ex, listeners);
       throw new IllegalStateException(ex);
    }

    try {
       listeners.running(context);
    }
    catch (Throwable ex) {
       handleRunFailure(context, ex, null);
       throw new IllegalStateException(ex);
    }
    return context;
}
```