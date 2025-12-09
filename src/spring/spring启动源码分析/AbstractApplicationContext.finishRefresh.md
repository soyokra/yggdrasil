## 简述
完成ApplicationContext的刷新过程，发布相应的事件。

这是refresh()方法的第12步，也是正常流程的最后一步。在这一步中：
- 清理资源缓存
- 初始化生命周期处理器
- 调用生命周期处理器的onRefresh方法（**WebServer在这里启动**）
- 发布ContextRefreshedEvent事件
- 注册到JMX MBeanServer（如果需要）

## 核心流程
1. 清理资源缓存（ResourceLoader的缓存）
2. 初始化LifecycleProcessor（生命周期处理器）
3. 调用LifecycleProcessor.onRefresh()方法，启动Lifecycle Bean
4. 发布ContextRefreshedEvent事件
5. 注册ApplicationContext到LiveBeansView MBean

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... 其他步骤
                
                // 完成刷新，发布相应事件
                finishRefresh();
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    protected void finishRefresh() {
        // 1. 清理资源缓存（例如ASM元数据和扫描包的缓存）
        clearResourceCaches();

        // 2. 初始化生命周期处理器
        // 如果容器中有名为"lifecycleProcessor"的Bean就使用它
        // 否则创建默认的DefaultLifecycleProcessor
        initLifecycleProcessor();

        // 3. 调用生命周期处理器的onRefresh方法
        // 这会启动所有实现了Lifecycle接口且设置了autoStartup=true的Bean
        // WebServer就是在这里启动的！
        getLifecycleProcessor().onRefresh();

        // 4. 发布ContextRefreshedEvent事件
        // 监听此事件的Bean会收到通知
        publishEvent(new ContextRefreshedEvent(this));

        // 5. 注册到LiveBeansView MBean（用于JMX管理）
        if (!NativeDetector.inNativeImage()) {
            LiveBeansView.registerApplicationContext(this);
        }
    }

    protected void clearResourceCaches() {
        this.resourceCaches.clear();
    }

    protected void initLifecycleProcessor() {
        ConfigurableListableBeanFactory beanFactory = getBeanFactory();
        if (beanFactory.containsLocalBean(LIFECYCLE_PROCESSOR_BEAN_NAME)) {
            this.lifecycleProcessor =
                    beanFactory.getBean(LIFECYCLE_PROCESSOR_BEAN_NAME, LifecycleProcessor.class);
        }
        else {
            DefaultLifecycleProcessor defaultProcessor = new DefaultLifecycleProcessor();
            defaultProcessor.setBeanFactory(beanFactory);
            this.lifecycleProcessor = defaultProcessor;
            beanFactory.registerSingleton(LIFECYCLE_PROCESSOR_BEAN_NAME, this.lifecycleProcessor);
        }
    }
}
```

## LifecycleProcessor详解

LifecycleProcessor负责管理实现了Lifecycle接口的Bean的生命周期：

```java
public interface Lifecycle {
    void start();
    void stop();
    boolean isRunning();
}

public interface LifecycleProcessor extends Lifecycle {
    void onRefresh();
    void onClose();
}
```

DefaultLifecycleProcessor的实现：

```java
public class DefaultLifecycleProcessor implements LifecycleProcessor {

    @Override
    public void onRefresh() {
        startBeans(true);
        this.running = true;
    }

    private void startBeans(boolean autoStartupOnly) {
        // 获取所有Lifecycle Bean
        Map<String, Lifecycle> lifecycleBeans = getLifecycleBeans();
        
        // 按阶段（phase）分组
        Map<Integer, LifecycleGroup> phases = new TreeMap<>();
        lifecycleBeans.forEach((beanName, bean) -> {
            if (!autoStartupOnly || (bean instanceof SmartLifecycle && 
                    ((SmartLifecycle) bean).isAutoStartup())) {
                int phase = getPhase(bean);
                phases.computeIfAbsent(phase, p -> new LifecycleGroup(...))
                      .add(beanName, bean);
            }
        });
        
        // 按阶段顺序启动
        if (!phases.isEmpty()) {
            phases.values().forEach(LifecycleGroup::start);
        }
    }
}
```

## WebServer在这里启动

SpringBoot的WebServer实现了SmartLifecycle接口，因此在finishRefresh阶段会被自动启动：

```java
// WebServerStartStopLifecycle是在onRefresh()阶段创建并注册的
class WebServerStartStopLifecycle implements SmartLifecycle {

    private final ServletWebServerApplicationContext applicationContext;
    private final WebServer webServer;
    
    @Override
    public void start() {
        // 启动WebServer（Tomcat、Jetty或Undertow）
        this.webServer.start();
        // 发布ServletWebServerInitializedEvent事件
        this.applicationContext.publishEvent(
            new ServletWebServerInitializedEvent(this.webServer, this.applicationContext));
    }

    @Override
    public boolean isAutoStartup() {
        return true;  // 自动启动
    }

    @Override
    public int getPhase() {
        return Integer.MAX_VALUE - 1;  // 最后启动
    }
}
```

## SmartLifecycle接口

SmartLifecycle扩展了Lifecycle，提供更精细的控制：

```java
public interface SmartLifecycle extends Lifecycle, Phased {
    
    // 是否自动启动（在容器refresh时）
    default boolean isAutoStartup() {
        return true;
    }

    // 停止回调
    default void stop(Runnable callback) {
        stop();
        callback.run();
    }

    // 启动阶段（数字越小越先启动）
    default int getPhase() {
        return DEFAULT_PHASE;
    }
}
```

## 启动阶段（Phase）说明

不同的Lifecycle Bean可以设置不同的phase值来控制启动顺序：

- **负数或较小值**：优先启动
- **0**：默认值
- **正数或较大值**：后启动

例如：
- 数据源连接池：phase = -100（先启动）
- 消息队列消费者：phase = 0（默认）
- WebServer：phase = Integer.MAX_VALUE - 1（最后启动）

## ContextRefreshedEvent事件

ContextRefreshedEvent是Spring的内置事件，在ApplicationContext初始化或刷新完成时发布。

监听此事件的常见场景：
- 缓存预热
- 数据初始化
- 定时任务启动
- 连接池建立

示例：
```java
@Component
public class StartupListener implements ApplicationListener<ContextRefreshedEvent> {
    
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        // 容器启动完成，执行初始化逻辑
        System.out.println("ApplicationContext已启动完成");
    }
}
```

或使用注解方式：
```java
@Component
public class StartupHandler {
    
    @EventListener
    public void handleContextRefresh(ContextRefreshedEvent event) {
        // 容器启动完成
    }
}
```

## 与onRefresh()的区别

| 方法 | 时机 | 用途 | 典型应用 |
|------|------|------|----------|
| onRefresh() | Bean实例化之前 | 创建特殊Bean | 创建WebServer实例 |
| finishRefresh() | Bean实例化之后 | 启动服务、发布事件 | 启动WebServer、发布事件 |

注意：
- **onRefresh()**：创建WebServer对象（但未启动）
- **finishRefresh()**：启动WebServer（调用start方法）

## 参考调用栈

```text
finishRefresh:883, AbstractApplicationContext (org.springframework.context.support)
refresh:553, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## WebServer启动调用栈

```text
start:88, TomcatWebServer (org.springframework.boot.web.embedded.tomcat)
start:197, WebServerStartStopLifecycle (org.springframework.boot.web.servlet.context)
startBeans:177, DefaultLifecycleProcessor (org.springframework.context.support)
onRefresh:137, DefaultLifecycleProcessor (org.springframework.context.support)
finishRefresh:932, AbstractApplicationContext (org.springframework.context.support)
refresh:553, AbstractApplicationContext (org.springframework.context.support)
```

## 相关链接
- [AbstractApplicationContext.onRefresh](AbstractApplicationContext.onRefresh.md)
- [ServletWebServerApplicationContext.onRefresh](ServletWebServerApplicationContext.onRefresh.md)

