## 简述
完成BeanFactory的初始化工作，实例化所有非懒加载的单例Bean。

这是refresh()方法的第11步，也是最重要的步骤之一，在这一步中会创建应用中的所有Bean实例。

## 核心流程
1. 初始化ConversionService（类型转换服务）
2. 注册默认的值解析器（用于处理@Value等占位符）
3. 提前初始化LoadTimeWeaverAware类型的Bean（AOP相关）
4. 停止使用临时ClassLoader
5. 冻结BeanDefinition配置（不允许再修改）
6. **实例化所有非懒加载的单例Bean**（核心）

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    protected void finishBeanFactoryInitialization(ConfigurableListableBeanFactory beanFactory) {
        // 1. 初始化类型转换服务，用于Bean属性的类型转换
        if (beanFactory.containsBean(CONVERSION_SERVICE_BEAN_NAME) &&
                beanFactory.isTypeMatch(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class)) {
            beanFactory.setConversionService(
                    beanFactory.getBean(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class));
        }

        // 2. 注册默认的值解析器（如果没有BeanFactoryPostProcessor注册过）
        // 用于解析@Value注解中的${...}占位符
        if (!beanFactory.hasEmbeddedValueResolver()) {
            beanFactory.addEmbeddedValueResolver(strVal -> getEnvironment().resolvePlaceholders(strVal));
        }

        // 3. 提前初始化LoadTimeWeaverAware类型的Bean
        // 允许尽早注册它们的转换器（用于AOP字节码增强）
        String[] weaverAwareNames = beanFactory.getBeanNamesForType(LoadTimeWeaverAware.class, false, false);
        for (String weaverAwareName : weaverAwareNames) {
            getBean(weaverAwareName);
        }

        // 4. 停止使用临时ClassLoader进行类型匹配
        beanFactory.setTempClassLoader(null);

        // 5. 冻结配置，缓存所有BeanDefinition元数据
        // 此后不再期望有进一步的修改
        beanFactory.freezeConfiguration();

        // 6. 实例化所有剩余的（非懒加载）单例Bean
        beanFactory.preInstantiateSingletons();
    }
}
```

## preInstantiateSingletons详细过程

DefaultListableBeanFactory中的实现：

```java
public class DefaultListableBeanFactory extends AbstractAutowireCapableBeanFactory
        implements ConfigurableListableBeanFactory, BeanDefinitionRegistry {

    @Override
    public void preInstantiateSingletons() throws BeansException {
        List<String> beanNames = new ArrayList<>(this.beanDefinitionNames);

        // 第一阶段：实例化所有非懒加载的单例Bean
        for (String beanName : beanNames) {
            RootBeanDefinition bd = getMergedLocalBeanDefinition(beanName);
            
            // 不是抽象的 && 是单例 && 不是懒加载
            if (!bd.isAbstract() && bd.isSingleton() && !bd.isLazyInit()) {
                if (isFactoryBean(beanName)) {
                    // 如果是FactoryBean，先获取FactoryBean实例
                    Object bean = getBean(FACTORY_BEAN_PREFIX + beanName);
                    if (bean instanceof FactoryBean) {
                        FactoryBean<?> factory = (FactoryBean<?>) bean;
                        boolean isEagerInit = (factory instanceof SmartFactoryBean &&
                                ((SmartFactoryBean<?>) factory).isEagerInit());
                        if (isEagerInit) {
                            // 如果是SmartFactoryBean且设置为提前初始化
                            getBean(beanName);
                        }
                    }
                }
                else {
                    // 普通Bean，直接获取（触发实例化）
                    getBean(beanName);
                }
            }
        }

        // 第二阶段：触发所有SmartInitializingSingleton的回调
        // 在所有单例Bean实例化完成后执行
        for (String beanName : beanNames) {
            Object singletonInstance = getSingleton(beanName);
            if (singletonInstance instanceof SmartInitializingSingleton) {
                SmartInitializingSingleton smartSingleton = (SmartInitializingSingleton) singletonInstance;
                smartSingleton.afterSingletonsInstantiated();
            }
        }
    }
}
```

## Bean的完整生命周期

在preInstantiateSingletons调用getBean时，会触发Bean的完整生命周期：

```mermaid
graph TD
    A[getBean] --> B[实例化Bean]
    B --> C[属性填充]
    C --> D[Aware接口回调]
    D --> E[BeanPostProcessor.before]
    E --> F[初始化方法]
    F --> G[BeanPostProcessor.after]
    G --> H[Bean就绪]
    
    D --> D1[BeanNameAware]
    D --> D2[BeanFactoryAware]
    D --> D3[ApplicationContextAware]
    
    F --> F1[@PostConstruct]
    F --> F2[InitializingBean.afterPropertiesSet]
    F --> F3[自定义init-method]
```

### Bean实例化的详细步骤

1. **实例化（Instantiation）**：创建Bean对象实例
   - 通过构造函数反射创建
   - 或通过工厂方法创建

2. **属性填充（Populate Properties）**：注入依赖
   - @Autowired字段注入
   - Setter方法注入
   - 构造函数注入

3. **Aware接口回调**：注入容器相关对象
   - BeanNameAware：注入Bean名称
   - BeanFactoryAware：注入BeanFactory
   - ApplicationContextAware：注入ApplicationContext

4. **BeanPostProcessor前置处理**
   - 执行所有BeanPostProcessor.postProcessBeforeInitialization
   - 例如：@PostConstruct注解的方法在这里执行

5. **初始化方法执行**
   - InitializingBean.afterPropertiesSet()
   - 自定义init-method

6. **BeanPostProcessor后置处理**
   - 执行所有BeanPostProcessor.postProcessAfterInitialization
   - AOP代理在这里创建（如果需要）

7. **Bean就绪**：可以被应用使用

8. **销毁（容器关闭时）**
   - @PreDestroy方法
   - DisposableBean.destroy()
   - 自定义destroy-method

## 重要的BeanPostProcessor

在Bean实例化过程中，以下BeanPostProcessor会起作用：

| BeanPostProcessor | 作用 |
|-------------------|------|
| AutowiredAnnotationBeanPostProcessor | 处理@Autowired、@Value、@Inject注解 |
| CommonAnnotationBeanPostProcessor | 处理@Resource、@PostConstruct、@PreDestroy注解 |
| ApplicationContextAwareProcessor | 处理Aware接口回调 |
| AnnotationAwareAspectJAutoProxyCreator | 创建AOP代理 |

## 循环依赖的处理

Spring通过三级缓存解决单例Bean的循环依赖：

1. **singletonObjects**：一级缓存，存放完全初始化好的Bean
2. **earlySingletonObjects**：二级缓存，存放早期暴露的Bean（未完成属性填充）
3. **singletonFactories**：三级缓存，存放Bean工厂

只有单例Bean的setter注入能解决循环依赖，构造函数注入和原型Bean无法解决。

## SmartInitializingSingleton回调

在所有单例Bean实例化完成后，会回调实现了SmartInitializingSingleton接口的Bean：

```java
public interface SmartInitializingSingleton {
    void afterSingletonsInstantiated();
}
```

典型应用：
- **EventListenerMethodProcessor**：在这里处理@EventListener注解
- **ScheduledAnnotationBeanPostProcessor**：在这里处理@Scheduled注解

## 参考调用栈

```text
preInstantiateSingletons:862, DefaultListableBeanFactory (org.springframework.beans.factory.support)
finishBeanFactoryInitialization:877, AbstractApplicationContext (org.springframework.context.support)
refresh:549, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关文档
- [Bean生命周期图示](bean_lifecycle_001.png)
- [Bean生命周期详细图](bean_lifecycle_002.png)