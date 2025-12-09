## 简述
配置BeanFactory的标准特性，为后续的Bean创建做准备。

这是refresh()方法的第3步，在BeanFactory创建完成（obtainFreshBeanFactory）之后执行。

主要工作包括：
- 设置类加载器和表达式解析器
- 添加基础的BeanPostProcessor
- 忽略特定的依赖接口（Aware接口）
- 注册可解析的依赖（BeanFactory、ApplicationContext等）
- 注册环境相关的单例Bean

## 核心流程
1. 设置BeanFactory的ClassLoader和SpEL表达式解析器
2. 添加ApplicationContextAwareProcessor（处理Aware接口回调）
3. 忽略Aware接口的自动装配
4. 注册可解析依赖（BeanFactory、ResourceLoader等）
5. 注册环境Bean（environment、systemProperties等）

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {
	protected void prepareBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // Tell the internal bean factory to use the context's class loader etc.
        beanFactory.setBeanClassLoader(getClassLoader());
        beanFactory.setBeanExpressionResolver(new StandardBeanExpressionResolver(beanFactory.getBeanClassLoader()));
        beanFactory.addPropertyEditorRegistrar(new ResourceEditorRegistrar(this, getEnvironment()));
    
        // Configure the bean factory with context callbacks.
        beanFactory.addBeanPostProcessor(new ApplicationContextAwareProcessor(this));
        beanFactory.ignoreDependencyInterface(EnvironmentAware.class);
        beanFactory.ignoreDependencyInterface(EmbeddedValueResolverAware.class);
        beanFactory.ignoreDependencyInterface(ResourceLoaderAware.class);
        beanFactory.ignoreDependencyInterface(ApplicationEventPublisherAware.class);
        beanFactory.ignoreDependencyInterface(MessageSourceAware.class);
        beanFactory.ignoreDependencyInterface(ApplicationContextAware.class);
    
        // BeanFactory interface not registered as resolvable type in a plain factory.
        // MessageSource registered (and found for autowiring) as a bean.
        beanFactory.registerResolvableDependency(BeanFactory.class, beanFactory);
        beanFactory.registerResolvableDependency(ResourceLoader.class, this);
        beanFactory.registerResolvableDependency(ApplicationEventPublisher.class, this);
        beanFactory.registerResolvableDependency(ApplicationContext.class, this);
    
        // Register early post-processor for detecting inner beans as ApplicationListeners.
        beanFactory.addBeanPostProcessor(new ApplicationListenerDetector(this));
    
        // Detect a LoadTimeWeaver and prepare for weaving, if found.
        if (beanFactory.containsBean(LOAD_TIME_WEAVER_BEAN_NAME)) {
            beanFactory.addBeanPostProcessor(new LoadTimeWeaverAwareProcessor(beanFactory));
            // Set a temporary ClassLoader for type matching.
            beanFactory.setTempClassLoader(new ContextTypeMatchClassLoader(beanFactory.getBeanClassLoader()));
        }
    
        // Register default environment beans.
        if (!beanFactory.containsLocalBean(ENVIRONMENT_BEAN_NAME)) {
            beanFactory.registerSingleton(ENVIRONMENT_BEAN_NAME, getEnvironment());
        }
        if (!beanFactory.containsLocalBean(SYSTEM_PROPERTIES_BEAN_NAME)) {
            beanFactory.registerSingleton(SYSTEM_PROPERTIES_BEAN_NAME, getEnvironment().getSystemProperties());
        }
        if (!beanFactory.containsLocalBean(SYSTEM_ENVIRONMENT_BEAN_NAME)) {
            beanFactory.registerSingleton(SYSTEM_ENVIRONMENT_BEAN_NAME, getEnvironment().getSystemEnvironment());
        }
    }
}
```

## 各项配置的作用详解

### 1. 设置ClassLoader

```java
beanFactory.setBeanClassLoader(getClassLoader());
```

作用：
- BeanFactory使用此ClassLoader加载Bean的Class
- 默认使用Thread.currentThread().getContextClassLoader()
- 确保Bean类可以被正确加载

### 2. 设置SpEL表达式解析器

```java
beanFactory.setBeanExpressionResolver(new StandardBeanExpressionResolver(beanFactory.getBeanClassLoader()));
```

作用：
- 用于解析Bean定义中的SpEL表达式
- 支持`#{}`语法，例如：`@Value("#{systemProperties['user.home']}")`
- 可以在XML配置中使用：`<property name="age" value="#{userBean.age + 10}"/>`

### 3. 添加属性编辑器注册器

```java
beanFactory.addPropertyEditorRegistrar(new ResourceEditorRegistrar(this, getEnvironment()));
```

作用：
- 注册一系列属性编辑器（PropertyEditor）
- 用于类型转换，例如String→File、String→URL等
- 支持Resource类型的自动转换

常见的PropertyEditor：
- FileEditor: String → File
- URLEditor: String → URL
- ClassEditor: String → Class
- ResourceEditor: String → Resource

### 4. 添加ApplicationContextAwareProcessor

```java
beanFactory.addBeanPostProcessor(new ApplicationContextAwareProcessor(this));
```

作用：
- 处理各种Aware接口的回调
- 在Bean初始化前注入容器相关对象

ApplicationContextAwareProcessor处理的Aware接口：
- **EnvironmentAware**: 注入Environment
- **EmbeddedValueResolverAware**: 注入值解析器
- **ResourceLoaderAware**: 注入ResourceLoader
- **ApplicationEventPublisherAware**: 注入事件发布器
- **MessageSourceAware**: 注入MessageSource
- **ApplicationContextAware**: 注入ApplicationContext

示例：
```java
@Component
public class MyBean implements ApplicationContextAware {
    
    private ApplicationContext context;
    
    @Override
    public void setApplicationContext(ApplicationContext context) {
        this.context = context;
        // 可以在这里使用ApplicationContext
    }
}
```

### 5. 忽略Aware接口的自动装配

```java
beanFactory.ignoreDependencyInterface(EnvironmentAware.class);
beanFactory.ignoreDependencyInterface(EmbeddedValueResolverAware.class);
beanFactory.ignoreDependencyInterface(ResourceLoaderAware.class);
beanFactory.ignoreDependencyInterface(ApplicationEventPublisherAware.class);
beanFactory.ignoreDependencyInterface(MessageSourceAware.class);
beanFactory.ignoreDependencyInterface(ApplicationContextAware.class);
```

作用：
- 防止这些接口通过@Autowired等方式被自动装配
- 这些接口的setter方法由ApplicationContextAwareProcessor专门处理
- 避免冲突和重复注入

### 6. 注册可解析依赖

```java
beanFactory.registerResolvableDependency(BeanFactory.class, beanFactory);
beanFactory.registerResolvableDependency(ResourceLoader.class, this);
beanFactory.registerResolvableDependency(ApplicationEventPublisher.class, this);
beanFactory.registerResolvableDependency(ApplicationContext.class, this);
```

作用：
- 允许直接注入这些类型，即使它们不是Bean
- 注入时会使用这里注册的实例

示例：
```java
@Component
public class MyService {
    
    // 可以直接注入，不需要定义Bean
    @Autowired
    private ApplicationContext context;
    
    @Autowired
    private BeanFactory beanFactory;
    
    @Autowired
    private ResourceLoader resourceLoader;
}
```

### 7. 添加ApplicationListenerDetector

```java
beanFactory.addBeanPostProcessor(new ApplicationListenerDetector(this));
```

作用：
- 检测实现了ApplicationListener接口的Bean
- 自动将它们注册为事件监听器
- 在Bean销毁时自动移除

### 8. 处理LoadTimeWeaver

```java
if (beanFactory.containsBean(LOAD_TIME_WEAVER_BEAN_NAME)) {
    beanFactory.addBeanPostProcessor(new LoadTimeWeaverAwareProcessor(beanFactory));
    beanFactory.setTempClassLoader(new ContextTypeMatchClassLoader(beanFactory.getBeanClassLoader()));
}
```

作用：
- 支持AspectJ的加载时织入（Load-Time Weaving）
- 用于在类加载时进行字节码增强
- 需要JVM启动参数：`-javaagent:spring-instrument.jar`

### 9. 注册环境Bean

```java
if (!beanFactory.containsLocalBean(ENVIRONMENT_BEAN_NAME)) {
    beanFactory.registerSingleton(ENVIRONMENT_BEAN_NAME, getEnvironment());
}
if (!beanFactory.containsLocalBean(SYSTEM_PROPERTIES_BEAN_NAME)) {
    beanFactory.registerSingleton(SYSTEM_PROPERTIES_BEAN_NAME, getEnvironment().getSystemProperties());
}
if (!beanFactory.containsLocalBean(SYSTEM_ENVIRONMENT_BEAN_NAME)) {
    beanFactory.registerSingleton(SYSTEM_ENVIRONMENT_BEAN_NAME, getEnvironment().getSystemEnvironment());
}
```

作用：
- 注册环境相关的单例Bean
- 可以直接注入使用

注册的Bean：
- **environment**: StandardEnvironment实例
- **systemProperties**: System.getProperties()
- **systemEnvironment**: System.getenv()

示例：
```java
@Component
public class MyConfig {
    
    @Autowired
    @Qualifier("systemProperties")
    private Map<String, Object> systemProperties;
    
    @Autowired
    @Qualifier("systemEnvironment")
    private Map<String, Object> systemEnvironment;
    
    public void printInfo() {
        System.out.println("Java Home: " + systemProperties.get("java.home"));
        System.out.println("PATH: " + systemEnvironment.get("PATH"));
    }
}
```

## BeanPostProcessor的作用

此阶段添加的BeanPostProcessor会在Bean实例化过程中起作用：

| BeanPostProcessor | 作用时机 | 主要功能 |
|-------------------|----------|----------|
| ApplicationContextAwareProcessor | 初始化前 | 处理Aware接口回调 |
| ApplicationListenerDetector | 初始化后 | 注册ApplicationListener |
| LoadTimeWeaverAwareProcessor | 初始化前 | 处理LoadTimeWeaverAware |

## 执行时机

在prepareBeanFactory执行时：
- ✅ BeanFactory已创建
- ✅ 可以配置BeanFactory
- ❌ BeanDefinition还未注册（在invokeBeanFactoryPostProcessors中注册）
- ❌ Bean还未实例化

## 参考调用栈

```text
prepareBeanFactory:665, AbstractApplicationContext (org.springframework.context.support)
refresh:525, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.obtainFreshBeanFactory](AbstractApplicationContext.obtainFreshBeanFactory.md)
- [AbstractApplicationContext.postProcessBeanFactory](AbstractApplicationContext.postProcessBeanFactory.md)
- [AbstractApplicationContext.invokeBeanFactoryPostProcessors](AbstractApplicationContext.invokeBeanFactoryPostProcessors.md)