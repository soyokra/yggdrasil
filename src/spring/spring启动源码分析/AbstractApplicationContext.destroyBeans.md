## 简述
销毁容器中的所有单例Bean，释放资源。

这个方法在以下情况下被调用：
1. refresh()过程中发生异常，需要清理已创建的Bean
2. 容器正常关闭时（close()方法）

## 核心流程
1. 调用BeanFactory的destroySingletons()方法
2. 执行所有单例Bean的销毁回调
3. 释放Bean占用的资源

## 源码分析

AbstractApplicationContext中的调用：

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... 各种初始化步骤
            }
            catch (BeansException ex) {
                if (logger.isWarnEnabled()) {
                    logger.warn("Exception encountered during context initialization - " +
                            "cancelling refresh attempt: " + ex);
                }

                // 销毁已经创建的单例Bean，避免资源悬挂
                destroyBeans();

                // 重置'active'标志
                cancelRefresh(ex);

                throw ex;
            }
            finally {
                // ... 清理缓存
            }
        }
    }

    protected void destroyBeans() {
        getBeanFactory().destroySingletons();
    }

    @Override
    public void close() {
        synchronized (this.startupShutdownMonitor) {
            doClose();
            // 如果注册了shutdown hook，移除它
            if (this.shutdownHook != null) {
                try {
                    Runtime.getRuntime().removeShutdownHook(this.shutdownHook);
                }
                catch (IllegalStateException ex) {
                    // 忽略：虚拟机已经在关闭
                }
            }
        }
    }

    protected void doClose() {
        if (this.active.get() && this.closed.compareAndSet(false, true)) {
            if (logger.isDebugEnabled()) {
                logger.debug("Closing " + this);
            }

            LiveBeansView.unregisterApplicationContext(this);

            try {
                // 发布关闭事件
                publishEvent(new ContextClosedEvent(this));
            }
            catch (Throwable ex) {
                logger.warn("Exception thrown from ApplicationListener handling ContextClosedEvent", ex);
            }

            // 停止所有Lifecycle Bean
            if (this.lifecycleProcessor != null) {
                try {
                    this.lifecycleProcessor.onClose();
                }
                catch (Throwable ex) {
                    logger.warn("Exception thrown from LifecycleProcessor on context close", ex);
                }
            }

            // 销毁所有单例Bean
            destroyBeans();

            // 关闭BeanFactory
            closeBeanFactory();

            // 子类可以做额外的清理
            onClose();

            // 重置激活状态
            if (this.earlyApplicationListeners != null) {
                this.applicationListeners.clear();
                this.applicationListeners.addAll(this.earlyApplicationListeners);
            }

            this.active.set(false);
        }
    }
}
```

## DefaultListableBeanFactory的实现

```java
public class DefaultListableBeanFactory extends AbstractAutowireCapableBeanFactory
        implements ConfigurableListableBeanFactory, BeanDefinitionRegistry, Serializable {

    @Override
    public void destroySingletons() {
        super.destroySingletons();
        // 清理按类型缓存的Bean名称
        updateManualSingletonNames(Set::clear, set -> !set.isEmpty());
        clearByTypeCache();
    }
}
```

DefaultSingletonBeanRegistry中的具体实现：

```java
public class DefaultSingletonBeanRegistry extends SimpleAliasRegistry implements SingletonBeanRegistry {

    /** 一次性Bean实例集合：bean name -> DisposableBean */
    private final Map<String, Object> disposableBeans = new LinkedHashMap<>();

    public void destroySingletons() {
        if (logger.isTraceEnabled()) {
            logger.trace("Destroying singletons in " + this);
        }
        
        // 设置销毁标志
        synchronized (this.singletonObjects) {
            this.singletonsCurrentlyInDestruction = true;
        }

        String[] disposableBeanNames;
        synchronized (this.disposableBeans) {
            disposableBeanNames = StringUtils.toStringArray(this.disposableBeans.keySet());
        }
        
        // 按照依赖关系逆序销毁
        for (int i = disposableBeanNames.length - 1; i >= 0; i--) {
            destroySingleton(disposableBeanNames[i]);
        }

        // 清理各种缓存
        this.containedBeanMap.clear();
        this.dependentBeanMap.clear();
        this.dependenciesForBeanMap.clear();

        clearSingletonCache();
    }

    public void destroySingleton(String beanName) {
        // 移除已注册的单例Bean
        removeSingleton(beanName);

        // 销毁对应的DisposableBean实例
        DisposableBean disposableBean;
        synchronized (this.disposableBeans) {
            disposableBean = (DisposableBean) this.disposableBeans.remove(beanName);
        }
        destroyBean(beanName, disposableBean);
    }

    protected void destroyBean(String beanName, @Nullable DisposableBean bean) {
        // 首先触发依赖于当前Bean的其他Bean的销毁
        Set<String> dependencies;
        synchronized (this.dependentBeanMap) {
            dependencies = this.dependentBeanMap.remove(beanName);
        }
        if (dependencies != null) {
            for (String dependentBeanName : dependencies) {
                destroySingleton(dependentBeanName);
            }
        }

        // 执行Bean自身的销毁逻辑
        if (bean != null) {
            try {
                bean.destroy();
            }
            catch (Throwable ex) {
                logger.warn("Destruction of bean with name '" + beanName + 
                          "' threw an exception", ex);
            }
        }

        // 触发包含的Bean的销毁（例如内部Bean）
        Set<String> containedBeans;
        synchronized (this.containedBeanMap) {
            containedBeans = this.containedBeanMap.remove(beanName);
        }
        if (containedBeans != null) {
            for (String containedBeanName : containedBeans) {
                destroySingleton(containedBeanName);
            }
        }

        // 从其他Bean的依赖列表中移除当前Bean
        synchronized (this.dependentBeanMap) {
            for (Iterator<Map.Entry<String, Set<String>>> it = 
                    this.dependentBeanMap.entrySet().iterator(); it.hasNext();) {
                Map.Entry<String, Set<String>> entry = it.next();
                Set<String> dependenciesToClean = entry.getValue();
                dependenciesToClean.remove(beanName);
                if (dependenciesToClean.isEmpty()) {
                    it.remove();
                }
            }
        }

        // 从依赖关系映射中移除当前Bean
        this.dependenciesForBeanMap.remove(beanName);
    }

    protected void removeSingleton(String beanName) {
        synchronized (this.singletonObjects) {
            this.singletonObjects.remove(beanName);
            this.singletonFactories.remove(beanName);
            this.earlySingletonObjects.remove(beanName);
            this.registeredSingletons.remove(beanName);
        }
    }

    protected void clearSingletonCache() {
        synchronized (this.singletonObjects) {
            this.singletonObjects.clear();
            this.singletonFactories.clear();
            this.earlySingletonObjects.clear();
            this.registeredSingletons.clear();
            this.singletonsCurrentlyInDestruction = false;
        }
    }
}
```

## Bean的销毁回调

Bean可以通过多种方式定义销毁回调：

### 1. 实现DisposableBean接口

```java
@Component
public class MyBean implements DisposableBean {
    
    @Override
    public void destroy() throws Exception {
        System.out.println("MyBean is being destroyed");
        // 清理资源
    }
}
```

### 2. 使用@PreDestroy注解

```java
@Component
public class MyBean {
    
    @PreDestroy
    public void cleanup() {
        System.out.println("Cleanup before destroy");
        // 清理资源
    }
}
```

### 3. 自定义destroy-method

```java
@Bean(destroyMethod = "close")
public DataSource dataSource() {
    // DataSource的close方法会在销毁时调用
    return new HikariDataSource();
}
```

### 4. 实现AutoCloseable

```java
@Component
public class MyResource implements AutoCloseable {
    
    @Override
    public void close() {
        System.out.println("Closing resource");
        // 自动调用
    }
}
```

## 销毁顺序

Bean的销毁顺序与创建顺序相反：
1. 最后创建的Bean最先销毁
2. 如果Bean A依赖Bean B，则A会在B之前销毁
3. 这样保证了依赖关系的正确性

示例：
```
创建顺序：A -> B -> C (C依赖B, B依赖A)
销毁顺序：C -> B -> A
```

## 销毁过程中的异常处理

```java
protected void destroyBean(String beanName, @Nullable DisposableBean bean) {
    // ...
    
    if (bean != null) {
        try {
            bean.destroy();
        }
        catch (Throwable ex) {
            // 记录警告，但不抛出异常
            // 这样一个Bean的销毁失败不会影响其他Bean
            logger.warn("Destruction of bean with name '" + beanName + 
                      "' threw an exception", ex);
        }
    }
    
    // ...
}
```

销毁过程中的异常不会传播，只会记录日志，这样：
- 一个Bean的销毁失败不会影响其他Bean
- 容器可以尽可能多地清理资源
- 避免部分清理导致的资源泄漏

## 何时调用destroyBeans？

### 1. refresh异常时

```java
try {
    // finishBeanFactoryInitialization等步骤
    // 如果这里抛出异常...
}
catch (BeansException ex) {
    // ...会在这里销毁已创建的Bean
    destroyBeans();
    cancelRefresh(ex);
    throw ex;
}
```

### 2. 容器关闭时

```java
public void close() {
    synchronized (this.startupShutdownMonitor) {
        doClose();
        // ...
    }
}

protected void doClose() {
    // ...
    
    // 停止Lifecycle Bean
    if (this.lifecycleProcessor != null) {
        this.lifecycleProcessor.onClose();
    }

    // 销毁所有Bean
    destroyBeans();
    
    // ...
}
```

### 3. Shutdown Hook

SpringBoot会注册一个shutdown hook，在JVM关闭时自动关闭容器：

```java
public class SpringApplication {
    private void refreshContext(ConfigurableApplicationContext context) {
        refresh(context);
        if (this.registerShutdownHook) {
            // 注册shutdown hook
            context.registerShutdownHook();
        }
    }
}

public abstract class AbstractApplicationContext {
    @Override
    public void registerShutdownHook() {
        if (this.shutdownHook == null) {
            this.shutdownHook = new Thread(() -> {
                synchronized (startupShutdownMonitor) {
                    doClose();
                }
            });
            Runtime.getRuntime().addShutdownHook(this.shutdownHook);
        }
    }
}
```

## 典型的资源清理

在destroy回调中常见的清理操作：

```java
@Component
public class ResourceManager implements DisposableBean {
    
    private ExecutorService executorService;
    private DataSource dataSource;
    private Connection connection;
    
    @Override
    public void destroy() throws Exception {
        // 关闭线程池
        if (executorService != null) {
            executorService.shutdown();
            executorService.awaitTermination(30, TimeUnit.SECONDS);
        }
        
        // 关闭数据库连接
        if (connection != null && !connection.isClosed()) {
            connection.close();
        }
        
        // 关闭数据源
        if (dataSource instanceof AutoCloseable) {
            ((AutoCloseable) dataSource).close();
        }
        
        // 清理临时文件
        // 释放锁
        // 注销监听器
        // 等等
    }
}
```

## 参考调用栈

异常销毁：
```text
destroyBeans:1059, AbstractApplicationContext (org.springframework.context.support)
refresh:555, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

正常关闭：
```text
destroyBeans:1059, AbstractApplicationContext (org.springframework.context.support)
doClose:1033, AbstractApplicationContext (org.springframework.context.support)
close:987, AbstractApplicationContext (org.springframework.context.support)
```

## 相关链接
- [AbstractApplicationContext.cancelRefresh](AbstractApplicationContext.cancelRefresh.md)
- [AbstractApplicationContext.finishBeanFactoryInitialization](AbstractApplicationContext.finishBeanFactoryInitialization.md)

