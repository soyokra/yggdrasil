## 简述
重置Spring核心的通用内省缓存，减少内存占用。

这是refresh()方法finally块中的最后一步，无论refresh成功还是失败都会执行。

在refresh完成后，某些用于类型分析的元数据缓存可能不再需要，清理这些缓存可以释放内存。

## 核心流程
1. 清理ReflectionUtils的缓存
2. 清理AnnotationUtils的缓存
3. 清理ResolvableType的缓存
4. 清理CachedIntrospectionResults的缓存

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 准备刷新
            
            try {
                // ... 各种初始化步骤
            }
            catch (BeansException ex) {
                // 异常处理
                destroyBeans();
                cancelRefresh(ex);
                throw ex;
            }
            finally {
                // 无论成功还是失败，都清理缓存
                // 因为我们可能不再需要单例Bean的元数据了
                resetCommonCaches();
            }
        }
    }

    /**
     * 重置Spring核心中的通用内省缓存
     * 从Spring 4.2开始，因为我们可能不再需要单例Bean的元数据
     */
    protected void resetCommonCaches() {
        ReflectionUtils.clearCache();
        AnnotationUtils.clearCache();
        ResolvableType.clearCache();
        CachedIntrospectionResults.clearClassLoader(getClassLoader());
    }
}
```

## 各个缓存的作用

### 1. ReflectionUtils缓存

ReflectionUtils缓存反射相关的信息以提高性能：

```java
public abstract class ReflectionUtils {

    /**
     * 方法缓存：Class -> Method数组
     * 缓存类的所有声明方法
     */
    private static final Map<Class<?>, Method[]> declaredMethodsCache = 
            new ConcurrentReferenceHashMap<>(256);

    /**
     * 字段缓存：Class -> Field数组
     * 缓存类的所有声明字段
     */
    private static final Map<Class<?>, Field[]> declaredFieldsCache = 
            new ConcurrentReferenceHashMap<>(256);

    /**
     * 清理缓存
     */
    public static void clearCache() {
        declaredMethodsCache.clear();
        declaredFieldsCache.clear();
    }

    /**
     * 获取类的所有方法（使用缓存）
     */
    private static Method[] getDeclaredMethods(Class<?> clazz) {
        Method[] result = declaredMethodsCache.get(clazz);
        if (result == null) {
            try {
                Method[] declaredMethods = clazz.getDeclaredMethods();
                // 过滤合成方法等
                List<Method> defaultMethods = findConcreteMethodsOnInterfaces(clazz);
                if (defaultMethods != null) {
                    result = new Method[declaredMethods.length + defaultMethods.size()];
                    System.arraycopy(declaredMethods, 0, result, 0, declaredMethods.length);
                    int index = declaredMethods.length;
                    for (Method defaultMethod : defaultMethods) {
                        result[index] = defaultMethod;
                        index++;
                    }
                }
                else {
                    result = declaredMethods;
                }
                declaredMethodsCache.put(clazz, result);
            }
            catch (Throwable ex) {
                throw new IllegalStateException("Failed to introspect Class [" + 
                        clazz.getName() + "]", ex);
            }
        }
        return result;
    }
}
```

用途：
- 在Bean实例化时查找构造函数
- 在依赖注入时查找字段和方法
- 在AOP代理时分析方法

### 2. AnnotationUtils缓存

AnnotationUtils缓存注解查找结果：

```java
public abstract class AnnotationUtils {

    /**
     * 注解属性缓存
     */
    private static final Map<AnnotationCacheKey, Annotation> findAnnotationCache = 
            new ConcurrentReferenceHashMap<>(256);

    /**
     * 可合成注解缓存
     */
    private static final Map<AnnotationCacheKey, Boolean> metaPresentCache = 
            new ConcurrentReferenceHashMap<>(256);

    /**
     * 清理缓存
     */
    static void clearCache() {
        findAnnotationCache.clear();
        metaPresentCache.clear();
        // 其他缓存...
    }

    /**
     * 查找注解（使用缓存）
     */
    @Nullable
    public static <A extends Annotation> A findAnnotation(Class<?> clazz, 
            @Nullable Class<A> annotationType) {
        if (annotationType == null) {
            return null;
        }
        
        AnnotationCacheKey cacheKey = new AnnotationCacheKey(clazz, annotationType);
        A result = (A) findAnnotationCache.get(cacheKey);
        if (result == null) {
            result = findAnnotation(clazz, annotationType, new HashSet<>());
            if (result != null) {
                findAnnotationCache.put(cacheKey, result);
            }
        }
        return result;
    }
}
```

用途：
- 查找类上的注解（@Component、@Service等）
- 查找方法上的注解（@Autowired、@Transactional等）
- 查找元注解（注解的注解）

### 3. ResolvableType缓存

ResolvableType缓存泛型类型信息：

```java
public class ResolvableType implements Serializable {

    /**
     * 类型缓存：Type -> ResolvableType
     */
    private static final ConcurrentReferenceHashMap<ResolvableType, ResolvableType> cache = 
            new ConcurrentReferenceHashMap<>(256);

    /**
     * 清理缓存
     */
    public static void clearCache() {
        cache.clear();
        SerializableTypeWrapper.cache.clear();
    }

    /**
     * 获取ResolvableType（使用缓存）
     */
    public static ResolvableType forType(@Nullable Type type) {
        return forType(type, null, null);
    }

    static ResolvableType forType(@Nullable Type type, 
            @Nullable TypeProvider typeProvider, 
            @Nullable VariableResolver variableResolver) {
        if (type == null && typeProvider != null) {
            type = SerializableTypeWrapper.forTypeProvider(typeProvider);
        }
        if (type == null) {
            return NONE;
        }

        ResolvableType resultType = new ResolvableType(type, typeProvider, variableResolver);
        ResolvableType cachedType = cache.get(resultType);
        if (cachedType == null) {
            cachedType = resultType;
            cache.put(cachedType, cachedType);
        }
        return cachedType;
    }
}
```

用途：
- 解析泛型类型（List<String>、Map<String, Object>等）
- 匹配Bean的类型
- 事件监听器的类型匹配

### 4. CachedIntrospectionResults缓存

CachedIntrospectionResults缓存JavaBeans内省结果：

```java
public final class CachedIntrospectionResults {

    /**
     * 类加载器 -> 内省结果映射
     */
    static final ConcurrentMap<Class<?>, CachedIntrospectionResults> strongClassCache = 
            new ConcurrentHashMap<>(64);

    static final ConcurrentMap<Class<?>, CachedIntrospectionResults> softClassCache = 
            new ConcurrentReferenceHashMap<>(64);

    /**
     * 接受的类加载器集合
     */
    private static final Set<ClassLoader> acceptedClassLoaders = 
            Collections.newSetFromMap(new ConcurrentHashMap<>(16));

    /**
     * 清理指定类加载器的缓存
     */
    public static void clearClassLoader(@Nullable ClassLoader classLoader) {
        acceptedClassLoaders.removeIf(registeredLoader ->
                isUnderneathClassLoader(registeredLoader, classLoader));
        
        strongClassCache.keySet().removeIf(beanClass ->
                isUnderneathClassLoader(beanClass.getClassLoader(), classLoader));
        
        softClassCache.keySet().removeIf(beanClass ->
                isUnderneathClassLoader(beanClass.getClassLoader(), classLoader));
    }

    /**
     * 判断是否是子类加载器
     */
    private static boolean isUnderneathClassLoader(@Nullable ClassLoader candidate, 
            @Nullable ClassLoader parent) {
        if (candidate == parent) {
            return true;
        }
        if (candidate == null) {
            return false;
        }
        ClassLoader classLoaderToCheck = candidate;
        while (classLoaderToCheck != null) {
            classLoaderToCheck = classLoaderToCheck.getParent();
            if (classLoaderToCheck == parent) {
                return true;
            }
        }
        return false;
    }
}
```

用途：
- 缓存Bean的属性描述符（PropertyDescriptor）
- 用于属性绑定和数据绑定
- 提高BeanWrapper的性能

## 为什么要清理缓存？

### 1. 减少内存占用

在refresh完成后：
- 所有Bean已经实例化完成
- 元数据缓存主要在Bean创建阶段使用
- 清理缓存可以释放可观的内存

### 2. 避免内存泄漏

某些缓存可能持有Class引用，如果不清理：
- 在类重新加载时可能导致内存泄漏
- 在测试环境中尤其重要

### 3. 适用于单例Bean场景

Spring的设计假设：
- 大部分Bean是单例的
- 单例Bean在refresh后不再需要重复创建
- 因此元数据缓存可以安全清理

## 何时不应该清理？

如果应用需要频繁创建原型Bean，清理缓存可能影响性能：

```java
// 自定义ApplicationContext，不清理缓存
public class CustomApplicationContext extends AnnotationConfigApplicationContext {
    
    @Override
    protected void resetCommonCaches() {
        // 不清理缓存，保持性能
        // super.resetCommonCaches();
    }
}
```

但通常情况下，保留默认行为即可。

## 缓存清理的时机

```java
@Override
public void refresh() throws BeansException, IllegalStateException {
    synchronized (this.startupShutdownMonitor) {
        prepareRefresh();

        try {
            // ... 所有初始化步骤
            // 在这些步骤中会使用各种缓存
            finishBeanFactoryInitialization(beanFactory);
            finishRefresh();
        }
        catch (BeansException ex) {
            // 即使失败也要清理
            destroyBeans();
            cancelRefresh(ex);
            throw ex;
        }
        finally {
            // 最后清理缓存
            // 无论成功还是失败都执行
            resetCommonCaches();
        }
    }
}
```

时机选择的原因：
- **在finally块中**：确保无论成功失败都执行
- **在最后一步**：确保所有可能使用缓存的操作都已完成

## 内存影响

根据应用规模，这些缓存可能占用的内存：

| 应用规模 | Bean数量 | 预估缓存大小 |
|----------|----------|--------------|
| 小型 | < 100 | < 1MB |
| 中型 | 100-500 | 1-5MB |
| 大型 | > 500 | 5-20MB |

对于大型应用，清理这些缓存可以节省可观的内存。

## ConcurrentReferenceHashMap

Spring使用ConcurrentReferenceHashMap作为缓存，它支持弱引用和软引用：

```java
// 弱引用缓存（GC时可以回收）
Map<Class<?>, Method[]> cache = new ConcurrentReferenceHashMap<>(256, ReferenceType.WEAK);

// 软引用缓存（内存不足时回收）
Map<Class<?>, Method[]> cache = new ConcurrentReferenceHashMap<>(256, ReferenceType.SOFT);
```

即使不显式清理，GC也可能回收这些缓存，但显式清理更及时。

## 开发和生产环境的差异

### 开发环境
- 可能需要热重载
- 缓存清理很重要，避免内存泄漏
- Spring DevTools会自动处理

### 生产环境
- 应用启动后很少重启
- 缓存清理节省启动后的内存
- 原型Bean较少，影响有限

## 最佳实践

### 1. 保持默认行为
大多数情况下，不需要自定义：

```java
// 推荐：使用默认实现
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 2. 监控内存使用

```java
@Component
public class MemoryMonitor implements ApplicationListener<ContextRefreshedEvent> {
    
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        Runtime runtime = Runtime.getRuntime();
        long usedMemory = runtime.totalMemory() - runtime.freeMemory();
        System.out.println("Memory used after refresh: " + 
                          (usedMemory / 1024 / 1024) + "MB");
    }
}
```

### 3. 大量原型Bean的处理

如果应用有大量原型Bean：

```java
@Configuration
public class PrototypeBeanConfig {
    
    // 考虑使用对象池而不是每次创建
    @Bean
    public GenericObjectPool<MyPrototypeBean> beanPool() {
        return new GenericObjectPool<>(new MyPrototypeBeanFactory());
    }
}
```

## 参考调用栈

```text
resetCommonCaches:1065, AbstractApplicationContext (org.springframework.context.support)
refresh:561, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [AbstractApplicationContext.finishRefresh](AbstractApplicationContext.finishRefresh.md)
- [AbstractApplicationContext.cancelRefresh](AbstractApplicationContext.cancelRefresh.md)

