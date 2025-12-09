## 简述
注册应用监听器，将所有ApplicationListener注册到ApplicationEventMulticaster中。

这是refresh()方法的第10步，在onRefresh之后、Bean实例化之前执行。

这一步会注册三类监听器：
1. 静态指定的监听器（通过代码添加）
2. 容器中已定义的ApplicationListener Bean
3. 发布早期事件（在多播器创建之前缓存的事件）

## 核心流程
1. 注册静态指定的ApplicationListener
2. 注册容器中ApplicationListener类型的Bean名称（还未实例化）
3. 发布早期事件（earlyApplicationEvents）
4. 清空早期事件集合

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    /** 应用监听器集合 */
    private final Set<ApplicationListener<?>> applicationListeners = new LinkedHashSet<>();

    /** 早期应用监听器（refresh前的监听器） */
    @Nullable
    private Set<ApplicationListener<?>> earlyApplicationListeners;

    /** 早期应用事件（多播器创建前的事件） */
    @Nullable
    private Set<ApplicationEvent> earlyApplicationEvents;

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... initMessageSource
                // ... initApplicationEventMulticaster
                // ... onRefresh
                
                // 注册监听器
                registerListeners();
                
                // finishBeanFactoryInitialization
                // ... 后续步骤
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    protected void registerListeners() {
        // 1. 首先注册静态指定的监听器
        // 这些监听器是通过addApplicationListener方法添加的
        for (ApplicationListener<?> listener : getApplicationListeners()) {
            getApplicationEventMulticaster().addApplicationListener(listener);
        }

        // 2. 注册容器中ApplicationListener类型的Bean名称
        // 注意：这里只注册Bean名称，不实例化Bean（懒加载）
        // 实际的监听器Bean会在后面的finishBeanFactoryInitialization中实例化
        String[] listenerBeanNames = getBeanNamesForType(ApplicationListener.class, true, false);
        for (String listenerBeanName : listenerBeanNames) {
            getApplicationEventMulticaster().addApplicationListenerBean(listenerBeanName);
        }

        // 3. 发布早期应用事件
        // 这些事件是在ApplicationEventMulticaster创建之前发布的
        // 在prepareRefresh中创建了earlyApplicationEvents集合来缓存这些事件
        Set<ApplicationEvent> earlyEventsToProcess = this.earlyApplicationEvents;
        this.earlyApplicationEvents = null;  // 清空，之后的事件直接发布
        
        if (!CollectionUtils.isEmpty(earlyEventsToProcess)) {
            for (ApplicationEvent earlyEvent : earlyEventsToProcess) {
                getApplicationEventMulticaster().multicastEvent(earlyEvent);
            }
        }
    }

    @Override
    public void addApplicationListener(ApplicationListener<?> listener) {
        Assert.notNull(listener, "ApplicationListener must not be null");
        if (this.applicationEventMulticaster != null) {
            this.applicationEventMulticaster.addApplicationListener(listener);
        }
        this.applicationListeners.add(listener);
    }
}
```

## 三类监听器

### 1. 静态指定的监听器

通过代码直接添加的监听器，在ApplicationContext创建时就已经存在：

```java
public class Application {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(Application.class);
        
        // 添加静态监听器
        app.addListeners(new ApplicationListener<ApplicationEvent>() {
            @Override
            public void onApplicationEvent(ApplicationEvent event) {
                System.out.println("Event: " + event);
            }
        });
        
        app.run(args);
    }
}
```

SpringBoot在启动时会自动添加一些内置监听器：
- LoggingApplicationListener
- BackgroundPreinitializer
- DelegatingApplicationListener
- 等等

### 2. Bean定义的监听器

容器中定义的ApplicationListener Bean：

```java
// 方式1：实现接口
@Component
public class MyListener implements ApplicationListener<ContextRefreshedEvent> {
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("Context refreshed");
    }
}

// 方式2：使用@EventListener注解
@Component
public class MyEventHandler {
    @EventListener
    public void handleContextRefreshed(ContextRefreshedEvent event) {
        System.out.println("Context refreshed");
    }
}
```

注意：在registerListeners阶段，这些监听器Bean还未实例化，只是将Bean名称注册到多播器。实际的实例化在finishBeanFactoryInitialization阶段。

### 3. 早期事件

在ApplicationEventMulticaster创建之前（initApplicationEventMulticaster步骤之前），如果有事件需要发布，会先缓存在earlyApplicationEvents集合中。

这些事件会在registerListeners阶段被重新发布。

## 为什么只注册Bean名称而不实例化？

```java
// 只注册Bean名称
String[] listenerBeanNames = getBeanNamesForType(ApplicationListener.class, true, false);
for (String listenerBeanName : listenerBeanNames) {
    getApplicationEventMulticaster().addApplicationListenerBean(listenerBeanName);
}
```

原因：
1. **保持Bean的生命周期一致性**：所有普通Bean都在finishBeanFactoryInitialization阶段统一实例化
2. **避免依赖问题**：监听器Bean可能依赖其他Bean，过早实例化可能导致依赖注入失败
3. **懒加载优化**：如果某个监听器从未被触发，可以不实例化（取决于具体实现）

## AbstractApplicationEventMulticaster的监听器管理

```java
public abstract class AbstractApplicationEventMulticaster 
        implements ApplicationEventMulticaster {

    /** 监听器检索器辅助类 */
    private final ListenerRetriever defaultRetriever = new ListenerRetriever();

    /** 监听器Bean的BeanFactory */
    @Nullable
    private BeanFactory beanFactory;

    @Override
    public void addApplicationListener(ApplicationListener<?> listener) {
        synchronized (this.defaultRetriever) {
            // 如果是代理对象，移除原对象避免重复
            Object singletonTarget = AopProxyUtils.getSingletonTarget(listener);
            if (singletonTarget instanceof ApplicationListener) {
                this.defaultRetriever.applicationListeners.remove(singletonTarget);
            }
            this.defaultRetriever.applicationListeners.add(listener);
        }
    }

    @Override
    public void addApplicationListenerBean(String listenerBeanName) {
        synchronized (this.defaultRetriever) {
            this.defaultRetriever.applicationListenerBeans.add(listenerBeanName);
        }
    }

    /**
     * 获取对指定事件感兴趣的所有监听器
     */
    protected Collection<ApplicationListener<?>> getApplicationListeners(
            ApplicationEvent event, ResolvableType eventType) {
        
        Object source = event.getSource();
        Class<?> sourceType = (source != null ? source.getClass() : null);
        
        // 从缓存中查找
        ListenerCacheKey cacheKey = new ListenerCacheKey(eventType, sourceType);
        ListenerRetriever newRetriever = null;
        
        // ... 缓存处理逻辑
        
        // 检索匹配的监听器
        return retrieveApplicationListeners(eventType, sourceType, newRetriever);
    }

    private Collection<ApplicationListener<?>> retrieveApplicationListeners(
            ResolvableType eventType, @Nullable Class<?> sourceType, 
            @Nullable ListenerRetriever retriever) {
        
        List<ApplicationListener<?>> allListeners = new ArrayList<>();
        
        // 1. 处理已实例化的监听器
        for (ApplicationListener<?> listener : this.defaultRetriever.applicationListeners) {
            if (supportsEvent(listener, eventType, sourceType)) {
                allListeners.add(listener);
            }
        }
        
        // 2. 处理监听器Bean（需要时实例化）
        if (!this.defaultRetriever.applicationListenerBeans.isEmpty()) {
            BeanFactory beanFactory = getBeanFactory();
            for (String listenerBeanName : this.defaultRetriever.applicationListenerBeans) {
                try {
                    if (supportsEvent(beanFactory, listenerBeanName, eventType, sourceType)) {
                        // 从容器中获取监听器Bean（触发实例化）
                        ApplicationListener<?> listener = 
                            beanFactory.getBean(listenerBeanName, ApplicationListener.class);
                        if (!allListeners.contains(listener)) {
                            allListeners.add(listener);
                        }
                    }
                }
                catch (NoSuchBeanDefinitionException ex) {
                    // 忽略：Bean可能已被删除
                }
            }
        }
        
        // 排序
        AnnotationAwareOrderComparator.sort(allListeners);
        return allListeners;
    }
}
```

## 监听器的执行顺序

可以通过以下方式控制监听器的执行顺序：

### 1. 实现Ordered接口

```java
@Component
public class FirstListener implements ApplicationListener<ContextRefreshedEvent>, Ordered {
    
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("First listener");
    }
    
    @Override
    public int getOrder() {
        return 1;  // 数字越小越先执行
    }
}

@Component
public class SecondListener implements ApplicationListener<ContextRefreshedEvent>, Ordered {
    
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("Second listener");
    }
    
    @Override
    public int getOrder() {
        return 2;
    }
}
```

### 2. 使用@Order注解

```java
@Component
@Order(1)
public class FirstListener implements ApplicationListener<ContextRefreshedEvent> {
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("First listener");
    }
}

@Component
@Order(2)
public class SecondListener implements ApplicationListener<ContextRefreshedEvent> {
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("Second listener");
    }
}
```

### 3. @EventListener with @Order

```java
@Component
public class MyEventHandler {
    
    @EventListener
    @Order(1)
    public void handleFirst(ContextRefreshedEvent event) {
        System.out.println("First handler");
    }
    
    @EventListener
    @Order(2)
    public void handleSecond(ContextRefreshedEvent event) {
        System.out.println("Second handler");
    }
}
```

## 监听器的条件执行

可以使用SpEL表达式来条件性地执行监听器：

```java
@Component
public class ConditionalEventHandler {
    
    @EventListener(condition = "#event.success == true")
    public void handleSuccessEvent(MyEvent event) {
        System.out.println("Only handle success events");
    }
    
    @EventListener(condition = "#root.event.source.active")
    public void handleActiveSourceEvent(MyEvent event) {
        System.out.println("Only handle events from active sources");
    }
}
```

## 早期事件的典型场景

早期事件通常是在ApplicationContext准备阶段发布的一些通知事件：

```java
// 在prepareContext阶段
private void prepareContext(ConfigurableApplicationContext context, ...) {
    // ... 
    
    // 发布ApplicationStartingEvent（这是早期事件）
    listeners.contextPrepared(context);
    
    // ...
}
```

SpringBoot的早期事件包括：
- ApplicationStartingEvent
- ApplicationEnvironmentPreparedEvent
- ApplicationContextInitializedEvent
- ApplicationPreparedEvent

## 参考调用栈

```text
registerListeners:895, AbstractApplicationContext (org.springframework.context.support)
refresh:546, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.initApplicationEventMulticaster](AbstractApplicationContext.initApplicationEventMulticaster.md)
- [AbstractApplicationContext.finishBeanFactoryInitialization](AbstractApplicationContext.finishBeanFactoryInitialization.md)
- [Spring官方文档 - Application Events and Listeners](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.spring-application.application-events-and-listeners)

