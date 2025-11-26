# SQL执行

mybatis-plus查询方法有三种

一种是继承BaseMapper，可以称之为mybatis-plus内置查询

一种是继承ServiceImpl，这个类的方法是对BaseMapper的增强，底层也是调用BaseMapper的方法，也称之为mybatis-plus内置查询

一种是mybatis方式，即注解和xml。可以称之为mybatis原生方式

无论是通过那种方式执行查询，首先会根据@DS注解进行动态数据源切换。

对于mybatis-plus内置查询，会通过代理的方式用mybatis的SqlSession执行SQL。

执行的SQL由两部分组成，一个是预生成的MappedStatement，也就是SQL模板。一个是Wrapper对象，也就是动态参数。mybatis-plus生成的SQL模板内的占位符不仅仅有查询参数，还有查询字段，SQL片段这种占位符
然后通过Wrapper动态生成where条件，查询字段等替换掉SQL模板的占位符，构成完整的SQL。参见[SQL模板注册](SQL模板注册.md)

SqlSession使用的DataSource是mybatis-plus注入的DynamicRoutingDataSource。DynamicRoutingDataSource底层使用的数据源可以是Hikari, Druid。。。参见[DataSource](DataSource.md)。


## DynamicDataSourceAutoConfiguration

dynamicDatasourceAnnotationAdvisor()方法将DynamicDataSourceAnnotationInterceptor注册为Advisor类型的Bean，DS注解类作为Pointcut

```java
@Slf4j
@Configuration
@EnableConfigurationProperties(DynamicDataSourceProperties.class)
@AutoConfigureBefore(value = DataSourceAutoConfiguration.class, name = "com.alibaba.druid.spring.boot.autoconfigure.DruidDataSourceAutoConfigure")
@Import(value = {DruidDynamicDataSourceConfiguration.class, DynamicDataSourceCreatorAutoConfiguration.class})
@ConditionalOnProperty(prefix = DynamicDataSourceProperties.PREFIX, name = "enabled", havingValue = "true", matchIfMissing = true)
public class DynamicDataSourceAutoConfiguration implements InitializingBean {
    @Role(BeanDefinition.ROLE_INFRASTRUCTURE)
    @Bean
    @ConditionalOnProperty(prefix = DynamicDataSourceProperties.PREFIX + ".aop", name = "enabled", havingValue = "true", matchIfMissing = true)
    public Advisor dynamicDatasourceAnnotationAdvisor(DsProcessor dsProcessor) {
        DynamicDatasourceAopProperties aopProperties = properties.getAop();
        DynamicDataSourceAnnotationInterceptor interceptor = new DynamicDataSourceAnnotationInterceptor(aopProperties.getAllowedPublicOnly(), dsProcessor);
        DynamicDataSourceAnnotationAdvisor advisor = new DynamicDataSourceAnnotationAdvisor(interceptor, DS.class);
        advisor.setOrder(aopProperties.getOrder());
        return advisor;
    }
}
```

## AbstractAdvisorAutoProxyCreator

通过getAdvicesAndAdvisorsForBean为使用了@DS注解的bean创建cglib代理，执行所有方法的时候，都会执行到DynamicDataSourceAnnotationInterceptor

```java
public abstract class AbstractAdvisorAutoProxyCreator extends AbstractAutoProxyCreator {
    @Override
    @Nullable
    protected Object[] getAdvicesAndAdvisorsForBean(
           Class<?> beanClass, String beanName, @Nullable TargetSource targetSource) {

        List<Advisor> advisors = findEligibleAdvisors(beanClass, beanName);
        if (advisors.isEmpty()) {
           return DO_NOT_PROXY;
        }
        return advisors.toArray();
    }
}
```

## DynamicDataSourceAnnotationInterceptor

- DynamicDataSourceAnnotationInterceptor实现MethodInterceptor接口，MethodInterceptor继承自Interceptor接口，Interceptor继承自Advice接口。因此，DynamicDataSourceAnnotationInterceptor就是AOP的Advice

- Spring会调用到DynamicDataSourceAnnotationInterceptor的invoke方法，将当前注解的数据源设置到DynamicDataSourceContextHolder类的当前线程，并且这个线程使用的数据结构是栈

```java
public class DynamicDataSourceAnnotationInterceptor implements MethodInterceptor {
    @Override
    public Object invoke(MethodInvocation invocation) throws Throwable {
        String dsKey = determineDatasourceKey(invocation);
        DynamicDataSourceContextHolder.push(dsKey);
        try {
            return invocation.proceed();
        } finally {
            DynamicDataSourceContextHolder.poll();
        }
    }
}

public final class DynamicDataSourceContextHolder {
    private static final ThreadLocal<Deque<String>> LOOKUP_KEY_HOLDER = new NamedThreadLocal<Deque<String>>("dynamic-datasource") {
        @Override
        protected Deque<String> initialValue() {
            return new ArrayDeque<>();
        }
    };

    public static String push(String ds) {
        String dataSourceStr = StringUtils.isEmpty(ds) ? "" : ds;
        LOOKUP_KEY_HOLDER.get().push(dataSourceStr);
        return dataSourceStr;
    }

    public static void poll() {
        Deque<String> deque = LOOKUP_KEY_HOLDER.get();
        deque.poll();
        if (deque.isEmpty()) {
            LOOKUP_KEY_HOLDER.remove();
        }
    }
}
```

## TradeProvider

- TradeProvider 继承了ServiceImpl，ServiceImpl实现了IService接口。
- TradeProvider.list() => IService.list() => this.getBaseMapper().selectList(queryWrapper)
- getBaseMapper()返回的mapper就是MapperScan扫描并且注册的MybatisMapperProxy代理

```java
@Service
public class TradeProvider extends BaseTblProvider<TradeMapper, Trade> implements TradeContract {

}


public class ServiceImpl<M extends BaseMapper<T>, T> implements IService<T> {
    @Autowired
    protected M baseMapper;

    public M getBaseMapper() {
        return this.baseMapper;
    }
}

public interface IService<T> {
    default List<T> list(Wrapper<T> queryWrapper) {
        return this.getBaseMapper().selectList(queryWrapper);
    }

    default List<T> list() {
        return this.list(Wrappers.emptyWrapper());
    }
}
```

## MybatisMapperProxy

MybatisMapperProxy 的 invoke调用的是MybatisMapperMethod的execute方法，

```java
public class MybatisMapperProxy<T> implements InvocationHandler, Serializable {
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        try {
            if (Object.class.equals(method.getDeclaringClass())) {
                return method.invoke(this, args);
            } else {
                return cachedInvoker(method).invoke(proxy, method, args, sqlSession);
            }
        } catch (Throwable t) {
            throw ExceptionUtil.unwrapThrowable(t);
        }
    }

    private static class PlainMethodInvoker implements MapperMethodInvoker {
        private final MybatisMapperMethod mapperMethod;

        public PlainMethodInvoker(MybatisMapperMethod mapperMethod) {
            super();
            this.mapperMethod = mapperMethod;
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args, SqlSession sqlSession) throws Throwable {
            return mapperMethod.execute(sqlSession, args);
        }
    }
}
```

## MybatisMapperMethod

MybatisMapperMethod的execute()最终调用的是mybatis的sqlSession.select()，这个SqlSession就是之前Datasource适配注册的SqlTemplate

```java
public class MybatisMapperMethod {
    public Object execute(SqlSession sqlSession, Object[] args) {
        Object result;
        switch (command.getType()) {
            case INSERT: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.insert(command.getName(), param));
                break;
            }
            case UPDATE: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.update(command.getName(), param));
                break;
            }
            case DELETE: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.delete(command.getName(), param));
                break;
            }
            case SELECT:
                if (method.returnsVoid() && method.hasResultHandler()) {
                    executeWithResultHandler(sqlSession, args);
                    result = null;
                } else if (method.returnsMany()) {
                    result = executeForMany(sqlSession, args);
                } else if (method.returnsMap()) {
                    result = executeForMap(sqlSession, args);
                } else if (method.returnsCursor()) {
                    result = executeForCursor(sqlSession, args);
                } else {
                    // TODO 这里下面改了
                    if (IPage.class.isAssignableFrom(method.getReturnType())) {
                        result = executeForIPage(sqlSession, args);
                        // TODO 这里上面改了
                    } else {
                        Object param = method.convertArgsToSqlCommandParam(args);
                        result = sqlSession.selectOne(command.getName(), param);
                        if (method.returnsOptional()
                                && (result == null || !method.getReturnType().equals(result.getClass()))) {
                            result = Optional.ofNullable(result);
                        }
                    }
                }
                break;
            case FLUSH:
                result = sqlSession.flushStatements();
                break;
            default:
                throw new BindingException("Unknown execution method for: " + command.getName());
        }
        if (result == null && method.getReturnType().isPrimitive() && !method.returnsVoid()) {
            throw new BindingException("Mapper method '" + command.getName()
                    + " attempted to return null from a method with a primitive return type (" + method.getReturnType() + ").");
        }
        return result;
    }
}   
```

## ibatis执行

通过ASTProperty类和反射的方式执行到mybatis-plus的AbstractWrapper方法

```java
public class ASTProperty extends SimpleNode implements NodeType {
    protected Object getValueBody(OgnlContext context, Object source) throws OgnlException {
        Object property = this.getProperty(context, source);
        Object result = OgnlRuntime.getProperty(context, source, property);
        if (result == null) {
            result = OgnlRuntime.getNullHandler(OgnlRuntime.getTargetClass(source)).nullPropertyValue(context, source, property);
        }

        return result;
    }
}

public abstract class AbstractWrapper<T, R, Children extends AbstractWrapper<T, R, Children>> extends Wrapper<T>
        implements Compare<Children, R>, Nested<Children, Children>, Join<Children>, Func<Children, R> {
    @Override
    public MergeSegments getExpression() {
        return expression;
    }

    public Map<String, Object> getParamNameValuePairs() {
        return paramNameValuePairs;
    }
}
```
