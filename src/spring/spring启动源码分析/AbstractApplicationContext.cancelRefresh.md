## 简述
取消refresh操作，重置容器的激活状态。

当refresh()过程中发生异常时，会调用此方法来标记刷新失败，重置容器状态。

## 核心流程
1. 重置容器的active标志为false
2. 记录异常信息

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    /** 容器是否激活的标志 */
    private final AtomicBoolean active = new AtomicBoolean();

    /** 容器是否关闭的标志 */
    private final AtomicBoolean closed = new AtomicBoolean();

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 准备刷新
            
            try {
                // ... 各种初始化步骤
                
                // finishBeanFactoryInitialization(beanFactory);
                // finishRefresh();
            }
            catch (BeansException ex) {
                if (logger.isWarnEnabled()) {
                    logger.warn("Exception encountered during context initialization - " +
                            "cancelling refresh attempt: " + ex);
                }

                // 销毁已经创建的单例Bean
                destroyBeans();

                // 重置'active'标志，标记刷新失败
                cancelRefresh(ex);

                // 向调用者传播异常
                throw ex;
            }
            finally {
                // 重置Spring核心的内省缓存
                resetCommonCaches();
            }
        }
    }

    /**
     * 取消此Context的刷新尝试，在抛出异常后重置active标志
     */
    protected void cancelRefresh(BeansException ex) {
        this.active.set(false);
    }
}
```

## 状态标志说明

AbstractApplicationContext维护了两个重要的状态标志：

| 标志 | 类型 | 含义 | 设置时机 |
|------|------|------|----------|
| active | AtomicBoolean | 容器是否处于激活状态 | prepareRefresh时设为true，cancelRefresh/doClose时设为false |
| closed | AtomicBoolean | 容器是否已关闭 | prepareRefresh时设为false，doClose时设为true |

## 状态转换

容器的状态转换流程：

```
初始状态: active=false, closed=false
    ↓
prepareRefresh(): active=true, closed=false
    ↓
    ├─→ 成功: active=true, closed=false (运行中)
    │       ↓
    │   close(): active=false, closed=true
    │
    └─→ 失败: 
          ├─→ destroyBeans(): 清理已创建的Bean
          ├─→ cancelRefresh(): active=false, closed=false
          └─→ throw exception
```

## 完整的异常处理流程

```java
@Override
public void refresh() throws BeansException, IllegalStateException {
    synchronized (this.startupShutdownMonitor) {
        // 1. 准备刷新，设置 active=true, closed=false
        prepareRefresh();

        ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();
        prepareBeanFactory(beanFactory);

        try {
            postProcessBeanFactory(beanFactory);
            
            // 假设在这里抛出异常
            invokeBeanFactoryPostProcessors(beanFactory);
            registerBeanPostProcessors(beanFactory);
            initMessageSource();
            initApplicationEventMulticaster();
            onRefresh();
            registerListeners();
            
            // 或者在Bean实例化时抛出异常
            finishBeanFactoryInitialization(beanFactory);
            finishRefresh();
        }
        catch (BeansException ex) {
            if (logger.isWarnEnabled()) {
                logger.warn("Exception encountered during context initialization - " +
                        "cancelling refresh attempt: " + ex);
            }

            // 2. 销毁已创建的Bean，避免资源泄漏
            destroyBeans();

            // 3. 重置active标志为false
            cancelRefresh(ex);

            // 4. 向上抛出异常
            throw ex;
        }
        finally {
            // 5. 清理缓存
            resetCommonCaches();
        }
    }
}
```

## 异常类型

refresh过程中可能抛出的异常：

### 1. BeanCreationException
Bean创建失败：
```java
@Component
public class ProblematicBean {
    @Autowired
    private NonExistentBean dependency;  // 找不到依赖
}
```

### 2. BeanDefinitionStoreException
Bean定义解析失败：
```java
@Configuration
public class InvalidConfig {
    @Bean
    public Object invalid() {
        throw new RuntimeException("Cannot create bean");
    }
}
```

### 3. NoSuchBeanDefinitionException
找不到必需的Bean：
```java
@Component
public class MyService {
    @Autowired
    @Qualifier("notExists")
    private DataSource dataSource;  // Bean不存在
}
```

### 4. BeanCurrentlyInCreationException
循环依赖（构造函数注入）：
```java
@Component
public class BeanA {
    public BeanA(BeanB b) {}
}

@Component
public class BeanB {
    public BeanB(BeanA a) {}  // 无法解决的循环依赖
}
```

## 为什么需要cancelRefresh？

### 1. 标记状态
明确标记容器初始化失败，防止后续误用。

### 2. 一致性
保证容器状态的一致性：
- 如果refresh成功：active=true
- 如果refresh失败：active=false

### 3. 可重试性
某些场景下，可以在捕获异常后重新尝试refresh：

```java
ConfigurableApplicationContext context = new AnnotationConfigApplicationContext();
try {
    context.refresh();
} catch (BeansException ex) {
    // cancelRefresh已被调用，active=false
    logger.error("First refresh failed", ex);
    
    // 修复问题后可以重试
    // 注意：GenericApplicationContext只允许refresh一次
    // 但AbstractRefreshableApplicationContext可以多次refresh
}
```

## 与doClose的区别

| 方法 | 调用时机 | 操作 | 最终状态 |
|------|----------|------|----------|
| cancelRefresh() | refresh失败 | 只设置active=false | active=false, closed=false |
| doClose() | 正常关闭 | 停止Lifecycle、销毁Bean、设置标志 | active=false, closed=true |

cancelRefresh只是标记初始化失败，而doClose是完整的关闭流程。

## 相关检查方法

```java
public abstract class AbstractApplicationContext {
    
    @Override
    public boolean isActive() {
        return this.active.get();
    }

    /**
     * 断言此Context的BeanFactory当前是激活的
     */
    protected void assertBeanFactoryActive() {
        if (!this.active.get()) {
            if (this.closed.get()) {
                throw new IllegalStateException(getDisplayName() + " has been closed already");
            }
            else {
                throw new IllegalStateException(getDisplayName() + " has not been refreshed yet");
            }
        }
    }
}
```

这些方法用于在执行操作前检查容器状态：

```java
@Override
public Object getBean(String name) throws BeansException {
    assertBeanFactoryActive();  // 检查容器是否激活
    return getBeanFactory().getBean(name);
}
```

## 最佳实践

### 1. 捕获并记录异常

```java
public class Application {
    public static void main(String[] args) {
        ConfigurableApplicationContext context = null;
        try {
            context = SpringApplication.run(Application.class, args);
        } catch (Exception ex) {
            // refresh失败，cancelRefresh已被调用
            log.error("Application failed to start", ex);
            System.exit(1);
        }
    }
}
```

### 2. 确保资源清理

```java
ConfigurableApplicationContext context = new AnnotationConfigApplicationContext();
try {
    context.register(AppConfig.class);
    context.refresh();
    
    // 使用context
} catch (BeansException ex) {
    // cancelRefresh已自动调用
    log.error("Failed to initialize", ex);
} finally {
    // 如果有部分资源需要额外清理
    if (context != null && !context.isActive()) {
        // 自定义清理逻辑
    }
}
```

## 参考调用栈

```text
cancelRefresh:589, AbstractApplicationContext (org.springframework.context.support)
refresh:557, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.destroyBeans](AbstractApplicationContext.destroyBeans.md)
- [AbstractApplicationContext.prepareRefresh](AbstractApplicationContext.prepareRefresh.md)
- [AbstractApplicationContext.refreshContext](Application.refreshContext.md)

