## 简述
spring boot的Application.refreshContext方法
实际上调用的是spring framework的AbstractApplicationContext.refresh方法

- 创建BeanFactory
- BeanFactory后置处理
  - 处理注解类文件，生成和注册BeanDefinition
  - 占位符解析
- 消息本地化，事件广播，实例化webServer，注册监听器
- 实例化bean

## 源码分析
```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // Prepare this context for refreshing.
            prepareRefresh();

            // Tell the subclass to refresh the internal bean factory.
            ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();

            // Prepare the bean factory for use in this context.
            prepareBeanFactory(beanFactory);

            try {
                // 后置处理BeanFactory，预留的方法扩展点，子类可以在BeanFactory实例化完成后做点什么
                postProcessBeanFactory(beanFactory);

                // 调用BeanFactory后置处理器。接口扩展点
                invokeBeanFactoryPostProcessors(beanFactory);

                // 注册bean后置处理器
                registerBeanPostProcessors(beanFactory);

                // 消息本地化机制
                initMessageSource();

                // 事件广播
                initApplicationEventMulticaster();

                // 模板方法，让子类能够实例化一些特殊的bean
                // webServer就是这一步实例化的
                onRefresh();

                //注册监听器
                registerListeners();

                // 实例化所有非懒加载的bean
                finishBeanFactoryInitialization(beanFactory);

                // 完成后的一些工作
                finishRefresh();
            } catch (BeansException ex) {
                if (logger.isWarnEnabled()) {
                    logger.warn("Exception encountered during context initialization - " +
                            "cancelling refresh attempt: " + ex);
                }

                // Destroy already created singletons to avoid dangling resources.
                destroyBeans();

                // Reset 'active' flag.
                cancelRefresh(ex);

                // Propagate exception to caller.
                throw ex;
            } finally {
                // Reset common introspection caches in Spring's core, since we
                // might not ever need metadata for singleton beans anymore...
                resetCommonCaches();
            }
        }
    }
}
```

## 参考调用栈
```text
refresh:520, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refresh:747, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
main:18, SprivalApplication (com.soyokra.sprival)
```

