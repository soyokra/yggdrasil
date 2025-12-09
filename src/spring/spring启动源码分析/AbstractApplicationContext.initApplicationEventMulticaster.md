## 简述
初始化ApplicationEventMulticaster（应用事件多播器），用于事件的发布和监听。

这是refresh()方法的第8步，在MessageSource初始化之后执行。

ApplicationEventMulticaster负责将ApplicationEvent事件广播给所有注册的监听器。

## 核心流程
1. 检查BeanFactory中是否已有名为"applicationEventMulticaster"的Bean
2. 如果有，直接使用
3. 如果没有，创建默认的SimpleApplicationEventMulticaster
4. 将ApplicationEventMulticaster注册为单例Bean

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    /** ApplicationEventMulticaster的Bean名称 */
    public static final String APPLICATION_EVENT_MULTICASTER_BEAN_NAME = "applicationEventMulticaster";

    /** ApplicationEventMulticaster实例 */
    @Nullable
    private ApplicationEventMulticaster applicationEventMulticaster;

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... registerBeanPostProcessors
                // ... initMessageSource
                
                // 初始化事件多播器
                initApplicationEventMulticaster();
                
                // onRefresh
                // registerListeners
                // ... 后续步骤
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    protected void initApplicationEventMulticaster() {
        ConfigurableListableBeanFactory beanFactory = getBeanFactory();
        
        // 检查是否已有applicationEventMulticaster Bean
        if (beanFactory.containsLocalBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME)) {
            // 如果有，获取并使用
            this.applicationEventMulticaster =
                    beanFactory.getBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, 
                                       ApplicationEventMulticaster.class);
            
            if (logger.isTraceEnabled()) {
                logger.trace("Using ApplicationEventMulticaster [" + 
                           this.applicationEventMulticaster + "]");
            }
        }
        else {
            // 如果没有，创建默认的SimpleApplicationEventMulticaster
            this.applicationEventMulticaster = new SimpleApplicationEventMulticaster(beanFactory);
            
            // 注册为单例Bean
            beanFactory.registerSingleton(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, 
                                         this.applicationEventMulticaster);
            
            if (logger.isTraceEnabled()) {
                logger.trace("No '" + APPLICATION_EVENT_MULTICASTER_BEAN_NAME + 
                           "' bean, using [" + this.applicationEventMulticaster + "]");
            }
        }
    }
}
```

## ApplicationEventMulticaster接口

```java
public interface ApplicationEventMulticaster {

    /**
     * 添加监听器
     */
    void addApplicationListener(ApplicationListener<?> listener);

    /**
     * 通过Bean名称添加监听器
     */
    void addApplicationListenerBean(String listenerBeanName);

    /**
     * 移除监听器
     */
    void removeApplicationListener(ApplicationListener<?> listener);

    /**
     * 移除指定Bean名称的监听器
     */
    void removeApplicationListenerBean(String listenerBeanName);

    /**
     * 移除所有监听器
     */
    void removeAllListeners();

    /**
     * 广播事件给所有合适的监听器
     */
    void multicastEvent(ApplicationEvent event);

    /**
     * 广播事件给所有合适的监听器（带事件类型）
     */
    void multicastEvent(ApplicationEvent event, @Nullable ResolvableType eventType);
}
```

## SimpleApplicationEventMulticaster实现

默认的事件多播器实现：

```java
public class SimpleApplicationEventMulticaster extends AbstractApplicationEventMulticaster {

    @Nullable
    private Executor taskExecutor;

    @Nullable
    private ErrorHandler errorHandler;

    @Override
    public void multicastEvent(ApplicationEvent event) {
        multicastEvent(event, resolveDefaultEventType(event));
    }

    @Override
    public void multicastEvent(final ApplicationEvent event, @Nullable ResolvableType eventType) {
        ResolvableType type = (eventType != null ? eventType : resolveDefaultEventType(event));
        Executor executor = getTaskExecutor();
        
        // 获取所有对该事件感兴趣的监听器
        for (ApplicationListener<?> listener : getApplicationListeners(event, type)) {
            if (executor != null) {
                // 如果配置了Executor，异步执行
                executor.execute(() -> invokeListener(listener, event));
            }
            else {
                // 否则同步执行
                invokeListener(listener, event);
            }
        }
    }

    protected void invokeListener(ApplicationListener<?> listener, ApplicationEvent event) {
        ErrorHandler errorHandler = getErrorHandler();
        if (errorHandler != null) {
            try {
                doInvokeListener(listener, event);
            }
            catch (Throwable err) {
                errorHandler.handleError(err);
            }
        }
        else {
            doInvokeListener(listener, event);
        }
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private void doInvokeListener(ApplicationListener listener, ApplicationEvent event) {
        try {
            listener.onApplicationEvent(event);
        }
        catch (ClassCastException ex) {
            String msg = ex.getMessage();
            if (msg == null || matchesClassCastMessage(msg, event.getClass())) {
                // 可能只是泛型类型不匹配，记录日志后忽略
                Log logger = LogFactory.getLog(getClass());
                if (logger.isTraceEnabled()) {
                    logger.trace("Non-matching event type for listener: " + listener, ex);
                }
            }
            else {
                throw ex;
            }
        }
    }
}
```

## 自定义ApplicationEventMulticaster

可以自定义事件多播器来实现异步事件处理或错误处理：

```java
@Configuration
public class EventConfig {

    @Bean
    public ApplicationEventMulticaster applicationEventMulticaster() {
        SimpleApplicationEventMulticaster multicaster = 
                new SimpleApplicationEventMulticaster();
        
        // 设置线程池，使事件异步处理
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("event-");
        executor.initialize();
        multicaster.setTaskExecutor(executor);
        
        // 设置错误处理器
        multicaster.setErrorHandler(t -> {
            System.err.println("Error in event listener: " + t.getMessage());
        });
        
        return multicaster;
    }
}
```

## 事件发布流程

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void publishEvent(ApplicationEvent event) {
        publishEvent(event, null);
    }

    protected void publishEvent(Object event, @Nullable ResolvableType eventType) {
        Assert.notNull(event, "Event must not be null");

        // 如果需要，将事件包装为ApplicationEvent
        ApplicationEvent applicationEvent;
        if (event instanceof ApplicationEvent) {
            applicationEvent = (ApplicationEvent) event;
        }
        else {
            applicationEvent = new PayloadApplicationEvent<>(this, event);
            if (eventType == null) {
                eventType = ((PayloadApplicationEvent<?>) applicationEvent).getResolvableType();
            }
        }

        // 如果在多播器创建之前，暂存早期事件
        if (this.earlyApplicationEvents != null) {
            this.earlyApplicationEvents.add(applicationEvent);
        }
        else {
            // 使用多播器广播事件
            getApplicationEventMulticaster().multicastEvent(applicationEvent, eventType);
        }

        // 如果有父上下文，也在父上下文中发布
        if (this.parent != null) {
            if (this.parent instanceof AbstractApplicationContext) {
                ((AbstractApplicationContext) this.parent).publishEvent(event, eventType);
            }
            else {
                this.parent.publishEvent(event);
            }
        }
    }
}
```

## 内置事件类型

Spring提供了多个内置的ApplicationEvent：

| 事件类型 | 触发时机 |
|---------|---------|
| ContextRefreshedEvent | ApplicationContext初始化或刷新完成时 |
| ContextStartedEvent | ApplicationContext启动时 |
| ContextStoppedEvent | ApplicationContext停止时 |
| ContextClosedEvent | ApplicationContext关闭时 |
| RequestHandledEvent | HTTP请求处理完成时（Web应用）|
| ServletWebServerInitializedEvent | WebServer初始化完成时 |

## 自定义事件

### 1. 定义事件

```java
public class UserRegisteredEvent extends ApplicationEvent {
    
    private final String username;
    private final String email;
    
    public UserRegisteredEvent(Object source, String username, String email) {
        super(source);
        this.username = username;
        this.email = email;
    }
    
    public String getUsername() {
        return username;
    }
    
    public String getEmail() {
        return email;
    }
}
```

### 2. 发布事件

```java
@Service
public class UserService {
    
    @Autowired
    private ApplicationEventPublisher eventPublisher;
    
    public void registerUser(String username, String email) {
        // 注册用户逻辑
        // ...
        
        // 发布事件
        eventPublisher.publishEvent(new UserRegisteredEvent(this, username, email));
    }
}
```

### 3. 监听事件

方式一：实现ApplicationListener接口
```java
@Component
public class UserRegisteredListener implements ApplicationListener<UserRegisteredEvent> {
    
    @Override
    public void onApplicationEvent(UserRegisteredEvent event) {
        System.out.println("用户注册: " + event.getUsername() + ", " + event.getEmail());
        // 发送欢迎邮件等
    }
}
```

方式二：使用@EventListener注解
```java
@Component
public class UserEventHandler {
    
    @EventListener
    public void handleUserRegistered(UserRegisteredEvent event) {
        System.out.println("用户注册: " + event.getUsername());
    }
    
    @EventListener
    @Async  // 异步处理
    public void sendWelcomeEmail(UserRegisteredEvent event) {
        // 发送欢迎邮件
    }
}
```

## 同步 vs 异步事件处理

### 默认（同步）
- 事件在发布者的线程中同步执行
- 监听器的异常会影响发布者
- 执行顺序可以通过@Order控制

### 异步配置
```java
// 方式1：配置ApplicationEventMulticaster
@Bean
public ApplicationEventMulticaster applicationEventMulticaster() {
    SimpleApplicationEventMulticaster multicaster = new SimpleApplicationEventMulticaster();
    multicaster.setTaskExecutor(new SimpleAsyncTaskExecutor());
    return multicaster;
}

// 方式2：在监听器方法上使用@Async
@EnableAsync
@Configuration
public class AsyncConfig {
    // 启用@Async支持
}

@Component
public class EventHandler {
    @Async
    @EventListener
    public void handleEvent(MyEvent event) {
        // 异步处理
    }
}
```

## 参考调用栈

```text
initApplicationEventMulticaster:877, AbstractApplicationContext (org.springframework.context.support)
refresh:540, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.registerListeners](AbstractApplicationContext.registerListeners.md)
- [Spring官方文档 - Standard and Custom Events](https://docs.spring.io/spring-framework/docs/current/reference/html/core.html#context-functionality-events)

