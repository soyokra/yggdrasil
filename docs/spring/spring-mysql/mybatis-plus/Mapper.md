# mybatis-plus Mapper 源码分析
> 本文深入解读mybatis-plus Mapper的实现原理，MapperScan的注册原理

mybatis通常的用法如下：

定义接口

```java
public interface UserMapper {
    User selectUser(int id);
}
```

定义xml文件

```xml
<mapper namespace="com.example.UserMapper">
    <select id="selectUser" parameterType="int" resultType="User">
        SELECT * FROM users WHERE id = #{id}
    </select>
</mapper>
```

执行

```java
class Test {
    public static void main(String[] args) {
        try (SqlSession session = sqlSessionFactory.openSession()) {
            UserMapper mapper = session.getMapper(UserMapper.class);
            User user = mapper.selectUser(1);
            System.out.println(user);
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
}
```

mapper使用JDK动态代理生成的代理对象，集成Spring就是通过MapperScan注解扫描指定目录的mapper文件集合，生成代理对象，并且注册为Bean

这里的UserMapper实现是代理MapperProxy。

集成到Spring的时候，需要将项目中定义的所有Mapper转换为Proxy，并且注册为Bean。

mybatis通过MapperScan注解扫描mapper接口，注册为bean的时候的是FactoryBean模式将实现类转换为MapperProxy代理，

对于mybatis-plus来说，通过注册SqlSessionTemplate这个bean，将MapperProxy代理替换成自己的MybatisMapperProxy代理

mybatis-plus集成mybatis的时候，使用MybatisMapperProxy

## 主要的调用链路

```text
@MapperScan("com.soyokra.sprival.dao.*.mapper")
=> MapperScan @Import({MapperScannerRegistrar.class})：注册MapperScannerRegistrar
=> MapperScannerRegistrar.registerBeanDefinitions：设置MapperScannerConfigurer属性的basePackage为com.soyokra.sprival.dao.*.mapper
=> MapperScannerConfigurer.postProcessBeanDefinitionRegistry
=> ClassPathMapperScanner.processBeanDefinitions：扫描basePackage生成BeanDefinition，并且设置BeanClass为MapperFactoryBean
=> Mapper注册为Bean的时候，通过MapperFactoryBean的getObject()转到了SqlSessionTemplate.getMapper()
=> SqlSessionTemplate调用的是 getConfiguration().getMapper(type, this)。这个SqlSessionTemplate是mybatis-plus注册的Bean，Configuration是mybatis-plus的
=> 最终通过mybatis-plus的MybatisMapperRegistry执行到MybatisMapperProxyFactory，生成了MybatisMapperProxy代理类作为Mapper接口的实现
```

## MapperScan

@MapperScan("com.soyokra.sprival.dao.*.mapper")设置了需要扫描的包basePackages为"com.soyokra.sprival.dao.*.mapper"

```java
@MapperScan("com.soyokra.sprival.dao.*.mapper")
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@Documented
@Import(MapperScannerRegistrar.class)
@Repeatable(MapperScans.class)
public @interface MapperScan {
    String[] value() default {};
}
```

## MapperScannerRegistrar

- MapperScan注解本身注解了@Import({MapperScannerRegistrar.class})
- MapperScannerRegistrar这个类实现了接口ImportBeanDefinitionRegistrar
- 通过registerBeanDefinitions方法注册MapperScannerConfigurer这个类的BeanDefinition的时候， 把MapperScan注解设置需要扫描的包设置到了MapperScannerConfigurer这个类的属性basePackages

```java
public class MapperScannerRegistrar implements ImportBeanDefinitionRegistrar, ResourceLoaderAware {
    void registerBeanDefinitions(AnnotationMetadata annoMeta, AnnotationAttributes annoAttrs,
                                 BeanDefinitionRegistry registry, String beanName) {

        BeanDefinitionBuilder builder = BeanDefinitionBuilder.genericBeanDefinition(MapperScannerConfigurer.class);

        builder.addPropertyValue("basePackage", StringUtils.collectionToCommaDelimitedString(basePackages));

        registry.registerBeanDefinition(beanName, builder.getBeanDefinition());

    }
}
```

## MapperScannerConfigurer

- MapperScannerConfigurer这个类实现了BeanDefinitionRegistryPostProcessor的接口
- 在postProcessBeanDefinitionRegistry方法里实例化了ClassPathMapperScanner，通过ClassPathMapperScanner进行类文件扫描和BeanDefinition的注册

```java
public class MapperScannerConfigurer 
        implements BeanDefinitionRegistryPostProcessor, InitializingBean, ApplicationContextAware, BeanNameAware {
    @Override
    public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
        ClassPathMapperScanner scanner = new ClassPathMapperScanner(registry);
        scanner.setMapperFactoryBeanClass(this.mapperFactoryBeanClass);
        scanner.scan(StringUtils.tokenizeToStringArray(this.basePackage, ConfigurableApplicationContext.CONFIG_LOCATION_DELIMITERS));
    }
}
```

## ClassPathMapperScanner

对basePackages下的文件进行扫描注册成BeanDefinition，并且设置了BeanDefinition的属性beanClass为MapperFactoryBean

```java
public class ClassPathMapperScanner extends ClassPathBeanDefinitionScanner {
    @Override
    public Set<BeanDefinitionHolder> doScan(String... basePackages) {
        Set<BeanDefinitionHolder> beanDefinitions = super.doScan(basePackages);
        processBeanDefinitions(beanDefinitions);
        return beanDefinitions;
    }

    private void processBeanDefinitions(Set<BeanDefinitionHolder> beanDefinitions) {
        AbstractBeanDefinition definition;
        BeanDefinitionRegistry registry = getRegistry();
        for (BeanDefinitionHolder holder : beanDefinitions) {
            definition = (AbstractBeanDefinition) holder.getBeanDefinition();
            definition.setBeanClass(this.mapperFactoryBeanClass); // this.mapperFactoryBeanClass => MapperFactoryBean
        }
    }
}
```

## MapperFactoryBean

- MapperFactoryBean实现了FactoryBean接口
- Spring将Mapper注册为Bean的时候，用的是MapperFactoryBean的getObject()，这个方法调用到了SqlSessionTemplate.getMapper()

```java
public class MapperFactoryBean<T> extends SqlSessionDaoSupport implements FactoryBean<T> {
    @Override
    public T getObject() throws Exception {
        return getSqlSession().getMapper(this.mapperInterface);
    }

    public SqlSession getSqlSession() {
        return this.sqlSessionTemplate;
    }
}

public abstract class SqlSessionDaoSupport extends DaoSupport {
    public SqlSession getSqlSession() {
        return this.sqlSessionTemplate;
    }
}
```

## SqlSessionTemplate

SqlSessionTemplate调用的是 getConfiguration().getMapper(type, this)。由于这个SqlSessionTemplate是mybatis-plus注册的Bean，Configuration实际上是mybatis-plus
实现的，最终最终通过mybatis-plus的MybatisMapperRegistry执行到MybatisMapperProxyFactory，生成了MybatisMapperProxy代理类作为Mapper接口的实现

```java
public class SqlSessionTemplate implements SqlSession, DisposableBean {
    @Override
    public <T> T getMapper(Class<T> type) {
        return getConfiguration().getMapper(type, this);
    }

    @Override
    public Configuration getConfiguration() {
        return this.sqlSessionFactory.getConfiguration();
    }
}
```

## MybatisPlusAutoConfiguration

mybatis-plus注册SqlSessionFactory 和 SqlSessionTemplate bean

```java
public class MybatisPlusAutoConfiguration implements InitializingBean {

    @Bean
    @ConditionalOnMissingBean
    public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
        MybatisSqlSessionFactoryBean factory = new MybatisSqlSessionFactoryBean();
        factory.setDataSource(dataSource);
        return factory.getObject();
    }

    @Bean
    @ConditionalOnMissingBean
    public SqlSessionTemplate sqlSessionTemplate(SqlSessionFactory sqlSessionFactory) {
        ExecutorType executorType = this.properties.getExecutorType();
        return executorType != null ? new SqlSessionTemplate(sqlSessionFactory, executorType) : new SqlSessionTemplate(sqlSessionFactory);
    }
}
```
