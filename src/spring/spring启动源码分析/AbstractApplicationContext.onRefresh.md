## 简述
onRefresh()是refresh()过程中的一个模板方法，留给子类扩展，用于初始化特定的Bean。

这是refresh()的第9步，在所有普通Bean实例化之前执行，允许子类创建一些特殊的Bean。

对于SpringBoot的Web应用，ServletWebServerApplicationContext在这一步创建并初始化嵌入式Web服务器（Tomcat、Jetty或Undertow）。

## 核心流程
1. AbstractApplicationContext提供空实现
2. ServletWebServerApplicationContext重写此方法
3. 创建WebServer（通过ServletWebServerFactory）
4. 将WebServer相关的生命周期Bean注册到容器中

## 源码分析

AbstractApplicationContext的模板方法（空实现）：
```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... prepareBeanFactory、postProcessBeanFactory等
                
                // 调用onRefresh模板方法
                onRefresh();
                
                // ... 后续步骤
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    /**
     * 模板方法，子类可以重写以初始化特殊的Bean
     * 在单例Bean实例化之前调用
     */
    protected void onRefresh() throws BeansException {
        // 默认空实现，供子类重写
    }
}
```

## ServletWebServerApplicationContext的实现

详见：[ServletWebServerApplicationContext.onRefresh](ServletWebServerApplicationContext.onRefresh.md)

ServletWebServerApplicationContext重写了onRefresh方法，创建嵌入式Web服务器：

```java
public class ServletWebServerApplicationContext extends GenericWebApplicationContext
        implements ConfigurableWebServerApplicationContext {

    @Override
    protected void onRefresh() {
        // 调用父类实现
        super.onRefresh();
        try {
            // 创建Web服务器
            createWebServer();
        }
        catch (Throwable ex) {
            throw new ApplicationContextException("Unable to start web server", ex);
        }
    }

    private void createWebServer() {
        WebServer webServer = this.webServer;
        ServletContext servletContext = getServletContext();
        
        if (webServer == null && servletContext == null) {
            // 获取ServletWebServerFactory（Tomcat/Jetty/Undertow）
            ServletWebServerFactory factory = getWebServerFactory();
            // 创建WebServer实例
            this.webServer = factory.getWebServer(getSelfInitializer());
            
            // 注册WebServer生命周期Bean
            getBeanFactory().registerSingleton("webServerGracefulShutdown",
                    new WebServerGracefulShutdownLifecycle(this.webServer));
            getBeanFactory().registerSingleton("webServerStartStop",
                    new WebServerStartStopLifecycle(this, this.webServer));
        }
        else if (servletContext != null) {
            // 外部Servlet容器的情况
            try {
                getSelfInitializer().onStartup(servletContext);
            }
            catch (ServletException ex) {
                throw new ApplicationContextException("Cannot initialize servlet context", ex);
            }
        }
        initPropertySources();
    }
}
```

## 为什么在这个时机创建WebServer？

1. **在普通Bean之前**：WebServer需要在应用Bean实例化前准备好
2. **BeanFactory已配置**：此时BeanFactory已经准备完毕，可以获取配置Bean
3. **BeanDefinition已注册**：所有的Bean定义都已经注册，可以查找ServletWebServerFactory
4. **还未实例化Bean**：WebServer的Servlet初始化器可能需要访问Spring Bean

## 其他可能的扩展点

不同类型的ApplicationContext可以在onRefresh中做不同的初始化：

- **ServletWebServerApplicationContext**：创建嵌入式Web服务器
- **ReactiveWebServerApplicationContext**：创建响应式Web服务器
- **StaticWebApplicationContext**：可以注册特殊的作用域
- **自定义ApplicationContext**：可以初始化任何特定资源

## 与其他扩展点的区别

| 扩展点 | 时机 | 用途 |
|--------|------|------|
| postProcessBeanFactory() | BeanFactory创建后 | 修改BeanFactory配置 |
| onRefresh() | BeanPostProcessor注册后 | 初始化特殊Bean |
| finishRefresh() | 所有Bean实例化后 | 发布完成事件 |

## 参考调用栈
```text
onRefresh:923, AbstractApplicationContext (org.springframework.context.support)
refresh:545, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

