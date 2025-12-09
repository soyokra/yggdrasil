## 简述
获取刷新后的BeanFactory，这是refresh()方法的第二步。

对于SpringBoot应用来说，使用的是GenericApplicationContext，BeanFactory在创建ApplicationContext时就已经实例化好了，这一步只是简单地返回已有的BeanFactory。

如果是传统的Spring应用（如XML配置），会在这一步重新创建BeanFactory并加载Bean定义。

## 核心流程
1. 调用子类的refreshBeanFactory()方法
2. 对于GenericApplicationContext：只是设置refreshed标志为true
3. 对于AbstractRefreshableApplicationContext：会销毁旧的BeanFactory，创建新的DefaultListableBeanFactory
4. 返回BeanFactory实例

## 源码分析

AbstractApplicationContext中的方法：
```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    protected ConfigurableListableBeanFactory obtainFreshBeanFactory() {
        // 刷新BeanFactory，由子类实现
        refreshBeanFactory();
        // 返回BeanFactory实例
        return getBeanFactory();
    }

    protected abstract void refreshBeanFactory() throws BeansException, IllegalStateException;

    public abstract ConfigurableListableBeanFactory getBeanFactory() throws IllegalStateException;
}
```

SpringBoot使用的GenericApplicationContext实现：
```java
public class GenericApplicationContext extends AbstractApplicationContext implements BeanDefinitionRegistry {

    private final DefaultListableBeanFactory beanFactory;
    
    private final AtomicBoolean refreshed = new AtomicBoolean();

    public GenericApplicationContext() {
        // BeanFactory在构造方法中就创建了
        this.beanFactory = new DefaultListableBeanFactory();
    }

    @Override
    protected final void refreshBeanFactory() throws IllegalStateException {
        // 只允许刷新一次
        if (!this.refreshed.compareAndSet(false, true)) {
            throw new IllegalStateException(
                    "GenericApplicationContext does not support multiple refresh attempts: just call 'refresh' once");
        }
        this.beanFactory.setSerializationId(getId());
    }

    @Override
    public final ConfigurableListableBeanFactory getBeanFactory() {
        return this.beanFactory;
    }
}
```

传统Spring应用使用的AbstractRefreshableApplicationContext实现（供参考）：
```java
public abstract class AbstractRefreshableApplicationContext extends AbstractApplicationContext {

    private DefaultListableBeanFactory beanFactory;

    @Override
    protected final void refreshBeanFactory() throws BeansException {
        // 如果已有BeanFactory，先销毁
        if (hasBeanFactory()) {
            destroyBeans();
            closeBeanFactory();
        }
        try {
            // 创建新的BeanFactory
            DefaultListableBeanFactory beanFactory = createBeanFactory();
            beanFactory.setSerializationId(getId());
            customizeBeanFactory(beanFactory);
            // 加载Bean定义（XML配置）
            loadBeanDefinitions(beanFactory);
            this.beanFactory = beanFactory;
        }
        catch (IOException ex) {
            throw new ApplicationContextException("I/O error parsing bean definition source", ex);
        }
    }
}
```

## GenericApplicationContext与DefaultListableBeanFactory的关系

- **GenericApplicationContext**：ApplicationContext的实现类，提供完整的应用上下文功能
- **DefaultListableBeanFactory**：BeanFactory的默认实现，负责Bean的管理和依赖注入
- GenericApplicationContext通过组合的方式持有DefaultListableBeanFactory实例
- GenericApplicationContext提供高层功能（事件、资源、环境），委托BeanFactory处理Bean相关操作

## SpringBoot的优势
与传统Spring XML配置方式不同，SpringBoot在创建ApplicationContext时就初始化了BeanFactory，不需要在refresh时重新创建，这使得：
1. refresh()方法可以被多次调用（在某些测试场景中）
2. 可以在refresh之前通过编程方式注册Bean定义
3. 启动性能更好，避免重复创建对象

## 参考调用栈
```text
obtainFreshBeanFactory:620, AbstractApplicationContext (org.springframework.context.support)
refresh:522, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

