## 简述
BeanFactory的后置处理，这是一个模板方法，允许子类在BeanFactory创建完成后进行额外的配置。

这是refresh()方法的第4步，在BeanFactory创建完成（obtainFreshBeanFactory）和配置完成（prepareBeanFactory）之后执行。

AbstractApplicationContext提供空实现，具体的ApplicationContext子类可以重写此方法来添加特定的配置。

## 核心流程
1. AbstractApplicationContext提供空实现（模板方法）
2. 子类可以重写以添加特定配置
3. 例如：Web应用添加request/session作用域

## 源码分析

AbstractApplicationContext的空实现：

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            // 获取BeanFactory
            ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();

            // 配置BeanFactory的标准特性
            prepareBeanFactory(beanFactory);

            try {
                // 后置处理BeanFactory（模板方法）
                postProcessBeanFactory(beanFactory);
                
                // ... 后续步骤
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    /**
     * 模板方法：在标准初始化之后修改ApplicationContext的内部BeanFactory
     * 所有Bean定义都已加载，但还没有Bean被实例化
     * 允许在某些ApplicationContext实现中注册特殊的BeanPostProcessor等
     */
    protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 默认空实现，供子类重写
    }
}
```

## ServletWebServerApplicationContext的实现

Web应用需要添加Web相关的配置：

```java
public class ServletWebServerApplicationContext extends GenericWebApplicationContext
        implements ConfigurableWebServerApplicationContext {

    @Override
    protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 1. 添加WebApplicationContextServletContextAwareProcessor
        // 用于处理ServletContextAware和ServletConfigAware接口
        beanFactory.addBeanPostProcessor(
                new WebApplicationContextServletContextAwareProcessor(this));
        
        // 2. 忽略ServletContextAware接口的自动装配
        // 因为已经由WebApplicationContextServletContextAwareProcessor处理
        beanFactory.ignoreDependencyInterface(ServletContextAware.class);

        // 3. 注册Web相关的作用域
        registerWebApplicationScopes();
    }

    private void registerWebApplicationScopes() {
        // 获取ServletContext
        ServletContext servletContext = getServletContext();
        if (servletContext != null) {
            // 注册request作用域
            beanFactory.registerScope(WebApplicationContext.SCOPE_REQUEST,
                    new RequestScope());
            
            // 注册session作用域
            beanFactory.registerScope(WebApplicationContext.SCOPE_SESSION,
                    new SessionScope());
            
            // 注册application作用域（等同于ServletContext）
            beanFactory.registerScope(WebApplicationContext.SCOPE_APPLICATION,
                    new ServletContextScope(servletContext));
            
            // 注册ServletContext为可解析依赖
            beanFactory.registerResolvableDependency(ServletContext.class, servletContext);
        }
    }
}
```

## GenericWebApplicationContext的实现

更通用的Web应用上下文实现：

```java
public class GenericWebApplicationContext extends GenericApplicationContext
        implements ConfigurableWebApplicationContext, ThemeSource {

    @Override
    protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 1. 添加ServletContextAwareProcessor
        if (this.servletContext != null) {
            beanFactory.addBeanPostProcessor(
                    new ServletContextAwareProcessor(this.servletContext));
            beanFactory.ignoreDependencyInterface(ServletContextAware.class);
        }
        
        // 2. 注册Web作用域
        WebApplicationContextUtils.registerWebApplicationScopes(beanFactory, this.servletContext);
        
        // 3. 注册环境Bean
        WebApplicationContextUtils.registerEnvironmentBeans(beanFactory, 
                this.servletContext, this.servletConfig);
    }
}
```

## 添加的Web相关作用域

| 作用域 | 说明 | 生命周期 |
|--------|------|----------|
| request | 请求作用域 | 每个HTTP请求创建一个Bean实例 |
| session | 会话作用域 | 每个HTTP Session创建一个Bean实例 |
| application | 应用作用域 | 整个ServletContext共享一个Bean实例 |
| websocket | WebSocket作用域 | 每个WebSocket会话一个Bean实例 |

使用示例：
```java
@Component
@Scope("request")
public class RequestScopedBean {
    // 每个HTTP请求都会创建新实例
}

@Component
@Scope(value = "session", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class SessionScopedBean {
    // 每个HTTP Session创建新实例
    // proxyMode用于在单例Bean中注入会话作用域Bean
}
```

## 与prepareBeanFactory的区别

| 方法 | 时机 | 修改范围 | 典型操作 |
|------|------|----------|----------|
| prepareBeanFactory() | BeanFactory创建后 | 通用配置 | 添加通用BeanPostProcessor、注册依赖 |
| postProcessBeanFactory() | prepareBeanFactory之后 | 子类特定配置 | 添加特定作用域、特定BeanPostProcessor |

prepareBeanFactory是AbstractApplicationContext的标准配置，所有类型的应用都需要。
postProcessBeanFactory是子类的扩展点，不同类型的应用有不同的需求。

## 常见子类的实现

### 1. AnnotationConfigApplicationContext
基本不需要额外配置，使用默认空实现。

### 2. ClassPathXmlApplicationContext
基本不需要额外配置，使用默认空实现。

### 3. StaticWebApplicationContext（测试用）
```java
@Override
protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
    beanFactory.addBeanPostProcessor(new ServletContextAwareProcessor(this.servletContext));
    beanFactory.ignoreDependencyInterface(ServletContextAware.class);
}
```

### 4. ReactiveWebServerApplicationContext（响应式Web）
```java
@Override
protected void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
    // 添加响应式Web相关配置
    beanFactory.addBeanPostProcessor(new WebApplicationContextServletContextAwareProcessor(this));
    beanFactory.ignoreDependencyInterface(ReactiveAdapterRegistry.class);
}
```

## 执行时机说明

在postProcessBeanFactory执行时：
- ✅ BeanFactory已创建
- ✅ BeanFactory已配置（ClassLoader、BeanPostProcessor等）
- ✅ 可以注册额外的BeanPostProcessor
- ✅ 可以注册额外的作用域
- ❌ BeanDefinition还未处理（在下一步invokeBeanFactoryPostProcessors中处理）
- ❌ Bean还未实例化

## 参考调用栈

```text
postProcessBeanFactory:678, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:530, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.prepareBeanFactory](AbstractApplicationContext.prepareBeanFactory.md)
- [AbstractApplicationContext.invokeBeanFactoryPostProcessors](AbstractApplicationContext.invokeBeanFactoryPostProcessors.md)

