## 简述
准备刷新ApplicationContext，初始化一些基础设施。

这是refresh()方法的第一步，主要做一些准备工作：
- 设置启动时间和激活状态
- 初始化属性源（property sources）
- 验证必需的属性
- 准备早期事件集合

## 核心流程
1. 设置启动时间戳和活跃标志
2. 初始化属性源（由子类实现）
3. 验证所有必需的属性是否已配置
4. 创建早期ApplicationEvent集合

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // 第一步：准备刷新
            prepareRefresh();
            
            // ... 后续步骤
        }
    }

    protected void prepareRefresh() {
        // 1. 设置启动时间和活跃标志
        this.startupDate = System.currentTimeMillis();
        this.closed.set(false);
        this.active.set(true);

        if (logger.isDebugEnabled()) {
            if (logger.isTraceEnabled()) {
                logger.trace("Refreshing " + this);
            }
            else {
                logger.debug("Refreshing " + getDisplayName());
            }
        }

        // 2. 初始化属性源（模板方法，由子类实现）
        // 例如：ServletContext参数、JNDI属性等
        initPropertySources();

        // 3. 验证所有标记为required的属性是否可解析
        // 如果有必需属性缺失，会抛出异常
        getEnvironment().validateRequiredProperties();

        // 4. 存储预刷新阶段的ApplicationListener
        if (this.earlyApplicationListeners == null) {
            this.earlyApplicationListeners = new LinkedHashSet<>(this.applicationListeners);
        }
        else {
            // 重置本地应用监听器为预刷新状态
            this.applicationListeners.clear();
            this.applicationListeners.addAll(this.earlyApplicationListeners);
        }

        // 5. 创建早期事件集合，用于存储在多播器创建之前发布的事件
        this.earlyApplicationEvents = new LinkedHashSet<>();
    }

    /**
     * 模板方法，由子类实现以初始化额外的属性源
     */
    protected void initPropertySources() {
        // 默认空实现，供子类重写
    }
}
```

## initPropertySources的实现

### ServletWebServerApplicationContext的实现

Web应用需要将ServletContext相关的属性添加到Environment中：

```java
public class GenericWebApplicationContext extends GenericApplicationContext
        implements ConfigurableWebApplicationContext, ThemeSource {

    @Override
    protected void initPropertySources() {
        ConfigurableEnvironment env = getEnvironment();
        if (env instanceof ConfigurableWebEnvironment) {
            ((ConfigurableWebEnvironment) env).initPropertySources(
                    this.servletContext, null);
        }
    }
}
```

WebApplicationContextUtils会将以下属性源添加到Environment：
- **ServletContext初始化参数**：web.xml中的context-param
- **ServletConfig初始化参数**：servlet配置参数

## Environment和PropertySource

Spring的Environment提供了统一的属性访问接口，底层由多个PropertySource组成：

```
Environment
  └── MutablePropertySources
        ├── systemProperties (System.getProperties())
        ├── systemEnvironment (System.getenv())
        ├── servletContextInitParams (web.xml的context-param)
        ├── servletConfigInitParams
        ├── jndiProperties
        └── applicationConfig (application.properties/yml)
```

属性查找顺序：从上到下，找到即返回。

## 验证必需属性

可以通过编程方式设置必需的属性：

```java
@Component
public class ApplicationContextInitializer {
    
    @Autowired
    private ConfigurableEnvironment environment;
    
    public void init() {
        // 标记某些属性为必需
        environment.setRequiredProperties("database.url", "database.username");
        
        // 在prepareRefresh时会验证这些属性
        // 如果缺失会抛出MissingRequiredPropertiesException
    }
}
```

或者在SpringApplication启动前设置：

```java
public class Application {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(Application.class);
        app.addInitializers(context -> {
            context.getEnvironment().setRequiredProperties("app.version");
        });
        app.run(args);
    }
}
```

## 早期事件处理

在ApplicationEventMulticaster创建之前（在initApplicationEventMulticaster步骤），如果有事件需要发布，会先存储在`earlyApplicationEvents`集合中。

在ApplicationEventMulticaster创建之后，这些早期事件会被重新发布。

```java
@Override
public void publishEvent(ApplicationEvent event) {
    // 如果多播器还未创建，暂存事件
    if (this.earlyApplicationEvents != null) {
        this.earlyApplicationEvents.add(event);
    }
    else {
        // 多播器已创建，直接发布
        getApplicationEventMulticaster().multicastEvent(event);
    }
}
```

## 状态标志说明

| 标志 | 类型 | 说明 |
|------|------|------|
| startupDate | long | 容器启动时间戳 |
| active | AtomicBoolean | 容器是否处于活跃状态 |
| closed | AtomicBoolean | 容器是否已关闭 |

这些标志用于：
- 判断容器状态
- 防止重复刷新
- 控制并发访问

## 参考调用栈

```text
prepareRefresh:587, AbstractApplicationContext (org.springframework.context.support)
refresh:519, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.refreshContext](Application.refreshContext.md)

