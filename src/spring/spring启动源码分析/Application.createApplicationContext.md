## 简介
createApplicationContext方法主要功能是为了实例化一个Context

实际上的Context实例是AnnotationConfigServletWebServerApplicationContext这个类的实例

同时在构造方法设置了对象属性

实例化AnnotatedBeanDefinitionReader类作为reader属性

实例化ClassPathBeanDefinitionScanner作为scanner属性

获取的AppClassLoader作为classLoader属性

实例化DefaultListableBeanFactory作为beanFactory属性

## 源码分析
servlet应用类型创建的context是AnnotationConfigServletWebServerApplicationContext

```java
public class SpringApplication {
    protected ConfigurableApplicationContext createApplicationContext() {
        Class<?> contextClass = this.applicationContextClass;
        if (contextClass == null) {
            try {
                switch (this.webApplicationType) {
                    case SERVLET:
                        contextClass = Class.forName(DEFAULT_SERVLET_WEB_CONTEXT_CLASS);
                        break;
                    case REACTIVE:
                        contextClass = Class.forName(DEFAULT_REACTIVE_WEB_CONTEXT_CLASS);
                        break;
                    default:
                        contextClass = Class.forName(DEFAULT_CONTEXT_CLASS);
                }
            }
            catch (ClassNotFoundException ex) {
                throw new IllegalStateException(
                        "Unable create a default ApplicationContext, please specify an ApplicationContextClass", ex);
            }
        }
        return (ConfigurableApplicationContext) BeanUtils.instantiateClass(contextClass);
    }
}
```


使用BeanUtils.instantiateClass方法，主要是通过反射机制实例化指定类的对象

```text
(ConfigurableApplicationContext) BeanUtils.instantiateClass(Class.forName(DEFAULT_SERVLET_WEB_CONTEXT_CLASS));
```


经过链路
```text
<init>:73, AnnotationConfigServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
newInstance0:-1, NativeConstructorAccessorImpl (sun.reflect)
newInstance:62, NativeConstructorAccessorImpl (sun.reflect)
newInstance:45, DelegatingConstructorAccessorImpl (sun.reflect)
newInstance:423, Constructor (java.lang.reflect)
instantiateClass:204, BeanUtils (org.springframework.beans)
instantiateClass:139, BeanUtils (org.springframework.beans)
instantiateClass:204, BeanUtils (org.springframework.beans)
instantiateClass:139, BeanUtils (org.springframework.beans)
```

调用了AnnotationConfigServletWebServerApplicationContext的构造方法，初始化reader和scanner

```java
public class AnnotationConfigServletWebServerApplicationContext extends ServletWebServerApplicationContext
		implements AnnotationConfigRegistry {
    public AnnotationConfigServletWebServerApplicationContext() {
        this.reader = new AnnotatedBeanDefinitionReader(this);
        this.scanner = new ClassPathBeanDefinitionScanner(this);
    }
}
```

默认会先调用父类的无参构造方法，初始化了类加载器(classLoader)，类加载器使用的是AppClassLoader；bean工厂(beanFactory)，bean工厂使用的是DefaultListableBeanFactory

```java

public class GenericApplicationContext extends AbstractApplicationContext implements BeanDefinitionRegistry {
    public GenericApplicationContext() {
        this.beanFactory = new DefaultListableBeanFactory();
    }
}

public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {
    public AbstractApplicationContext() {
        this.resourcePatternResolver = getResourcePatternResolver();
    }
}

public class DefaultResourceLoader implements ResourceLoader {
    public DefaultResourceLoader() {
        this.classLoader = ClassUtils.getDefaultClassLoader();
    }
}

```

实例化AnnotatedBeanDefinitionReader，调用构造方法

```java
public class AnnotatedBeanDefinitionReader {
    public AnnotatedBeanDefinitionReader(BeanDefinitionRegistry registry) {
        this(registry, getOrCreateEnvironment(registry));
    }

    public AnnotatedBeanDefinitionReader(BeanDefinitionRegistry registry, Environment environment) {
        Assert.notNull(registry, "BeanDefinitionRegistry must not be null");
        Assert.notNull(environment, "Environment must not be null");
        this.registry = registry;
        this.conditionEvaluator = new ConditionEvaluator(registry, environment, null);
        AnnotationConfigUtils.registerAnnotationConfigProcessors(this.registry);
    }
}
```

调用到AnnotationConfigUtils的registerAnnotationConfigProcessors，通过 registry.registerBeanDefinition(beanName, definition)注册了5个RootBeanDefinition到
AnnotationConfigServletWebServerApplicationContext
```java
public abstract class AnnotationConfigUtils {
    public static Set<BeanDefinitionHolder> registerAnnotationConfigProcessors(
            BeanDefinitionRegistry registry, @Nullable Object source) {

        DefaultListableBeanFactory beanFactory = unwrapDefaultListableBeanFactory(registry);
        if (beanFactory != null) {
            if (!(beanFactory.getDependencyComparator() instanceof AnnotationAwareOrderComparator)) {
                beanFactory.setDependencyComparator(AnnotationAwareOrderComparator.INSTANCE);
            }
            if (!(beanFactory.getAutowireCandidateResolver() instanceof ContextAnnotationAutowireCandidateResolver)) {
                beanFactory.setAutowireCandidateResolver(new ContextAnnotationAutowireCandidateResolver());
            }
        }

        Set<BeanDefinitionHolder> beanDefs = new LinkedHashSet<>(8);

        if (!registry.containsBeanDefinition(CONFIGURATION_ANNOTATION_PROCESSOR_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition(ConfigurationClassPostProcessor.class);
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, CONFIGURATION_ANNOTATION_PROCESSOR_BEAN_NAME));
        }

        if (!registry.containsBeanDefinition(AUTOWIRED_ANNOTATION_PROCESSOR_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition(AutowiredAnnotationBeanPostProcessor.class);
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, AUTOWIRED_ANNOTATION_PROCESSOR_BEAN_NAME));
        }

        // Check for JSR-250 support, and if present add the CommonAnnotationBeanPostProcessor.
        if (jsr250Present && !registry.containsBeanDefinition(COMMON_ANNOTATION_PROCESSOR_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition(CommonAnnotationBeanPostProcessor.class);
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, COMMON_ANNOTATION_PROCESSOR_BEAN_NAME));
        }

        // Check for JPA support, and if present add the PersistenceAnnotationBeanPostProcessor.
        if (jpaPresent && !registry.containsBeanDefinition(PERSISTENCE_ANNOTATION_PROCESSOR_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition();
            try {
                def.setBeanClass(ClassUtils.forName(PERSISTENCE_ANNOTATION_PROCESSOR_CLASS_NAME,
                        AnnotationConfigUtils.class.getClassLoader()));
            }
            catch (ClassNotFoundException ex) {
                throw new IllegalStateException(
                        "Cannot load optional framework class: " + PERSISTENCE_ANNOTATION_PROCESSOR_CLASS_NAME, ex);
            }
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, PERSISTENCE_ANNOTATION_PROCESSOR_BEAN_NAME));
        }

        if (!registry.containsBeanDefinition(EVENT_LISTENER_PROCESSOR_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition(EventListenerMethodProcessor.class);
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, EVENT_LISTENER_PROCESSOR_BEAN_NAME));
        }

        if (!registry.containsBeanDefinition(EVENT_LISTENER_FACTORY_BEAN_NAME)) {
            RootBeanDefinition def = new RootBeanDefinition(DefaultEventListenerFactory.class);
            def.setSource(source);
            beanDefs.add(registerPostProcessor(registry, def, EVENT_LISTENER_FACTORY_BEAN_NAME));
        }

        return beanDefs;
    }

    private static BeanDefinitionHolder registerPostProcessor(
            BeanDefinitionRegistry registry, RootBeanDefinition definition, String beanName) {

        definition.setRole(BeanDefinition.ROLE_INFRASTRUCTURE);
        registry.registerBeanDefinition(beanName, definition);
        return new BeanDefinitionHolder(definition, beanName);
    }
    
}
```

5个RootBeanDefinition

```text
ConfigurationClassPostProcessor
AutowiredAnnotationBeanPostProcessor
CommonAnnotationBeanPostProcessor
EventListenerProcessor
EventListenerFactory
```


