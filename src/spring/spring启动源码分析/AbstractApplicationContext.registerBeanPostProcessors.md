## 简述
注册Bean后置处理器（BeanPostProcessor），这些处理器会在Bean的生命周期中被调用。

这是refresh()方法的第6步，在BeanFactory后置处理器执行完成（invokeBeanFactoryPostProcessors）之后。

BeanPostProcessor是Spring的核心扩展点之一，可以在Bean实例化和初始化的前后进行处理，例如：
- 依赖注入（@Autowired）
- 注解处理（@PostConstruct）
- AOP代理创建
- 等等

## 核心流程
1. 获取所有BeanPostProcessor类型的Bean名称
2. 按优先级分组：PriorityOrdered > Ordered > 普通
3. 按顺序实例化并注册BeanPostProcessor
4. 重新注册MergedBeanDefinitionPostProcessor（移到最后）
5. 重新注册ApplicationListenerDetector（移到最后）

## 注册顺序的重要性
BeanPostProcessor的注册顺序决定了它们的执行顺序，这对于某些场景非常重要：
- **依赖注入处理器**应该在**AOP代理处理器**之前执行
- **内部处理器**应该最后执行，以便处理已经被其他处理器修改过的Bean

## 源码分析

```java
final class PostProcessorRegistrationDelegate {
    public static void registerBeanPostProcessors(
           ConfigurableListableBeanFactory beanFactory, AbstractApplicationContext applicationContext) {
    
        String[] postProcessorNames = beanFactory.getBeanNamesForType(BeanPostProcessor.class, true, false);
    
        // Register BeanPostProcessorChecker that logs an info message when
        // a bean is created during BeanPostProcessor instantiation, i.e. when
        // a bean is not eligible for getting processed by all BeanPostProcessors.
        int beanProcessorTargetCount = beanFactory.getBeanPostProcessorCount() + 1 + postProcessorNames.length;
        beanFactory.addBeanPostProcessor(new BeanPostProcessorChecker(beanFactory, beanProcessorTargetCount));
    
        // Separate between BeanPostProcessors that implement PriorityOrdered,
        // Ordered, and the rest.
        List<BeanPostProcessor> priorityOrderedPostProcessors = new ArrayList<>();
        List<BeanPostProcessor> internalPostProcessors = new ArrayList<>();
        List<String> orderedPostProcessorNames = new ArrayList<>();
        List<String> nonOrderedPostProcessorNames = new ArrayList<>();
        for (String ppName : postProcessorNames) {
           if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
              BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
              priorityOrderedPostProcessors.add(pp);
              if (pp instanceof MergedBeanDefinitionPostProcessor) {
                 internalPostProcessors.add(pp);
              }
           }
           else if (beanFactory.isTypeMatch(ppName, Ordered.class)) {
              orderedPostProcessorNames.add(ppName);
           }
           else {
              nonOrderedPostProcessorNames.add(ppName);
           }
        }
    
        // First, register the BeanPostProcessors that implement PriorityOrdered.
        sortPostProcessors(priorityOrderedPostProcessors, beanFactory);
        registerBeanPostProcessors(beanFactory, priorityOrderedPostProcessors);
    
        // Next, register the BeanPostProcessors that implement Ordered.
        List<BeanPostProcessor> orderedPostProcessors = new ArrayList<>(orderedPostProcessorNames.size());
        for (String ppName : orderedPostProcessorNames) {
           BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
           orderedPostProcessors.add(pp);
           if (pp instanceof MergedBeanDefinitionPostProcessor) {
              internalPostProcessors.add(pp);
           }
        }
        sortPostProcessors(orderedPostProcessors, beanFactory);
        registerBeanPostProcessors(beanFactory, orderedPostProcessors);
    
        // Now, register all regular BeanPostProcessors.
        List<BeanPostProcessor> nonOrderedPostProcessors = new ArrayList<>(nonOrderedPostProcessorNames.size());
        for (String ppName : nonOrderedPostProcessorNames) {
           BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
           nonOrderedPostProcessors.add(pp);
           if (pp instanceof MergedBeanDefinitionPostProcessor) {
              internalPostProcessors.add(pp);
           }
        }
        registerBeanPostProcessors(beanFactory, nonOrderedPostProcessors);
    
        // Finally, re-register all internal BeanPostProcessors.
        sortPostProcessors(internalPostProcessors, beanFactory);
        registerBeanPostProcessors(beanFactory, internalPostProcessors);
    
        // Re-register post-processor for detecting inner beans as ApplicationListeners,
        // moving it to the end of the processor chain (for picking up proxies etc).
        beanFactory.addBeanPostProcessor(new ApplicationListenerDetector(applicationContext));
    }
}
```

新注册了以下的BeanPostProcessor
```text
PostProcessorRegistrationDelegate$BeanPostProcessorChecker
ConfigurationPropertiesBindingPostProcessor
AnnotationAwareAspectJAutoProxyCreator
RabbitConnectionFactoryMetricsPostProcessor
DataSourceInitializerPostProcessor
AsyncAnnotationBeanPostProcessor
MethodValidationPostProcessor
RabbitListenerAnnotationBeanPostProcessor
PersistenceExceptionTranslationPostProcessor
WebServerFactoryCustomizerBeanPostProcessor
ErrorPageRegistrarBeanPostProcessor
HealthEndpointConfiguration$HealthEndpointGroupsBeanPostProcessor
MeterRegistryPostProcessor
CommonAnnotationBeanPostProcessor
AutowiredAnnotationBeanPostProcessor
```

之前就已经注册的BeanPostProcessor
```text
ApplicationContextAwareProcessor
ApplicationListenerDetector
WebApplicationContextServletContextAwareProcessor
ConfigurationClassPostProcessor$ImportAwareBeanPostProcessor
```

## 各类BeanPostProcessor的作用

### 核心BeanPostProcessor

| BeanPostProcessor | 作用 | 处理时机 |
|-------------------|------|----------|
| **AutowiredAnnotationBeanPostProcessor** | 处理@Autowired、@Value、@Inject | 实例化后、初始化前 |
| **CommonAnnotationBeanPostProcessor** | 处理@Resource、@PostConstruct、@PreDestroy | 实例化后、初始化前/后 |
| **ApplicationContextAwareProcessor** | 处理Aware接口回调 | 初始化前 |
| **AnnotationAwareAspectJAutoProxyCreator** | 创建AOP代理 | 初始化后 |

### 1. AutowiredAnnotationBeanPostProcessor

最常用的BeanPostProcessor，处理依赖注入：

```java
@Component
public class MyService {
    
    @Autowired  // 字段注入
    private UserRepository userRepository;
    
    @Autowired  // 方法注入
    public void setOrderService(OrderService orderService) {
        // ...
    }
    
    @Value("${app.name}")  // 配置注入
    private String appName;
    
    @Inject  // JSR-330标准注入
    private ProductService productService;
}
```

### 2. CommonAnnotationBeanPostProcessor

处理JSR-250注解：

```java
@Component
public class MyBean {
    
    @Resource(name = "userService")  // 按名称注入
    private UserService userService;
    
    @PostConstruct  // 初始化方法
    public void init() {
        System.out.println("Bean初始化完成");
    }
    
    @PreDestroy  // 销毁方法
    public void cleanup() {
        System.out.println("Bean即将销毁");
    }
}
```

### 3. ConfigurationPropertiesBindingPostProcessor

处理@ConfigurationProperties注解：

```java
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String name;
    private int timeout;
    
    // getters and setters
}
```

对应配置文件：
```properties
app.name=MyApplication
app.timeout=3000
```

### 4. AnnotationAwareAspectJAutoProxyCreator

创建AOP代理，支持@AspectJ注解：

```java
@Aspect
@Component
public class LoggingAspect {
    
    @Before("@annotation(org.springframework.web.bind.annotation.GetMapping)")
    public void logBefore(JoinPoint joinPoint) {
        System.out.println("方法执行前: " + joinPoint.getSignature());
    }
}

@RestController
public class UserController {
    
    @GetMapping("/users")  // 会被AOP拦截
    public List<User> getUsers() {
        // ...
    }
}
```

### 5. AsyncAnnotationBeanPostProcessor

处理@Async注解，支持异步方法：

```java
@Service
public class NotificationService {
    
    @Async
    public void sendEmail(String to, String subject) {
        // 异步发送邮件
        System.out.println("发送邮件到: " + to);
    }
}
```

需要配置：
```java
@Configuration
@EnableAsync
public class AsyncConfig {
    // 启用@Async支持
}
```

### 6. MethodValidationPostProcessor

支持方法级别的参数校验：

```java
@Service
@Validated
public class UserService {
    
    public void createUser(@NotNull @Valid UserDTO user) {
        // 参数会被自动校验
    }
    
    @Size(min = 1)
    public List<User> searchUsers(@NotBlank String keyword) {
        // 参数和返回值都会被校验
    }
}
```

### 7. PersistenceExceptionTranslationPostProcessor

将JPA异常转换为Spring的DataAccessException：

```java
@Repository
public class UserRepositoryImpl {
    
    @PersistenceContext
    private EntityManager entityManager;
    
    public User findById(Long id) {
        // JPA异常会被自动转换为Spring异常
        return entityManager.find(User.class, id);
    }
}
```

## BeanPostProcessor的执行时机

在Bean的生命周期中，BeanPostProcessor在以下时机被调用：

```
创建Bean实例
  ↓
属性填充 ← AutowiredAnnotationBeanPostProcessor
  ↓
Aware接口回调 ← ApplicationContextAwareProcessor
  ↓
postProcessBeforeInitialization ← CommonAnnotationBeanPostProcessor执行@PostConstruct
  ↓
InitializingBean.afterPropertiesSet()
  ↓
自定义init-method
  ↓
postProcessAfterInitialization ← AnnotationAwareAspectJAutoProxyCreator创建代理
  ↓
Bean就绪
```

## BeanPostProcessor接口

```java
public interface BeanPostProcessor {

    /**
     * 在Bean初始化之前调用
     * 可以返回原Bean或包装后的Bean
     */
    @Nullable
    default Object postProcessBeforeInitialization(Object bean, String beanName) 
            throws BeansException {
        return bean;
    }

    /**
     * 在Bean初始化之后调用
     * 可以返回原Bean或代理Bean
     */
    @Nullable
    default Object postProcessAfterInitialization(Object bean, String beanName) 
            throws BeansException {
        return bean;
    }
}
```

## 自定义BeanPostProcessor

可以实现BeanPostProcessor接口来自定义处理逻辑：

```java
@Component
public class CustomBeanPostProcessor implements BeanPostProcessor {
    
    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) {
        System.out.println("初始化前: " + beanName);
        return bean;
    }
    
    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        System.out.println("初始化后: " + beanName);
        
        // 可以在这里创建代理
        if (bean instanceof MyInterface) {
            return Proxy.newProxyInstance(
                bean.getClass().getClassLoader(),
                bean.getClass().getInterfaces(),
                (proxy, method, args) -> {
                    System.out.println("方法调用: " + method.getName());
                    return method.invoke(bean, args);
                }
            );
        }
        
        return bean;
    }
}
```

## 特殊的BeanPostProcessor

### MergedBeanDefinitionPostProcessor

在Bean实例化后立即调用，用于处理合并的Bean定义：

```java
public interface MergedBeanDefinitionPostProcessor extends BeanPostProcessor {
    
    void postProcessMergedBeanDefinition(RootBeanDefinition beanDefinition, 
                                         Class<?> beanType, 
                                         String beanName);
}
```

例如：`AutowiredAnnotationBeanPostProcessor`实现了此接口，用于缓存需要注入的字段和方法。

### InstantiationAwareBeanPostProcessor

在Bean实例化前后调用：

```java
public interface InstantiationAwareBeanPostProcessor extends BeanPostProcessor {
    
    // 在Bean实例化之前调用，可以返回代理对象代替默认实例
    @Nullable
    default Object postProcessBeforeInstantiation(Class<?> beanClass, String beanName) {
        return null;
    }
    
    // 在Bean实例化之后、属性填充之前调用
    default boolean postProcessAfterInstantiation(Object bean, String beanName) {
        return true;
    }
    
    // 处理属性值
    @Nullable
    default PropertyValues postProcessProperties(PropertyValues pvs, Object bean, String beanName) {
        return null;
    }
}
```

## 执行顺序示例

假设有以下BeanPostProcessor：

```
1. BeanPostProcessorChecker (order=无)
2. ConfigurationPropertiesBindingPostProcessor (PriorityOrdered, order=HIGHEST_PRECEDENCE+1)
3. AnnotationAwareAspectJAutoProxyCreator (Ordered, order=HIGHEST_PRECEDENCE)
4. AsyncAnnotationBeanPostProcessor (Ordered, order=HIGHEST_PRECEDENCE)
5. MethodValidationPostProcessor (无序)
6. CommonAnnotationBeanPostProcessor (最后注册，内部处理器)
7. AutowiredAnnotationBeanPostProcessor (最后注册，内部处理器)
8. ApplicationListenerDetector (最后注册)
```

执行顺序：
```
PriorityOrdered组：
  - ConfigurationPropertiesBindingPostProcessor

Ordered组：
  - AnnotationAwareAspectJAutoProxyCreator
  - AsyncAnnotationBeanPostProcessor

普通组：
  - BeanPostProcessorChecker
  - MethodValidationPostProcessor

内部组（MergedBeanDefinitionPostProcessor）：
  - CommonAnnotationBeanPostProcessor
  - AutowiredAnnotationBeanPostProcessor

最后：
  - ApplicationListenerDetector
```

## 参考调用栈

```text
registerBeanPostProcessors:710, AbstractApplicationContext (org.springframework.context.support)
refresh:536, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.invokeBeanFactoryPostProcessors](AbstractApplicationContext.invokeBeanFactoryPostProcessors.md)
- [AbstractApplicationContext.finishBeanFactoryInitialization](AbstractApplicationContext.finishBeanFactoryInitialization.md)
- [Bean生命周期图](bean_lifecycle_001.png)